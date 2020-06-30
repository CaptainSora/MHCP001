from json import dump, load
from Apps.bank import id, new_user
from discord import Embed
from Help.help import help_page

ICONS = {
    "first": "🥇",
    "second": "🥈",
    "third": "🥉",
    "medal": "🏅",
    "ribbon": "🎗️",
    "sparkle": "❇️",
    "die": "🎲",
    "gem": "💎",
    "stocks": "📈",
    "dna": "🧬",
    "trophy": "🏆",
    "crown": "👑",
    "slots": "🎰",
    "fire": "🔥",
    "money": "💰",
    "other": "🎯🔰🧮🎉🌸⚡☄️💥🛡️🪓⚔️🗡️🎁"
}

TIERS = ['🎗️', '🥉', '🥈', '🥇', '🏆', '👑']

async def badges(ctx, userid):
    """
    Returns a list of badges for the user
    """
    badges = []
    # Open badge list
    with open('Apps/badges.json') as f:
        badge_dict = load(f)
    for b, v in badge_dict.items():
        tiers = [t for t in range(6) if userid in badge_dict[b]['users'][t]]
        if not tiers:
            continue
        maxtier = max(tiers)
        badges.append([
            maxtier,
            ' '.join([
                TIERS[maxtier],
                b.replace('&', f'{v["reqs"][maxtier]:,}')
                ]
            )
        ])
    badges.sort(key=lambda x: x[0], reverse=True)
    return list(zip(*badges))[1]

async def all_badges(ctx, args):
    # Check for match filter
    match = ''
    if len(args) > 0:
        if args[0] in ['untouchable', 'u']:
            match = 'UNTOUCHABLE'
        elif args[0] in ['stocks', 's']:
            match = 'Stocks'
        elif args[0] in ['roulette', 'r']:
            match = 'Roulette'
        elif args[0] in ['bank', 'b']:
            match = 'Bank'
    # Open badge list
    with open('Apps/badges.json') as f:
        badge_dict = load(f)
    badge_list = []
    # Loop
    for b, v in badge_dict.items():
        if match and match not in b.split():
            continue
        badge_set = []
        for i in range(6):
            badge_set.append(
                ' '.join([TIERS[5-i], b.replace('&', f'{v["reqs"][5-i]:,}')])
            )
        badge_list.append('\n'.join(badge_set))
    # Embed
    embed = Embed(
        title='All badges',
        description='\n\n'.join(badge_list),
        colour=0xa600a0
    )
    await ctx.send(embed=embed)
    

async def add_badge(ctx, args):
    """
    Safe to call anytime
    """
    pass

async def display_user(ctx, embed, userid):
    # Bank balance
    with open('Apps/bank.json') as f:
        bank_dict = load(f)
    balance = bank_dict[userid]['cor']
    # Stock value
    stock_value = 0
    for v in bank_dict[userid]['stocks'].values():
        stock_value += v['qty'] * v['avg_value']
    # Badges
    badge_list = '\n'.join(await badges(ctx, userid))
    # Embed
    embed.add_field(
        name='Bank Balance',
        value=f"{balance:,} Cor",
        inline=False
    )
    embed.add_field(
        name='Stock Value',
        value=f"{stock_value:,} Cor",
        inline=False
    )
    embed.add_field(
        name='Badges',
        value=badge_list,
        inline=False
    )
    await ctx.send(embed=embed)

async def profile(ctx, args):
    # User check
    user = ctx.message.author
    userid = id(user)
    await new_user(ctx, userid)
    # Read bank dict
    with open('Apps/bank.json') as f:
        bank_dict = load(f)
    # Embed
    embed = Embed(
        title = userid,
        description = "No title",
        colour = 0xa600a0
    )
    # Logic
    if len(args) == 0:
        await display_user(ctx, embed, userid)
    elif args[0] in ['help']:
        await help_page(ctx, 'profile')
    elif args[0] in bank_dict:
        embed.title = args[0]
        await display_user(ctx, embed, args[0])
