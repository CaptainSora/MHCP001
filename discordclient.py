from asyncio import sleep
from os import getenv
from random import choice

from discord import Activity, ActivityType, Client, Status
from discord.ext import commands
from discord.utils import get
from dotenv import load_dotenv

load_dotenv()
TOKEN = getenv('API_ACCESS')

bot = commands.Bot(command_prefix='.')

@bot.event
async def on_ready():
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
    if 'ping' in message.content.lower():
        emoji = get(bot.emojis, name='omaewamou')
        await message.channel.send(emoji)
    if 'dab' in message.content.lower():
        emoji = get(bot.emojis, name='dabby')
        await message.channel.send(emoji)
    if 'uwu' in message.content.lower():
        emoji = get(bot.emojis, name='uwu')
        await message.channel.send(emoji)
    if 'pls' in message.content.lower():
        emoji = get(bot.emojis, name='pepe_pls')
        await message.channel.send(emoji)
    await bot.process_commands(message)  # NECESSARY TO NOT BREAK COMMANDS

bot.run(TOKEN)
