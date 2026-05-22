import asyncio
import logging
import tomllib
import discord
from discord import app_commands
from discord.ext import commands

# Load config
with open("config.toml", "rb") as f:
    _config = tomllib.load(f)

TOKEN = _config["TOKEN"]
REQUIRED_SERVER_ID = _config["server"]["required_server_id"]
VERIFIED_ROLE_ID = _config["server"]["verified_role_id"]

# Configure console logger
logging.basicConfig(
    level=logging.INFO,
    format='[ ZNE ]  - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="z", intents=intents)

@bot.event
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CheckFailure):
        try:
            await interaction.response.send_message("❌ You or this server is blacklisted from using the bot.", ephemeral=True)
        except discord.InteractionResponded:
            await interaction.followup.send("❌ You or this server is blacklisted from using the bot.", ephemeral=True)


COGS = [
    "commands.raid",
    "commands.owner",
    "commands.ghost",
    "commands.fake",
    "commands.dm",
    "commands.ad",
    "commands.lag",
]

from utils.db import init_db
from views import JoinMessage, VerifiedRoleMessage
from utils.globals import command_count, save_command_count
from utils.helpers import post_commands_to_api


@bot.event
async def on_ready():
    await init_db()
    logger.info("Database initialized!")

    for cog in COGS:
        await bot.load_extension(cog)
        logger.info(f"Loaded cog: {cog}")

    await bot.tree.sync()
    logger.info(f"Logged in as {bot.user}")

    await post_commands_to_api(bot)
    
    activity = discord.Activity(
        name=f"{command_count} raids...",
        type=discord.ActivityType.streaming,
        url="https://twitch.tv"
    )
    await bot.change_presence(activity=activity)

    invite_url = f"https://discord.com/api/oauth2/authorize?client_id={bot.user.id}&permissions=8&scope=bot"
    logger.info(f"Bot invite: {invite_url}")


async def main():
    await bot.start(TOKEN)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot has been shut down.")
