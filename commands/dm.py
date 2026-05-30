import asyncio
import discord
import tomllib
from discord import app_commands
from discord.ext import commands

with open("config.toml", "rb") as f:
    _config = tomllib.load(f)

DEFAULT_BUTTON_MESSAGE = _config["messages"]["og_msg"]

from utils.helpers import log_command


class DmCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="dmanon", description="dm someone.")
    @app_commands.describe(user_id="User ID to DM", message="Message to send")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def dmanon(self, interaction: discord.Interaction, user_id: str, message: str):
        await interaction.response.defer(ephemeral=True)
        try:
            user = await self.bot.fetch_user(int(user_id))
            await user.send(message)
            await interaction.followup.send(f"✅ DM sent to {user.display_name}!", ephemeral=True)
            await log_command(interaction, "anon-dm", f"sent DM to {user_id}")
        except discord.Forbidden:
            await interaction.followup.send("❌ Cannot send DM - user has DMs disabled or bot is blocked.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Error sending DM: {e}", ephemeral=True)

    @app_commands.command(name="dmflood", description="Send 20 DMs to a user.")
    @app_commands.describe(user_id="User ID to flood", message="Message to send")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def dmflood(self, interaction: discord.Interaction, user_id: str, message: str):
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send("⏳ Flooding started in background...", ephemeral=True)
        
        async def flood_task():
            try:
                user = await self.bot.fetch_user(int(user_id))
                for i in range(20):
                    await user.send(f"{message}")
                await interaction.followup.send(f"✅ Flooded {user.display_name} with 20 DMs!", ephemeral=True)
            except discord.Forbidden:
                await interaction.followup.send("❌ Cannot send DM - user has DMs disabled or bot is blocked.", ephemeral=True)
            except Exception as e:
                await interaction.followup.send(f"❌ Error sending DM: {e}", ephemeral=True)
        
        asyncio.create_task(flood_task())


async def setup(bot: commands.Bot):
    await bot.add_cog(DmCog(bot))
