from discord import Client

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
    
    if ".poke" in message.content:
        await message.channel.send("No poking.")

with open("token.txt") as f:
    token = f.read()

client.run(token)
