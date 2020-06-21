from asyncio import sleep, TimeoutError
from json import load
from os import getenv
from random import choice

from discord import Activity, ActivityType, Client, Embed, File, Status
from discord.ext import commands
from discord.utils import get
from dotenv import load_dotenv

import Apps.bank
import Apps.stocks
import Apps.untouchable

load_dotenv()
TOKEN = getenv('API_ACCESS')

bot = commands.Bot(command_prefix='.')

dict_ready = False

@bot.event
async def on_ready():
    global emote_dict, gif_dict, react_dict, dict_ready
    print(
        f"{bot.user.name} is here to fix bugs and cause chaos. And she's"
        f" all out of bugs."
    )
    await bot.change_presence(
        activity=Activity(
            name="your mental health | .help",
            type=ActivityType.watching
        )
    )
    with open('Apps/emote.json') as f:
        emote_dict = load(f)
    with open('Apps/gif.json') as f:
        gif_dict = load(f)
    with open('Apps/react.json') as f:
        react_dict = load(f)
    dict_ready = True


@bot.command(name='poke')
async def poke(ctx):
    await ctx.send("No poking. For real this time.")

@bot.command(name='emote', help='Displays a random emote')
async def emote(ctx):
    await ctx.send(choice(bot.emojis))

@bot.command(name='emotes', help='Displays a list of all emotes')
async def emotes(ctx):
    await ctx.send('\n'.join(sorted(list(emote_dict.keys()))))

@bot.command(name='gifs', help='Displays a list of all gifs')
async def gifs(ctx):
    entries = sorted([str(x) for x in gif_dict.keys()])
    for i in range(len(entries)):
        if type(gif_dict[entries[i]]) == type([]):
            entries[i] += f' ({len(gif_dict[entries[i]])})'
    await ctx.send('\n'.join(entries))

@bot.command(name='time', aliases=['now', 't', 'utc'])
async def utc_time_wrapper(ctx, *args):
    await Apps.bank.utc_time(ctx)

@bot.command(name='bank', aliases=['b'], help='bank game')
async def bank_wrapper(ctx, *args):
    await Apps.bank.bank(ctx, args)

@bot.command(
    name='untouchable',
    aliases=['lottery', 'lotto', 'u', 'l'],
    help='Play the lottery and win Cor!'
)
async def untouchable_wrapper(ctx, *args):
    await Apps.untouchable.untouchable(ctx, bot.emojis, args)

@bot.command(
    name='stocks',
    aliases=['stock', 's'],
    help='Invest in the stock market!'
)
async def stocks_wrapper(ctx, *args):
    await Apps.stocks.stocks(ctx, bot.emojis, args)

@bot.command(name='logout', help='Admin command')
@commands.is_owner()
async def logout(ctx):
    await bot.change_presence(activity=None, status=Status('offline'))
    print("Goodnight!")
    await bot.logout()


@bot.event
async def on_message(message):
    if not dict_ready:
        return
    if message.author == bot.user:
        await confirm(message)
        return
    for k in emote_dict:
        if k in message.content.lower().split():
            if (":" + emote_dict[k] + ":") not in message.content.lower():
                emoji = get(bot.emojis, name=emote_dict[k])
                await message.channel.send(emoji)
                break
    for k in gif_dict:
        if k == message.content.lower():
            url = gif_dict[k]
            if type(url) == type([]):
                url = choice(url)
            embed = Embed()
            embed.set_image(url=url)
            # embed.set_footer(text=k)
            # await message.delete()
            await message.channel.send(embed=embed)
    for k in react_dict:
        if k in message.content.lower().split():
            # Check for message exact requirement
            # Deprecated
            # if 'exact' in react_dict[k]:
            #     if k != message.content.lower():
            #         continue
            # else:
            #     if k not in message.content.lower().split():
            #         continue
            for k, v in react_dict[k].items():
                if k == 'unicode':
                    await message.add_reaction(chr(int(v, base=16)))
                elif k == 'name':
                    emoji = get(bot.emojis, name=v)
                    await message.add_reaction(emoji)
    await bot.process_commands(message)  # NECESSARY TO NOT BREAK COMMANDS

async def confirm(message):
    if len(message.embeds) == 0:
        return

    def check(reaction, user):
        return str(user) in message.embeds[0].description \
            and str(reaction) == '✅'
    
    try:
        reaction, user = await bot.wait_for(
            'reaction_add',
            timeout=15.0,
            check=check
        )
        reaction = reaction  # Unused variable
    except TimeoutError:
        if message.embeds[0].title == 'Aincrad Stock Exchange' \
                and "cancel in 15 seconds" in message.embeds[0].description:
            # Edit message
            embed=Embed(
                title='Aincrad Stock Exchange',
                description=f"Cancelled Transaction for {str(user)}",
                colour=0x140088
            )
            await message.edit(embed=embed)
    else:
        if message.embeds[0].title == 'Aincrad Stock Exchange' \
                and "cancel in 15 seconds" in message.embeds[0].description:
            fields = message.embeds[0].fields
            await Apps.stocks.sell_confirmed(message, fields, str(user))

# @bot.event
# async def on_raw_reaction_add(payload):
#     user = bot.get_user(payload.user_id)
#     if user == bot.user:
#         return
#     channel = bot.get_channel(payload.channel_id)
#     message = await channel.fetch_message(payload.message_id)
#     await channel.send(f"Reaction added by {user.mention}")
#     # await channel.send(message.embeds[0].title)


bot.run(TOKEN)
