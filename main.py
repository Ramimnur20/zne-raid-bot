# made by ramim using a100's code
# its there to make sure no one thinks im a skid lmao
import os
import re
import io
import json
import time
import base64
import asyncio
import random
import logging
import requests
import aiohttp
from io import BytesIO
from datetime import datetime, timedelta
from colorama import Fore, Style, init
import discord
from discord import User, Embed, Interaction, Permissions, AllowedMentions, ButtonStyle, app_commands
from discord.ext import commands
from discord.ui import Modal, TextInput, View, Button
from PIL import Image, ImageDraw, ImageFont, ImageOps
import requests

init(autoreset=True)

LOG_WEBHOOK_URL = "" # webhook for all logs
PREMIUM_FILE = "premium.json"
PRESETS_FILE = "presets.json"

class RateLimitFilter(logging.Filter):
    def filter(self, record):
        if "is rate limited" in record.getMessage():
            if not hasattr(record, "already_logged"):
                record.already_logged = True
            return False 
        return True  

logger = logging.getLogger("discord.webhook.async_")
logger.addFilter(RateLimitFilter())

with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)
    
class CooldownManager:
    def __init__(self, cooldown_seconds: int):
        self.cooldown_seconds = cooldown_seconds
        self.user_timestamps = {}

    def can_use(self, user_id: int) -> (bool, int):
        now = time.time()
        last_time = self.user_timestamps.get(user_id, 0)
        elapsed = now - last_time
        if elapsed >= self.cooldown_seconds:
            self.user_timestamps[user_id] = now
            self.cleanup()
            return True, 0
        else:
            return False, int(self.cooldown_seconds - elapsed)

    def cleanup(self):
        now = time.time()
        to_delete = [user for user, ts in self.user_timestamps.items() if now - ts > self.cooldown_seconds]
        for user in to_delete:
            del self.user_timestamps[user]

cooldown_manager = CooldownManager(100)


def load_premium_users():
    if not os.path.exists(PREMIUM_FILE):
        return []
    with open(PREMIUM_FILE, "r") as f:
        return json.load(f)

def save_premium_users(user_ids):
    with open(PREMIUM_FILE, "w") as f:
        json.dump(user_ids, f, indent=2)

def add_premium_user(user_id: int):
    premium_users = load_premium_users()
    if user_id not in premium_users:
        premium_users.append(user_id)
        save_premium_users(premium_users)

def is_premium_user(user_id: int):
    premium_users = load_premium_users()
    return user_id in premium_users

def remove_premium_user(user_id: int) -> bool:
    premium_users = load_premium_users()
    if user_id in premium_users:
        premium_users.remove(user_id)
        save_premium_users(premium_users)
        return True
    return False

def update_leaderboard(user_id: int):
    leaderboard_file = "leaderboard.json"

    if not os.path.exists(leaderboard_file):
        with open(leaderboard_file, "w") as f:
            json.dump({}, f)

    with open(leaderboard_file, "r") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = {}

    user_id_str = str(user_id)

    if user_id_str in data:
        data[user_id_str] += 1
    else:
        data[user_id_str] = 1

    with open(leaderboard_file, "w") as f:
        json.dump(data, f, indent=4)


def update_leaderboard(user_id: int, command_name: str):
    leaderboard_file = "leaderboard.json"

    if not os.path.exists(leaderboard_file):
        with open(leaderboard_file, "w") as f:
            json.dump({}, f)

    with open(leaderboard_file, "r") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = {}

    user_id_str = str(user_id)

    if user_id_str not in data:
        data[user_id_str] = {
            "overall": 0
        }

    data[user_id_str]["overall"] += 1

    if command_name not in data[user_id_str]:
        data[user_id_str][command_name] = 1
    else:
        data[user_id_str][command_name] += 1

    with open(leaderboard_file, "w") as f:
        json.dump(data, f, indent=4)

def save_token(token):
    with open("config.json", "w") as file:
        json.dump({"TOKEN": token}, file)

def load_token():
    try:
        with open("config.json", "r") as file:
            data = json.load(file)
            return data.get("TOKEN")
    except FileNotFoundError:
        print(Fore.RED + "Error: 2 not found.")
        return None
    except json.JSONDecodeError:
        print(Fore.RED + "Error: Invalid JSON format in config.json.")
        return None

logo = f"""{Fore.MAGENTA}

  ___ _  _ ___  ___  __  __ _  _ ___   _   
 |_ _| \| / __|/ _ \|  \/  | \| |_ _| /_\  
  | || .` \__ \ (_) | |\/| | .` || | / _ \ 
 |___|_|\_|___/\___/|_|  |_|_|\_|___/_/ \_\
{Fore.WHITE}     raiding made easy                        
 
"""



def display_status(connected):
    if connected:
        print(Fore.GREEN + "Status: Connected")
    else:
        print(Fore.RED + "Status: Disconnected")

def token_management():
    os.system('cls' if os.name == 'nt' else 'clear') 
    print(Fore.CYAN + "Welcome to the bot token management!\n")
    print("1. Set new token")
    print("2. Load previous token")
    
    print()

    choice = input(f"{Fore.YELLOW}>{Fore.WHITE} Choose an option (1, 2){Fore.YELLOW}:{Fore.WHITE} ")

    if choice == "1":
        new_token = input(Fore.GREEN + "Enter the new token: ")
        save_token(new_token)
        print(Fore.GREEN + "Token successfully set!")
        return new_token
    elif choice == "2":
        token = load_token()
        if token:
            print(f"{Fore.GREEN}>{Fore.WHITE} Previous token loaded: {Fore.GREEN}{token}{Fore.WHITE}.")
            return token
        else:
            print(Fore.RED + "No token found.")
            return None
    else:
        print(Fore.RED + "Invalid choice. Please try again.")
        return None

