import sqlite3

CONN = None

# PRIVATE FUNCTIONS

def create_connection():
    global CONN
    if CONN is None:
        CONN = sqlite3.connect('TheMind/gamedata.db')
        CONN.row_factory = sqlite3.Row

def close_connection():
    if CONN is not None:
        CONN.commit()
        CONN.close()

def create_db():
    create_connection()
    sql_create_table = (
        "CREATE TABLE IF NOT EXISTS history("
        "rowid INTEGER PRIMARY KEY,"
        "players TEXT NOT NULL,"
        "numplayers INTEGER NOT NULL,"
        "mode TEXT NOT NULL,"
        "liveslost INTEGER NOT NULL,"
        "starsused INTEGER NOT NULL,"
        "gametime INTEGER NOT NULL"
        ")"
    )
    CONN.execute(sql_create_table)
    CONN.commit()

# ACCESSIBLE FUNCTIONS

def insert(players, mode, liveslost, starsused, gametime):
    """
    players: list of ints (userid)
    mode: str
    liveslost: int
    starsused: int
    gametime: int (game duration in seconds)
    """
    players = [str(p) for p in sorted(players)]
    sql_insert = (
        "INSERT INTO history(players, numplayers, mode, liveslost, starsused,"
        "gametime) "
        "VALUES(?,?,?,?,?,?)"
    )
    values = (
        ','.join(players), len(players), mode, liveslost, starsused,
        gametime
    )
    create_connection()
    CONN.execute(sql_insert, values)
    CONN.commit()