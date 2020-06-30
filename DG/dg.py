from random import choice
from discord import Embed
import sqlite3
from Apps.bank import id

STATUS = False

def create_connection():
    conn = sqlite3.connect('dg_db.sqlite')
    return conn

async def check_status(ctx, embed):
    global STATUS
    if STATUS:
        embed.description = "Ready for you to (ab)use."
    else:
        embed.description = "Offline. Try again later..."
    await ctx.send(embed=embed)

def toggle_status():
    global STATUS
    STATUS = not STATUS

async def dg(ctx, args):
    global STATUS
    embed = Embed(
        name="Suffering on demand",
        description="I may regret this"
    )
    if args[0] in ['status', 's']:
        await check_status(ctx, embed)
    elif id(ctx.message.author) == 'CapSora#7528':
        if args[0] in ['disable', 'd']:
            pass
    else:
        pass