async def log_command_use(
    user: discord.User,
    command_name: str,
    message: str = None,
    channel: discord.abc.Messageable = None
):
    user_display = f"{user.display_name} ({user.name}) [{user.id}]"

    fields = [
        {
            "name": "User",
            "value": user_display,
            "inline": True
        },
        {
            "name": "Command",
            "value": f"`{command_name}`",
            "inline": True
        },
        {
            "name": "Time",
            "value": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
            "inline": True
        }
    ]

    if channel:
        fields.append({
            "name": "Channel",
            "value": str(channel),
            "inline": True
        })

    if message:
        if command_name == "avatar":
            fields.append({
                "name": "Avatar Checked",
                "value": f"[Avatar Link]({message})",
                "inline": False
            })
        else:
            trimmed = message if len(message) <= 1024 else message[:1021] + "..."
            fields.append({
                "name": "Message Content",
                "value": trimmed,
                "inline": False
            })

    embed = {
        "title": "⚡ Command Executed",
        "color": 0xa874d1,
        "fields": fields,
        "author": {
            "name": user.display_name,
            "icon_url": user.display_avatar.url
        },
        "footer": {
            "text": "ZNE Logger",
            "icon_url": user._state._get_client().user.avatar.url
            if user._state._get_client().user.avatar
            else None
        }
    }

    if command_name == "avatar" and message:
        embed["thumbnail"] = {"url": message}

    webhook_data = {"embeds": [embed]}

    async with aiohttp.ClientSession() as session:
        async with session.post(LOG_WEBHOOK_URL, json=webhook_data) as resp:
            if resp.status != 204:
                print(f"Failed to send log webhook, status: {resp.status}")

intents = discord.Intents.default()
intents.messages = False  
intents.message_content = False  
intents.members = False  
intents.guilds = False  
intents.typing = False 
intents.presences = False  

bot = commands.Bot(command_prefix="!", intents=intents)


