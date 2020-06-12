from discord import Client, ActivityType, Activity
from asyncio import sleep
from random import choice

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
            await client.change_presence(
                activity=Activity(
                    name="your mental health | .help",
                    type=ActivityType.watching
                )
            )
            break


CALL_RESP = {
    ".poke": "No poking.",
    ".taco": "I love spicy tacos!",
    ".spicytaco": "Mm! Spicy...",
    ".navi": [
        "Your destination is on the right in three sandwiches.",
        "Head northeast until you reach a wall. Then stop. Timeout."
    ]
}

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content in CALL_RESP:
        response = CALL_RESP[message.content]
        if type(response) == type([]):
            response = choice(response)
        await message.channel.send(response)
    elif message.content == ".firewall":
        await message.channel.send("...bypassing security...")
        message = await message.channel.send("...10%...")
        for i in range(2, 11):
            await sleep(1)
            await message.edit(content=f"...{i}0%...")
        await message.delete()
        await message.channel.send("Security clearance granted!")
    elif message.content == ".joke":
        await message.channel.send("Searching up jokes...")
        message = await message.channel.send("| 0%")
        for i in range(1, 11):
            await sleep(0.2)
            await message.edit(content=f"{'█' * i} {i}0%")
        await message.delete()
        await message.channel.send(
            "Why was he called Thinker if he wasn't good at thinking?"
        )
    elif message.content.startswith(".riddle"):
        await riddle(message)
    elif message.content.startswith(".solve"):
        await solve_riddle(message)
    elif message.content.startswith(".giveup"):
        await giveup_riddle(message)


riddle_num = None
RIDDLES = [
    [(
        "The more you take, the more you leave behind. What am I?"
    ), "footsteps"],
    [(
        "What is more useful when it is broken?"
    ), "egg"],
    [(
        "What is black when you buy it, red when you use it, and grey when you"
        " throw it away?"
    ), "coal"],
    [(
        "I am full of holes but I still hold water. What am I?"
    ), "sponge"],
    [(
        "What seven letter word is spelled the same way backwards and "
        "forwards?"
    ), "racecar"],
    [(
        "You have three stoves: a gas stove, a wood stove, and a coal stove, "
        "but only one match. Which should you light first?"
    ), "match"],
    [(
        "I'm not clothing but I cover your body. The more I'm used, the "
        "thinner I grow. What am I?"
    ), "soap"],
    [(
        "What 5 letter word typed in all capital letters is the same upside "
        "down?"
    ), "swims"],
    [(
        "Until I am measured I am not known, yet how you miss me when I have "
        "flown. What am I?"
    ), "time"],
    [(
        "If you drop me, I'm sure to crack. Give me a smile, and I'll smile "
        "back. What am I?"
    ), "mirror"],
    [(
        "I'm tall when I'm young and short when I'm old. What am I?"
    ), "candle", "pencil"],
    [(
        "What runs, but has no legs?"
    ), "water", "nose"],
    [(
        "What can you break, even without touching it?"
    ), "sweat", "promise"],
    [(
        "What goes up but never comes down?"
    ), "age"],
    [(
        "A man who was outside in the rain without an umbrella, hat, or jacket"
        " didn't get a single hair on his head wet. Why?"
    ), "bald"],
    [(
        "What gets wet while drying?"
    ), "towel"],
    [(
        "I have branches, but no fruit, trunk, or leaves. What am I?"
    ), "bank"],
    [(
        "David's parents have three children, Snap, Crackle, and ...?"
    ), "david"],
    [(
        "What can you hold in one hand but not the other?"
    ), "elbow", "hand", "arm", "wrist"],
    [(
        "Where does today come before yesterday?"
    ), "dictionary"],
    [(
        "What has lots of eyes, but can't see?"
    ), "potato"],
    [(
        "What has one eye, but can't see?"
    ), "needle"],
    [(
        "What has hands, but can't clap?"
    ), "clock"],
    [(
        "I am an odd number. Take a letter away and I become even. What am I?"
    ), "seven"],
    [(
        "If there are three apples and you take away two, how many apples do "
        "you have?"
    ), "two"],
    [(
        "What five-letter word becomes shorter when you add two letters to it?"
    ), "short"],
    [(
        "What begins with an 'e', ends with an 'e', and contains one letter?"
    ), "envelope"],
    [(
        "What do you break, the moment you say it?"
    ), "silence"],
    [(
        "I am lighter than a feather, but no person can hold me for very long."
        " What am I?"
    ), "breath"],
    [(
        "Feed me and I live, give me a drink and I die. What am I?"
    ), "fire"],
    [(
        "I have four fingers and a thumb, but I'm not alive. What am I?"
    ), "glove"],
    [(
        "I have keys but no locks, and space but no room. You can enter, but "
        "you can't go outside. What am I?"
    ), "keyboard"],
    [(
        "What runs but never walks, and has a mouth but never talks?"
    ), "river"],
    [(
        "When things go wrong, what can you always count on?"
    ), "fingers"],
    [(
        "What has a neck but no head?"
    ), "bottle"],
    [(
        "What can you catch but not throw?"
    ), "cold"],
    [(
        "What begins with 't', ends with 't', and has 't' in it?"
    ), "teapot"],
    [(
        "What can you never eat for breakfast?"
    ), "lunch", "dinner"],
    [(
        "I fly all day long, but don't go anywhere. What am I?"
    ), "flag"],
    [(
        "What english word sounds the same even after removing four of its "
        "five letters?"
    ), "queue"],
    [(
        "I shave all day but still have a beard. Who am I?"
    ), "barber"]
]


async def riddle(message):
    global riddle_num
    if riddle_num is None:
        riddle_num = choice(range(len(RIDDLES)))
    await message.channel.send(RIDDLES[riddle_num][0])
    await message.channel.send("Use '.solve <solution>' to solve!")


async def giveup_riddle(message):
    global riddle_num
    await message.channel.send("Use '.riddle' to get a new riddle.")
    riddle_num = None


async def solve_riddle(message):
    global riddle_num
    guess = message.content
    await message.delete()
    for i in range(1, len(RIDDLES[riddle_num])):
        if RIDDLES[riddle_num][i] in guess.lower():
            riddle_num = None
            await message.channel.send(
                f"{message.author.mention} Correct!"
            )
            return
    await message.channel.send(
        f"{message.author.mention} Incorrect! Try again!"
    )


with open("token.txt") as f:
    token = f.read()

client.run(token)
