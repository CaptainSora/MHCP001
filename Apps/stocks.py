"""
Maybe multiple stocks,
NerveGear (NVG), Augma (AUG), AmuSphere (AMS), Soul Translator (STL),
Medicuboid (MCB)
Each stock has its own "center" price
Small fee per transaction, for selling (100 cor + 5%?)
"""
from datetime import datetime, timezone
from json import dump, load
from math import sqrt
from random import random

import numpy as np
from dateutil import tz
from dateutil.parser import parse
from discord import Embed
from discord.utils import get

from Apps.bank import id, new_user


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

async def stock_help(ctx, embed):
    embed.description = "Trade Instructions"
    embed.add_field(
        name="Buying and selling",
        value=(
            "Use .stocks <buy/sell> <brief> <qty> to buy stocks!\n"
            "Stocks and traders refresh every hour."
        ),
        inline=True
    )
    embed.add_field(
        name="Notes",
        value=(
            "1. Buyers and sellers are shared among all users\n"
            "2. There is a fee for completed transactions (selling) so trade "
            "wisely!"
        )
    )
    await ctx.send(embed=embed)

async def invalid_brief(ctx, embed):
    embed.add_field(
        name="Invalid stock brief",
        value="Please enter the three-letter stock brief to trade a stock."
    )
    await ctx.send(embed=embed)

async def invalid_qty(ctx, embed):
    embed.add_field(
        name="Invalid quantity",
        value="Stocks can only be traded in positive integer amounts."
    )
    await ctx.send(embed=embed)

async def invalid_funds(ctx, embed):
    embed.add_field(
        name="Invalid funds",
        value="You do not have enough Cor to buy these stocks."
    )
    await ctx.send(embed=embed)

async def invalid_stocks(ctx, embed):
    embed.add_field(
        name="Invalid stocks",
        value="You do not have enough stock to sell."
    )
    await ctx.send(embed=embed)

async def invalid_traders(ctx, embed):
    embed.add_field(
        name="Invalid traders",
        value="There are not enough traders to complete your transaction."
    )
    await ctx.send(embed=embed)

# Requires valid input
def trade_stock(userid, price, brief, qty, value, buy=True):
    """
    Qty is negative for sales, positive for purchases
    Assumes trade is valid
    Price > 0
    Qty > 0 if buy, < 0 if not buy
    Value < 0 if buy, > 0 if not buy
    Value is change in cor for user, includes seller fees
    TRADERS MUST BE REMOVED EXTERNALLY
    """
    # Open bank dict
    with open('Apps/bank.json') as f:
        bank_dict = load(f)
    stockdata = bank_dict[userid]['stocks'][brief]
    if buy:
        bank_dict[userid]['stocks'][brief]['avg_value'] = round(
            (stockdata['qty'] * stockdata['avg_value'] + price * qty)
            / (stockdata['qty'] + qty)
        )
    else:
        # profit = (sell price - fees) + (qty * avg_price)
        # note qty < 0
        bank_dict[userid]['stocks'][brief]['profit'] += round(
            value + (qty * stockdata['avg_value'])
        )
    bank_dict[userid]['stocks'][brief]['qty'] += qty
    bank_dict[userid]['cor'] += value
    # Save data
    with open('Apps/bank.json', 'w') as f:
        dump(bank_dict, f)