def load_presets():
    if not os.path.exists(PRESETS_FILE):
        return {}

    try:
        with open(PRESETS_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return {}
            return json.loads(content)
    except json.JSONDecodeError:
        return {}

def save_preset(user_id, message):
    data = load_presets()
    data[str(user_id)] = message

    with open(PRESETS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def get_preset(user_id):
    data = load_presets()
    return data.get(str(user_id))

class PresetModal(Modal, title="Set Your Custom Raid Message"):
    def __init__(self, user_id: int):
        super().__init__()
        self.user_id = user_id
        self.message_input = TextInput(label="Enter your spam message", style=discord.TextStyle.long, max_length=2000)
        self.add_item(self.message_input)

    async def on_submit(self, interaction: Interaction):
        save_preset(self.user_id, self.message_input.value)
        await interaction.response.send_message("✅ Preset message saved successfully!", ephemeral=True)

class PresetView(View):
    def __init__(self, user_id: int):
        super().__init__(timeout=180)
        self.user_id = user_id

    @discord.ui.button(label="Set Message", style=ButtonStyle.green)
    async def set_message(self, interaction: Interaction, button: Button):
        await interaction.response.send_modal(PresetModal(user_id=self.user_id))

    @discord.ui.button(label="Preview Message", style=ButtonStyle.primary)
    async def preview_message(self, interaction: Interaction, button: Button):
        message = get_preset(self.user_id)
        if message:
            await interaction.response.send_message(f"📄 **Your preset message:**\n```{message}```", ephemeral=True)
        else:
            await interaction.response.send_message("⚠️ No preset message found. Please set one first.", ephemeral=True)

@bot.tree.command(name="preset-message", description="Manage your custom raid message preset.")
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def preset_message(interaction: discord.Interaction):
    if not is_premium_user(interaction.user.id):
        await interaction.response.send_message("💎 This command is only available for premium users.", ephemeral=True)
        return
    view = PresetView(user_id=interaction.user.id)
    embed = discord.Embed(
        title="⚡ Preset Message",
        description="Use the buttons below to set or preview your raid message.",
        color=0xa874d1
    )
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class SpamButton(discord.ui.View):
    def __init__(self, message):
        super().__init__()
        self.message = message

    @discord.ui.button(label="Spam", style=discord.ButtonStyle.red)
    async def spam_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        allowed = discord.AllowedMentions(everyone=True, users=True, roles=True)
        for _ in range(5):  
            await interaction.followup.send(self.message, allowed_mentions=allowed)  

@bot.tree.command(name="custom-raid", description="[💎] Premium Raid with your own message. (premium only!)")
@app_commands.describe(message="Optional: your custom message to spam (use /preset-message if you want to save it)")
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def custom_raid(interaction: discord.Interaction, message: str = None):
    if not is_premium_user(interaction.user.id):
        await interaction.response.send_message("💎 This command is only available for premium users.", ephemeral=True)
        return

    if not message:
        message = get_preset(interaction.user.id)
        if not message:
            await interaction.response.send_message("❌ You have not set a preset message. Use `/preset-message` to set one.", ephemeral=True)
            return

    view = SpamButton(message)
    await interaction.response.send_message(f"💎 SPAM TEXT:\n```{message}```", view=view, ephemeral=True)

    await log_command_use(
        user=interaction.user,
        command_name="💎 custom-raid",
        channel=interaction.channel,
        message=message
    )
    update_leaderboard(interaction.user.id, "custom-raid")




class PingButton(discord.ui.View):
    def __init__(self, user_ids: list[str], pings_per_message: int = 1):
        super().__init__(timeout=None)
        self.user_ids = user_ids
        self.pings_per_message = pings_per_message
        self.delay = 1

    @discord.ui.button(label="🔁 Ping!", style=discord.ButtonStyle.red)
    async def ping_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.user_ids:
            await interaction.response.send_message("⚠️ No IDs available to ping.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        max_retries = 2

        for _ in range(5):
            selected_ids = random.sample(self.user_ids, min(self.pings_per_message, len(self.user_ids)))
            mentions = " ".join(f"<@{uid}>" for uid in selected_ids)
            pingmsg = '''
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
                                  ***@ZNE**   `🌙`
                  raid b__o__t  ﹒ s__o__cial  ﹒ to__xic__
                         `🌟`     _join to [RAID](https://tenor.com/view/playboi-carti-discord-discord-raid-gif-21005635) any server __Without Admin perms__, free to use_ :moneybag: 

⠀⠀⠀⠀⠀⠀⠀                            **[JOIN](https://discord.gg/4urameavzE) TODAY, AND R__AI__D EVER__Y__ SERVER YOU WANT WITHOUT [ADMIN](https://tenor.com/view/mooning-show-butt-shake-butt-pants-down-gif-17077775)**
            '''
            message_content = f"{mentions}\n{pingmsg}"
            retries = 0
            while retries <= max_retries:
                try:
                    await interaction.followup.send(message_content, ephemeral=False)
                    break
                except discord.errors.HTTPException as e:
                    if e.status == 429:
                        retry_after = getattr(e, "retry_after", 1.5)
                        retry_after = min(retry_after, 5)
                        print(f"Rate limit hit, retrying after {retry_after:.2f}s (retry {retries + 1}/{max_retries})")
                        await asyncio.sleep(retry_after)
                        retries += 1
                    else:
                        raise e
            else:
                print("Failed to send message after max retries, skipping.")


@bot.tree.command(name="ping", description="Ping random user IDs from a .txt file using a button.")
@app_commands.describe(
    file="A .txt file containing user IDs (one per line)",
    pings_per_message="amount of users to ping per message (most servers block 5+ pings per message so keep it low)"
)
@app_commands.rename(pings_per_message="amount")
async def ping_from_file(
    interaction: discord.Interaction,
    file: discord.Attachment,
    pings_per_message: int = 1
):

    try:
        if not file.filename.endswith(".txt"):
            await interaction.response.send_message("❌ Please upload a valid `.txt` file with user IDs.", ephemeral=True)
            return

        file_content = await file.read()
        text = file_content.decode("utf-8")
        user_ids = [line.strip() for line in text.splitlines() if line.strip().isdigit()]

        if not user_ids:
            await interaction.response.send_message("⚠️ No valid user IDs found in the file.", ephemeral=True)
            return

        view = PingButton(user_ids, pings_per_message)
        await interaction.response.send_message("🔴 Click to ping random users!", view=view, ephemeral=True)


    except Exception as e:
        if interaction.response.is_done():
            await interaction.followup.send(f"❌ Error: `{e}`", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ Error: `{e}`", ephemeral=True)




class AvatarView(discord.ui.View): # made that shit in 5min its really ass
    def __init__(self, user: discord.User, banner_url: str = None):
        super().__init__()
        avatar_url = user.display_avatar.url

        self.add_item(discord.ui.Button(label="Download Avatar as JPG", url=avatar_url + "?format=jpg"))
        self.add_item(discord.ui.Button(label="Download Avatar as PNG", url=avatar_url + "?format=png"))

        if banner_url:
            self.add_item(discord.ui.Button(
                label="View Banner",
                style=discord.ButtonStyle.blurple, 
                url=banner_url
            ))
            self.add_item(discord.ui.Button(label="Download Banner as JPG", url=banner_url + "?format=jpg"))
            self.add_item(discord.ui.Button(label="Download Banner as PNG", url=banner_url + "?format=png"))

class AvatarView(discord.ui.View):
    def __init__(self, user: discord.User, banner_url: str = None):
        super().__init__()
        avatar_url = user.display_avatar.url

        self.add_item(discord.ui.Button(label="Download Avatar", url=avatar_url + "?format=png"))

        if banner_url:
            self.add_item(discord.ui.Button(label="Download Banner", url=banner_url + "?format=png"))

@bot.tree.command(name="avatar", description="Get a user's avatar and banner.")
@app_commands.describe(user="The user whose avatar you want to see")
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def avatar(interaction: discord.Interaction, user: discord.User = None):
    user = user or interaction.user

    full_user = await interaction.client.fetch_user(user.id)
    banner_url = full_user.banner.url if full_user.banner else None

    embed = discord.Embed(
        title=f"{user.display_name}'s Avatar & Banner",
        color=0xa874d1
    )
    
    embed.set_thumbnail(url=user.display_avatar.url)

    if banner_url:
        embed.set_image(url=banner_url)

    embed.set_footer(
        text=f"Requested by {interaction.user.display_name}",
        icon_url=interaction.client.user.avatar.url if interaction.client.user.avatar else None
    )

    view = AvatarView(user, banner_url)

    await interaction.response.send_message(embed=embed, view=view)

    await log_command_use(
        user=interaction.user,
        command_name="avatar",
        channel=interaction.channel,
        message=user.display_avatar.url
    )


class FloodButton(discord.ui.View):
    def __init__(self, message, delay):
        super().__init__()
        self.message = message
        self.delay = delay

    @discord.ui.button(label="⚡ Execute Command", style=discord.ButtonStyle.blurple)
    async def flood_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        max_retries = 2

        for _ in range(5):
            retries = 0
            while retries <= max_retries:
                try:
                    await interaction.followup.send(self.message, allowed_mentions=discord.AllowedMentions(everyone=True))
                    await asyncio.sleep(self.delay + random.uniform(0.1, 0.5))
                    break
                except discord.errors.HTTPException as e:
                    if e.status == 429:
                        retry_after = getattr(e, "retry_after", 1.5)
                        retry_after = min(retry_after, 5)
                        print(f"{Fore.YELLOW}>{Fore.WHITE} Rate limit hit, retrying after {Fore.YELLOW}{retry_after:.2f}s{Fore.WHITE} (retry {Fore.YELLOW}{retries + 1}{Fore.WHITE}/{Fore.YELLOW}{max_retries}{Fore.WHITE})")
                        await asyncio.sleep(retry_after)
                        retries += 1
                    else:
                        raise e
            else:
                print(f"{Fore.RED}>{Fore.WHITE} Failed to send message after max retries, skipping{Fore.RED}.{Fore.WHITE}")



class IPView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

@bot.tree.command(name="ip", description="Reveal a user's IP to scare them! (fake)")
@app_commands.describe(user="The user you want to trace")
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def ip(interaction: discord.Interaction, user: discord.User):
    fake_ip = ".".join(str(random.randint(1, 255)) for _ in range(4))
    port = random.choice([22, 443, 8080])
    trace_id = f"#ZTA-{random.randint(1000, 9999)}"

    embed = discord.Embed(
        title="🚨 CRITICAL: Unauthorized Network Access Detected",
        description=(
            f"Intrusion Detection System has traced your connection: **IP {fake_ip}, Port {port}**, Subnet **255.255.255.0**.\n"
            f"Your activity has been flagged as a potential security breach and logged for further analysis. "
            f"Cease unauthorized actions immediately or face escalation.\n\n"
            f"🔒 **Security Alert**\n"
            f"Your IP address has been identified as: **{fake_ip}**. This information has been logged for security monitoring.\n\n"
            f"**Threat Level**: HIGH\n"
            f"**Trace ID**: `{trace_id}`\n"
            f"**Timestamp**: {discord.utils.format_dt(interaction.created_at, style='F')}"
        ),
        color=discord.Color.red()
    )

    await interaction.response.send_message("🔍 Tracing IP...", ephemeral=True)

    await interaction.followup.send(
        content=f"{user.mention}",
        embed=embed,
        view=IPView()
    )
    await log_command_use(interaction.user, "ip reveal")
    update_leaderboard(interaction.user.id, "ip")

@ip.error
async def ip_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.errors.TransformError):
        await interaction.response.send_message("User not found. Please mention a valid member.", ephemeral=True)
    else:
        await interaction.response.send_message(f"An error occurred: {error}", ephemeral=True)

import base64


def get_badges(user: discord.Member) -> str:
    flags = user.public_flags
    badges = []

    if flags.hypesquad: badges.append("🏠 HypeSquad")
    if flags.hypesquad_bravery: badges.append("🦁 Bravery")
    if flags.hypesquad_brilliance: badges.append("🧠 Brilliance")
    if flags.hypesquad_balance: badges.append("⚖️ Balance")
    if flags.early_supporter: badges.append("🌟 Early Supporter")
    if flags.staff: badges.append("👔 Staff")
    if flags.partner: badges.append("🤝 Partner")
    if flags.verified_bot: badges.append("🤖 Verified Bot")
    if flags.verified_bot_developer: badges.append("👨‍💻 Bot Dev")

    return ", ".join(badges) if badges else "No Badges"

@bot.tree.command(name="hack", description="Hack to scare them! (fake)")
@app_commands.describe(user="The user you want to hack")
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def hack(interaction: discord.Interaction, user: discord.User):
    user_id_str = str(user.id)
    b64_id = base64.b64encode(user_id_str.encode()).decode()[:-2]

    badges = get_badges(user)

    file_options = [
        "stealer_base_23.04.2025.txt",
        "stealer_base_11.10.2022.db",
        "stealer_logs_240520.txt",
        "stealer_base202401.db",
        "breach_base_01_03_2021.txt",
        "breach_logs_2025.txt"
        "stealer_base_23.04.2025.txt",
        "stealer_base_11.10.2022.db",
        "stealer_logs_240520.txt",
        "stealer_base202401.db",
        "breach_base_01_03_2021.txt",
        "breach_logs_2025.txt",
        "stealer_backup_15.08.2023.db",
        "breach_archive_202212.txt",
        "stealer_data_03122024.db",
        "breach_base_99_99_9999.txt",
        "stealer_records_07.07.2020.txt",
        "logs_stealer_202503.db",
        "breach_dump_12_12_2022.txt",
        "stealer_cache_20240115.db",
        "breach_data_2025_backup.txt",
        "stealer_base_old_201901.db"
    ]
    found_in_file = random.choice(file_options)

    embed = discord.Embed(
        title=f"Found in: {found_in_file}",
        color=discord.Color.purple()
    )

    embed.add_field(
        name=f"{user.name} ({user.id})",
        value=(
            f"🪙 **Token:**\n`{b64_id}****`\n\n"
            f":e_mail:  Gmail: `Hidden`\n"
            f":iphone: Phone: `Hidden`\n"
            f":globe_with_meridians: Earth IP: `Hidden`"
        ),
        inline=False
    )

    embed.add_field(name="🎖 Badges:", value=badges, inline=True)
    embed.add_field(name="💳 Billing:", value="`(no billing)`", inline=True)
    embed.add_field(name="👥 HQ Friends:", value="`None`", inline=True)
    embed.add_field(name="🌍 Guilds:", value="`None`", inline=True)
    embed.add_field(name="🎁 Gift codes:", value="`None`", inline=True)

    embed.set_thumbnail(url=user.avatar.url if user.avatar else None)
    embed.set_footer(text="ZNE")

    await interaction.response.send_message(":computer: breaching account...", ephemeral=True)

    await interaction.followup.send(
        content=f"{user.mention}",
        embed=embed,
        view=IPView()
    )


@hack.error
async def hack_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.errors.TransformError):
        await interaction.response.send_message("User not found. Please mention a valid member.", ephemeral=True)
    else:
        await interaction.response.send_message(f"An error occurred: {error}", ephemeral=True)



RAGEBAIT = ["""
# JOIN ZNE AND START RAIDING
# JOIN ZNE AND START RAIDING
# JOIN ZNE AND START RAIDING
# JOIN ZNE AND START RAIDING
# JOIN ZNE AND START RAIDING
# JOIN ZNE AND START RAIDING
# JOIN ZNE AND START RAIDING
# JOIN ZNE AND START RAIDING
# JOIN ZNE AND START RAIDING
# JOIN ZNE AND START RAIDING
# JOIN ZNE AND START RAIDING
# JOIN ZNE AND START RAIDING
# JOIN ZNE AND START RAIDING
# JOIN ZNE AND START RAIDING
# JOIN ZNE AND START RAIDING
# JOIN ZNE AND START RAIDING
# JOIN ZNE AND START RAIDING
# JOIN ZNE AND START RAIDING
# JOIN ZNE AND START RAIDING
# JOIN ZNE AND START RAIDING
# JOIN ZNE AND START RAIDING
# JOIN ZNE AND START RAIDING
# JOIN ZNE AND START RAIDING
# JOIN ZNE AND START RAIDING
# JOIN ZNE AND START RAIDING
# JOIN ZNE AND START RAIDING
# JOIN ZNE AND START RAIDING
@everyone
discord.gg/4urameavzE
https://tenor.com/view/mooning-show-butt-shake-butt-pants-down-gif-17077775
https://media.discordapp.net/attachments/1215053612028526653/1219435249763750028/1218622476645564527_1650x1080.gif?ex=686c5f93&is=686b0e13&hm=1f0bd7f260f88162001a02772b415d14168a43cf7ee7cc94c2c9f03af54d9bed&
    """,
    """
# YOU HAVE BEEN RAIDED BY [ZNE 🆘](https://tenor.com/view/mooning-show-butt-shake-butt-pants-down-gif-17077775)
# RAID ANY SERVER WITHOUT ADMIN PERMS 🔐
# FREE, EASY TO USE, UP 24/7
# ANONYMOUSLY RAID ANY SERVER YOU WANT
# "IF YOU CANT BEAT THEM, [JOIN](https://discord.gg/4urameavzE) THEM! @everyone"
⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀                            [JOIN ZNE, RAID ANY SERVER YOU WANT, ANYTIME, ANYWHERE, ANYWHERE](https://discord.gg/4urameavzE)
 
[穹忩犈垃箚泗趨菋纳攇幀驼懅七](https://cdn.discordapp.com/attachments/1153733814732992573/1166450104350290020/d480327590432d30f979d4ce46baea6b.gif?ex=686e1290&is=686cc110&hm=312bf638b772621b7e9f33ac2f62832c5d417a7dbd08a307d5ae94e96cc9d8d1&)
    """,
    """
# [ZNE](https://discord.gg/4urameavzE) OWNS ME AND ALL :zany_face: 
# GET RAIDED U BRAINDEAD NIGGERS :rofl: :rofl: :rofl:
# IMAGINE U CANT SETUP A SERVER LMAOOOO
# BETTER [JOIN](https://discord.gg/4urameavzE) ZNE AND START RAIDING U TWAT 
https://tenor.com/view/cat-hacking-silly-cat-hacker-cat-hacker-gif-14852445362476137270
[穹忩犈垃箚泗趨菋纳攇幀驼懅七](https://cdn.discordapp.com/attachments/1153733814732992573/1166450104350290020/d480327590432d30f979d4ce46baea6b.gif?ex=686e1290&is=686cc110&hm=312bf638b772621b7e9f33ac2f62832c5d417a7dbd08a307d5ae94e96cc9d8d1&)
@everyone
    """,
    """
# [ZNE](https://tenor.com/view/flashbang-guy-screaming-guy-getting-flashbang-blinded-blinding-gif-1425127881206275521) __DOMINATES__ ALL 👑
# GET __RAIDED__, YOU RETARDS CAN'T HANDLE THIS 😭 🥀 🥀
# IMAGINE NOT BEING ABLE TO SETUP A SERVER LMAO
# BETTER [JOIN](https://discord.gg/4urameavzE) ZNE AND START RAIDING, YOU KNOW YOU WANT TO!
@everyone
    """
]


SCARY = [
    """
    # [ZNE](https://media.tenor.com/uw5s-aHlviAAAAAM/scary-ghost.gif)
    # [ZNE](https://discord.gg/4urameavzE)
    # [ZNE](https://tenor.com/view/yapping-creepy-under-the-bed-talking-ghost-gif-10296050582380126660)
    # [ZNE](https://cdn.discordapp.com/attachments/1416037733322719364/1418258241879539733/RussianSleepExperimentGuy.png?ex=68cd776a&is=68cc25ea&hm=4141a571871aebcf5e93aa57d505285a924103536892e8a5b3ff0636c7ff2590&)
    @everyone
    """,
    """
    # [ZNE](https://media.tenor.com/HMtY33kDWFwAAAAM/donk.gif)
    # [ZNE](https://nightmarenostalgia.com/wp-content/uploads/2023/07/main-qimg-522ae83e590c80bfaf895b3919462bcb.gif?w=480)
    # [ZNE](https://media.tenor.com/ihDOwbsgwRcAAAAM/scary-scary-face.gif)
    # [ZNE](https://discord.gg/4urameavzE)
    @everyone
    """
]

THUG = [
"""
# @everyone
# https://discord.gg/4urameavzE
# https://cdn.discordapp.com/attachments/1328198321549873170/1435067852125241404/x-downloader.com_sQe9oS.mov?ex=690bf016&is=690a9e96&hm=d4d55bfaa3caa06e5c00b143dce3601fdf398c94487aece676149d146d7bcf92&
# https://cdn.discordapp.com/attachments/1328198321549873170/1435334505769734225/lv_0_20251104202536.mp4?ex=690c3fad&is=690aee2d&hm=152cadada93f4a3b492a809dab92a6c57577800100aea6e4445d7dc7b9596f98&
# https://cdn.discordapp.com/attachments/1328198321549873168/1434966854354342042/Screen_Recording_20250318_213048_Discord.mp4?ex=690c3ac6&is=690ae946&hm=bd3371ef632a82835603513867a3659b4c20f6bea9301e6555ba6d6118d06e80&
""",

"""
# @everyone
# https://discord.gg/4urameavzE
# https://cdn.discordapp.com/attachments/1328198321549873168/1434998533391384638/caption.gif?ex=690baf87&is=690a5e07&hm=e3f21c157324c2d17cfbd2c2805c2137b10273860eb3f64fa1f0e615c9aa566a&
# https://cdn.discordapp.com/attachments/1328198321549873168/1435044195571339264/yallgonmakmibus.mp4?ex=690bda0e&is=690a888e&hm=87269b7b8d8fcf4177124f0816a16f974122f1d2d909ac2e8306d9602bfb6c0f&
# https://cdn.discordapp.com/attachments/1328198321549873168/1435396524166221967/RDT_20231016_230719.mp4?ex=690bd0af&is=690a7f2f&hm=2cf3a1940b2e80bff7e42bf5b55e71a7163b1f7f487ea257fdfff9be3c7c4b6a&
""",

"""
# @everyone
# https://discord.gg/4urameavzE
# https://cdn.discordapp.com/attachments/1328198321549873168/1434752159425232977/image0.jpg?ex=690c1b93&is=690aca13&hm=9656386d21da56a252912e47a088fd05734084dc3f2f87db875fd77b7ac37a15&
# https://cdn.discordapp.com/attachments/1328198321549873168/1434713726350528626/lv_0_20240713232041-1.mp4?ex=690bf7c8&is=690aa648&hm=5a092fcef3b135bc57e42c3592792274746c4f91295aac3c791c17850c2fe3ca&
# https://cdn.discordapp.com/attachments/1328198321549873168/1434713437942055061/-1390408780751690326.mp4?ex=690bf783&is=690aa603&hm=23f5fc559986200021585d19fb03edd43884af53840374bc0e07f4229fef4fec&
""",

"""
# @everyone
# https://discord.gg/4urameavzE
# https://cdn.discordapp.com/attachments/1328198321549873168/1436391015232700537/ssstwitter.com_1762382218309.mp4?ex=691017a0&is=690ec620&hm=c748644e56064aa68c9f4569536a356b7968fc66c00c057a831b3f1f8f48edc4&
# https://cdn.discordapp.com/attachments/1328198321549873168/1436328764505063477/BIRTHDAY-1.mp4?ex=69108667&is=690f34e7&hm=71fb41800d363202ef54ce092c12c85d9663d2a343fdb0caa63fae399fc14d64&
# https://cdn.discordapp.com/attachments/1328198321549873168/1436173818442809455/2025-10-13-223055307.mp4?ex=690ff619&is=690ea499&hm=bec1cf145e3c3803130036f6c160fb5dedb8e7b6cca3c4ae25ba80ed9913efbb&
""",

"""
# @everyone
# https://discord.gg/4urameavzE
# https://cdn.discordapp.com/attachments/1328198321549873168/1436173202207281352/655387ff42aa253083283c7e32d6115a.mp4?ex=690ff586&is=690ea406&hm=7f0f9fd031deca53912583a182f70031240918cdea99dc3ab41ef9c346c1e402&
# https://cdn.discordapp.com/attachments/1328198321549873168/1436171490587574323/IMG-20250829-WA0103.jpg?ex=690ff3ee&is=690ea26e&hm=04dd9b9136fd5b48812f4f3ff5f04c1c42d59b0c078214f7059b38a9ee8f8859&
# https://cdn.discordapp.com/attachments/1328198321549873168/1436059623063818301/Screenshot_2025-07-15_214614.png?ex=6910347e&is=690ee2fe&hm=6a0ccb1b5d9ec5726f57708d61d375b2e94092ce8cafa5ec2276753d15327e76&
"""
]

class BspamButton(discord.ui.View):
    def __init__(self, spam_texts, delay):
        super().__init__(timeout=900)
        self.spam_texts = spam_texts
        self.delay = delay

    @discord.ui.button(label="🚨 Spam Button", style=discord.ButtonStyle.danger)
    async def start_spam(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        for _ in range(20):
            random_text = random.choice(self.spam_texts)
            await interaction.followup.send(random_text, allowed_mentions=discord.AllowedMentions(everyone=True))
            await asyncio.sleep(self.delay)



@bot.tree.command(name="b-spam", description="Spam random messages with different styles.")
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.describe(
    style="Choose spam style (ragebait, scary, ascii, hentai)",
    delay="Delay between messages (0.01 to 5.00 seconds)."
)
async def bspam(interaction: discord.Interaction, style: str, delay: float = 0.5):
    if delay < 0.01 or delay > 5.00:
        await interaction.response.send_message(
            "**Error: Delay must be between 0.01 and 5.00 seconds.**",
            ephemeral=True
        )
        return

    style = style.lower()
    if style == "ragebait":
        spam_list = RAGEBAIT
    elif style == "scary":
        spam_list = SCARY
    elif style == "thug":
        spam_list = THUG
    else:
        await interaction.response.send_message("❌ Invalid style! Choose `standart`, `scary` or `ascii`.", ephemeral=True)
        return

    view = BspamButton(spam_list, delay)
    await interaction.response.send_message(
        f"🚨 Press the button to start spamming\n mode: **{style.upper()}**",
        view=view,
        ephemeral=True
    )



@bspam.autocomplete("style")
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def style_autocomplete(interaction: discord.Interaction, current: str):
    styles = ["ragebait", "scary", "thug"]
    return [
        app_commands.Choice(name=s, value=s)
        for s in styles if current.lower() in s
    ]


@bot.tree.command(name="a-raid", description="RAID Any Server.")
@app_commands.describe(delay="Delay between messages in seconds (0.01 to 5.00).")
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.user_install()
async def araid(interaction: discord.Interaction, delay: float = 0.01):
    if delay < 0.01 or delay > 5.00:
        await interaction.response.send_message("**Error: Delay must be between 0.01 and 5.00 seconds.**", ephemeral=True)
        return

    raid_message = '''
    # @everyone
    ## **Can't** even *Setup a Server* properly LMAO join **ZNE** for fast and EASY Raiding today!
    # ZNE owns you For Sure!, Join NOW for **Easy Raiding**
    # **THE** Only server who *isn't* a [Discord Gangster](https://tenor.com/view/playboi-carti-discord-discord-raid-gif-21005635)
    # [Join](https://discord.gg/4urameavzE) ZNE today
'''
    try:
        view = FloodButton(raid_message, delay)
        await interaction.response.send_message("Press the button to start raiding.", view=view, ephemeral=True)
    except discord.HTTPException as e:
        if e.code == 40094:  # follow-up message limit reached
            print(f"[A-RAID ERROR] Max follow-up messages reached for interaction {interaction.id}")
        else:
            print(f"[A-RAID ERROR] Unexpected HTTPException: {e}")
            raise

    await log_command_use(
        user=interaction.user,
        command_name="a-raid",
        channel=interaction.channel
    )
    update_leaderboard(interaction.user.id, "a-raid")



@bot.tree.command(name="say", description="Make the bot say something you want, anonymously.")
@app_commands.describe(message="The message you want the bot to say.")
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.user_install()
async def say(interaction: discord.Interaction, message: str):
    if is_premium_user(interaction.user.id):
        full_message = f"{message}"
    else:
        full_message = f"{message} \n\n discord.gg/4urameavzE"

    await interaction.response.send_message("Sending.. 🔊", ephemeral=True)
    allowed = discord.AllowedMentions(everyone=True, users=True, roles=True)
    await interaction.followup.send(full_message, allowed_mentions=allowed)

    await log_command_use(
        user=interaction.user,
        command_name="say",
        message=message,
        channel=interaction.channel
    )
    update_leaderboard(interaction.user.id, "say")


@bot.tree.command(
    name="ghostping",
    description="GhostPing Somebody multiple times! The best delay is 0.3 seconds"
)
@app_commands.describe(
    user="📔 The user you want to ghost ping",
    seconds="🕰️ The delay (in seconds) before each message is deleted. Best is 0.3 🕰️",
    times="🔁 How many times to ghost ping them 🔁"
)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.user_install()
async def ghostping(
    interaction: discord.Interaction,
    user: discord.User,
    seconds: float = 0.3,
    times: int = 3
):
    await interaction.response.send_message("Ghost pinging...", ephemeral=True)
    await log_command_use(interaction.user, "ghostping")
    update_leaderboard(interaction.user.id, "ghostping")

    for i in range(times):
        try:
            message = await interaction.followup.send(f"{user.mention}")
            await asyncio.sleep(seconds)
            await message.delete()
        except discord.HTTPException as e:
            if e.code == 40094:  
                print(f"[ghostping] follow up messages reached – stopped after {i} pings.")
                break
            else:
                raise

whitelist = config.get("whitelist", [])

@bot.tree.command(name="x-add-premium", description="Grant premium access to a user. (owner only)")
@app_commands.describe(user="The user to grant premium access to")
async def add_premium(interaction: discord.Interaction, user: discord.User):
    if interaction.user.id not in whitelist:
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return
    
    add_premium_user(user.id)
    await interaction.response.send_message(f"✅ {user.mention} has been granted premium access!", ephemeral=False)

@bot.tree.command(name="x-rem-premium", description="Remove premium access from a user. (owner only)")
@app_commands.describe(user="The user to remove premium access from")
async def rem_premium(interaction: discord.Interaction, user: discord.User):
    if interaction.user.id not in whitelist:
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return

    removed = remove_premium_user(user.id)
    if removed:
        await interaction.response.send_message(f"✅ User {user.mention} has been removed from premium access!", ephemeral=False)
    else:
        await interaction.response.send_message(f"⚠️ User {user.mention} does not have premium access.", ephemeral=True)



class RoastButton(discord.ui.View):
    def __init__(self, user: discord.User, delay: float = 0.5):
        super().__init__()
        self.user = user
        self.delay = delay

    @discord.ui.button(label="⚡ Send Roast", style=discord.ButtonStyle.blurple)
    async def roast_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        max_retries = 2

        try:
            with open("roasts.txt", "r", encoding="utf-8") as f:
                roasts = [line.strip() for line in f if line.strip()]
            if not roasts:
                await interaction.followup.send("No roasts found 😅")
                return
        except FileNotFoundError:
            await interaction.followup.send("The file `roasts.txt` was not found.")
            return

        for _ in range(5):
            roast_text = random.choice(roasts)
            retries = 0
            while retries <= max_retries:
                try:
                    allowed = discord.AllowedMentions(everyone=True, users=True, roles=True)
                    await interaction.followup.send(f"{roast_text} {self.user.mention}", allowed_mentions=allowed)
                    await asyncio.sleep(self.delay + random.uniform(0.1, 0.5))
                    break
                except discord.errors.HTTPException as e:
                    if e.status == 429:
                        retry_after = getattr(e, "retry_after", 1.5)
                        retry_after = min(retry_after, 5)
                        print(f"Rate limit hit, retrying after {retry_after:.2f}s (retry {retries + 1}/{max_retries})")
                        await asyncio.sleep(retry_after)
                        retries += 1
                    else:
                        raise e
            else:
                print("Failed to send roast after max retries, skipping.")


@bot.tree.command(name="roast", description="Send a random roast to a user via button.")
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.describe(user="The user to roast")
async def roast(interaction: discord.Interaction, user: discord.User):
    view = RoastButton(user, delay=0.5)
    await interaction.response.send_message("Press the button to send roasts! (5 per click)", view=view, ephemeral=True)



def random_time_today():
    base_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    random_minutes = random.randint(0, 23 * 60 + 59)  # 0 bis 1439 Minuten
    random_time = base_date + timedelta(minutes=random_minutes)
    return random_time

@bot.tree.command(name="spoof-message", description="Send a realistic fake message as image.")
@app_commands.describe(username="Name to display", message="Fake message to show", avatar_url="Avatar image URL")
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def spoof_image(interaction: discord.Interaction, username: str, message: str, avatar_url: str = None):
    await interaction.response.send_message("🕵️ Spoofing message...", ephemeral=True)

    if not avatar_url:
        avatar_url = "https://cdn.discordapp.com/embed/avatars/0.png"

    response = requests.get(avatar_url)
    avatar = Image.open(BytesIO(response.content)).convert("RGBA")
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
    now = random_time_today().strftime("Today at %I:%M %p").lstrip("0").replace(" 0", " ")

    draw.text((70, 18), username, font=font_bold, fill=(255, 255, 255))
    draw.text((70 + draw.textlength(username, font=font_bold) + 10, 21), now, font=font_timestamp, fill=(153, 170, 181))
    draw.text((70, 45), message, font=font_regular, fill=(220, 221, 222))

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    file = discord.File(fp=buffer, filename="spoof.png")

    await interaction.followup.send(file=file)

    await log_command_use(user=interaction.user, command_name="spoof-message", message=message)
    update_leaderboard(interaction.user.id, "spoof-message")



@bot.tree.command(name="blame", description="Blame somebody else for raiding, and get them banned!")
@app_commands.describe(user="📰 The user you want to blame..")
async def blame(interaction: discord.Interaction, user: discord.User):
    await interaction.response.send_message("Blaming... ✏️", ephemeral=True)
    await interaction.followup.send(f"{user.mention}, Your Raid Command has been Successfully Completed! ✅")
    await log_command_use(interaction.user, "blame")



@bot.tree.command(name="anon-dm", description="Anonymously DM someone with a message.")
@app_commands.describe(user="The user you want to DM", message="The message to send")
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.user_install()
async def anon_dm(interaction: discord.Interaction, user: discord.User, message: str):
    try:
        await user.send(f"{message}")
        await interaction.response.send_message("Message sent anonymously ✅", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message("❌ Couldn't send message. User has DMs closed.", ephemeral=True)
    await log_command_use(
        user=interaction.user,
        command_name="anon-dm",
        channel=interaction.channel,
        message=message
    )


@bot.tree.command(name="flooduser", description="[💎] Flood a user's DMs with messages. (premium only!)")
@app_commands.describe(user="The user to DM spam", message="Message to spam", times="How many times to send", delay="Delay between messages (in sec)")
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.user_install()
async def flooduser(interaction: discord.Interaction, user: discord.User, message: str, times: int = 5, delay: float = 0.3):
    if not is_premium_user(interaction.user.id):
     await interaction.response.send_message("💎 This command is only available for premium users.", ephemeral=True)
     return
    await interaction.response.send_message("Flooding user... 💣", ephemeral=True)
    await log_command_use(
        user=interaction.user,
        command_name="💎 flooduser",
        channel=interaction.channel,
        message=message
    )
    for _ in range(times):
        try:
            await user.send(message)
            await asyncio.sleep(delay)
        except discord.Forbidden:
            await interaction.followup.send("❌ Could not DM user (they may have DMs closed).", ephemeral=True)
            break



@bot.event
async def on_ready():
    print(logo)
    print(f"{Fore.MAGENTA}>{Fore.WHITE} Logged in as {Fore.MAGENTA}{bot.user}{Fore.WHITE}.")
    try:
        synced = await bot.tree.sync()
        print(f"{Fore.MAGENTA}>{Fore.WHITE} Synced {Fore.MAGENTA}{len(synced)} {Fore.WHITE}commands{Fore.MAGENTA}.{Fore.WHITE}")
    except Exception as e:
        print(f"Failed to sync commands: {e}")


if __name__ == "__main__":
    TOKEN = "enter the token here boi"

    while True:
        try:
            bot.run(TOKEN)
        except discord.errors.LoginFailure:
            print(Fore.RED + "Can't connect to token. Invalid token.")
            break
        except Exception as e:
            print(Fore.RED + f"An unexpected error occurred: {e}")
            input(Fore.YELLOW + "Press Enter to restart...")
