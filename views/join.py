import discord
import tomllib

with open("config.toml", "rb") as f:
    _config = tomllib.load(f)

REQUIRED_SERVER_ID = _config["server"]["required_server_id"]
VERIFIED_ROLE_ID = _config["server"]["verified_role_id"]
ZNE_INVITE = _config.get("zne_invite", "https://discord.gg/RqTCnuyhGN")


class JoinMessage(discord.ui.LayoutView):
    container1 = discord.ui.Container(
        discord.ui.Section(
            discord.ui.TextDisplay(content="# YOU MUST BE IN THE SERVER TO USE THE BOT!"),
            accessory=discord.ui.Thumbnail(
                media="https://cdn.discordapp.com/icons/1486292011152576644/3eaa8659d83e16f0c028a172e5c2f749.png?size=1024",
            ),
        ),
        discord.ui.ActionRow(
                discord.ui.Button(
                    url=ZNE_INVITE,
                    style=discord.ButtonStyle.link,
                    label="JOIN",
                ),
        ),
    )


class VerifiedRoleMessage(discord.ui.LayoutView):
    container1 = discord.ui.Container(
        discord.ui.Section(
            discord.ui.TextDisplay(content="# YOU MUST BE VERIFIED TO USE THE BOT!\nGet the verified role in the server first."),
            accessory=discord.ui.Thumbnail(
                media="https://cdn.discordapp.com/icons/1486292011152576644/3eaa8659d83e16f0c028a172e5c2f749.png?size=1024",
            ),
        ),
        discord.ui.ActionRow(
                discord.ui.Button(
                    url=ZNE_INVITE,
                    style=discord.ButtonStyle.link,
                    label="JOIN",
                ),
        ),
    )