async def trade(ctx, embed, userid, args, buy=True):
    # Invalid trade command
    if len(args) < 3:
        await stock_help(ctx, embed)
        return
    embed.description = f"Transaction for {userid}"
    # Load stock history
    with open('Apps/stocks.json') as f:
        stock_history = load(f)
    # Command validation
    if args[1].upper() not in stock_history['stocks']:
        await invalid_brief(ctx, embed)
        return
    if (not args[2].isdecimal()) or (int(args[2]) <= 0):
        await invalid_qty(ctx, embed)
        return
    # Variable setup
    brief = args[1].upper()
    stock = stock_history['stocks'][brief] # Shortcut
    price = stock['values'][0]
    name = stock['name']
    qty = int(args[2])
    if not buy:
        qty *= -1  # Negative qty for selling stock
    value = (-1) * price * qty  # Positive for selling stock
    # Seller validation
    if (buy and abs(qty) > stock['sellers']) or \
            (not buy and abs(qty) > stock['buyers']):
        await invalid_traders(ctx, embed)
        return
    # Trade validation
    with open('Apps/bank.json') as f:
        bank_dict = load(f)
    if bank_dict[userid]['cor'] + value < 0:
        await invalid_funds(ctx, embed)
        return
    if 'stocks' not in bank_dict[userid]:
        bank_dict[userid]['stocks'] = {}
    if brief not in bank_dict[userid]['stocks']:
        bank_dict[userid]['stocks'][brief] = {
            "name": name,
            "qty": 0,
            "avg_value": 0,
            "profit": 0
        }
    if bank_dict[userid]['stocks'][brief]['qty'] + qty < 0:
        await invalid_stocks(ctx, embed)
        return
    # Valid trade (hopefully)
    if buy:
        trade_stock(userid, price, brief, qty, value, buy=True)
        # Remove traders
        stock_history['stocks'][brief]['sellers'] -= qty
        with open('Apps/stocks.json', 'w') as f:
            dump(stock_history, f)
        # Print confirmation
        embed.add_field(
            name=f"Successful purchase of {name} ({brief})",
            value=(f"{qty} shares"),
            inline=False
        )
        embed.add_field(
            name=f"Price per share",
            value=f"{price} Cor"
        )
        embed.add_field(
            name=f"Total purchase price",
            value=f"{abs(value):,} Cor"
        )
        await ctx.send(embed=embed)
    else:
        # Confirm sale
        embed.description += (
            "\n\nPlease react with ✅ to confirm your transaction.\n"
            "This will automatically cancel in 15 seconds."
        )
        embed.add_field(  # Field 0
            name=f"Selling {name} ({brief})",
            value=(f"{abs(qty)} shares"),
            inline=False
        )
        embed.add_field(  # Field 1
            name=f"Price per share",
            value=f"{price} Cor"
        )
        # 100 Cor + 5% fees
        fees = 100 + (value * 0.05)
        embed.add_field(  # Field 2
            name=f"Transaction fees",
            value=f"{fees:,} Cor"
        )
        embed.add_field(   # Field 3
            name=f"Total sale price",
            value=f"{value - fees:,} Cor"
        )
        msg = await ctx.send(embed=embed)
        await msg.add_reaction('✅')

async def sell_confirmed(message, fields, userid):
    # Field 0: Name, Brief
    name = fields[0].name.split()[1]
    brief = fields[0].name[-4:-1]
    # Field 0: Quantity
    qty = (-1) * int(fields[0].value.split()[0])
    # Field 1: Price per share
    price = int(fields[1].value.split()[0])
    # Field 2: Fees paid
    fees = int(fields[2].value.split()[0].replace(',', ''))
    # Field 3: Final value
    value = int(fields[3].value.split()[0].replace(',', ''))
    # Complete transaction
    trade_stock(userid, price, brief, qty, value, buy=False)
    # Remove traders
    with open('Apps/stocks.json') as f:
        stock_history = load(f)
    stock_history['stocks'][brief]['buyers'] += qty  # qty < 0
    with open('Apps/stocks.json', 'w') as f:
        dump(stock_history, f)
    # Print confirmation
    embed=Embed(
        title='Aincrad Stock Exchange',
        description=f"Transaction for {userid}",
        colour=0x140088
    )
    embed.add_field(
        name=f"Successful purchase of {name} ({brief})",
        value=(f"{qty} shares"),
        inline=False
    )
    embed.add_field(
        name=f"Price per share",
        value=f"{price} Cor"
    )
    embed.add_field(
        name=f"Fees paid",
        value=f"{fees:,} Cor"
    )
    embed.add_field(
        name=f"Total sale price",
        value=f"{value:,} Cor"
    )
    await message.channel.send(embed=embed)

# async def test(ctx, embed):
#     embed.description = f"Testing {ctx.message.author}"
#     embed.add_field(name="This is a name", value="This is a value")
#     msg = await ctx.send(embed=embed)
#     await msg.add_reaction('✅')

# async def test_success(msg, name='', value=''):
#     print("Test success", msg)
#     print(name, value)

