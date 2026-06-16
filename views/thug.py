import asyncio
import random
import aiohttp
import discord
from utils.constants import CROSS
from utils.helpers import send_message_http, ZNE_INVITE

def load_gifs() -> list[str]:
    try:
        with open("gifs.txt", "r") as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        return []


class ThugView(discord.ui.LayoutView):
    def __init__(self, user_id: int):
        super().__init__(timeout=None)
        self.user_id = user_id

    container1 = discord.ui.Container(
        discord.ui.Section(
            discord.ui.TextDisplay(content=f"# press button to thug the server 😂\njoin [our server]({ZNE_INVITE}) for more swag bots!!"),
            accessory=discord.ui.Button(
                style=discord.ButtonStyle.primary,
                label="Send",
                custom_id="gif_spam_send_button"
            )
        )
    )

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.data.get("custom_id") == "gif_spam_send_button":
            await interaction.response.defer()

            gifs = load_gifs()
            if len(gifs) < 3:

                await interaction.followup.send(f"{CROSS} ERROR `could not load gifs from thug.txt, it has less than 3 gifs!`", ephemeral=True)
                return False

            app_id = interaction.client.application_id
            token = interaction.token

            async with aiohttp.ClientSession() as session:
                async def send_gif_group():
                    chosen = random.sample(gifs, 3)
                    msg = "@everyone\n" + "\n".join(f"# {g}" for g in chosen)
                    await send_message_http(session, app_id, token, msg)

                await asyncio.gather(*[send_gif_group() for _ in range(5)])

            return False
        return True