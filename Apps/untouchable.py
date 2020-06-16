from datetime import datetime, timedelta, timezone
from random import randrange
from json import dump, load
from math import comb, sqrt

from dateutil import tz
from dateutil.parser import parse
from discord import Embed

from Apps.bank import id, new_user, user_exists

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
            f'{cooldown.seconds- time_since_last_play.seconds}s'
        )
    )
    await ctx.send(embed=embed)

async def lottery(ctx, embed, guess):
    embed.add_field(
        name=f"{ctx.message.author}'s Guess",
        value=str(guess),
        inline=False
    )
    lotto = f'{randrange(1000000):06}'
    matches = sum(a == b for a, b in zip(str(guess), lotto))
    embed.add_field(name='Winning Number', value=lotto, inline=False)
    embed.add_field(
        name=f'Matches: {matches}',
        value=f'Payout: {PAYOUTS[matches]} Cor!'
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
            stdev = sqrt(sum(win_array) * p**2)
            z = (wins - exp) / stdev
            value += f' ({z:+.2f}σ)' 
        embed.add_field(name=f'{i} matches', value=value, inline=True)
    cor_exp = sum(PAYOUTS[k] * binom(6, 0.1, k) for k in range(7))
    cor_true = sum(PAYOUTS[k] * win_array[k] for k in range(7))
    cor_diff = cor_true - sum(win_array) * cor_exp
    embed.add_field(name='\u200b', value='\u200b')
    embed.add_field(
        name='Total Plays',
        value=str(sum(win_array))
    )
    embed.add_field(
        name='Expected payout',
        value=f'{sum(win_array) *cor_exp:,.0f}'
    )
    embed.add_field(
        name='Actual payout',
        value=f'{cor_true:,}'
    )
    embed.add_field(name='Payout difference', value=f'{cor_diff:+,.0f}')
    await ctx.send(embed=embed)

async def leaderboards(ctx, embed, bank_dict, num=-1):
    """
    num=-1 does leaderboard by earnings
    """
    lb = []
    if num < -1 or num > 6:
        await ctx.send("Invalid argument.")
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
        for i in range(min(len(lb), 5)):
            title = f'{i+1}. {lb[i][0]}'
            if num == -1:
                text = f'{lb[i][1]} lifetime Cor'
            else:
                text = f'{lb[i][1]} draws with {num} {matches}'
            text += f' ({lb[i][2]} total draws)'
            embed.add_field(name=title, value=text, inline=False)
        await ctx.send(embed=embed)


async def untouchable(ctx, args):
    # Set up variables
    with open('Apps/bank.json') as f:
        bank_dict = load(f)
    user = ctx.message.author
    userid = id(user)
    # User checks
    if not await user_exists(userid):
        await new_user(ctx, bank_dict, userid)
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
    elif args[0] in ['rates', 'payout', 'payouts']:
        await rates(ctx, embed)
    elif args[0] in ['history', 'hist', 'h']:
        if len(args) >= 2 and args[1] in bank_dict:
            userid = args[1]
        await history(ctx, embed, userid, bank_dict[userid])
    elif args[0] in ['leaderboards', 'leaders', 'lb']:
        num = -1
        if len(args) >= 2 and args[1].isnumeric():
            num = int(args[1])
        await leaderboards(ctx, embed, bank_dict, num)
    elif now - last_play < cooldown_dur:
        await cooldown(ctx, embed, cooldown_dur, now - last_play)
    else:
        if args[0] in ['random', 'rand', 'r']:
            guess = f'{randrange(1000000):06}'
        elif len(args[0]) == 6 and str(args[0]).isnumeric():
            guess = str(args[0])
        else:
            await ctx.send('Command not found.')
            return
        matches = await lottery(ctx, embed, guess)
        # Add value to bank dict
        bank_dict[userid]['cor'] += PAYOUTS[matches]
        bank_dict[userid]['untouchable']['wins'][matches] += 1
        bank_dict[userid]['untouchable']['last_played'] = str(now)
        with open('Apps/bank.json', 'w') as f:
            dump(bank_dict, f)
        