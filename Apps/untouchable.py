from datetime import datetime, timedelta, timezone
from random import randrange
from json import dump, load

from dateutil import tz
from dateutil.parser import parse
from discord import Embed

from Apps.bank import new_user, user_exists

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

async def untouchable(ctx, args):
    # Set up variables
    with open('Apps/bank.json') as f:
        bank_dict = load(f)
    user = ctx.message.author
    userid = '#'.join([str(user.name), str(user.discriminator)])
    # Sanity checks
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
    # Guess arg formatting
    guess = None
    if len(args) > 0:
        guess = args[0]
    if guess == 'random':
        guess = f'{randrange(1000000):06}'
    # Logic
    if guess is None:
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
    elif guess in ['rates', 'payout', 'payouts']:
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
    elif now - last_play < timedelta(minutes=5):
        embed.add_field(
            name='Please wait...',
            value=f'Play again in {5 * 60 - (now - last_play).seconds}s'
        )
    elif len(guess) == 6 and str(guess).isdecimal():
        embed.add_field(name='Your Guess', value=str(guess), inline=False)
        lotto = f'{randrange(1000000):06}'
        matches = sum(a == b for a, b in zip(str(guess), lotto))
        embed.add_field(name='Winning Number', value=lotto, inline=False)
        embed.add_field(
            name=f'Matches: {matches}',
            value=f'Payout: {PAYOUTS[matches]} Cor!'
        )
        # Add value to bank dict
        bank_dict[userid]['cor'] += PAYOUTS[matches]
        bank_dict[userid]['untouchable']['wins'][matches] += 1
        bank_dict[userid]['untouchable']['last_played'] = str(now)
        with open('Apps/bank.json', 'w') as f:
            dump(bank_dict, f)
    await ctx.send(embed=embed)