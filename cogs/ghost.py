import asyncio
import discord
from discord import app_commands
from discord.ext import commands

from utils.helpers import log_command
from utils.views import PingPanel


class GhostCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    ghost_group = app_commands.Group(name="ghost", description="Ghost commands")

    @ghost_group.command(name="ping", description="Ghostping a user or everyone.")
    @app_commands.describe(user="The user to ping")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def ping(self, interaction: discord.Interaction, user: discord.User):
        await interaction.response.send_message(view=PingPanel(user.id), ephemeral=True)
        await log_command(interaction, "ghost ping", f"user ghost-pinged: {user.id}")

    @ghost_group.command(name="say", description="Make the bot say something and delete it after 1 second.")
    @app_commands.describe(text="The text for the bot to say")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def say(self, interaction: discord.Interaction, text: str):
        await interaction.response.defer(ephemeral=True)
        loading_msg = await interaction.followup.send("⏳ Sending...", ephemeral=True)
        message = await interaction.followup.send(text)
        await asyncio.sleep(0.2)
        await message.delete()
        await loading_msg.delete()
        await log_command(interaction, "ghost say", f"user ghost-said: {text}")


async def setup(bot: commands.Bot):
    await bot.add_cog(GhostCog(bot))