async def stock_prices(ctx, embed, emojis):
    # Load stock information
    with open('Apps/stocks.json') as f:
        stock_history = load(f)
    green = get(emojis, name='uparrow')
    red = get(emojis, name='downarrow')
    yellow = get(emojis, name='nochange')
    for stock, data in stock_history['stocks'].items():
        diff = data['values'][0] - data['values'][1]
        if diff < 0:
            arrow = red
        elif diff == 0:
            arrow = yellow
        else:
            arrow = green
        embed.add_field(
            name=f"{data['name']} ({stock})",
            value=(f"{data['values'][0]} {arrow} {abs(diff)}")
        )
        embed.add_field(name='Buyers', value=f"{data['buyers']}")
        embed.add_field(name='Sellers', value=f"{data['sellers']}")
    await ctx.send(embed=embed)

async def stock_price_history(ctx, embed, emojis):
    dur = 8
    # Load stock information
    with open('Apps/stocks.json') as f:
        stock_history = load(f)
    embed.description = f'{dur} hour history, most recent on right'
    green = get(emojis, name='uparrow')
    red = get(emojis, name='downarrow')
    yellow = get(emojis, name='nochange')
    for stock, data in stock_history['stocks'].items():
        outstr = f"{data['values'][dur-1]}"
        for i in range(dur-1):
            diff = data['values'][dur-2-i] - data['values'][dur-1-i]
            if diff > 0:
                outstr += f' {green} '
            elif diff == 0:
                outstr += f' {yellow} '
            else:
                outstr += f' {red} '
            outstr += f"{data['values'][dur-2-i]}"
        embed.add_field(
            name=f"{data['name']} ({stock})",
            value=outstr,
            inline=False
        )
    await ctx.send(embed=embed)

async def view_holdings(ctx, embed, userid):
    # User check
    user = ctx.message.author
    userid = id(user)
    await new_user(ctx, userid)
    # Read data
    with open('Apps/bank.json') as f:
        bank_dict = load(f)
    embed.description = f"Stock holdings for {userid}"
    if "stocks" in bank_dict[userid]:
        holdings = sorted([s for s in bank_dict[userid]['stocks']])
        for brief in holdings:
            data = bank_dict[userid]['stocks']['brief']
            embed.add_field(
                name=f"{data['name']} ({brief})",
                value=f"{data['qty']}"
            )
            embed.add_field(name="Avg. value", value=f"{data['avg_value']}")
            embed.add_field(name='\u200b', value='\u200b')
    await ctx.send(embed=embed)

for s in sorted(['NVG', 'AUG', 'AMS', 'STL', 'MCB']):
    print(s, stock_home_value(s))

if "-3".isdecimal():
    print("-3 is a decimal")

async def stocks(ctx, emojis, args):
    # User check
    user = ctx.message.author
    userid = id(user)
    await new_user(ctx, userid)
    # Read data (only used for holdings command atm)
    with open('Apps/bank.json') as f:
        bank_dict = load(f)
    # Update stock history
    check_history()
    # Embed
    embed=Embed(
        title='Aincrad Stock Exchange',
        description=(
            'Good credit? Bad credit? No credit? No problem!\n'
            "Oh you dead? F*** it, GHOST CREDIT!\nᴵ'ᵐ ᵍᵒⁿ ᵍᵉᵗ ᵃ ˢᵘᵇᵃʳᵘ"
        ),
        colour=0x140088
    )
    # Logic
    if len(args) == 0:
        await stock_prices(ctx, embed, emojis)
    elif args[0] in ['help']:
        await stock_help(ctx, embed)
    elif args[0] in ['history', 'h']:
        await stock_price_history(ctx, embed, emojis)
    elif args[0] in ['holdings', 'owned']:
        if len(args) >= 2 and args[1] in bank_dict:
            userid = args[1]
        await view_holdings(ctx, embed, userid)
    # elif args[0] in ['test', 't']:
    #     await test(ctx, embed)
    elif args[0] in ['buy', 'b']:
        await trade(ctx, embed, userid, args, buy=True)
    elif args[0] in ['sell', 's']:
        await trade(ctx, embed, userid, args, buy=False)
