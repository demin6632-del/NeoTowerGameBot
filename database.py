import json
import sqlite3
import time

DATABASE = "neotower.db"


def connect():
    db = sqlite3.connect(DATABASE, timeout=30)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA busy_timeout=30000")
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA synchronous=NORMAL")
    db.execute("PRAGMA foreign_keys=ON")
    return db


def init_db():
    db = connect()
    cursor = db.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS players(
        id INTEGER PRIMARY KEY,
        name TEXT,
        hero TEXT,
        hp INTEGER,
        damage INTEGER,
        armor INTEGER,
        level INTEGER,
        xp INTEGER,
        floor INTEGER,
        credits INTEGER,
        inventory TEXT,
        equipment TEXT
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS battle_sessions(
        user_id INTEGER PRIMARY KEY,
        state TEXT NOT NULL,
        updated_at INTEGER NOT NULL
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS daily_rewards(
        user_id INTEGER PRIMARY KEY,
        day_key TEXT NOT NULL
    )
    """)
    db.commit()
    db.close()


def get_player(user_id):
    db = connect()
    player = db.execute(
        "SELECT * FROM players WHERE id=?",
        (user_id,),
    ).fetchone()
    db.close()
    return player


def create_player(user_id, name, hero, hp, damage, armor):
    db = connect()
    cursor = db.cursor()
    cursor.execute(
        """INSERT OR IGNORE INTO players
        (id,name,hero,hp,damage,armor,level,xp,floor,credits,inventory,equipment)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
        (user_id, name, hero, hp, damage, armor, 1, 0, 1, 0, "iron_sword", "iron_sword")
    )
    created = cursor.rowcount == 1
    db.commit()
    db.close()
    return created


def get_inventory(user_id):
    player = get_player(user_id)
    if not player or not player["inventory"]:
        return []
    return [item for item in player["inventory"].split(",") if item]


def add_reward(user_id, xp, credits, item=None):
    db = connect()
    try:
        with db:
            player = db.execute(
                "SELECT * FROM players WHERE id=?",
                (user_id,),
            ).fetchone()
            if not player:
                return

            inventory = player["inventory"] or ""
            if item and item not in inventory.split(","):
                inventory = inventory + ("," if inventory else "") + item

            new_xp = player["xp"] + xp
            new_level = max(1, 1 + new_xp // 500)
            db.execute(
                "UPDATE players SET xp=?, level=?, credits=?, inventory=? WHERE id=?",
                (new_xp, new_level, player["credits"] + credits, inventory, user_id)
            )
    finally:
        db.close()


def update_stats(user_id, hp=None, damage=None, armor=None):
    db = connect()
    try:
        with db:
            player = db.execute(
                "SELECT * FROM players WHERE id=?",
                (user_id,),
            ).fetchone()
            if not player:
                return

            db.execute(
                "UPDATE players SET hp=?, damage=?, armor=? WHERE id=?",
                (
                    hp if hp is not None else player["hp"],
                    damage if damage is not None else player["damage"],
                    armor if armor is not None else player["armor"],
                    user_id
                )
            )
    finally:
        db.close()


def equip_item(user_id, item):
    db = connect()
    try:
        with db:
            player = db.execute(
                "SELECT inventory FROM players WHERE id=?",
                (user_id,),
            ).fetchone()
            if not player:
                return False

            inventory = [x for x in (player["inventory"] or "").split(",") if x]
            if item not in inventory:
                return False

            db.execute(
                "UPDATE players SET equipment=? WHERE id=?",
                (item, user_id)
            )
            return True
    finally:
        db.close()


def unequip_item(user_id):
    db = connect()
    try:
        with db:
            db.execute(
                "UPDATE players SET equipment='' WHERE id=?",
                (user_id,)
            )
    finally:
        db.close()


def get_equipment(user_id):
    player = get_player(user_id)
    return player["equipment"] if player else ""


def next_floor(user_id):
    db = connect()
    try:
        with db:
            player = db.execute(
                "SELECT floor FROM players WHERE id=?",
                (user_id,),
            ).fetchone()
            if player:
                db.execute(
                    "UPDATE players SET floor=? WHERE id=?",
                    (player["floor"] + 1, user_id)
                )
    finally:
        db.close()


def get_battle_session(user_id):
    db = connect()
    try:
        row = db.execute(
            "SELECT state FROM battle_sessions WHERE user_id=?",
            (user_id,),
        ).fetchone()
        if not row:
            return None
        try:
            return json.loads(row["state"])
        except (TypeError, ValueError):
            db.execute("DELETE FROM battle_sessions WHERE user_id=?", (user_id,))
            db.commit()
            return None
    finally:
        db.close()


def save_battle_session(user_id, state):
    payload = json.dumps(state, ensure_ascii=False, separators=(",", ":"))
    db = connect()
    try:
        with db:
            db.execute(
                """INSERT INTO battle_sessions(user_id,state,updated_at)
                   VALUES(?,?,?)
                   ON CONFLICT(user_id) DO UPDATE SET
                   state=excluded.state,
                   updated_at=excluded.updated_at""",
                (user_id, payload, int(time.time()))
            )
    finally:
        db.close()


def delete_battle_session(user_id):
    db = connect()
    try:
        with db:
            db.execute(
                "DELETE FROM battle_sessions WHERE user_id=?",
                (user_id,)
            )
    finally:
        db.close()
