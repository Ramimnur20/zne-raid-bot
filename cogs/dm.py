import asyncio
import discord
from discord import app_commands
from discord.ext import commands

from utils.db import is_user_dm_blacklisted, add_user_dm_blacklist
from utils.helpers import log_command
from utils.config import DEFAULT_BUTTON_MESSAGE


class DmCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    dm_group = app_commands.Group(name="dm", description="DM commands")

    @dm_group.command(name="anon", description="Send an anonymous DM to a user.")
    @app_commands.describe(user_id="User ID to DM", message="Message to send")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def anon_dm(self, interaction: discord.Interaction, user_id: str, message: str):
        await interaction.response.defer(ephemeral=True)
        
        # Check if user is blacklisted
        if await is_user_dm_blacklisted(int(user_id)):
            await interaction.followup.send("❌ That user is blacklisted from receiving DMs.", ephemeral=True)
            return
        
        try:
            user = await self.bot.fetch_user(int(user_id))
            await user.send(message)
            await interaction.followup.send(f"✅ DM sent to {user.display_name}!", ephemeral=True)
            await log_command(interaction, "anon-dm", f"sent DM to {user_id}")
        except discord.Forbidden:
            await interaction.followup.send("❌ Cannot send DM - user has DMs disabled or bot is blocked.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Error sending DM: {e}", ephemeral=True)

    @dm_group.command(name="flood", description="Send 20 DMs to a user.")
    @app_commands.describe(user_id="User ID to flood", message="Message to send")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def flood_dm(self, interaction: discord.Interaction, user_id: str, message: str):
        await interaction.response.defer(ephemeral=True)
        
        # Check if user is blacklisted
        if await is_user_dm_blacklisted(int(user_id)):
            await interaction.followup.send("❌ That user is blacklisted from receiving DMs.", ephemeral=True)
            return
        
        try:
            user = await self.bot.fetch_user(int(user_id))
            
            for i in range(20):
                await user.send(f"{message} ({i+1}/20)")
                await asyncio.sleep(0.5)
            
            await interaction.followup.send(f"✅ Flooded {user.display_name} with 20 DMs!", ephemeral=True)
            await log_command(interaction, "flood-dm", f"flooded DM to {user_id}")
        except discord.Forbidden:
            await interaction.followup.send("❌ Cannot send DM - user has DMs disabled or bot is blocked.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Error sending DM: {e}", ephemeral=True)

    @dm_group.command(name="blacklist", description="Blacklist yourself from receiving DMs from the bot.")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def blacklist_dm(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        user_id = interaction.user.id
        await add_user_dm_blacklist(user_id)
        
        await interaction.followup.send("✅ You have been blacklisted from receiving DMs.", ephemeral=True)
        await log_command(interaction, "blacklist-dm", f"user {user_id} blacklisted themselves")


async def setup(bot: commands.Bot):
    await bot.add_cog(DmCog(bot))
