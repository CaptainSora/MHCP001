from difflib import SequenceMatcher
from json import dump, load

from discord import Embed

EMOJIDICT = {
    "None": ":new:",
    "Bronze": ":third_place:",
    "Silver": ":second_place:",
    "Gold": ":first_place:",
    "Platinum": ":medal:",
    True: ":white_check_mark:",
    False: ":heavy_check_mark:"
}

STAGEDICT = {
    "B": "Bronze",
    "S": "Silver",
    "G": "Gold",
    "P": "Platinum"
}

async def display_completion(ctx):
    embed = Embed(
        title='Moving Out Completion',
        description='Story',
        color=0x63abeb
    )
    embed.set_footer(text="Page 1 of 2")
    with open('MovingOut/completion.json') as f:
        compdict = load(f)['Story']
    for stage, prog in compdict.items():
        embed.add_field(
            name=stage,
            value=' '.join([EMOJIDICT[p] for p in prog])
        )
        if len(embed.fields) >= 15:
            await ctx.send(embed=embed)
            embed.clear_fields()
            embed.set_footer(text="Page 2 of 2")
    if len(embed.fields) > 0:
        await ctx.send(embed=embed)

async def update_completion(ctx, args):
    # Sample command:
    # .mooupdate S23 Holly's Home
    embed = Embed(
        title='Moving Out Update',
        color=0xd60606 # Red
    )
    if len(args) < 2:
        embed.description = (
            "Invalid command. Sample usage:\n"
            ".mooupdate S23 Holly's Home"
        )
        await ctx.send(embed=embed)
        return
    score = args[0]
    if score[0] not in "BSGP" or any(c not in "123" for c in score[1:]):
        embed.description = (
            "Invalid score argument.\n"
            "Argument format: [BSGP](1)(2)(3)"
        )
        await ctx.send(embed=embed)
    level = ' '.join(args[1:])
    with open('MovingOut/completion.json') as f:
        compdict = load(f)
    bestkey = None
    bestratio = 0.3
    for l in compdict["Story"]:
        r = SequenceMatcher(lambda x: x == " ", level, l).ratio()
        if r > bestratio:
            bestkey = l
            bestratio = r
    if bestkey is None:
        embed.description = f"Could not find level '{level}'."
        await ctx.send(embed=embed)
        return
    embed.colour = 0x00bd5b # Green
    compdict["Story"][bestkey] = [
        STAGEDICT[score[0]], "1" in score, "2" in score, "3" in score
    ]
    with open('MovingOut/completion.json', 'w') as f:
        dump(compdict, f)
    embed.description = (
        f"Successfully updated {bestkey} to "
        f"{' '.join([EMOJIDICT[p] for p in compdict['Story'][bestkey]])}."
    )
    await ctx.send(embed=embed)
    await display_completion(ctx)
    