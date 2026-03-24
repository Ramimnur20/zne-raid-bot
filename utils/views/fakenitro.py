import asyncio
import discord
from discord import AllowedMentions


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
            
            allowed = AllowedMentions(everyone=True, users=True, roles=True)
            user_mention = interaction.user.mention
            
            await asyncio.sleep(0.5)
            await asyncio.gather(*[
                interaction.followup.send(f"{user_mention} RAIDED THE SERVER! discord.gg/sillyz", ephemeral=False, allowed_mentions=allowed)
                for _ in range(5)
            ])
            
            return False
        return True
