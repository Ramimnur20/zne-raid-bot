import discord
import tomllib
from discord import app_commands

with open("config.toml", "rb") as f:
    _config = tomllib.load(f)

OWNER_IDS = _config["owner_ids"]
OWNER_BLACKLIST_BYPASS = _config.get("owner_blacklist_bypass", 1)


def is_owner(interaction: discord.Interaction) -> bool:
    return interaction.user.id in OWNER_IDS


async def enforce_blacklist(interaction: discord.Interaction) -> bool:
    if is_owner(interaction) and OWNER_BLACKLIST_BYPASS == 1:
        return True
    if interaction.guild_id:
        from utils.db import is_server_blacklisted
        if await is_server_blacklisted(interaction.guild_id):
            raise app_commands.CheckFailure("Server blacklisted")
    from utils.db import is_user_blacklisted
    if await is_user_blacklisted(interaction.user.id):
        raise app_commands.CheckFailure("User blacklisted")
    return True
