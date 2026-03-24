import discord


REQUIRED_SERVER_ID = 1459804477770039386


class JoinMessage(discord.ui.LayoutView):
    container1 = discord.ui.Container(
        discord.ui.Section(
            discord.ui.TextDisplay(content="# YOU MUST BE IN THE SERVER TO USE THE BOT!"),
            accessory=discord.ui.Thumbnail(
                media="https://images-ext-1.discordapp.net/external/SdF5jJ6M8ZzTSiGNeNXAW4DOkxvo6puA8S6L3wdv0JQ/%3Fsize%3D1024/https/cdn.discordapp.com/icons/1459804477770039386/a_3a7ef8bea173246c3b7383b3cf536158.gif?width=288&height=288",
            ),
        ),
        discord.ui.ActionRow(
                discord.ui.Button(
                    url="https://discord.gg/sillyz",
                    style=discord.ButtonStyle.link,
                    label="JOIN",
                ),
        ),
    )
