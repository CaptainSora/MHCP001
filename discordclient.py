from asyncio import sleep
from os import getenv
from random import choice

from discord import Activity, ActivityType, Client, File, Status
from discord.ext import commands
from discord.utils import get
from dotenv import load_dotenv

from json import load

load_dotenv()
TOKEN = getenv('API_ACCESS')

bot = commands.Bot(command_prefix='.')

@bot.event
async def on_ready():
    global emote_dict, gif_dict, react_dict
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


@bot.command(name='poke')
async def poke(ctx):
    await ctx.send("No poking. For real this time.")

@bot.command(name='emote')
async def emote(ctx):
    await ctx.send(choice(bot.emojis))

@bot.command(name='logout')
@commands.is_owner()
async def logout(ctx):
    await bot.change_presence(activity=None, status=Status('offline'))
    print("Goodnight!")
    await bot.logout()


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    for k in emote_dict:
        if k in message.content.lower():
            emoji = get(bot.emojis, name=emote_dict[k])
            await message.channel.send(emoji)
            break
    for k in gif_dict:
        if k in message.content.lower():
            await message.channel.send(file=File(gif_dict[k]))
    for k in react_dict:
        if k in message.content.lower():
            if 'exact' in react_dict[k] and k != message.content.lower():
                continue
            for k, v in react_dict[k].items():
                if k == 'unicode':
                    await message.add_reaction(chr(int(v, base=16)))
    await bot.process_commands(message)  # NECESSARY TO NOT BREAK COMMANDS

bot.run(TOKEN)
