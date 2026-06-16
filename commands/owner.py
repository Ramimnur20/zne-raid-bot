import discord
import re
from discord import app_commands
from discord.ext import commands

from utils.db import (
    set_global_default_message,
    set_server_blacklist,
    set_user_blacklist,
)
from utils.helpers import log_command, ZNE_INVITE
from utils.constants import CHECKMARK, CROSS
from utils.checks import is_owner


class OwnerCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.cogs_list = ["commands.raid", "commands.owner", "commands.ghost", "commands.fake", "commands.dm", "commands.ad", "commands.other"]

    @app_commands.command(name="x-admin", description="Admin tools for bot management")
    @app_commands.check(is_owner)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def x_admin(self, interaction: discord.Interaction):
        await interaction.response.send_message(view=Components(self.bot, self.cogs_list), ephemeral=True)


class Components(discord.ui.LayoutView):    
    def __init__(self, bot, cogs_list):
        super().__init__(timeout=None)
        self.bot = bot
        self.cogs_list = cogs_list

    container1 = discord.ui.Container(
        discord.ui.TextDisplay(content="## admin tools."),
        discord.ui.TextDisplay(content="use the buttons below to manage the bot"),
        discord.ui.ActionRow(
                discord.ui.Button(
                    style=discord.ButtonStyle.primary,
                    label="set new message",
                    custom_id="setmessage",
                ),
                discord.ui.Button(
                    style=discord.ButtonStyle.secondary,
                    label="reload cogs",
                    custom_id="reloadcogs",
                ),
                discord.ui.Button(
                    style=discord.ButtonStyle.danger,
                    label="blacklist a server",
                    custom_id="blacklistserver",
                ),
                discord.ui.Button(
                    style=discord.ButtonStyle.danger,
                    label="blacklist someone",
                    custom_id="blacklistuser",
                ),
        ),
        accent_colour=discord.Colour(16777215),
    )

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        cid = interaction.data.get("custom_id")
        
        if cid == "setmessage":
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
                    await modal_interaction.response.send_message(f"{CHECKMARK} Global message set!", ephemeral=True)
                    await log_command(interaction, "x-admin", f"Updated global message")

            await interaction.response.send_modal(SetGlobalMessageModal())
            return False

        elif cid == "reloadcogs":
            options = [discord.SelectOption(label="All Cogs", value="all")]
            for cog in self.cogs_list:
                options.append(discord.SelectOption(label=cog, value=cog))

            class CogSelect(discord.ui.Select):
                def __init__(self2, bot, cogs_list):
                    self2.bot = bot
                    self2.cogs_list = cogs_list
                    super().__init__(placeholder="Choose a cog to reload...", options=options)

                async def callback(self2, it: discord.Interaction):
                    await it.response.defer(ephemeral=True)
                    selection = self2.values[0]
                    reloaded, failed = [], []
                    
                    to_reload = self2.cogs_list if selection == "all" else [selection]
                    for cog in to_reload:
                        try:
                            await self2.bot.reload_extension(cog)
                            reloaded.append(cog)
                        except Exception as e:
                            failed.append(f"{cog}: {e}")
                    
                    msg = f"{CHECKMARK} Reloaded: {', '.join(reloaded)}"
                    if failed: msg += f"\n{CROSS} Failed: {', '.join(failed)}"
                    await it.edit_original_response(content=msg, view=None)

            class ReloadView(discord.ui.View):
                def __init__(self2, bot, cogs_list):
                    super().__init__()
                    self2.add_item(CogSelect(bot, cogs_list))

            await interaction.response.send_message("Select a cog to reload:", view=ReloadView(self.bot, self.cogs_list), ephemeral=True)
            return False

        elif cid == "blacklistserver":
            class BlacklistServerModal(discord.ui.Modal, title="Blacklist Server"):
                id_input = discord.ui.TextInput(label="Server ID", placeholder="Enter server ID...")
                action = discord.ui.TextInput(label="Action", placeholder="blacklist / unblacklist")

                async def on_submit(self2, it: discord.Interaction):
                    # Strip non-digits (handles accidental spaces or mentions)
                    val = re.sub(r'\D', '', self2.id_input.value)
                    if not val:
                        return await it.response.send_message(f"{CROSS} Invalid Server ID.", ephemeral=True)

                    is_blacklisting = self2.action.value.lower() == "blacklist"
                    await set_server_blacklist(val, is_blacklisting)
                    status = "blacklisted" if is_blacklisting else "unblacklisted"
                    await it.response.send_message(f"{CHECKMARK} Server `{val}` {status}!", ephemeral=True)
                    await log_command(it, "x-admin", f"{status} server {val}")
            
            await interaction.response.send_modal(BlacklistServerModal())
            return False

        elif cid == "blacklistuser":
            class BlacklistUserModal(discord.ui.Modal, title="Blacklist User"):
                id_input = discord.ui.TextInput(label="User ID", placeholder="Enter user ID...")
                action = discord.ui.TextInput(label="Action", placeholder="blacklist / unblacklist")

                async def on_submit(self2, it: discord.Interaction):
                    # Strip non-digits (handles accidental spaces or mentions)
                    val = re.sub(r'\D', '', self2.id_input.value)
                    if not val:
                        return await it.response.send_message(f"{CROSS} Invalid User ID.", ephemeral=True)

                    is_blacklisting = self2.action.value.lower() == "blacklist"
                    await set_user_blacklist(val, is_blacklisting)
                    status = "blacklisted" if is_blacklisting else "unblacklisted"
                    await it.response.send_message(f"{CHECKMARK} User `{val}` {status}!", ephemeral=True)
                    await log_command(it, "x-admin", f"{status} user {val}")
            
            await interaction.response.send_modal(BlacklistUserModal())
            return False

        return True


async def setup(bot: commands.Bot):
    await bot.add_cog(OwnerCog(bot))