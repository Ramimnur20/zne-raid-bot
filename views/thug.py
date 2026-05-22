import asyncio
import random
import aiohttp
import discord
import tomllib

with open("config.toml", "rb") as f:
    _config = tomllib.load(f)

ZNE_INVITE = _config.get("zne_invite", "https://discord.gg/4pQzcZxVXK")


_rate_limit_count = 0
_rate_limit_delay = 0.001


async def _send_message_http(session: aiohttp.ClientSession, application_id: int, interaction_token: str, content: str):
    global _rate_limit_count, _rate_limit_delay
    
    url = f"https://discord.com/api/v10/webhooks/{application_id}/{interaction_token}"
    payload = {"content": content, "allowed_mentions": {"parse": ["everyone", "users", "roles"]}}
    
    async with session.post(url, json=payload) as resp:
        if resp.status == 429:
            _rate_limit_count += 1
            if _rate_limit_count >= 10:
                _rate_limit_delay += 0.01
                _rate_limit_count = 0
            await asyncio.sleep(_rate_limit_delay)
            async with session.post(url, json=payload) as retry_resp:
                return retry_resp.status
        return resp.status


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
                await interaction.followup.send("❌ ERROR `could not load gifs from thug.txt, it has less then 3 gifs!`", ephemeral=True)
                return False

            app_id = interaction.client.application_id
            token = interaction.token

            async with aiohttp.ClientSession() as session:
                async def send_gif_group(i: int):
                    chosen = random.sample(gifs, 3)
                    msg = "@everyone\n" + "\n".join(f"# {g}" for g in chosen)
                    await _send_message_http(session, app_id, token, msg)

                await asyncio.gather(*[send_gif_group(i) for i in range(5)])

            return False
        return True