from random import choice
from discord import Embed
import sqlite3
from Apps.bank import id, add_cor
from datetime import datetime, timedelta, timezone
from dateutil import tz
from dateutil.parser import parse
from json import load, dump
from Help.help import help_page

# Currently allows entering data twice

STATUS = False
CONN = None
COOLDOWN = 5

async def ping_owner(ctx, message=''):
    if not message:
        message = choice([
            "Hey! Suffering waits for no one.",
            "No pressure, only potential pain."
        ])
    await ctx.send("<@!278589912184258562> " + message)

def create_connection():
    global CONN
    if CONN is None:
        CONN = sqlite3.connect('DG/dg.db')

def close_connection():
    if CONN is not None:
        CONN.commit()
        CONN.close()

def create_db():
    create_connection()
    sql_create_throws = (
        "CREATE TABLE IF NOT EXISTS throws("
        "request_id INTEGER PRIMARY KEY,"
        "flags TEXT,"
        "distance INTEGER NOT NULL,"
        "throw_type TEXT NOT NULL,"
        "userid TEXT NOT NULL,"
        "request_time TEXT NOT NULL,"
        "score INTEGER,"
        "pressure INTEGER,"
        "punishment TEXT,"
        "qty INTEGER,"
        "complete_time TEXT"
        ")"
    )
    sql_create_dgpayouts = (
        "CREATE TABLE IF NOT EXISTS dgpayouts("
        "payout_id INTEGER PRIMARY KEY,"
        "request_id INTEGER NOT NULL,"
        "userid TEXT NOT NULL,"
        "cor INTEGER NOT NULL,"
        "timestamp TEXT NOT NULL"
        ")"
    )
    CONN.execute(sql_create_throws)
    CONN.execute(sql_create_dgpayouts)
    CONN.commit()
    
async def create_request(ctx, embed, flags):
    create_connection()
    if unfinished_request() is not None:
        embed.description = "There is already an existing request."
        await ctx.send(embed=embed)
        await ping_owner(ctx)
        await print_unfinished_request(ctx, embed)
        return
    cd = cooldown()
    if cd > 0:
        mins = int(cd / 60)
        secs = cd % 60
        embed.description = (
            f'Cooldown active. Try again in {mins}m {secs}s. ⏱️'
        )
        await ctx.send(embed=embed)
        return
    sql = (
        "INSERT INTO throws(flags, distance, throw_type, userid, request_time)"
        " VALUES(?,?,?,?,?)"
    )
    flag_list = flags.split()
    if '-15' in flag_list:
        dist = '15'
    elif '-20' in flag_list:
        dist = '20'
    else:
        dist = choice(['15', '20', '20', '20'])
    if '-s' in flag_list:
        throw_type = "straddle"
    elif '-l' in flag_list:
        throw_type = "lunge"
    else:
        throw_type = choice(["Straddle", "Lunge"])
    userid = id(ctx.message.author)
    request_time = str(datetime.now(timezone.utc))
    values = (flags, dist, throw_type, userid, request_time)
    CONN.execute(sql, values)
    CONN.commit()
    await ping_owner(ctx)
    await print_unfinished_request(ctx, embed, values)
    return values

async def payouts(ctx, embed):
    """
    Must be called after putts completed
    """
    create_connection()
    sql_last = (
        "SELECT request_id, flags, distance, userid, score, pressure "
        "FROM throws ORDER BY request_id DESC LIMIT 1"
    )
    throw_entry = CONN.execute(sql_last).fetchone()
    sql = (
        "INSERT INTO dgpayouts(request_id, userid, cor, timestamp) "
        "VALUES(?,?,?,?)"
    )
    BASE_COR = 10
    request_id = throw_entry[0]
    flags = throw_entry[1]
    dist = throw_entry[2]
    userid = throw_entry[3]
    score = throw_entry[4] + 2 * throw_entry[5]  # Max 12
    now = str(datetime.now(timezone.utc))
    # Requester
    cor1 = (12 - score) * BASE_COR * 2
    if dist == '15':
        cor1 *= 2
    CONN.execute(sql, (request_id, userid, cor1, now))
    # CapSora
    cor2 = score * BASE_COR
    if '-d' in flags:
        cor2 *= 2
    CONN.execute(sql, (request_id, 'CapSora#7528', cor2, now))
    CONN.commit()
    # Embed
    embed.description = "Payouts"
    embed.clear_fields()
    embed.add_field(name=userid, value=f"{cor1}")
    embed.add_field(name='CapSora#7528', value=f"{cor2}")
    await ctx.send(embed=embed)
    # REMOVE ME AFTER MIGRATION
    add_cor(userid, cor1)
    add_cor("CapSora#7528", cor2)

