import asyncio
import json
import logging
import os

logger = logging.getLogger(__name__)

LEADERBOARD_PATH = os.path.abspath("leaderboard.json")


def _to_int(value) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _normalize_entry(entry: dict) -> dict:
    normalized = {"total_commands": _to_int(entry.get("total_commands", 0))}

    for key, value in entry.items():
        if key in {"userid", "user_id", "id", "total_commands"}:
            continue
        normalized[key] = _to_int(value)

    return normalized


def _entry_to_row(user_id: str, entry: dict) -> dict:
    row = {"userid": str(user_id), "total_commands": _to_int(entry.get("total_commands", 0))}

    for key, value in entry.items():
        if key in {"userid", "user_id", "id", "total_commands"}:
            continue
        row[key] = _to_int(value)

    return row


def _normalize_users(data) -> tuple[dict, int]:
    users = {}
    global_total = 0

    if isinstance(data, list):
        for entry in data:
            if not isinstance(entry, dict):
                continue
            user_id = entry.get("userid") or entry.get("user_id") or entry.get("id")
            if not user_id:
                continue
            normalized = _normalize_entry(entry)
            users[str(user_id)] = normalized
            global_total += normalized["total_commands"]
        return users, global_total

    if not isinstance(data, dict):
        return users, global_total

    if "users" in data:
        user_data = data["users"]
    else:
        user_data = data

    if isinstance(user_data, list):
        for entry in user_data:
            if not isinstance(entry, dict):
                continue
            user_id = entry.get("userid") or entry.get("user_id") or entry.get("id")
            if not user_id:
                continue
            normalized = _normalize_entry(entry)
            users[str(user_id)] = normalized
            global_total += normalized["total_commands"]
    elif isinstance(user_data, dict):
        for user_id, entry in user_data.items():
            if not isinstance(entry, dict):
                continue
            users[str(user_id)] = _normalize_entry(entry)
            global_total += users[str(user_id)]["total_commands"]

    if "users" in data:
        global_total = _to_int(data.get("global_total_commands", global_total))

    return users, global_total


def load_leaderboard() -> tuple[dict, int]:
    if not os.path.exists(LEADERBOARD_PATH):
        return {}, 0

    try:
        with open(LEADERBOARD_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        logger.error(f"Failed to load {LEADERBOARD_PATH}: {e}")
        return {}, 0

    return _normalize_users(data)


def save_leaderboard(data: dict, global_total: int):
    tmp_path = f"{LEADERBOARD_PATH}.tmp"
    rows = [_entry_to_row(user_id, entry) for user_id, entry in data.items()]
    rows.sort(key=lambda row: row["userid"])
    payload = {
        "global_total_commands": global_total,
        "users": rows,
    }
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
        f.write("\n")
    os.replace(tmp_path, LEADERBOARD_PATH)


async def track_command(user_id: str, command_name: str):
    data, global_total = load_leaderboard()
    user_id = str(user_id)
    command_name = str(command_name)

    entry = data.setdefault(user_id, {"total_commands": 0})
    entry["total_commands"] = _to_int(entry.get("total_commands", 0)) + 1
    entry[command_name] = _to_int(entry.get(command_name, 0)) + 1

    global_total += 1
    await asyncio.to_thread(save_leaderboard, data, global_total)
