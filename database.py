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
    cursor = db.cursor()
    cursor.execute("SELECT * FROM players WHERE id=?", (user_id,))
    player = cursor.fetchone()
    db.close()
    return player


def create_player(user_id, name, hero, hp, damage, armor):
    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """INSERT INTO players VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
        (user_id, name, hero, hp, damage, armor, 1, 0, 1, 0, "iron_sword", "")
    )

    db.commit()
    db.close()
