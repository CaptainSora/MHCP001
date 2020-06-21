from datetime import datetime, timezone
from json import dump, load
from math import ceil

from discord import Embed

def id(user):
    return '#'.join([str(user.name), str(user.discriminator)])

async def utc_time(ctx):
    await ctx.send(datetime.now(timezone.utc).strftime('%H:%M:%S') + ' UTC')

async def bank(ctx, args):
    """
    Calls the appropriate function, and saves data to file.
    """
    user = ctx.message.author
    userid = id(user)
    await new_user(ctx, userid)  # Initialize user, if not exists
    if len(args) == 0:
        # Display balance
        await balance(ctx, userid)
    elif args[0] in ['help', 'h']:
        await bankhelp()
    elif args[0] in ['claim', 'interest', 'c', 'i']:
        await interest(ctx, userid)
    else:
        print("bank.py, bank(): Invalid arguments")

async def bankhelp():
    pass

async def new_user(ctx, userid):
    """
    Initializes a new user, if necessary. Safe to call on existing users.
    Returns True if new user was created, False otherwise.
    Please ensure that you read a new copy of bank_dict after calling new_user.
    """
    with open('Apps/bank.json') as f:
        bank_dict = load(f)
    if userid in bank_dict:
        # Existing user
        return False
    embed = Embed(
        title='Bank of Aincrad',
        description=(
            "Hello and welcome to the Bank of Aincrad!\n"
            "As this is your first time here, please take this welcome "
            "bonus of 100 Cor!\n"
            "Please feel free to use `.bankhelp` to see what services we "
            "offer, and don't forget to claim your interest daily with "
            "`.bank claim`!"
        ),
        colour=0xffff33
    )
    cur_time = datetime.now(timezone.utc)
    bank_dict[userid] = {
        "cor": 100,
        "interest": {
            "tier": 0,
            "last_collected": str(cur_time.date())
        },
        "untouchable": {
            "wins": [0, 0, 0, 0, 0, 0, 0],
            "last_played": str(cur_time)
        }
    }
    await ctx.send(embed=embed)
    with open('Apps/bank.json', 'w') as f:
        dump(bank_dict, f)
    return True

async def balance(ctx, userid):
    """
    Prints the balance for the user, and checks if their interest is claimable.
    Requires: userid in bank_dict
    """
    with open('Apps/bank.json') as f:
        bank_dict = load(f)
    if userid not in bank_dict:
        return False
    embed = Embed(
        title='Bank of Aincrad',
        description=f'Balance for {userid}',
        colour=0xffff33
    )
    embed.add_field(name='Balance', value=f'{bank_dict[userid]["cor"]} Cor')
    cur_date = str(datetime.now(timezone.utc).date())
    if cur_date != bank_dict[userid]['interest']['last_collected']:
        embed.add_field(name='Interest', value='Claimable!')
    await ctx.send(embed=embed)

# Edits bank.json
async def interest(ctx, userid):
    """
    Earns daily interest.
    """
    # Read in data
    with open('Apps/bank.json') as f:
        bank_dict = load(f)
    if userid not in bank_dict:
        return False
    # Embed
    embed = Embed(
        title='Bank of Aincrad',
        description=f'Daily Interest for {userid}',
        colour=0xffff33
    )
    # Calculation
    cur_date = str(datetime.now(timezone.utc).date())
    balance = max(1, bank_dict[userid]['cor'])
    tier = bank_dict[userid]['interest']['tier']
    interest_rate = ((4 * tier) / (tier + 25)) + 1
    interest_earned = ceil(balance * (interest_rate / 100))
    if cur_date == bank_dict[userid]['interest']['last_collected']:
        now = datetime.now(timezone.utc)
        mins_left = (24 - now.hour - 1) * 60 + (60 - now.minute - 1)
        text = (
            f"Sorry, you have already claimed your interest for "
            f"`{cur_date}`.\n"
            f"You can claim again in {mins_left // 60}h {mins_left % 60}m."
        )
    else:
        bank_dict[userid]['interest']['last_collected'] = cur_date
        bank_dict[userid]['cor'] += interest_earned
        bank_dict[userid]['interest']['tier'] += 1
        text = f"Collected {interest_earned} Cor"
    embed.add_field(name='Interest', value=text)
    embed.add_field(name='Loyalty', value=f'{tier} days', inline=False)
    embed.add_field(name='Interest Rate', value=f'{interest_rate:.3f}%')
    await ctx.send(embed=embed)
    # Save data
    with open('Apps/bank.json', 'w') as f:
        dump(bank_dict, f)

# Used for stocks
# Edits bank.json
async def purchase(userid, value, objtype=None, obj=None, qty=None):
    """
    Adds value to userid's bank balance. Value can be + or -.
    Optionally adds an object of objtype, with name obj, with amount qty
    to user's inventory.
    """
    with open('Apps/bank.json') as f:
        bank_dict = load(f)
    if userid not in bank_dict:
        return 1  # User does not exist
    if not str(value).isdecimal():
        return 2  # Value must be numeric
    if bank_dict[userid]['col'] + int(value) < 0:
        return 3  # Cannot request more than in bank
    if objtype is not None:
        if obj is None or qty is None:
            return 4  # Require all optional arguments
        if not str(qty).isdecimal():
            return 5  # Qty must be numeric
        if objtype not in bank_dict[userid]:
            bank_dict[userid][objtype] = {}
        if obj not in bank_dict[userid][objtype]:
            bank_dict[userid][objtype][obj] = 0
        if bank_dict[userid][objtype][obj] + int(qty) < 0:
            return 6  # Cannot request more than owned
        bank_dict[userid][objtype][obj] += int(qty)
    bank_dict[userid]['col'] += int(value)
    with open('Apps/bank.json', 'w') as f:
        dump(bank_dict, f)
    return 0
