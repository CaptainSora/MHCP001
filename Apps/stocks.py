"""
Maybe multiple stocks,
NerveGear (NVG), Augma (AUG), AmuSphere (AMS), Soul Translator (STL),
Medicuboid (MCB)
Each stock has its own "center" price
Small fee per transaction, for selling (10 cor + 1%?)
"""
from math import sqrt
from random import random
from json import dump, load
from dateutil import tz
from dateutil.parser import parse
from datetime import datetime, timezone
import numpy as np
from Apps.bank import id, user_exists, new_user
from discord import Embed

def stock_home_value(stock_brief):
    """
    Generates the stock's home value from its 3-letter code.
    """
    values = [ord(x) for x in stock_brief]
    x = values[0] << 7
    x ^= x << values[1]
    x ^= x << values[2]
    y = sum(int(y) for y in str(int(x)))
    a = ord(stock_brief[0]) - ord('A')
    y += int(str(x)[a:a+2])
    return y

def stock_sigma(stock_brief):
    """
    Generates the stock's percentage volatility from its 3-letter code.
    """
    values = [ord(x) for x in stock_brief]
    x = values[0] << 13
    x ^= x << values[1]
    x ^= x << values[2]
    y = [int(z) for z in str(sum(int(y) for y in str(int(x))))]
    y[0] ^= y[1]
    y[0] ^= y[2]
    return y[0] / 100

def new_value(prev_value, stock_brief):
    """
    Uses a modified Geometric Brownian Motion to simulate stock prices.
    """
    home_value = stock_home_value(stock_brief)
    inv_drift = 5
    mu = ((home_value / prev_value) - 1) / inv_drift
    sigma = 0.25 + stock_sigma(stock_brief)
    delta_t = 1
    change = (mu * delta_t) + (sigma * (random() - 0.5) * sqrt(delta_t))
    return round(prev_value * (1 + change))

def gen_traders(lam):
    """ Generates traders with occurrence lambda. """
    rng = np.random.default_rng()
    return int(rng.poisson(lam, 1))

def check_history():
    # Constants
    history_limit = 48
    buyer_lambda = 8
    seller_lambda = 5
    # Open file
    with open('Apps/stocks.json') as f:
        stock_history = load(f)
    cur_time = datetime.now(timezone.utc)
    last_updated = parse(
        stock_history['last_updated'],
        tzinfos={"+00:00": tz.UTC}
    )
    hours_missing = 24 * (cur_time.date() - last_updated.date()).days \
        + (cur_time.time().hour - last_updated.time().hour)
    if hours_missing > 0:
        for s in stock_history['stocks']:
            v = stock_history['stocks'][s]['values']
            for _ in range(hours_missing):
                v.insert(0, new_value(v[0], s))
            if len(v) > history_limit:
                v = v[:history_limit]
            # Generate new buy/sell numbers
            stock_history['stocks'][s]['buyers'] = gen_traders(buyer_lambda)
            stock_history['stocks'][s]['sellers'] = gen_traders(seller_lambda)
    stock_history['last_updated'] = str(cur_time)
    with open('Apps/stocks.json', 'w') as f:
        dump(stock_history, f)

async def print_history(ctx, embed, stock_brief=None):
    pass

async def trade(ctx, embed, stock_brief, qty):
    pass

async def stocks(ctx, args):
    # Update stock information
    check_history()
    with open('Apps/stocks.json') as f:
        stock_history = load(f)
    user = ctx.message.author
    userid = id(user)
    # User checks
    if not await user_exists(userid):
        await new_user(ctx, bank_dict, userid)
    # Embed
    embed=Embed(
        title='Aincrad Stock Exchange',
        description='Good credit? Bad credit? No credit? No problem!',
        colour=0x140088
    )

# for s in sorted(['NVG', 'AUG', 'AMS', 'STL', 'MCB']):
#     print(stock_home_value(s), new_value(stock_home_value(s), s))