import asyncio
import lmdb
import json
from concurrent.futures import ThreadPoolExecutor
import os
import logging

logger = logging.getLogger(__name__)

env = None
dbs = {}
executor = ThreadPoolExecutor(max_workers=2)
DB_PATH = os.path.abspath("data.db")


def _open_db():
    global dbs
    logger.info(f"Opening LMDB database at: {DB_PATH}")
    environment = lmdb.open("data.db", max_dbs=10)
    
    dbs["user_presets"] = environment.open_db(b"user_presets", create=True)
    dbs["global_default"] = environment.open_db(b"global_default_message", create=True)
    dbs["blacklisted_servers"] = environment.open_db(b"blacklisted_servers", create=True)
    dbs["blacklisted_users"] = environment.open_db(b"blacklisted_users", create=True)
    return environment


async def init_db():
    global env
    loop = asyncio.get_event_loop()
    env = await loop.run_in_executor(executor, _open_db)


def _get_env():
    return env

async def get_user_presets(user_id: str) -> list[dict]:
    def _get():
        db_env = _get_env()
        with db_env.begin(db=dbs["user_presets"]) as txn:
            raw_data = txn.get(user_id.encode())
            if raw_data:
                try:
                    return json.loads(raw_data.decode())
                except json.JSONDecodeError:
                    return []
            return []
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, _get)

async def get_preset_by_title(user_id: str, title: str) -> str | None:
    def _get():
        db_env = _get_env()
        with db_env.begin(db=dbs["user_presets"]) as txn:
            raw_data = txn.get(user_id.encode())
            if raw_data:
                presets = json.loads(raw_data.decode())
                for p in presets:
                    if p['title'] == title:
                        return p['content']
            return None
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, _get)


async def save_user_preset(user_id: str, title: str, content: str):
    def _save():
        db_env = _get_env()
        with db_env.begin(write=True, db=dbs["user_presets"]) as txn:
            presets = json.loads(txn.get(user_id.encode(), default=b"[]").decode())
            
            # Update existing preset or add new one
            found = False
            for p in presets:
                if p['title'] == title:
                    p['content'] = content
                    found = True
                    break
            if not found:
                presets.append({"title": title, "content": content, "uses": 0})
            
            txn.put(user_id.encode(), json.dumps(presets).encode())
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(executor, _save)


async def delete_user_preset(user_id: str, title: str):
    def _delete():
        db_env = _get_env()
        with db_env.begin(write=True, db=dbs["user_presets"]) as txn:
            presets = json.loads(txn.get(user_id.encode(), default=b"[]").decode())
            presets = [p for p in presets if p['title'] != title]
            txn.put(user_id.encode(), json.dumps(presets).encode())
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(executor, _delete)


async def get_global_default_message() -> str | None:
    def _get():
        db_env = _get_env()
        with db_env.begin(db=dbs["global_default"]) as txn:
            val = txn.get(b"global")
            return val.decode() if val else None
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, _get)


async def set_global_default_message(message: str):
    def _set():
        db_env = _get_env()
        with db_env.begin(write=True, db=dbs["global_default"]) as txn:
            txn.put(b"global", message.encode())
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(executor, _set)

async def is_server_blacklisted(guild_id: str) -> bool:
    def _get():
        db_env = _get_env()
        with db_env.begin(db=dbs["blacklisted_servers"]) as txn:
            return txn.get(guild_id.encode()) is not None
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, _get)

async def set_server_blacklist(guild_id: str, state: bool):
    def _set():
        db_env = _get_env()
        with db_env.begin(write=True, db=dbs["blacklisted_servers"]) as txn:
            if state:
                txn.put(guild_id.encode(), b"1")
            else:
                txn.delete(guild_id.encode())
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(executor, _set)

async def is_user_blacklisted(user_id: str) -> bool:
    def _get():
        db_env = _get_env()
        with db_env.begin(db=dbs["blacklisted_users"]) as txn:
            return txn.get(user_id.encode()) is not None
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, _get)

async def set_user_blacklist(user_id: str, state: bool):
    def _set():
        db_env = _get_env()
        with db_env.begin(write=True, db=dbs["blacklisted_users"]) as txn:
            if state:
                txn.put(user_id.encode(), b"1")
            else:
                txn.delete(user_id.encode())
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(executor, _set)