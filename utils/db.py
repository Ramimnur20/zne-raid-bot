import aiosqlite

db = None


async def init_db():
    global db
    db = await aiosqlite.connect("custom_messages.db")

    await db.execute("""
        CREATE TABLE IF NOT EXISTS user_custom_send (
            user_id TEXT PRIMARY KEY,
            message TEXT
        )
    """)

    await db.execute("""
        CREATE TABLE IF NOT EXISTS farm_counts (
            user_id TEXT PRIMARY KEY,
            count INTEGER DEFAULT 0
        )
    """)

    await db.execute("""
        CREATE TABLE IF NOT EXISTS server_blacklist (
            server_id TEXT PRIMARY KEY
        )
    """)

    await db.execute("""
        CREATE TABLE IF NOT EXISTS global_default_message (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            message TEXT
        )
    """)

    await db.execute("""
        CREATE TABLE IF NOT EXISTS user_dm_blacklist (
            user_id TEXT PRIMARY KEY
        )
    """)

    await db.execute("""
        CREATE TABLE IF NOT EXISTS user_blacklist (
            user_id TEXT PRIMARY KEY
        )
    """)

    await db.commit()


async def get_custom_message(user_id: str) -> str | None:
    async with db.execute("SELECT message FROM user_custom_send WHERE user_id = ?", (user_id,)) as cursor:
        row = await cursor.fetchone()
    return row[0] if row else None


async def set_custom_message(user_id: str, message: str):
    await db.execute(
        "INSERT OR REPLACE INTO user_custom_send (user_id, message) VALUES (?, ?)",
        (user_id, message)
    )
    await db.commit()


async def delete_custom_message(user_id: str):
    await db.execute(
        "DELETE FROM user_custom_send WHERE user_id = ?",
        (user_id,)
    )
    await db.commit()


async def is_server_blacklisted(server_id: int) -> bool:
    async with db.execute("SELECT 1 FROM server_blacklist WHERE server_id = ?", (str(server_id),)) as cursor:
        row = await cursor.fetchone()
    return row is not None


async def add_server_blacklist(server_id: int):
    await db.execute(
        "INSERT OR IGNORE INTO server_blacklist (server_id) VALUES (?)",
        (str(server_id),)
    )
    await db.commit()


async def remove_server_blacklist(server_id: int):
    await db.execute(
        "DELETE FROM server_blacklist WHERE server_id = ?",
        (str(server_id),)
    )
    await db.commit()


async def get_blacklisted_servers() -> list:
    async with db.execute("SELECT server_id FROM server_blacklist") as cursor:
        rows = await cursor.fetchall()
    return [int(row[0]) for row in rows]


async def get_global_default_message() -> str | None:
    async with db.execute("SELECT message FROM global_default_message WHERE id = 1") as cursor:
        row = await cursor.fetchone()
    return row[0] if row else None


async def set_global_default_message(message: str):
    await db.execute(
        "INSERT OR REPLACE INTO global_default_message (id, message) VALUES (1, ?)",
        (message,)
    )
    await db.commit()


async def is_user_dm_blacklisted(user_id: int) -> bool:
    async with db.execute("SELECT 1 FROM user_dm_blacklist WHERE user_id = ?", (str(user_id),)) as cursor:
        row = await cursor.fetchone()
    return row is not None


async def add_user_dm_blacklist(user_id: int):
    await db.execute(
        "INSERT OR IGNORE INTO user_dm_blacklist (user_id) VALUES (?)",
        (str(user_id),)
    )
    await db.commit()


async def remove_user_dm_blacklist(user_id: int):
    await db.execute(
        "DELETE FROM user_dm_blacklist WHERE user_id = ?",
        (str(user_id),)
    )
    await db.commit()


async def is_user_blacklisted(user_id: int) -> bool:
    async with db.execute("SELECT 1 FROM user_blacklist WHERE user_id = ?", (str(user_id),)) as cursor:
        row = await cursor.fetchone()
    return row is not None


async def add_user_blacklist(user_id: int):
    await db.execute(
        "INSERT OR IGNORE INTO user_blacklist (user_id) VALUES (?)",
        (str(user_id),)
    )
    await db.commit()


async def remove_user_blacklist(user_id: int):
    await db.execute(
        "DELETE FROM user_blacklist WHERE user_id = ?",
        (str(user_id),)
    )
    await db.commit()
