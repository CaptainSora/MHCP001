# Roulette
# Blackjack
# Slots
from random import randrange
from Apps.bank import id, new_user
from discord import Embed
from json import load, dump

# Roulette
TRANSLATE = {
    'o': "Odd",
    'e': "Even",
    'r': "Red",
    'b': "Black",
    'i': "High",
    'l': "Low",
    'd1': "First dozen",
    'd2': "Second dozen",
    'd3': "Third dozen",
    'c1': "First column",
    'c2': "Second column",
    'c3': 'Third column'
}

async def help(ctx):
    helpstr = (
        "```"
        "Roulette Help Page\n"
        "\n"
        "Command: .roulette    Alias: .r\n"
        "\n"
        "This is a list of arguments passed in the form\n"
        "'.stocks (args) (addl args)'.\n"
        "Additional arguments can be <mandatory> or [optional].\n"
        "\n"
        ".untouchable ...    Alias   Details\n"
        "{no argument}               Displays roulette instructions\n"
        "table               (t)     Displays the roulette table\n"
        "rates                       Displays roulette payouts\n"
        "history [userid]    (h)     Displays your roulette history\n"
        "leaderboards        (lb)    Displays roulette leaderboards\n"
        "<guess> <bet>               Plays the lottery\n"
        "help                        Shows this page\n"
        "\n"
        "Additional argument info:\n"
        "[userid]: The user whose information you want to see\n"
        "            ex. 'CapSora#7528'\n"
        "<guess> : The numbers you would like to bet on.\n"
        "            ex. 'b' (Use .roulette to get full list)\n"
        "<bet>   : The amount you would like to bet, no more than 1000\n"
        "            ex. '100'\n"
        "```"
    )
    await ctx.send(helpstr)

def is_win(betstr, num):
    if betstr == 'l':
        return (num > 0) and (num < 19)
    elif betstr == 'i':
        return num > 18
    elif betstr == 'e':
        return (num > 0) and (num % 2 == 0)
    elif betstr == 'o':
        return (num > 0) and (num % 2 == 1)
    elif betstr == 'd1':
        return (num > 0) and (num < 13)
    elif betstr == 'd2':
        return (num > 12) and (num < 25)
    elif betstr == 'd3':
        return num > 24
    elif betstr == 'c1':
        return (num > 0) and (num % 3 == 1)
    elif betstr == 'c2':
        return (num > 0) and (num % 3 == 2)
    elif betstr == 'c3':
        return (num > 0) and (num % 3 == 0)
    elif betstr == 'r':
        return num in [
            1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36
        ]
    elif betstr == 'b':
        return num in [
            2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35
        ]
    else:
        return num == int(betstr)

async def bet(ctx, embed, betstr, betval, userid):
    num = randrange(37)
    winnings = (-1) * betval
    if is_win(betstr, num):
        if betstr in 'oerbil':
            embed.colour = 0x00ff0d
            winnings = betval
        elif betstr in ['d1', 'd2', 'd3', 'c1', 'c2', 'c3']:
            embed.colour = 0x00ff0d
            winnings = 2 * betval
        else:  # Numerical win
            embed.colour = 0xffff00
            winnings = 35 * betval
    else:
        embed.colour = 0x198700
    if betstr in TRANSLATE:
        guess = TRANSLATE[betstr]
    else:
        guess = str(guess)
    embed.add_field(
        name="Your Guess",
        value=guess
    )
    embed.add_field(
        name='Outcome',
        value=f'{num}'
    )
    embed.add_field(
        name='Winnings',
        value=f'{winnings:,}'
    )
    await ctx.send(embed=embed)
    # Save winnings to bank_dict
    with open('Apps/bank.json') as f:
        bank_dict = load(f)
    if 'roulette' not in bank_dict[userid]:
        bank_dict[userid]['roulette'] = {
            "plays": 0,
            "winnings": 0
        }
    bank_dict[userid]['roulette']['plays'] += 1
    bank_dict[userid]['roulette']['winnings'] += winnings
    with open('Apps/bank.json', 'w') as f:
        dump(bank_dict, f)

