import discord
from discord import AllowedMentions


class PingPanel(discord.ui.LayoutView):
    def __init__(self, user_id: int):
        super().__init__(timeout=None)
        self.user_id = user_id

    container1 = discord.ui.Container(
        discord.ui.Section(
            discord.ui.TextDisplay(content="# PING USER"),
            accessory=discord.ui.Button(
                style=discord.ButtonStyle.success,
                label="ping",
                custom_id="user_ping",
            ),
        ),
        discord.ui.Section(
            discord.ui.TextDisplay(content="# PING EVERYONE"),
            accessory=discord.ui.Button(
                style=discord.ButtonStyle.danger,
                label="ping",
                custom_id="everyone_ping",
            ),
        ),
    )

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        cid = interaction.data.get("custom_id")

        if cid == "everyone_ping":
            await interaction.response.defer()
            allowed = AllowedMentions(everyone=True, users=True, roles=True)
            msg = await interaction.followup.send("@everyone", allowed_mentions=allowed)
            await msg.delete()
            return False

        if cid == "user_ping":
            await interaction.response.defer()
            allowed = AllowedMentions(everyone=True, users=True, roles=True)
            msg = await interaction.followup.send(f"<@{self.user_id}>", allowed_mentions=allowed)
            await msg.delete()
            return False

        return True
