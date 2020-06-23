from datetime import datetime, timedelta, timezone
from json import dump, load
from math import comb, sqrt
from random import randrange

from dateutil import tz
from dateutil.parser import parse
from discord import Embed
from discord.utils import get

from Apps.bank import id, new_user

# E(X) = 207 Cor
PAYOUTS = {
    0: 10,
    1: 50,
    2: 250,
    3: 5000,
    4: 50000,
    5: 301500,
    6: 10000000
}

async def help(ctx):
    helpstr = (
        "```"
        "Lottery Help Page\n"
        "\n"
        "Command: .untouchable    Alias: .u\n"
        "\n"
        "This is a list of arguments passed in the form\n"
        "'.stocks (args) (addl args)'.\n"
        "Additional arguments can be <mandatory> or [optional].\n"
        "\n"
        ".untouchable ...    Alias   Details\n"
        "{no argument}               Displays lottery instructions\n"
        "rates                       Displays lottery odds\n"
        "history [userid]    (h)     Displays your lottery history\n"
        "luck [userid]       (l)     Calculates your luck\n"
        "leaderboards [num]  (lb)    Displays lottery leaderboards\n"
        "<guess>                     Plays the lottery\n"
        "random              (r)     Plays the lottery with a random number\n"
        "help                        Shows this page\n"
        "\n"
        "Additional argument info:\n"
        "[userid]: The user whose information you want to see\n"
        "            ex. 'CapSora#7528'\n"
        "[num]   : The specific outcome you want to see leaderboards for\n"
        "            ex. '3'\n"
        "<guess> : A six-digit (0-9) guess to play the lottery\n"
        "            ex. '012345'\n"
        "```"
    )
    await ctx.send(helpstr)

def binom(n, p, k):
    return comb(n, k) * pow(p, k) * pow((1-p), (n-k))

async def instructions(ctx, embed):
    embed.add_field(
        name='How to Play',
        value=(
            'UNTOUCHABLE is a lottery system named after the carnival game'
            ' in Gun Gale Online.\n'
            'To play UNTOUCHABLE, enter your guess in the form '
            '`.untouchable 123456` where the digits are 0-9.\n'
            'You may play UNTOUCHABLE once every 5 minutes.'
        )
    )
    await ctx.send(embed=embed)

async def rates(ctx, embed):
    embed.add_field(
        name='Approximate Rates',
        value=(
            f'0 matches: 1 in 2 -> {PAYOUTS[0]:,} Cor\n'
            f'1 matches: 1 in 3 -> {PAYOUTS[1]:,} Cor\n'
            f'2 matches: 1 in 10 -> {PAYOUTS[2]:,} Cor\n'
            f'3 matches: 1 in 70 -> {PAYOUTS[3]:,} Cor\n'
            f'4 matches: 1 in 800 -> {PAYOUTS[4]:,} Cor\n'
            f'5 matches: 1 in 20,000 -> {PAYOUTS[5]:,} Cor\n'
            f'6 matches: 1 in 1,000,000 -> {PAYOUTS[6]:,} Cor\n'
        )
    )
    await ctx.send(embed=embed)

async def cooldown(ctx, embed, cooldown, time_since_last_play):
    embed.add_field(
        name='Please wait...',
        value=(
            f'Play again in '
            f'{cooldown.seconds- time_since_last_play.seconds}s ⏱️'
        )
    )
    await ctx.send(embed=embed)

async def lottery(ctx, embed, emotes, guess):
    embed.add_field(
        name=f"{ctx.message.author}'s Guess",
        value=str(guess),
        inline=False
    )
    lotto = f'{randrange(1000000):06}'
    matches = sum(a == b for a, b in zip(str(guess), lotto))
    payout = f'Payout: {PAYOUTS[matches]} Cor'
    if matches == 0:
        emoji = get(emotes, name='icrierryday')
        payout += f"... {emoji}"
    elif matches == 1:
        emoji = get(emotes, name='geh')
        payout += f" {emoji}"
    elif matches == 2:
        emoji = get(emotes, name='dabby')
        payout += f"! {emoji}"
    elif matches >= 3:
        embed.colour = 0xffff00
        emoji = get(emotes, name='✨')
        payout += f'!!! {emoji}{emoji}{emoji}'
    embed.add_field(name='Winning Number', value=lotto, inline=False)
    embed.add_field(
        name=f'Matches: {matches}',
        value=payout
    )
    await ctx.send(embed=embed)
    return matches

async def history(ctx, embed, userid, userdata):
    embed.description = f'History for {userid}'
    win_array = userdata['untouchable']['wins']
    for i in range(7):
        wins = userdata['untouchable']['wins'][i]
        value = f"{wins}"
        if wins > 0:
            p = binom(6, 0.1, i)
            exp = sum(win_array) * p
            stdev = sqrt(sum(win_array) * p * (1 - p))
            z = (wins - exp) / stdev
            value += f' ({z:+.2f}σ)' 
        embed.add_field(name=f'{i} matches', value=value, inline=True)
    cor_true = sum(PAYOUTS[k] * win_array[k] for k in range(7))
    embed.add_field(name='\u200b', value='\u200b')
    embed.add_field(name='\u200b', value='\u200b')
    embed.add_field(
        name='Total draws',
        value=str(sum(win_array))
    )
    embed.add_field(
        name='Lifetime winnings',
        value=f'{cor_true:,}'
    )
    await ctx.send(embed=embed)

