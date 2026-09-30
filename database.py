import sqlite3

DATABASE = "neotower.db"


def connect():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
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
    db.commit()
    db.close()


def get_player(user_id):
    db = connect()
    player = db.execute(
        "SELECT * FROM players WHERE id=?",
        (user_id,)
    ).fetchone()
    db.close()
    return player


def create_player(user_id, name, hero, hp, damage, armor):
    db = connect()

    exists = db.execute(
        "SELECT id FROM players WHERE id=?",
        (user_id,)
    ).fetchone()

    if exists:
        db.close()
        return False

    db.execute(
        "INSERT INTO players VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
        (user_id, name, hero, hp, damage, armor, 1, 0, 1, 0, "iron_sword", "")
    )
    db.commit()
    db.close()
    return True


def add_reward(user_id, xp, credits, item=None):
    db = connect()
    player = get_player(user_id)
    if not player:
        db.close()
        return

    inventory = player["inventory"] or ""
    if item and item not in inventory:
        inventory = inventory + ("," if inventory else "") + item

    db.execute(
        "UPDATE players SET xp=?, credits=?, inventory=? WHERE id=?",
        (player["xp"] + xp, player["credits"] + credits, inventory, user_id)
    )
    db.commit()
    db.close()


def update_stats(user_id, hp=None, damage=None, armor=None):
    db = connect()
    player = get_player(user_id)
    if not player:
        db.close()
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
    db.commit()
    db.close()


def equip_item(user_id, item):
    db = connect()
    db.execute(
        "UPDATE players SET equipment=? WHERE id=?",
        (item, user_id)
    )
    db.commit()
    db.close()


def get_equipment(user_id):
    player = get_player(user_id)
    return player["equipment"] if player else ""


def next_floor(user_id):
    db = connect()
    player = get_player(user_id)
    if player:
        db.execute(
            "UPDATE players SET floor=? WHERE id=?",
            (player["floor"] + 1, user_id)
        )
        db.commit()
    db.close()
