import json
import os
import sqlite3
import time

from inventory import ITEMS

# On Render, point DATABASE_PATH at a mounted persistent disk (for example /var/data/neotower.db).
DATABASE = os.getenv("DATABASE_PATH", "neotower.db")


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
    # Migrate existing databases without deleting player progress.
    columns = {row["name"] for row in cursor.execute("PRAGMA table_info(players)").fetchall()}
    if "tower_cleared" not in columns:
        cursor.execute("ALTER TABLE players ADD COLUMN tower_cleared INTEGER NOT NULL DEFAULT 0")
    db.commit()
    db.close()


def get_player(user_id):
    db = connect()
    try:
        return db.execute("SELECT * FROM players WHERE id=?", (user_id,)).fetchone()
    finally:
        db.close()


def create_player(user_id, name, hero, hp, damage, armor):
    db = connect()
    try:
        cursor = db.cursor()
        cursor.execute(
            """INSERT OR IGNORE INTO players
            (id,name,hero,hp,damage,armor,level,xp,floor,credits,inventory,equipment)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
            (user_id, name, hero, hp, damage, armor, 1, 0, 1, 0, "iron_sword", "iron_sword")
        )
        db.commit()
        return cursor.rowcount == 1
    finally:
        db.close()


def get_inventory(user_id):
    player = get_player(user_id)
    if not player or not player["inventory"]:
        return []
    return [item for item in player["inventory"].split(",") if item]


def add_reward(user_id, xp, credits, item=None):
    """Apply rewards and permanent level-up stat growth atomically."""
    db = connect()
    try:
        with db:
            player = db.execute("SELECT * FROM players WHERE id=?", (user_id,)).fetchone()
            if not player:
                return

            inventory = player["inventory"] or ""
            if item:
                items = [x for x in inventory.split(",") if x]
                if item not in items or item == "health_potion":
                    items.append(item)
                    inventory = ",".join(items)

            new_xp = player["xp"] + xp
            new_level = max(1, 1 + new_xp // 500)
            levels_gained = max(0, new_level - player["level"])

            # Character progression: each level increases maximum HP, damage and armor.
            new_hp = player["hp"] + 20 * levels_gained
            new_damage = player["damage"] + 5 * levels_gained
            new_armor = player["armor"] + 3 * levels_gained

            db.execute(
                """UPDATE players
                   SET xp=?, level=?, credits=?, inventory=?, hp=?, damage=?, armor=?
                   WHERE id=?""",
                (new_xp, new_level, player["credits"] + credits, inventory,
                 new_hp, new_damage, new_armor, user_id)
            )
    finally:
        db.close()


def spend_credits(user_id, amount):
    if amount < 0:
        return False
    db = connect()
    try:
        with db:
            row = db.execute("SELECT credits FROM players WHERE id=?", (user_id,)).fetchone()
            if not row or row["credits"] < amount:
                return False
            db.execute("UPDATE players SET credits=credits-? WHERE id=?", (amount, user_id))
            return True
    finally:
        db.close()


def add_item(user_id, item):
    if item not in ITEMS:
        return False
    db = connect()
    try:
        with db:
            player = db.execute("SELECT inventory FROM players WHERE id=?", (user_id,)).fetchone()
            if not player:
                return False
            items = [x for x in (player["inventory"] or "").split(",") if x]
            if item in items and item != "health_potion":
                return False
            items.append(item)
            db.execute("UPDATE players SET inventory=? WHERE id=?", (",".join(items), user_id))
            return True
    finally:
        db.close()


def remove_item(user_id, item):
    db = connect()
    try:
        with db:
            player = db.execute("SELECT inventory,equipment FROM players WHERE id=?", (user_id,)).fetchone()
            if not player:
                return False
            items = [x for x in (player["inventory"] or "").split(",") if x]
            if item not in items:
                return False
            items.remove(item)
            equipment_items = [x for x in (player["equipment"] or "").split(",") if x]
            if item in equipment_items:
                equipment_items.remove(item)
            db.execute(
                "UPDATE players SET inventory=?, equipment=? WHERE id=?",
                (",".join(items), ",".join(equipment_items), user_id)
            )
            return True
    finally:
        db.close()


def get_daily_claim(user_id):
    db = connect()
    try:
        row = db.execute("SELECT day_key FROM daily_rewards WHERE user_id=?", (user_id,)).fetchone()
        return row["day_key"] if row else None
    finally:
        db.close()


def set_daily_claim(user_id, day_key):
    db = connect()
    try:
        with db:
            db.execute(
                "INSERT INTO daily_rewards(user_id,day_key) VALUES(?,?) "
                "ON CONFLICT(user_id) DO UPDATE SET day_key=excluded.day_key",
                (user_id, day_key)
            )
    finally:
        db.close()


def claim_daily_reward(user_id, day_key, xp=50, credits=250):
    """Atomically claim a daily reward; returns False if already claimed."""
    db = connect()
    try:
        db.execute("BEGIN IMMEDIATE")
        player = db.execute("SELECT xp, level, hp, damage, armor, credits FROM players WHERE id=?", (user_id,)).fetchone()
        if not player:
            db.rollback()
            return False
        row = db.execute("SELECT day_key FROM daily_rewards WHERE user_id=?", (user_id,)).fetchone()
        if row and row["day_key"] == day_key:
            db.rollback()
            return False

        new_xp = player["xp"] + xp
        new_level = max(1, 1 + new_xp // 500)
        levels_gained = max(0, new_level - player["level"])
        db.execute(
            "INSERT INTO daily_rewards(user_id,day_key) VALUES(?,?) "
            "ON CONFLICT(user_id) DO UPDATE SET day_key=excluded.day_key",
            (user_id, day_key)
        )
        db.execute(
            """UPDATE players SET xp=?, level=?, credits=credits+?,
               hp=hp+?, damage=damage+?, armor=armor+? WHERE id=?""",
            (new_xp, new_level, credits, 20 * levels_gained,
             5 * levels_gained, 3 * levels_gained, user_id)
        )
        db.commit()
        return True
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def complete_tower(user_id):
    db = connect()
    try:
        with db:
            db.execute("UPDATE players SET tower_cleared=1 WHERE id=?", (user_id,))
    finally:
        db.close()


def top_players(limit=10):
    db = connect()
    try:
        return db.execute(
            "SELECT name, hero, level, xp, floor, credits FROM players "
            "ORDER BY floor DESC, level DESC, xp DESC, credits DESC LIMIT ?",
            (limit,)
        ).fetchall()
    finally:
        db.close()


def update_stats(user_id, hp=None, damage=None, armor=None):
    db = connect()
    try:
        with db:
            player = db.execute("SELECT * FROM players WHERE id=?", (user_id,)).fetchone()
            if not player:
                return
            db.execute(
                "UPDATE players SET hp=?, damage=?, armor=? WHERE id=?",
                (hp if hp is not None else player["hp"],
                 damage if damage is not None else player["damage"],
                 armor if armor is not None else player["armor"], user_id)
            )
    finally:
        db.close()


def equip_item(user_id, item):
    # Consumables can be carried and used, but cannot be equipped.
    if ITEMS.get(item, {}).get("type") not in ("weapon", "armor"):
        return False
    db = connect()
    try:
        with db:
            player = db.execute(
                "SELECT inventory, equipment FROM players WHERE id=?",
                (user_id,),
            ).fetchone()
            if not player:
                return False

            inventory = [x for x in (player["inventory"] or "").split(",") if x]
            if item not in inventory:
                return False

            equipment_items = [x for x in (player["equipment"] or "").split(",") if x]
            item_type = ITEMS[item]["type"]
            # Only one item of each equipment type can be active.
            equipment_items = [
                equipped for equipped in equipment_items
                if ITEMS.get(equipped, {}).get("type") != item_type
            ]
            equipment_items.append(item)
            db.execute(
                "UPDATE players SET equipment=? WHERE id=?",
                (",".join(equipment_items), user_id)
            )
            return True
    finally:
        db.close()


def unequip_item(user_id):
    db = connect()
    try:
        with db:
            db.execute("UPDATE players SET equipment='' WHERE id=?", (user_id,))
    finally:
        db.close()


def get_equipment(user_id):
    player = get_player(user_id)
    return player["equipment"] if player else ""


def next_floor(user_id):
    db = connect()
    try:
        with db:
            player = db.execute("SELECT floor FROM players WHERE id=?", (user_id,)).fetchone()
            if player:
                db.execute("UPDATE players SET floor=? WHERE id=?", (player["floor"] + 1, user_id))
    finally:
        db.close()


def get_battle_session(user_id):
    db = connect()
    try:
        row = db.execute("SELECT state FROM battle_sessions WHERE user_id=?", (user_id,)).fetchone()
        if not row:
            return None
        try:
            return json.loads(row["state"])
        except (TypeError, ValueError):
            with db:
                db.execute("DELETE FROM battle_sessions WHERE user_id=?", (user_id,))
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
            db.execute("DELETE FROM battle_sessions WHERE user_id=?", (user_id,))
    finally:
        db.close()
