import discord
import tomllib

with open("config.toml", "rb") as f:
    _config = tomllib.load(f)

REQUIRED_SERVER_ID = _config["server"]["main_server"]
VERIFIED_ROLE_ID = _config["server"]["verified_role_id"]
ZNE_INVITE = _config.get("zne_invite", "https://discord.gg/4pQzcZxVXK")

FALLBACK_ICON = "https://zne.breed.rip/assets/zne.png"


def get_access_denied_view(bot: discord.ClientUser) -> discord.ui.LayoutView:
    if bot and hasattr(bot, "display_avatar") and bot.display_avatar and bot.display_avatar.url:
        avatar_url = bot.display_avatar.url
    else:
        avatar_url = FALLBACK_ICON

    class Components(discord.ui.LayoutView):
        container1 = discord.ui.Container(
            discord.ui.Section(
                discord.ui.TextDisplay(content="# **access denied**\nyou need to be verified and in the server in order to use this bot."),
                accessory=discord.ui.Thumbnail(
                    media=avatar_url,
                ),
            ),
            discord.ui.Separator(visible=True, spacing=discord.SeparatorSpacing.small),
            discord.ui.ActionRow(
                    discord.ui.Button(
                        url=ZNE_INVITE,
                        style=discord.ButtonStyle.link,
                        label="join",
                    ),
            ),
        )

    return Components()
