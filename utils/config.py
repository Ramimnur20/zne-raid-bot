import json

with open("config.json", "r") as f:
    config = json.load(f)

TOKEN = config["TOKEN"]
OWNER_IDS = config["owner_ids"]
LOG_CHANNEL_ID = config.get("log_channel_id", 1474431646651387935)

DEFAULT_BUTTON_MESSAGE = """
# YOUR SERVER JUST GOT RAIDED BY [ZNE](https://discord.gg/sillyz)
** **          JOIN ZNE TODAY FOR FREE RAIDS 🚨 
> # OUR BOT **DOESN'T** REQUIRE MONEY 💰
-# also your server is shitty @everyone @here
"""
