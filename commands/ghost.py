import discord
from discord import app_commands
from discord.ext import commands

from utils.helpers import log_command
from views import PingPanel


class GhostCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="ghostping", description="ghostping a user or everyone.")
    @app_commands.describe(user="The user to ping")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def ghostping(self, interaction: discord.Interaction, user: discord.User):
        await interaction.response.defer(ephemeral=True, thinking=True)
        await interaction.followup.send(view=PingPanel(user.id), ephemeral=True)
        await log_command(interaction, "ghost ping", f"user ghost-pinged: {user.id}")

    @app_commands.command(name="ghostsay", description="say something then delete")
    @app_commands.describe(text="The text for the bot to say")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def ghostsay(self, interaction: discord.Interaction, text: str):
        await interaction.response.defer(ephemeral=True)
        loading_msg = await interaction.followup.send("⏳ Sending...", ephemeral=True)
        message = await interaction.followup.send(text)
        await message.delete()
        await log_command(interaction, "ghost say", f"user ghost-said: {text}")


async def setup(bot: commands.Bot):
    await bot.add_cog(GhostCog(bot))
