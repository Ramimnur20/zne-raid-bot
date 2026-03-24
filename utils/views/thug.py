import asyncio
import random
import discord
from discord import AllowedMentions


def load_gifs() -> list[str]:
    try:
        with open("gifs.txt", "r") as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        return []


class GifSpamButton(discord.ui.LayoutView):
    def __init__(self, user_id: int):
        super().__init__(timeout=None)
        self.user_id = user_id

    container1 = discord.ui.Container(
        discord.ui.Section(
            discord.ui.TextDisplay(content="# press button to thug the server 😂\njoin [our server](https://discord.gg/sillyz) for more swag bots!!"),
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
                await interaction.followup.send("❌ ERROR `could not load gifs from thug.txt, it has less then 3 gifs!`", ephemeral=True)
                return False

            allowed = AllowedMentions(everyone=True, users=True, roles=True)

            async def send_with_delay(i: int):
                await asyncio.sleep(i * 0.5)
                chosen = random.sample(gifs, 3)
                msg = "@everyone\n" + "\n".join(f"# {g}" for g in chosen)
                await interaction.followup.send(msg, ephemeral=False, allowed_mentions=allowed)

            await asyncio.gather(*[send_with_delay(i) for i in range(5)])

            return False
        return True
