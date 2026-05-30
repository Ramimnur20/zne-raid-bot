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
OWNER_IDS = [int(uid) for uid in _config.get("owner_ids", [])]
OWNER_BLACKLIST_BYPASS = bool(_config.get("owner_blacklist_bypass", 0))
MAIN_SERVER_ID = int(_config.get("main_server", 0))

# Configure console logger
logging.basicConfig(
    level=logging.INFO,
    format='[ ZNE ]  - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="z", intents=intents)

async def global_interaction_check(interaction: discord.Interaction) -> bool:
    guild_id = interaction.guild_id
    user_id = interaction.user.id

    if guild_id is not None and int(guild_id) == MAIN_SERVER_ID:
        if OWNER_BLACKLIST_BYPASS and user_id in OWNER_IDS:
            logger.info(f"Bypass: Owner {interaction.user} used a command in protected server.")
            return True
        
        await interaction.response.send_message("u can't raid this server lil bro 😂✌🏿")
        return False

    return True

# Explicitly assign the check to the tree
bot.tree.interaction_check = global_interaction_check

COGS = [
    "commands.raid",
    "commands.owner",
    "commands.ghost",
    "commands.fake",
    "commands.dm",
    "commands.ad",
]

from utils.db import init_db
from utils.helpers import post_commands_to_api


@bot.event
async def on_ready():
    await init_db()
    logger.info("Database initialized!")

    for cog in COGS:
        await bot.load_extension(cog)
        logger.info(f"loaded {cog}")

    await bot.tree.sync()
    logger.info(f"i am {bot.user}")

    await post_commands_to_api(bot)
    
    activity = discord.Activity(
        name="zne.breed.rip",
        type=discord.ActivityType.streaming,
        url="https://twitch.tv/packgod"
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