async def leaderboards(ctx, embed, bank_dict, num=-1):
    """
    num=-1 does leaderboard by earnings
    """
    lb = []
    if num < -1 or num > 6:
        await ctx.send("untouchable.py, leaderboards(): Invalid argument.")
    else:
        # Load player data
        for user in bank_dict:
            win_array = bank_dict[user]['untouchable']['wins']
            user_data = [user, 0, sum(win_array)]
            if num == -1:
                user_data[1] = sum(PAYOUTS[k] * win_array[k] for k in range(7))
            else:
                user_data[1] = win_array[num]
            lb.append(user_data)
        lb.sort(key=lambda x: x[1], reverse=True)
        # Set up grammar
        matches = 'matches'
        if num == 1:
            matches = 'match'
        if num == -1:
            embed.description = 'Leaderboards for overall earnings'
        else:
            embed.description = f'Leaderboards for {num} {matches}'
        medals = ['🥇', '🥈', '🥉', '🎗️', '🎗️']
        for i in range(min(len(lb), 5)):
            title = f'{i+1}. {lb[i][0]}'
            if num == -1:
                text = f'{medals[i]} {lb[i][1]} lifetime Cor'
            else:
                text = f'{medals[i]} {lb[i][1]} draws with {num} {matches}'
            text += f' ({lb[i][2]} total draws)'
            embed.add_field(name=title, value=text, inline=False)
        await ctx.send(embed=embed)

async def percentile(ctx, embed, userid, userdata, emotes):
    message = await ctx.send("Running simulations...")
    wins = userdata['untouchable']['wins']
    winnings = sum(wins[k] * PAYOUTS[k] for k in range(7))
    total_simulations = 10000
    montecarlo = []
    countnum = f'{randrange(10)}'
    for _ in range(total_simulations):
        total = 0
        for _ in range(sum(wins)):
            guess = f'{randrange(1000000):06}'
            total += PAYOUTS[guess.count(countnum)]
        montecarlo.append(total)
    percentile = (
        len([x for x in montecarlo if x <= winnings]) / total_simulations * 100
    )
    montecarlo.sort()
    embed.description = (
        f'Monte Carlo simulation of luck for {userid}'
        f' ({total_simulations:,} trials)'
    )
    embed.add_field(
        name="25th percentile",
        value=f'{montecarlo[int(total_simulations/4)]:,}'
    )
    embed.add_field(
        name="50th percentile",
        value=f'{montecarlo[int(total_simulations/2)]:,}'
    )
    embed.add_field(
        name="75th percentile",
        value=f'{montecarlo[int(3*total_simulations/4)]:,}'
    )
    embed.add_field(
        name="Total draws",
        value=f'{sum(wins):,}'
    )
    embed.add_field(
        name="Lifetime winnings",
        value=f'{winnings:,}'
    )
    arrows = ''
    green = get(emotes, name='omaewamou')
    red = get(emotes, name='poop')
    for p in [69.1, 84.1, 93.3, 97.7]:
        if percentile >= p:
            arrows += f'{green}'
        elif 100 - percentile >= p:
            arrows += f'{red}'
    if not arrows:
        arrows = f"{get(emotes, name='blobthinkingeyes')}"
    embed.add_field(
        name="Percentile",
        value = f"{percentile:.0f} {arrows}"
    )
    await message.delete()
    await ctx.send(content='', embed=embed)


# Edits bank.json
async def untouchable(ctx, emotes, args):
    # User check
    user = ctx.message.author
    userid = id(user)
    await new_user(ctx, userid)
    # Read data
    with open('Apps/bank.json') as f:
        bank_dict = load(f)
    # Embed
    embed = Embed(
        title='UNTOUCHABLE!',
        description=f'Test your luck! Win up to 10 Million Cor!',
        colour=0xff0033
    )
    # Time data
    now = datetime.now(timezone.utc)
    last_play = parse(
        bank_dict[userid]['untouchable']['last_played'],
        tzinfos={"+00:00": tz.UTC}
    )
    cooldown_dur = timedelta(minutes=5)
    # Logic
    if len(args) == 0:
        await instructions(ctx, embed)
    elif args[0] in ['help']:
        await help(ctx)
    elif args[0] in ['rates']:
        await rates(ctx, embed)
    elif args[0] in ['history', 'h']:
        if len(args) >= 2 and args[1] in bank_dict:
            userid = args[1]
        await history(ctx, embed, userid, bank_dict[userid])
    elif args[0] in ['luck', 'l']:
        if len(args) >= 2 and args[1] in bank_dict:
            userid = args[1]
        await percentile(ctx, embed, userid, bank_dict[userid], emotes)
    elif args[0] in ['leaderboards', 'lb']:
        num = -1
        if len(args) >= 2 and args[1].isnumeric():
            num = int(args[1])
        await leaderboards(ctx, embed, bank_dict, num)
    elif now - last_play < cooldown_dur:
        await cooldown(ctx, embed, cooldown_dur, now - last_play)
    else:
        if args[0] in ['random', 'r']:
            guess = f'{randrange(1000000):06}'
        elif len(args[0]) == 6 and str(args[0]).isnumeric():
            guess = str(args[0])
        else:
            await ctx.send('Please guess a 6-digit (0-9) number.')
            return
        matches = await lottery(ctx, embed, emotes, guess)
        # Add value to bank dict
        bank_dict[userid]['cor'] += PAYOUTS[matches]
        bank_dict[userid]['untouchable']['wins'][matches] += 1
        bank_dict[userid]['untouchable']['last_played'] = str(now)
        with open('Apps/bank.json', 'w') as f:
            dump(bank_dict, f)
