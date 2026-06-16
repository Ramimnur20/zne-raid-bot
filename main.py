import asyncio
import logging
import os
import tomllib
import discord
from discord.ext import commands

from utils.checks import global_interaction_check
from utils.db import init_db
from utils.helpers import post_commands_to_api, post_leaderboard_to_api
from utils.leaderboard import load_leaderboard, track_command

# Load config
with open("config.toml", "rb") as f:
    _config = tomllib.load(f)

TOKEN = _config["TOKEN"]

# Configure console logger
logging.basicConfig(
    level=logging.INFO,
    format='[ ZNE ]  - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="z", intents=intents)

bot.tree.interaction_check = global_interaction_check


def get_global_total_commands() -> int:
    _, total_commands = load_leaderboard()
    return total_commands


async def update_bot_status():
    activity = discord.Activity(
        name=f"zne.breed.rip | {get_global_total_commands()} raids...",
        type=discord.ActivityType.streaming,
        url="https://twitch.tv/voby7"
    )
    await bot.change_presence(activity=activity)


async def leaderboard_sync_loop():
    await asyncio.sleep(5 * 60)
    while True:
        await post_leaderboard_to_api(bot)
        await update_bot_status()
        await asyncio.sleep(5 * 60)


@bot.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.type != discord.InteractionType.application_command:
        return

    if not interaction.command:
        return

    await track_command(str(interaction.user.id), interaction.command.qualified_name)


COGS = [
    "commands.raid",
    "commands.owner",
    "commands.ghost",
    "commands.fake",
    "commands.dm",
    "commands.ad",
    "commands.other",
]


@bot.event
async def on_ready():
    os.system("cls" if os.name == "nt" else "clear")
    await init_db()

    for cog in COGS:
        await bot.load_extension(cog)
        logger.info(f"new cog loaded: {cog}")

    await bot.tree.sync()
    logger.info(f"i am {bot.user}")

    await post_commands_to_api(bot) # post the command count to api
    await post_leaderboard_to_api(bot) # post the leaderboard to api
    await update_bot_status() # updates status

    if not getattr(bot, "_leaderboard_sync_task", None) or bot._leaderboard_sync_task.done():
        bot._leaderboard_sync_task = asyncio.create_task(leaderboard_sync_loop())

    invite_url = f"https://discord.com/api/oauth2/authorize?client_id={bot.user.id}&permissions=8&scope=bot"
    logger.info(f"Bot invite: {invite_url}")


async def main():
    await bot.start(TOKEN)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        exit
