import discord
import re
import tomllib
from discord import app_commands
from discord.ext import commands

from utils.db import (
    set_global_default_message,
)
from utils.helpers import log_command, post_commands_to_api

with open("config.toml", "rb") as f:
    _config = tomllib.load(f)

ZNE_INVITE = _config.get("zne_invite", "https://discord.gg/4pQzcZxVXK")


class OwnerCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="x-setmessage", description="set global msg")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def setmessage(self, interaction: discord.Interaction):
        class SetGlobalMessageModal(discord.ui.Modal, title="Set Global Default Message"):
            message_input = discord.ui.TextInput(
                label="Global default message",
                style=discord.TextStyle.paragraph,
                placeholder="Enter the message that will be used by default for all commands"
            )

            async def on_submit(self2, modal_interaction: discord.Interaction):
                text = self2.message_input.value
                if "discord.gg/" in text.lower():
                    text = re.sub(r'(?:https?://)?discord\.gg/\S+', ZNE_INVITE, text)
                
                await set_global_default_message(text)
                await modal_interaction.response.send_message("Global default message has been set!", ephemeral=True)
                await log_command(interaction, "setmessage", f"New global message: {text}")

        await interaction.response.send_modal(SetGlobalMessageModal())

    @app_commands.command(name="x-reload-cogs", description="reload cogs")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def reload_cogs(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        cogs_to_reload = ["commands.raid", "commands.owner", "commands.ghost", "commands.fake", "commands.dm", "commands.ad"]
        reloaded = []
        failed = []
        
        for cog in cogs_to_reload:
            try:
                await self.bot.reload_extension(cog)
                reloaded.append(cog)
            except Exception as e:
                failed.append(f"{cog}: {e}")
        
        result = f"<:checkmark:1502219659074863185> Reloaded **{len(reloaded)}** cogs: {', '.join(reloaded)}"
        if failed:
            result += f"\n<:cross:1502219725063852092> Failed to reload **{len(failed)}** cogs: {', '.join(failed)}"
        
        await interaction.followup.send(result, ephemeral=True)
        await log_command(interaction, "reload-cogs", f"Reloaded {len(reloaded)} cogs")

    @app_commands.command(name="x-updatecmd", description="manually update command list on the website")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def update_cmd(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            await post_commands_to_api(self.bot)
            await interaction.followup.send("<:checkmark:1502219659074863185> Command list pushed to website API successfully.", ephemeral=True)
            await log_command(interaction, "update-cmd", "Manually synced command list to web")
        except Exception as e:
            await interaction.followup.send(f"<:cross:1502219725063852092> Error updating commands: {str(e)[:100]}", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(OwnerCog(bot))