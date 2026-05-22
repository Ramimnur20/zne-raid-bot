import discord
import tomllib
import logging
import aiohttp
from discord.ext import commands

with open("config.toml", "rb") as f:
    _config = tomllib.load(f)

OWNER_IDS = _config["owner_ids"]
LOG_CHANNEL_ID = _config["channels"]["log_channel_id"]

# Shared state for farm tokens: {user_id: [token, ...]}
user_farm_tokens: dict[int, list[str]] = {}


def is_owner(interaction: discord.Interaction) -> bool:
    return interaction.user.id in OWNER_IDS


async def log_command(interaction: discord.Interaction, name: str, details: str):
    username = interaction.user.name
    user_mention = interaction.user.mention
    avatar_url = interaction.user.display_avatar.url
    channel = interaction.client.get_channel(LOG_CHANNEL_ID)
    if not channel:
        return

    class Components(discord.ui.LayoutView):
        container1 = discord.ui.Container(
            discord.ui.Section(
                discord.ui.TextDisplay(
                    content=f"# COMMAND USED\n\nuser: `{username}` ({user_mention})\ncommand `{name}`"
                ),
                accessory=discord.ui.Thumbnail(
                    media=avatar_url
                ),
            ),
            discord.ui.Separator(visible=True, spacing=discord.SeparatorSpacing.small),
            discord.ui.TextDisplay(content=f"details:\n```{details}```"),
        )

    view = Components()
    try:
        await channel.send(view=view)
    except Exception:
        try:
            await channel.send(
                f"# COMMAND USED\n\nuser: `{username}` ({user_mention})\ncommand `{name}`\n\ndetails:\n```{details}```"
            )
        except Exception:
            pass


# API posting for web command list (used by on_ready and x-updatecmd)
API_CONFIG = _config.get("api", {})
API_URL = API_CONFIG.get("url", "https://zne-website.vercel.app/api/commands")
API_SECRET = API_CONFIG.get("secret", "")

api_logger = logging.getLogger(__name__)


async def post_commands_to_api(bot: commands.Bot):
    if not API_URL or not API_SECRET:
        api_logger.warning("API URL or secret not configured, skipping web command update")
        return

    CATEGORY_MAP = {
        "ra1d": "Raiding",
        "interaction-ra1d": "Raiding",
        "custom_ra1d": "Raiding",
        "thug": "Raiding",
        "blame": "Raiding",
        "say": "Raiding",
        "spam": "Raiding",
        "filespam": "Raiding",
        "info": "Raiding",
        "ad": "Advertisement",
        "lag": "Lag",
        "dmanon": "Direct Messages",
        "dmflood": "Direct Messages",
        "dmblacklist": "Direct Messages",
        "x-blacklist-server": "Owner",
        "x-blacklist-user": "Owner",
        "x-setmessage": "Owner",
        "x-reload-cogs": "Owner",
        "x-leaveall": "Owner",
        "x-updatecmd": "Owner",
        "fakenitro": "Fake",
        "fakemessage": "Fake",
        "ghostping": "Ghost",
        "ghostsay": "Ghost",
    }

    commands_list = []
    for cmd in bot.tree.get_commands():
        if hasattr(cmd, "name") and hasattr(cmd, "description"):
            cat = CATEGORY_MAP.get(cmd.name, "Other")
            commands_list.append({
                "name": cmd.name,
                "description": cmd.description or "No description.",
                "category": cat
            })

    if not commands_list:
        return

    payload = {
        "commands": commands_list,
        "secret": API_SECRET
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(API_URL, json=payload, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    api_logger.info(f"Posted {data.get('count', len(commands_list))} commands to web API successfully")
                else:
                    text = await resp.text()
                    api_logger.warning(f"Failed to post commands to API: HTTP {resp.status} - {text}")
    except Exception as e:
        api_logger.error(f"Error posting commands to API: {e}")
