import io
import random
import requests
import discord
from discord import app_commands
from discord.ext import commands
from PIL import Image, ImageDraw, ImageOps, ImageFont
from datetime import datetime

from utils.helpers import log_command
from utils.views import FakeNitroView


class FakeCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    fake_group = app_commands.Group(name="fake", description="Fake commands")

    @fake_group.command(name="nitro", description="Send a ULTRA realistic nitro embed.")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def fake_nitro(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send("⌛ Loading nitro panel...", ephemeral=True)
        await interaction.followup.send(view=FakeNitroView(), ephemeral=False)
        await log_command(interaction, "fake nitro", "user baited someone with a fake nitro.")

    @fake_group.command(name="message", description="Send a realistic fake message as image.")
    @app_commands.describe(user_id="User ID to spoof", message="Fake message to show")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def fake_message(self, interaction: discord.Interaction, user_id: str, message: str):
        await interaction.response.defer(ephemeral=True)

        # Fetch user from the ID
        try:
            user = await self.bot.fetch_user(int(user_id))
        except (ValueError, discord.NotFound):
            await interaction.followup.send("❌ Invalid user ID", ephemeral=True)
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

        font_bold = ImageFont.truetype("arialbd.ttf", 18)
        font_regular = ImageFont.truetype("arial.ttf", 16)
        font_timestamp = ImageFont.truetype("arial.ttf", 12)

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
        file = discord.File(fp=buffer, filename="spoof.png")

        await interaction.followup.send(file=file)
        await log_command(interaction, "fake message", f"user spoofed message as {username}")


async def setup(bot: commands.Bot):
    await bot.add_cog(FakeCog(bot))
