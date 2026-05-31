import re
import time
import psutil
import os
import asyncio
import aiohttp
import discord
import tomllib
from discord import app_commands
from discord.ext import commands

with open("config.toml", "rb") as f:
    _config = tomllib.load(f)

ZNE_INVITE = _config.get("zne_invite", "https://discord.gg/4pQzcZxVXK")
LAG_MESSAGE = _config.get("lag", {}).get("lag_msg", "LAGGED BY ZNE - https://discord.gg/4pQzcZxVXK")

from utils.helpers import log_command
from views import SpamButton, PingPanel, GifSpamButton, make_farm_panel, make_custom_spam_panel, make_filespam_panel, FakeNitroView, PresetManagementView
from utils.db import get_user_presets, get_preset_by_title


async def _send_message_http(session: aiohttp.ClientSession, application_id: int, interaction_token: str, content: str):
    url = f"https://discord.com/api/v10/webhooks/{application_id}/{interaction_token}"
    payload = {"content": content, "allowed_mentions": {"parse": ["everyone", "users", "roles"]}}
    
    async with session.post(url, json=payload) as resp:
        return resp.status


class LagButton(discord.ui.LayoutView):
    def __init__(self, user_id: int):
        super().__init__(timeout=None)
        self.user_id = user_id

    container1 = discord.ui.Container(
        discord.ui.ActionRow(
            discord.ui.Button(
                style=discord.ButtonStyle.secondary,
                label="LAG",
                emoji="<:evil_brown:1502233792193232987>",
                custom_id="send_lag_button",
            ),
        ),
    )

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.data.get("custom_id") == "send_lag_button":
            await interaction.response.defer()

            app_id = interaction.client.application_id
            token = interaction.token

            async with aiohttp.ClientSession() as session:
                tasks = [
                    _send_message_http(session, app_id, token, LAG_MESSAGE)
                    for _ in range(5)
                ]
                await asyncio.gather(*tasks)

            return False
        return True


class RaidCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def preset_autocomplete(self, interaction: discord.Interaction, current: str):
        presets = await get_user_presets(str(interaction.user.id))
        return [
            app_commands.Choice(name=p['title'], value=p['title'])
            for p in presets if current.lower() in p['title'].lower()
        ][:25]

    @app_commands.command(name="ra1d", description="[deprecated] self explanatory.")
    @app_commands.describe(preset="Optional preset to use for the raid")
    @app_commands.autocomplete(preset=preset_autocomplete)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def ra1d(self, interaction: discord.Interaction, preset: str = None):
        await interaction.response.defer(ephemeral=True, thinking=True)
        
        preset_content = None
        if preset:
            preset_content = await get_preset_by_title(str(interaction.user.id), preset)

        await interaction.followup.send(view=SpamButton(interaction.user.id, preset_content), ephemeral=True)
        await log_command(interaction, "ra1d", "user raided a server")

    @app_commands.command(name="interaction-ra1d", description="interaction raiding.")
    @app_commands.describe(preset="Optional preset to use for the interaction raid")
    @app_commands.autocomplete(preset=preset_autocomplete)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def interaction_ra1d(self, interaction: discord.Interaction, preset: str = None):
        await interaction.response.defer(ephemeral=True, thinking=True)

        preset_content = None
        if preset:
            preset_content = await get_preset_by_title(str(interaction.user.id), preset)

        await interaction.followup.send(
            view=make_farm_panel(interaction.user.id, 0, preset_content),
            ephemeral=True
        )
        await log_command(interaction, "interaction-ra1d", "user opened interaction farm panel")

    @app_commands.command(name="custom_ra1d", description="open the custom ra1d message panel")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def custom_ra1d(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        await interaction.followup.send(view=PresetManagementView(interaction.user.id), ephemeral=True)
        await log_command(interaction, "custom_ra1d", "user opened custom message panel")

    @app_commands.command(name="thug", description="thug the server!!")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def thug(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        await interaction.followup.send(view=GifSpamButton(interaction.user.id), ephemeral=True)
        await log_command(interaction, "thug", "user thugged a server 😂")

    @app_commands.command(name="blame", description="blame a user for raiding.")
    @app_commands.describe(user="The user to blame")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def blame(self, interaction: discord.Interaction, user: discord.User):
        await interaction.response.defer(ephemeral=True)
        loading_msg = await interaction.followup.send("❗ blaming....", ephemeral=True)
        expires_ts = int(time.time()) + 7 * 24 * 60 * 60
        avatar_url = user.display_avatar.url

        class Components(discord.ui.LayoutView):
            container1 = discord.ui.Container(
                discord.ui.Section(
                    discord.ui.TextDisplay(content=f"# {user.mention} ur raid was completed!\nthanks for using **ZNE** bot to raid servers! your trial will end in <t:{expires_ts}:R>"),
                    accessory=discord.ui.Thumbnail(
                        media=avatar_url,
                    ),
                ),
                discord.ui.ActionRow(
                    discord.ui.Button(
                        url="https://discord.gg/4pQzcZxVXK",
                        style=discord.ButtonStyle.link,
                        label="join",
                    ),
                ),
            )

        await interaction.followup.send(view=Components())
        await loading_msg.delete()
        await log_command(interaction, "blame", f"blamed user: {user.id}")

    @app_commands.command(name="say", description="say something through the bot.")
    @app_commands.describe(text="The text for the bot to say")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def say(self, interaction: discord.Interaction, text: str):
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send("sending..", ephemeral=True)
        await interaction.followup.send(text)

    @app_commands.command(name="spam", description="spam something.")
    @app_commands.describe(text="The message to spam")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def spam(self, interaction: discord.Interaction, text: str):
        await interaction.response.defer(ephemeral=True, thinking=True)

        if "discord.gg/" in text.lower():
            text = re.sub(r'(?:https?://)?discord\.gg/\S+', ZNE_INVITE, text)

        await interaction.followup.send(view=make_custom_spam_panel(interaction.user.id, text), ephemeral=True)
        await log_command(interaction, "spam", f"user spammed: {text}")

    @app_commands.command(name="filespam", description="spam a file attachment.")
    @app_commands.describe(attachment="The file to spam")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def filespam(self, interaction: discord.Interaction, attachment: discord.Attachment):
        await interaction.response.defer(ephemeral=True, thinking=True)
        await interaction.followup.send(view=make_filespam_panel(interaction.user.id, attachment), ephemeral=True)
        await log_command(interaction, "filespam", f"user filespammed: {attachment.filename}")

    @app_commands.command(name="info", description="info.")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def info(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
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
        zne_server = self.bot.get_guild(1470774657266483358)
        zne_member_count = zne_server.member_count if zne_server else "Server Terminated."
        
        # Get total synced commands
        total_synced_commands = len(self.bot.tree.get_commands())
        
        info_content = "## ☣ - BOT INFO\n" \
            f"made by [voby7](https://voby.page.gd/) for [zne]({ZNE_INVITE})\n" \
            f"zne member count: **{zne_member_count}**\n" \
            f"bot server count: **{bot_server_count}**\n" \
            "bot was made in **June 2025**\n" \
            "this is the **raid** bot\n" \
            f"total commands synced: **{total_synced_commands}**\n" \
            f"ram usage: **{ram_usage:.2f} MB**\n" \
            f"cpu usage: **{cpu_usage:.2f}%**\n\n" \
            f"libraries installed: \n - {libs_formatted}\n\n" \
            "language: **python**"
        
        class InfoView(discord.ui.LayoutView):
            container1 = discord.ui.Container(
                discord.ui.Section(
                    discord.ui.TextDisplay(content=info_content),
                    accessory=discord.ui.Thumbnail(
                        media="https://dnvsrzeijhduiqsrlkmc.supabase.co/storage/v1/object/public/hosted-files/54a084b2-a7e6-4415-81e9-cd4052d91c58/GFKcZn2f_a_3a7ef8bea173246c3b7383b3cf536158.gif",
                    ),
                ),
            )
        
        view = InfoView()
        await interaction.followup.send(view=view, ephemeral=True)
        await log_command(interaction, "info", "user viewed bot info")

    @app_commands.command(name="lag", description="crash peoples phones for fun.")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def lag(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        await interaction.followup.send(view=LagButton(interaction.user.id), ephemeral=True)
        await log_command(interaction, "lag", "user lagged a server")


async def setup(bot: commands.Bot):
    await bot.add_cog(RaidCog(bot))
