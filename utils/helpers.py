import discord
import tomllib
import logging
import aiohttp
from discord.ext import commands
from utils.leaderboard import load_leaderboard

with open("config.toml", "rb") as f:
    _config = tomllib.load(f)

OWNER_IDS = [int(uid) for uid in _config.get("owner_ids", [])]
LOG_CHANNEL_ID = _config["channels"]["log_channel_id"]
ZNE_INVITE = _config.get("zne_invite", "https://discord.gg/4pQzcZxVXK")


user_farm_tokens: dict[int, list[str]] = {}


async def log_command(interaction: discord.Interaction, name: str, details: str):
    username = interaction.user.name
    user_mention = interaction.user.mention
    avatar_url = interaction.user.display_avatar.url
    channel = interaction.client.get_channel(LOG_CHANNEL_ID)

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
    await channel.send(view=view)


API_CONFIG = _config.get("api", {})
API_URL = API_CONFIG.get("url", "https://zne-website.vercel.app/api/commands")
API_SECRET = API_CONFIG.get("secret", "")


def _default_leaderboard_url() -> str:
    if API_URL.endswith("/api/commands"):
        return API_URL[:-len("/api/commands")] + "/api/leaderboard"
    return API_URL.rstrip("/") + "/leaderboard"


API_LEADERBOARD_URL = API_CONFIG.get("leaderboard_url", _default_leaderboard_url())
API_LEADERBOARD_SECRET = API_CONFIG.get("leaderboard_secret", API_SECRET)

api_logger = logging.getLogger(__name__)


async def post_commands_to_api(bot: commands.Bot):
    if not API_SECRET:
        api_logger.info("Skipping web command update (api.secret not configured)")
        return

    commands_list = []
    for cmd in bot.tree.get_commands():
        if hasattr(cmd, "name") and hasattr(cmd, "description"):
            if cmd.binding:
                cat = getattr(cmd.binding, "qualified_name", cmd.binding.__class__.__name__)

                if cat.endswith("Cog"):
                    cat = cat[:-3]
            else:
                cat = "Other"

            arguments = []
            if hasattr(cmd, "parameters") and cmd.parameters:
                for param in cmd.parameters:
                    desc = getattr(param, "_describe", None) or getattr(param, "description", None) or ""
                    default = getattr(param, "default", None)
                    required = default is None

                    arguments.append({
                        "name": param.name,
                        "description": desc,
                        "required": required
                    })

            commands_list.append({
                "name": cmd.name,
                "description": cmd.description or "No description.",
                "category": cat,
                "arguments": arguments
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


async def post_leaderboard_to_api(bot: commands.Bot):
    if not API_LEADERBOARD_SECRET or not API_LEADERBOARD_URL:
        api_logger.info("Skipping web leaderboard update (api.leaderboard_secret or api.leaderboard_url not configured)")
        return

    data, global_total = load_leaderboard()
    if not data:
        api_logger.info("Skipping web leaderboard update (leaderboard.json is empty)")
        return

    users = []
    ignored_keys = {"userid", "user_id", "id", "total_commands"}

    for user_id, entry in sorted(data.items(), key=lambda item: int(item[1].get("total_commands", 0)), reverse=True):
        total_commands = int(entry.get("total_commands", 0))
        command_counts = {
            str(name): int(count)
            for name, count in entry.items()
            if name not in ignored_keys and int(count) > 0
        }

        user_payload = {
            "userid": str(user_id),
            "total_commands": total_commands,
            "commands": command_counts,
        }

        try:
            discord_user = await bot.fetch_user(int(user_id))
            user_payload.update({
                "username": discord_user.name,
                "display_name": discord_user.display_name,
                "avatar_url": discord_user.display_avatar.url,
            })
        except Exception as e:
            api_logger.debug(f"Could not fetch Discord user {user_id} for leaderboard: {e}")

        users.append(user_payload)

    payload = {
        "global_total_commands": global_total,
        "users": users,
        "secret": API_LEADERBOARD_SECRET,
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(API_LEADERBOARD_URL, json=payload, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 200:
                    api_logger.info(f"Posted leaderboard for {len(users)} users to web API successfully")
                else:
                    text = await resp.text()
                    api_logger.warning(f"Failed to post leaderboard to API: HTTP {resp.status} - {text}")
    except Exception as e:
        api_logger.error(f"Error posting leaderboard to API: {e}")


async def send_message_http(session: aiohttp.ClientSession, application_id: int, interaction_token: str, content: str):
    """
    Sends an HTTP message to a Discord webhook.
    """
    url = f"https://discord.com/api/v10/webhooks/{application_id}/{interaction_token}"
    payload = {"content": content, "allowed_mentions": {"parse": ["everyone", "users", "roles"]}}
    async with session.post(url, json=payload) as resp:
        return resp.status