async def instructions(ctx, embed):
    embed.add_field(
        name='How to Play',
        value=(
            "To play roulette, enter your guess in the form "
            "`.roulette <guess> <bet>` where the guess is one of the zones on "
            "the roulette board, and the bet is no more than 1000.\n\n"
            "Possible guesses are:\n"
            "o (odd), e (even), r (red), b (black), i (high), l (low)\n"
            "d1, d2, d3, c1, c2, c3 (1st/2nd/3rd dozens/columns)\n"
            "any specific number from 0-36 inclusive"
        )
    )
    embed.set_image(
        url="https://cdn.discordapp.com/attachments/279320769429766145/"
        "724711059851837480/roulette.png"
    )
    await ctx.send(embed=embed)

async def table(ctx, embed):
    embed.set_image(
        url="https://cdn.discordapp.com/attachments/279320769429766145/"
        "724711059851837480/roulette.png"
    )
    await ctx.send(embed=embed)

async def rates(ctx, embed):
    embed.add_field(
        name='Payouts',
        value=(
            f'Odd/Even/Red/Black/High/Low: 1 to 1\n'
            f'Dozen/Column: 2 to 1\n'
            f'Number: 35 to 1\n'
        )
    )
    await ctx.send(embed=embed)

async def history(ctx, embed, userid):
    with open('Apps/bank.json') as f:
        bank_dict = load(f)
    embed.description = f'History for {userid}'
    embed.add_field(
        name='Total Plays',
        value=f"{bank_dict[userid]['roulette']['plays']:,}"
    )
    embed.add_field(
        name='Net Profit',
        value=f"{bank_dict[userid]['roulette']['winnings']:,}"
    )
    await ctx.send(embed=embed)

async def leaderboards(ctx, embed):
    lb = []
    # Collect data
    with open('Apps/bank.json') as f:
        bank_dict = load(f)
    for user in bank_dict:
        if 'roulette' in bank_dict[user]:
            lb.append([
                user,
                bank_dict[user]['roulette']['winnings'],
                bank_dict[user]['roulette']['plays']
            ])
    lb.sort(key=lambda x: x[1], reverse=True)
    embed.description = 'Leaderboards for roulette'
    medals = ['🥇', '🥈', '🥉', '🎗️', '🎗️']
    for i in range(min(len(lb), 5)):
        embed.add_field(
            name=f'{i+1}. {lb[i][0]}',
            value=f'{medals[i]} {lb[i][1]} net Cor ({lb[i][2]} plays)',
            inline=False
        )
    await ctx.send(embed=embed)
    
async def roulette(ctx, args):
    cap = 1000
    # User check
    user = ctx.message.author
    userid = id(user)
    await new_user(ctx, userid)
    # Embed
    embed = Embed(
        title = "Roulette",
        description = "Place your bets now!",
        colour=0x009c2c
    )
    # Logic
    if len(args) == 0:
        await instructions(ctx, embed)
    elif args[0] in ['help']:
        await help(ctx)
    elif args[0] in ['rates']:
        await rates(ctx, embed)
    elif args[0] in ['table', 't']:
        await table(ctx, embed)
    elif args[0] in ['history', 'h']:
        # Read data
        with open('Apps/bank.json') as f:
            bank_dict = load(f)
        if len(args) >= 2 and args[1] in bank_dict:
            userid = args[1]
        await history(ctx, embed, userid)
    elif args[0] in ['leaderboards', 'lb']:
        await leaderboards(ctx, embed)
    elif len(args) < 2:
        await instructions(ctx, embed)
    elif (args[0] in TRANSLATE) \
            or (args[0].isdecimal() and int(args[0]) >= 0 \
                and int(args[0]) < 37):
        if args[1].isdecimal() and int(args[1]) > 0 and int(args[1]) < cap:
            await bet(ctx, embed, args[0], int(args[1]), userid)
    else:
        await instructions(ctx, embed)