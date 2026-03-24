import time
import random
import io
import requests
import psutil
import os
import discord
from discord import app_commands
from discord.ext import commands
from PIL import Image, ImageDraw, ImageOps, ImageFont
from datetime import datetime, timedelta

from utils.helpers import log_command
from utils.views import SpamButton, PingPanel, CustomButtonPanel, GifSpamButton, make_farm_panel, make_custom_spam_panel, make_filespam_panel, FakeNitroView
from utils.globals import command_count

class RaidCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="ra1d", description="self explanatory.")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def ra1d(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send(view=SpamButton(interaction.user.id), ephemeral=True)
        await log_command(interaction, "ra1d", "user raided a server")

    @app_commands.command(name="interaction-ra1d", description="Farm interaction tokens and raid with them")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def interaction_ra1d(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send(
            view=make_farm_panel(interaction.user.id, 0),
            ephemeral=True
        )
        await log_command(interaction, "interaction-ra1d", "user opened interaction farm panel")

    @app_commands.command(name="custom_ra1d", description="Opened the custom ra1d message panel")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def custom_ra1d(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send(view=CustomButtonPanel(interaction.user.id), ephemeral=True)
        await log_command(interaction, "custom_ra1d", "user opened custom message panel")

    @app_commands.command(name="thug", description="thug the server!!")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def thug(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send(view=GifSpamButton(interaction.user.id), ephemeral=True)
        await log_command(interaction, "thug", "user thugged a server 😂")

    @app_commands.command(name="blame", description="Blame a user for raiding with ZNE.")
    @app_commands.describe(user="The user to blame")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def blame(self, interaction: discord.Interaction, user: discord.User):
        await interaction.response.defer(ephemeral=True)
        loading_msg = await interaction.followup.send("❗ blaming....", ephemeral=True)
        expires_ts = int(time.time()) + 7 * 24 * 60 * 60
        await interaction.followup.send(
            f"✅ Thank you for raiding with **ZNE** {user.mention}, your trial expires in <t:{expires_ts}:R>"
        )
        await loading_msg.delete()
        await log_command(interaction, "blame", f"blamed user: {user.id}")


    @app_commands.command(name="say", description="Make the bot say something.")
    @app_commands.describe(text="The text for the bot to say")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def say(self, interaction: discord.Interaction, text: str):
        await interaction.response.send_message("sending..", ephemeral=True)
        await interaction.followup.send(text)

    @app_commands.command(name="spam", description="Spam a custom message.")
    @app_commands.describe(text="The message to spam")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def spam(self, interaction: discord.Interaction, text: str):
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send(view=make_custom_spam_panel(interaction.user.id, text), ephemeral=True)
        await log_command(interaction, "spam", f"user spammed: {text}")

    @app_commands.command(name="filespam", description="Spam a file attachment.")
    @app_commands.describe(attachment="The file to spam")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def filespam(self, interaction: discord.Interaction, attachment: discord.Attachment):
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send(view=make_filespam_panel(interaction.user.id, attachment), ephemeral=True)
        await log_command(interaction, "filespam", f"user filespammed: {attachment.filename}")

    @app_commands.command(name="info", description="Get information about the bot.")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def info(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        # Get system stats
        process = psutil.Process(os.getpid())
        ram_usage = process.memory_info().rss / 1024 / 1024  # Convert to MB
        cpu_usage = process.cpu_percent()
        
        # Get libraries as a list
        try:
            with open("requirements.txt", "r") as f:
                libs = [line.strip() for line in f if line.strip()]
                libs_formatted = "\n - ".join(libs)
        except:
            libs_formatted = "discord.py"
        
        # Get bot info
        bot_server_count = len(self.bot.guilds)
        
        # Get ZNE server member count
        zne_server = self.bot.get_guild(1459804477770039386)
        zne_member_count = zne_server.member_count if zne_server else "Server Teminated."
        
        # Get total synced commands
        total_synced_commands = len(self.bot.tree.get_commands())
        
        info_content = "## ☣ - BOT INFO\n" \
            "made by [voby7](https://voby.page.gd/) for [zne](https://discord.gg/sillyz)\n" \
            f"zne member count: **{zne_member_count}**\n" \
            f"bot server count: **{bot_server_count}**\n" \
            "bot was made in **June 2025**\n" \
            "this is the **raid** bot\n" \
            f"total commands synced: **{total_synced_commands}**\n" \
            f"total commands executed: **{command_count}**\n" \
            f"ram usage: **{ram_usage:.2f} MB**\n" \
            f"cpu usage: **{cpu_usage:.2f}%**\n\n" \
            f"libraries installed: \n - {libs_formatted}\n\n" \
            "language: **python**"
        
        class InfoView(discord.ui.LayoutView):
            container1 = discord.ui.Container(
                discord.ui.Section(
                    discord.ui.TextDisplay(content=info_content),
                    accessory=discord.ui.Thumbnail(
                        media="https://dnvsrzeijhduiqsrlkmc.supabase.co/storage/v1/object/public/hosted-files/54a084b2-a7e6-4415-81e9-cd4052d91c58/VI2Whjcx_206f5b851a8ad773cd5712f497583f6a.jpg?download=206f5b851a8ad773cd5712f497583f6a.jpg",
                    ),
                ),
            )
        
        view = InfoView()
        await interaction.followup.send(view=view, ephemeral=True)
        await log_command(interaction, "info", "user viewed bot info")


async def setup(bot: commands.Bot):
    await bot.add_cog(RaidCog(bot))
