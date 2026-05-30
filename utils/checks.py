import discord
import tomllib
from discord import app_commands

with open("config.toml", "rb") as f:
    _config = tomllib.load(f)

OWNER_IDS = _config["owner_ids"]
OWNER_BLACKLIST_BYPASS = _config.get("owner_blacklist_bypass", 1)


def is_owner(interaction: discord.Interaction) -> bool:
    return interaction.user.id in OWNER_IDS
