from asyncio import sleep, TimeoutError
from json import load
from os import getenv
from random import choice

from discord import Activity, ActivityType, Client, Embed, File, Status
from discord.ext import commands
from discord.utils import get
from dotenv import load_dotenv

import Apps.bank
import Apps.roulette
import Apps.stocks
import Apps.untouchable
import Apps.profile
import DG.dg
from Help.help import help_page

load_dotenv()
API_ACCESS = getenv('API_ACCESS')

bot = commands.Bot(command_prefix='.')
bot.remove_command('help')

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


@bot.command(name='help', aliases=['h'])
async def help(ctx):
    await help_page(ctx, "bot")

@bot.command(name='poke')
async def poke(ctx):
    phrases = [
        "Hey! No fair!",
        "No more poking. Hmpf.",
        "What's up?",
        "You called?",
        "\\*yawns\\*"
    ]
    await ctx.send(choice(phrases))

@bot.command(name='taco')
async def taco(ctx):
    phrases = [
        "Om nom nom...",
        "Mmm, tacos...",
        "Spicy!!",
        "Ish sho good!"
    ]
    await ctx.send(choice(phrases))

@bot.command(name='emote')
async def emote(ctx):
    await ctx.send(choice(bot.emojis))

@bot.command(name='emotes')
async def emotes(ctx):
    await ctx.send('\n'.join(sorted(list(emote_dict.keys()))))

@bot.command(name='gifs')
async def gifs(ctx):
    entries = sorted([str(x) for x in gif_dict.keys()])
    for i in range(len(entries)):
        if type(gif_dict[entries[i]]) == type([]):
            entries[i] += f' ({len(gif_dict[entries[i]])})'
    await ctx.send('\n'.join(entries))

@bot.command(name='reacts')
async def reacts(ctx):
    await ctx.send('\n'.join(sorted(list(react_dict.keys()))))

@bot.command(name='time', aliases=['utc'])
async def utc_time_wrapper(ctx, *args):
    await Apps.bank.utc_time(ctx)

@bot.command(name='bank', aliases=['b'])
async def bank_wrapper(ctx, *args):
   await Apps.bank.bank(ctx, args)

@bot.command(name='untouchable', aliases=['u'])
async def untouchable_wrapper(ctx, *args):
    await Apps.untouchable.untouchable(ctx, bot.emojis, args)

@bot.command(name='stocks', aliases=['s'])
async def stocks_wrapper(ctx, *args):
    await Apps.stocks.stocks(ctx, bot.emojis, args)

@bot.command(name='roulette', aliases=['r'])
async def roulette_wrapper(ctx, *args):
    await Apps.roulette.roulette(ctx, args)

@bot.command(name='profile', aliases=['p'])
async def profile_wrapper(ctx, *args):
    await Apps.profile.profile(ctx, args)

@bot.command(name='dg')
async def dg_wrapper(ctx, *args):
    await DG.dg.dg(ctx, args)

@bot.command(name='badges')
async def badge_wrapper(ctx, *args):
    await Apps.profile.all_badges(ctx, args)

@bot.command(name='status')
async def status(ctx):
    await ctx.send(
        f"{bot.user.name} is here to fix bugs and cause chaos. And she's all "
        f"out of bugs."
    )

@bot.command(name='logout', help='Admin command')
@commands.is_owner()
async def logout(ctx):
    await bot.change_presence(activity=None, status=Status('offline'))
    await ctx.send("Logging off. Goodnight!")
    await bot.logout()


@bot.event
async def on_message(message):
    if not dict_ready:
        return
    if message.author == bot.user:
        await confirm(message)
        return
    if message.content.startswith('.'):
        await bot.process_commands(message)  # NECESSARY TO NOT BREAK COMMANDS
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

async def confirm(message):
    if len(message.embeds) == 0:
        return
    if not message.embeds[0].description:
        return
    if "cancel in 15 seconds" not in message.embeds[0].description:
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
        if message.embeds[0].title == 'Aincrad Stock Exchange':
            userid = message.embeds[0].description.split()[2]
            # New message
            embed=Embed(
                title='Aincrad Stock Exchange',
                description=f"Cancelled Transaction for {userid}",
                colour=0x379cfa
            )
            await message.delete()
            await message.channel.send(embed=embed)
    else:
        if message.embeds[0].title == 'Aincrad Stock Exchange':
            fields = message.embeds[0].fields
            await Apps.stocks.sell_confirmed(message, fields, str(user))


bot.run(API_ACCESS)
