import asyncio
import logging
import os
import psutil
import discord
from discord.ext import commands, tasks

# Configure console logger
logging.basicConfig(
    level=logging.INFO,
    format='[ ZNE ] %(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

from utils.config import TOKEN
from utils.db import init_db, is_server_blacklisted, is_user_blacklisted
from utils.views import JoinMessage, REQUIRED_SERVER_ID
from utils.globals import command_count


intents = discord.Intents.default()
intents.guilds = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)


async def global_blacklist_check(interaction: discord.Interaction) -> bool:
    if interaction.guild_id and await is_server_blacklisted(interaction.guild_id):
        await interaction.followup.send("❌ `Cannot use this command in this server`", ephemeral=True)
        return False
    
    if await is_user_blacklisted(interaction.user.id):
        await interaction.followup.send("😡 You are blacklisted from using this bot.", ephemeral=True)
        return False
    
    # Increment command count
    global command_count
    command_count += 1
    
    # Check if user is in required server
    required_server = bot.get_guild(REQUIRED_SERVER_ID)
    if required_server is None:
        # Bot is not in the required server, cannot verify membership
        logger.warning(f"Bot is not in required server {REQUIRED_SERVER_ID}")
        return True
    
    try:
        # Try fetching from API first (more reliable for recently joined members)
        try:
            member = await required_server.fetch_member(interaction.user.id)
        except discord.NotFound:
            member = None
        except discord.Forbidden:
            logger.warning(f"Bot lacks permission to fetch member {interaction.user.id}")
            # Allow the command if we can't check
            return True
        
        if member is None:
            await interaction.followup.send(view=JoinMessage(), ephemeral=True)
            return False
    except Exception as e:
        logger.error(f"Error checking membership: {e}")
        # Allow the command on error
        return True
    
    return True

bot.tree.interaction_check = global_blacklist_check

COGS = [
    "cogs.raid",
    "cogs.owner",
    "cogs.ghost",
    "cogs.fake",
    "cogs.dm",
    "cogs.ad",
    "cogs.api",
]

INFO_CHANNEL_ID = 1477953681377853483


async def send_info_embed():
    """Send the info embed to the designated channel."""
    channel = bot.get_channel(INFO_CHANNEL_ID)
    if not channel:
        logger.warning(f"Could not find channel {INFO_CHANNEL_ID}")
        return
    
    # Get system stats
    process = psutil.Process(os.getpid())
    ram_usage = process.memory_info().rss / 1024 / 1024
    cpu_usage = process.cpu_percent()
    
    # Get libraries
    try:
        with open("requirements.txt", "r") as f:
            libs = [line.strip() for line in f if line.strip()]
            libs_formatted = "\n - ".join(libs)
    except:
        libs_formatted = "discord.py"
    
    # Get bot info
    bot_server_count = len(bot.guilds)
    
    # Get ZNE server member count
    zne_server = bot.get_guild(1459804477770039386)
    zne_member_count = zne_server.member_count if zne_server else "Server Teminated."
    
    # Get total synced commands
    total_synced_commands = len(bot.tree.get_commands())
    
    info_content = "## ☣ - BOT INFO\n" \
        "made by [voby7](https://voby.page.gd/) for [zne](https://discord.gg/sillyz)\n" \
        f"zne member count: **{zne_member_count}**\n" \
        f"bot server count: **{bot_server_count}**\n" \
        "bot was made in **June 2025**\n" \
        "this is the **raid** bot\n" \
        f"total commands synced: **{total_synced_commands}**\n" \
        f"total commands executed: **{command_count}**\n" \
        f"ram usage: **{ram_usage:.2f} MB**\n" \
        f"cpu usage: **{cpu_usage:.2f}%**\n\n" \
        f"libraries installed: \n - {libs_formatted}\n\n" \
        "language: **python**"
    
    class InfoView(discord.ui.LayoutView):
        container1 = discord.ui.Container(
            discord.ui.Section(
                discord.ui.TextDisplay(content=info_content),
                accessory=discord.ui.Thumbnail(
                    media="https://dnvsrzeijhduiqsrlkmc.supabase.co/storage/v1/object/public/hosted-files/54a084b2-a7e6-4415-81e9-cd4052d91c58/VI2Whjcx_206f5b851a8ad773cd5712f497583f6a.jpg?download=206f5b851a8ad773cd5712f497583f6a.jpg",
                ),
            ),
        )
    
    view = InfoView()
    
    try:
        await channel.send(view=view)
        logger.info("Info embed sent successfully")
    except Exception as e:
        logger.error(f"Failed to send info embed: {e}")


@tasks.loop(hours=6)
async def auto_send_info():
    """Task to send info embed every 6 hours."""
    await send_info_embed()


@bot.event
async def on_ready():
    await init_db()
    logger.info("Database initialized!")

    for cog in COGS:
        await bot.load_extension(cog)
        logger.info(f"Loaded cog: {cog}")

    await bot.tree.sync()
    logger.info(f"Logged in as {bot.user}")
    
    # Start the auto-send info task
    auto_send_info.start()


async def main():
    try:
        await bot.start(TOKEN)
    except KeyboardInterrupt:
        pass
    finally:
        if not bot.is_closed():
            await bot.close()
        print("Bot has been shut down.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot has been shut down.")