async def complete_putting(ctx, embed, made, pressure):
    create_connection()
    if made not in range(11) or pressure not in [0, 1]:
        return
    if unfinished_request() is None:
        return
    sql_update = (
        "UPDATE throws SET score = ?, pressure = ?, punishment = ?, "
        "qty = ?, complete_time = ? WHERE complete_time IS NULL"
    )
    p = None
    qty = 0
    embed.description = "Request complete. Starting cooldown timer."
    embed.add_field(name="Result", value=f"{made}/10")
    embed.add_field(name="Pressure", value=f"{pressure}/1")
    if made < 10 or pressure < 1:
        with open('DG/punishments.json') as f:
            punishments = load(f)
        p = choice(list(punishments.keys()))
        dist = unfinished_request(col='distance')
        if int(dist) == 15:
            i = 0
        elif int(dist) == 20:
            i = 1
        qty = punishments[p][i] * ((10 - made) + 2 * (1 - pressure))
        embed.add_field(name='Punishment', value=f"{qty} {p}", inline=False)
    else:
        embed.add_field(
            name="Coach Kamogawa",
            value="Nice work, kid.",
            inline=False
        )
    await ctx.send(embed=embed)
    now = str(datetime.now(timezone.utc))
    values = (made, pressure, p, qty, now)
    CONN.execute(sql_update, values)
    CONN.commit()
    await payouts(ctx, embed)

def duration_ago(timestamp):
    now = datetime.now(timezone.utc)
    last_play = parse(
        timestamp,
        tzinfos={"+00:00": tz.UTC}
    )
    time_since_request = (now - last_play).seconds
    timestr = ""
    if time_since_request > 60 * 60 * 24:
        timestr += f"{int(time_since_request / (60 * 60 * 24))}d "
    if time_since_request > 60 * 60:
        timestr += f"{int(time_since_request / (60 * 60)) % (60 * 60 * 24)}h "
    if time_since_request > 60:
        timestr += f"{int(time_since_request / 60) % (60 * 60)}m "
    timestr += f"{time_since_request % 60}s ago"
    return timestr

async def print_unfinished_request(ctx, embed, values=None):
    if unfinished_request() is None:
        embed.description = f'No unfinished requests.'
        await ctx.send(embed=embed)
        return
    if values is None:
        create_connection()
        sql = (
            "SELECT flags, distance, throw_type, userid, request_time "
            "FROM throws WHERE complete_time IS NULL"
        )
        values = CONN.execute(sql).fetchone()
    embed.description = f"Unfinished request by {values[3]}"
    embed.add_field(name="Distance", value=f"{values[1]}'")
    embed.add_field(name="Putt Type", value=f"{values[2]}")
    embed.add_field(name="Requested", value=duration_ago(values[4]))
    if '-d' in values[0]:
        embed.add_field(name="Modifiers", value="Doubled!")
    await ctx.send(embed=embed)

def unfinished_request(col='rowid'):
    """
    Returns the value of the unfinished request, or None.
    Vulnerable to SQL Injection.
    """
    create_connection()
    sql = f"SELECT {col} FROM throws WHERE complete_time IS NULL"
    row = CONN.execute(sql).fetchall()
    if row:
        if col == '*':
            return row[0]
        else:
            return row[0][0]
    else:
        return None

def last_request_time():
    """
    Returns the time of the last request as a datetime object
    """
    sql = "SELECT complete_time FROM throws ORDER BY request_id DESC LIMIT 1"
    table = CONN.execute(sql).fetchall()
    if table:
        last_play = parse(
            table[0][0],
            tzinfos={"+00:00": tz.UTC}
        )
    else:
        last_play = parse(
            "2020-07-02 18:00:00.000000+00:00",
            tzinfos={"+00:00": tz.UTC}
        )
    return last_play

def cooldown():
    if unfinished_request() is not None:
        return False
    now = datetime.now(timezone.utc)
    last_play = last_request_time()
    cooldown_dur = timedelta(minutes=COOLDOWN).seconds
    return max(0, (cooldown_dur - (now - last_play).seconds))

async def check_status(ctx, embed):
    if STATUS:
        embed.description = "Ready for you to (ab)use."
    else:
        embed.description = "Offline. Try again later..."
    await ctx.send(embed=embed)

async def dg(ctx, args):
    global STATUS, COOLDOWN
    embed = Embed(
        title="Suffering on demand",
        description="I may regret this"
    )
    if len(args) > 0 and args[0] in ['status', 's']:
        await check_status(ctx, embed)
    elif len(args) > 0 and args[0] in ['help']:
        await help_page(ctx, 'dg')
    elif id(ctx.message.author) == 'CapSora#7528':
        if len(args) == 0:
            await print_unfinished_request(ctx, embed)
        elif (args[0] in ['disable', 'd'] and STATUS) \
                or (args[0] in ['enable', 'e'] and not STATUS):
            STATUS = not STATUS
            await check_status(ctx, embed)
        elif len(args) >= 2 and args[0] in ['cooldown']:
            if args[1].isdecimal():
                COOLDOWN = int(args[1])
                embed.description = f"Cooldown set to {COOLDOWN} minute(s)."
                await ctx.send(embed=embed)
        elif len(args) >= 3 and args[0] in ['p', 'putting']:
            if args[1].isdecimal() and args[2].isdecimal():
                await complete_putting(ctx, embed, int(args[1]), int(args[2]))
        elif args[0] in ['override']:
            pass
    else:
        if not STATUS:
            await check_status(ctx, embed)
        else:
            await create_request(ctx, embed, ' '.join(args))

create_connection()
