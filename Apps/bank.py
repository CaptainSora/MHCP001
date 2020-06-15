from datetime import datetime, timezone
from json import dump, load
from math import ceil

from discord import Embed


async def bank(ctx, args):
    """
    Calls the appropriate function, and saves data to file.
    """
    with open('Apps/bank.json') as f:
        bank_dict = load(f)
    user = ctx.message.author
    userid = '#'.join([str(user.name), str(user.discriminator)])
    if len(args) == 0:
        # Initialize user
        await new_user(ctx, bank_dict, userid)
    elif args[0] in ['help', 'h']:
        await bankhelp()
    elif args[0] in ['balance', 'b']:
        # Display balance
        await balance(ctx, bank_dict, userid)
    elif args[0] in ['claim', 'interest', 'c', 'i']:
        await interest(ctx, bank_dict, userid)
    else:
        print("Invalid arguments")
    with open('Apps/bank.json', 'w') as f:
        dump(bank_dict, f)


async def bankhelp():
    pass

async def new_user(ctx, bank_dict, userid):
    """Initializes a new user"""
    if userid in bank_dict:
        # Existing user
        await balance(ctx, bank_dict, userid)
    else:
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

async def balance(ctx, bank_dict, userid):
    if userid not in bank_dict:
        await new_user(ctx, bank_dict, userid)
        return
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

async def interest(ctx, bank_dict, userid):
    if userid not in bank_dict:
        await new_user(ctx, bank_dict, userid)
        return
    embed = Embed(
        title='Bank of Aincrad',
        description=f'Daily Interest for {userid}',
        colour=0xffff33
    )
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
        bank_dict[userid]['last_collected'] = cur_date
        bank_dict[userid]['cor'] += interest_earned
        bank_dict[userid]['interest']['tier'] += 1
        text = f"Collected {interest_earned} Cor"
    embed.add_field(name='Interest', value=text)
    embed.add_field(name='Loyalty', value=f'{tier} days', inline=False)
    embed.add_field(name='Interest Rate', value=f'{interest_rate:.3f}%')
    await ctx.send(embed=embed)

async def user_exists(userid):
    with open('Apps/bank.json') as f:
        bank_dict = load(f)
    return userid in bank_dict

# async def add_balance(userid, value):
#     """
#     Adds value to userid's bank balance.
#     """
#     with open('Apps/bank.json') as f:
#         bank_dict = load(f)
#     if userid not in bank_dict:
#         return 1
#     if not str(value).isdecimal():
#         return 2
#     bank_dict[userid]['col'] += int(value)
#     with open('Apps/bank.json', 'w') as f:
#         dump(bank_dict, f)
#     return 0
