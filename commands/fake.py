import asyncio
import io
import random
import requests
import discord
from discord import app_commands
from discord.ext import commands
from PIL import Image, ImageDraw, ImageOps, ImageFont
from datetime import datetime

from utils.helpers import log_command
from utils.constants import CROSS, LOADING, CHECKMARK
from views import FakeNitroView, make_fake_giveaway


class FakeCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="fakenitro", description="send a ULTRA realistic nitro embed.")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def fake_nitro(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        await interaction.followup.send("⌛ Loading nitro panel...", ephemeral=True)
        await interaction.followup.send(view=FakeNitroView(), ephemeral=False)
        await log_command(interaction, "fake nitro", "user baited someone with a fake nitro.")

    @app_commands.command(name="fakegiveaway", description="send a fake giveaway embed.")
    @app_commands.describe(prize="The prize for the giveaway")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def fake_giveaway(self, interaction: discord.Interaction, prize: str):
        await interaction.response.defer(ephemeral=True, thinking=True)
        await interaction.followup.send("⌛ Loading giveaway panel...", ephemeral=True)
        await interaction.followup.send(view=make_fake_giveaway(prize), ephemeral=False)
        await log_command(interaction, "fake giveaway", f"user baited someone with a fake giveaway for: {prize}")

    @app_commands.command(name="fakemessage", description="send a fake message")
    @app_commands.describe(user_id="User ID to spoof", message="Fake message to show")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def fake_message(self, interaction: discord.Interaction, user_id: str, message: str):
        await interaction.response.defer(ephemeral=True, thinking=True)

        # Fetch user from the ID
        try:
            user = await self.bot.fetch_user(int(user_id))
        except (ValueError, discord.NotFound):
            await interaction.followup.send(f"{CROSS} Invalid user ID", ephemeral=True)
            return

        username = user.display_name
        avatar_url = user.display_avatar.url

        response = requests.get(avatar_url)
        avatar = Image.open(io.BytesIO(response.content)).convert("RGBA")
        avatar = avatar.resize((40, 40), Image.LANCZOS)

        mask = Image.new("L", avatar.size, 0)
        draw_mask = ImageDraw.Draw(mask)
        draw_mask.ellipse((0, 0) + avatar.size, fill=255)
        avatar = ImageOps.fit(avatar, mask.size, centering=(0.5, 0.5))
        avatar.putalpha(mask)

        width, height = 800, 80
        img = Image.new("RGBA", (width, height), "#36393F")
        draw = ImageDraw.Draw(img)

        font_bold = ImageFont.truetype("utils/font_bold.ttf", 18)
        font_regular = ImageFont.truetype("utils/font_regular.ttf", 16)
        font_timestamp = ImageFont.truetype("utils/font_regular.ttf", 12)

        img.paste(avatar, (20, 20), avatar)
        
        # Generate random time today
        now = datetime.now()
        random_hour = random.randint(0, now.hour)
        random_minute = random.randint(0, 59)
        timestamp = f"Today at {random_hour}:{random_minute:02d} {'AM' if random_hour < 12 else 'PM'}"

        draw.text((70, 18), username, font=font_bold, fill=(255, 255, 255))
        draw.text((70 + draw.textlength(username, font=font_bold) + 10, 21), timestamp, font=font_timestamp, fill=(153, 170, 181))
        draw.text((70, 45), message, font=font_regular, fill=(220, 221, 222))

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        file = discord.File(fp=buffer, filename="screenshot_26_02.png")

        await interaction.followup.send(file=file)
        await log_command(interaction, "fake message", f"user spoofed message as {username}")

    @app_commands.command(name="fakeban", description="simulates banning a user")
    @app_commands.describe(user="The user to fake ban", reason="The reason for the fake ban")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def fake_ban(self, interaction: discord.Interaction, user: discord.User, reason: str):
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send("banning user...", ephemeral=True)

        class BanningView(discord.ui.LayoutView):
            container1 = discord.ui.Container(
                discord.ui.TextDisplay(content=f"{LOADING} Banning {user.mention}..."),
            )
        
        # Send stage 1: Banning... (Non-ephemeral for everyone to see)
        ban_msg = await interaction.followup.send(view=BanningView(), ephemeral=False)

        await asyncio.sleep(2) # Simulate some processing time

        class BannedView(discord.ui.LayoutView):
            container1 = discord.ui.Container(
                discord.ui.TextDisplay(content=f"{CHECKMARK} Successfully banned {user.mention}\nReason: {reason}"),
            )
        
        # Edit the public message to stage 2: Successfully banned
        await ban_msg.edit(view=BannedView())
        await log_command(interaction, "fakeban", f"simulated ban for {user.id} with reason: {reason}")


async def setup(bot: commands.Bot):
    await bot.add_cog(FakeCog(bot))