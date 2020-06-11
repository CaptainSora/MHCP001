from discord import Client
from asyncio import sleep

client = Client()
GUILD = "Asteros"

@client.event
async def on_ready():
    for guild in client.guilds:
        if guild.name == GUILD:
            print(
                f"{client.user} is here to fix bugs and cause chaos. And she's"
                f" all out of bugs."
            )
            break


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content == ".poke":
        await message.channel.send("No poking.")
    elif message.content == ".taco":
        await message.channel.send("I love spicy tacos!")
    elif message.content == ".spicytaco":
        await message.channel.send("Mm!")
    elif message.content == ".firewall":
        await message.channel.send("...bypassing security...")
        message = await message.channel.send("...10%...")
        for i in range (2, 11):
            await sleep(1)
            await message.edit(content=f"...{i}0%...")
        message = await message.channel.send("Security clearance granted!")

with open("token.txt") as f:
    token = f.read()

client.run(token)
