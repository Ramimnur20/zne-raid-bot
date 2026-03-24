import discord
from discord import app_commands
from discord.ext import commands

from utils.db import (
    add_server_blacklist,
    add_user_blacklist,
    get_blacklisted_servers,
    set_global_default_message,
)
from utils.helpers import is_owner, log_command, user_farm_tokens


class OwnerCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    x_group = app_commands.Group(name="x", description="Owner commands")

    @x_group.command(name="blacklist-server", description="Blacklist a server from running commands (owner only)")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def blacklist_server(self, interaction: discord.Interaction, server_id: str = None):
        if not is_owner(interaction):
            await interaction.response.send_message("You are not authorized to use this command.", ephemeral=True)
            return

        if server_id is None:
            if interaction.guild_id:
                server_id = str(interaction.guild_id)
            else:
                await interaction.response.send_message("Please provide a server ID.", ephemeral=True)
                return

        try:
            server_id_int = int(server_id)
        except ValueError:
            await interaction.response.send_message("Invalid server ID. Please provide a valid numeric ID.", ephemeral=True)
            return

        await add_server_blacklist(server_id_int)
        await interaction.response.send_message(f"Server `{server_id}` has been blacklisted from running commands.", ephemeral=True)
        await log_command(interaction, "blacklist-server", f"Blacklisted server: {server_id}")

    @x_group.command(name="blacklist-user", description="Blacklist a user from running commands (owner only)")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def blacklist_user(self, interaction: discord.Interaction, user_id: str = None):
        if not is_owner(interaction):
            await interaction.response.send_message("You are not authorized to use this command.", ephemeral=True)
            return

        if user_id is None:
            await interaction.response.send_message("Please provide a user ID.", ephemeral=True)
            return

        try:
            user_id_int = int(user_id)
        except ValueError:
            await interaction.response.send_message("Invalid user ID. Please provide a valid numeric ID.", ephemeral=True)
            return

        await add_user_blacklist(user_id_int)
        await interaction.response.send_message(f"User `{user_id}` has been blacklisted from running commands.", ephemeral=True)
        await log_command(interaction, "blacklist-user", f"Blacklisted user: {user_id}")

    @x_group.command(name="setmessage", description="Set the global default spam message for all commands (owner only)")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def setmessage(self, interaction: discord.Interaction):
        if not is_owner(interaction):
            await interaction.response.send_message("You are not authorized to use this command.", ephemeral=True)
            return

        class SetGlobalMessageModal(discord.ui.Modal, title="Set Global Default Message"):
            message_input = discord.ui.TextInput(
                label="Global default message",
                style=discord.TextStyle.paragraph,
                placeholder="Enter the message that will be used by default for all commands"
            )

            async def on_submit(self2, modal_interaction: discord.Interaction):
                await set_global_default_message(self2.message_input.value)
                await modal_interaction.response.send_message("Global default message has been set!", ephemeral=True)
                await log_command(interaction, "setmessage", f"New global message: {self2.message_input.value}")

        await interaction.response.send_modal(SetGlobalMessageModal())

    @x_group.command(name="reload-cogs", description="Reload all cogs (owner only)")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def reload_cogs(self, interaction: discord.Interaction):
        if not is_owner(interaction):
            await interaction.response.send_message("You are not authorized to use this command.", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        cogs_to_reload = ["cogs.raid", "cogs.owner", "cogs.ghost", "cogs.fake", "cogs.dm", "cogs.api"]
        reloaded = []
        failed = []
        
        for cog in cogs_to_reload:
            try:
                await self.bot.reload_extension(cog)
                reloaded.append(cog)
            except Exception as e:
                failed.append(f"{cog}: {e}")
        
        result = f"✅ Reloaded **{len(reloaded)}** cogs: {', '.join(reloaded)}"
        if failed:
            result += f"\n❌ Failed to reload **{len(failed)}** cogs: {', '.join(failed)}"
        
        await interaction.followup.send(result, ephemeral=True)
        await log_command(interaction, "reload-cogs", f"Reloaded {len(reloaded)} cogs")

    @x_group.command(name="leaveall", description="Leave all servers (owner only)")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def leave_all(self, interaction: discord.Interaction):
        if not is_owner(interaction):
            await interaction.response.send_message("You are not authorized to use this command.", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        ZNE_SERVER_ID = 1459804477770039386
        guilds = list(self.bot.guilds)
        left_count = 0
        failed_count = 0
        skipped_count = 0
        
        for guild in guilds:
            if guild.id == ZNE_SERVER_ID:
                skipped_count += 1
                continue
            try:
                await guild.leave()
                left_count += 1
            except Exception:
                failed_count += 1
        
        result = f"✅ Left **{left_count}** servers"
        if skipped_count > 0:
            result += f"\n⏭️ Skipped **{skipped_count}** server (ZNE)"
        if failed_count > 0:
            result += f"\n❌ Failed to leave **{failed_count}** servers"
        
        await interaction.followup.send(result, ephemeral=True)
        await log_command(interaction, "leave-all", f"Left {left_count} servers")


async def setup(bot: commands.Bot):
    await bot.add_cog(OwnerCog(bot))
