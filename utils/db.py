import asyncio
import lmdb
from concurrent.futures import ThreadPoolExecutor
import os
import logging

logger = logging.getLogger(__name__)

env = None
executor = ThreadPoolExecutor(max_workers=2)
DB_PATH = os.path.abspath("data.db")


def _open_db():
    logger.info(f"Opening LMDB database at: {DB_PATH}")
    environment = lmdb.open("data.db", max_dbs=3)
    # ... rest unchanged
    user_custom_send_db = environment.open_db(b"user_custom_send", create=True)
    farm_counts_db = environment.open_db(b"farm_counts", create=True)
    global_default_message_db = environment.open_db(b"global_default_message", create=True)
    return environment


async def init_db():
    global env
    loop = asyncio.get_event_loop()
    env = await loop.run_in_executor(executor, _open_db)


def _get_env():
    return env


async def get_custom_message(user_id: str) -> str | None:
    def _get():
        db_env = _get_env()
        with db_env.begin() as txn:
            return txn.get(user_id.encode()).decode() if txn.get(user_id.encode()) else None
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, _get)


async def set_custom_message(user_id: str, message: str):
    def _set():
        db_env = _get_env()
        with db_env.begin(write=True) as txn:
            txn.put(user_id.encode(), message.encode())
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(executor, _set)


async def delete_custom_message(user_id: str):
    def _delete():
        db_env = _get_env()
        with db_env.begin(write=True) as txn:
            txn.delete(user_id.encode())
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(executor, _delete)


async def get_global_default_message() -> str | None:
    def _get():
        db_env = _get_env()
        with db_env.begin() as txn:
            val = txn.get(b"global")
            return val.decode() if val else None
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, _get)


async def set_global_default_message(message: str):
    def _set():
        db_env = _get_env()
        with db_env.begin(write=True) as txn:
            txn.put(b"global", message.encode())
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(executor, _set)