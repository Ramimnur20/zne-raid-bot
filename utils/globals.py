# Global variables shared across the bot
import json
import os

DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "data.json")


def _load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


_data = _load_data()
command_count = _data.get("command_count", 0)


def save_command_count():
    _data["command_count"] = command_count
    _save_data(_data)
