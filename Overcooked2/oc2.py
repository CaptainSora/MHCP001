from difflib import SequenceMatcher
from json import dump, load

from discord import Embed

from Overcooked2.greeny import get_rankings

def cur_max_stars(starlist):
    return (
        sum([3 * i if isinstance(i, bool) else i for i in starlist]),
        sum([3 if isinstance(i, bool) else 4 for i in starlist])
    )

def stars_counter(stardict):
    """
    Returns [(name, curstars, totalstars)]
    """
    starcount = []
    if "World" not in stardict:
        # stardict is not lowest level
        for area, subdict in stardict.items():
            substars = stars_counter(subdict)
            starcount.append([
                area,
                sum([t[1] for t in substars]),
                sum([t[2] for t in substars])
            ])
    else:
        # stardict is lowest level
        for zone in stardict:
            # Three possible depths for lowest level dict
            # int, [int, ...], [[int, ...], ...]
            if isinstance(stardict[zone], int):
                starcount.append([zone, stardict[zone], 4])
            elif isinstance(stardict[zone][0], int):
                c, m = cur_max_stars(stardict[zone])
                starcount.append([zone, c, m])
            else:
                for i in range(len(stardict[zone])):
                    c, m = cur_max_stars(stardict[zone][i])
                    starcount.append([f"{zone} {i+1}", c, m])
    return starcount

def stars_wrapper(path):
    with open('Overcooked2/stars.json', 'r') as f:
        stardict = load(f)
    
    selection = []
    for p in path:
        if isinstance(stardict[p], dict):
            stardict = stardict[p]
            selection.append(p)
        else:
            break
    
    return pathtext(selection), stars_counter(stardict)

async def display_stars(ctx, args):
    embed = Embed(
        title='Overcooked 2 Progress',
        color=0x63abeb
    )
    if len(args) > 0 and args[0] in ['h', 'help']:
        embed.description = "Function usage: .stars (path1 | path2)"
        await ctx.send(embed=embed)
    else:
        path, starcount = stars_wrapper(pathfinder(args))
        if path:
            embed.description = f"**{path}**"
        for area in starcount:
            star_emoji = ":star:"
            if area[1] == area[2]:
                star_emoji = ":sparkles:"
            embed.add_field(
                name=area[0],
                value=f"{area[1]}/{area[2]} {star_emoji}"
            )
        await ctx.send(embed=embed)

def pathfinder(args):
    """
    Takes user input and finds the closest matching traversal of stars.json.
    """
    with open('Overcooked2/stars.json', 'r') as f:
        curdict = load(f)
    path = []
    # Split user input
    userinput = [part.strip() for part in ' '.join(args).split('|')]
    wordinput = []
    numinput = []
    for part in userinput[-1].replace('-', ' ').split(' '):
        if numinput or part.isdecimal():
            numinput.append(int(part) - 1)
        else:
            wordinput.append(part)
    if not wordinput:
        wordinput = ["World"]
    userinput[-1] = ' '.join(wordinput)

    for userpath in userinput:
        userpath = userpath.strip()
        bestkey = None
        bestratio = 0.6
        for k in curdict:
            if len(userpath) >= 4 and k.lower().find(userpath.lower()) >= 0:
                bestkey = k
                break
            r = SequenceMatcher(lambda x: x == " ", userpath, k).ratio()
            if r > bestratio:
                bestkey = k
                bestratio = r
        if bestkey is None:
            return path
        else:
            path.append(bestkey)
            curdict = curdict[bestkey]
    
    path.extend(numinput)
    return path

def update(value, path):
    with open('Overcooked2/stars.json', 'r') as f:
        stars = load(f)
    obj = stars
    for p in path:
        obj = obj[p]
    if not isinstance(obj, (int, bool)):
        return False

    if len(path) == 2:
        stars[path[0]][path[1]] = value
    elif len(path) == 3:
        stars[path[0]][path[1]][path[2]] = value
    elif len(path) == 4:
        stars[path[0]][path[1]][path[2]][path[3]] = value
    elif len(path) == 5:
        stars[path[0]][path[1]][path[2]][path[3]][path[4]] = value
    else:
        return False
    
    with open('Overcooked2/stars.json', 'w') as f:
        dump(stars, f)
        return True

def pathtext(path):
    text = ""
    for p in path:
        if isinstance(p, int):
            p = str(p+1)
        if not text:
            text += p
        elif text[-1].isdecimal() and p.isdecimal():
            text += '-' + p
        elif p.isdecimal():
            text += ' ' + p
        else:
            text += ': ' + p
    return text

async def update_stars(ctx, args):
    embed = Embed(
        title='Overcooked 2 Update',
        color=0x63abeb
    )
    if len(args) < 3:
        embed.description = (
            "Function usage: .update [value] [path1 | path2] (| path3)"
        )
        await ctx.send(embed=embed)
        return
    if args[0].isdecimal() and 1 <= int(args[0]) and int(args[0]) <= 4:
        update_value = int(args[0])
    elif args[0].lower() in ['t', 'true', '100']:
        update_value = True
    elif args[0].lower() in ['f', 'false', '0']:
        update_value = False
    else:
        embed.description = "Unknown value."
        await ctx.send(embed=embed)
        return
    
    search_path = pathfinder(args[1:])
    path_text = pathtext(search_path)
    if update(update_value, search_path):
        embed.colour = 0x00bd5b
        embed.description = (
            f"Successfully updated {path_text} to {update_value}."
        )
        await ctx.send(embed=embed)
        await display_stars(ctx, args[1:])
    else:
        embed.colour = 0xd60606
        embed.description = (
            f"Failed to update {path_text}."
        )
        await ctx.send(embed=embed)

def th(num):
    # Assumes num >= 1
    if num == 1:
        return ":first_place: 1st"
    elif num == 2:
        return ":second_place: 2nd"
    elif num == 3:
        return ":third_place: 3rd"
    else:
        emote = ""
        if num <= 5:
            emote = ":cherry_blossom: "
        elif num <= 7:
            emote = ":snowflake: "
        elif num <= 10:
            emote = ":reminder_ribbon: "
        return f"{emote}{num}th"

def pts(rank):
    # Assumes rank >= 1
    lb_scores = [15, 10, 5, 3, 3, 2, 2, 1, 1, 1]
    if rank > 10:
        return 0
    else:
        return lb_scores[rank - 1]

async def dump_rankings(ctx, args):
    embed = Embed(
        title='Overcooked 2 Rankings',
        color=0x63abeb
    )
    lbpoints = 0
    totalpoints = 0
    t10 = [0 for _ in range(10)]
    s10 = [0 for _ in range(10)]
    # Manual search override
    override = False
    if len(args) > 0 and args[1].lower() in ['override', 'o']:
        override = True
    async with ctx.typing():
        rankings = get_rankings(override)
    for header, body in rankings.items():
        embed.description = header
        for level in body:
            embed.add_field(
                name=level[0],
                value=(
                    f"{th(level[1])} {level[2] * ':clapper:'} "
                    f"{level[3] * ':arrows_counterclockwise:'}"
                )
            )
            totalpoints += pts(level[1])
            lbpoints += level[2] * pts(level[1])
            if level[1] <= 10:
                t10[level[1] - 1] += 1
                if level[2]:
                    s10[level[1] - 1] += 1
            if len(embed.fields) >= 24:
                await ctx.send(embed=embed)
                embed.clear_fields()
        if len(embed.fields) > 0:
            await ctx.send(embed=embed)
            embed.clear_fields()
    embed.description = "Summary"
    embed.add_field(
        name="Leaderboard points:",
        value=f"{lbpoints} over {sum(s10)} levels",
        inline=False
    )
    embed.add_field(
        name="Total potential points:",
        value=f"{totalpoints} over {sum(t10)} levels",
        inline=False
    )
    embed.add_field(
        name="Ranks:",
        value='\n'.join([th(i+1) for i in range(10)])
    )
    embed.add_field(
        name="Frequency:",
        value='\n'.join([str(n) for n in t10])
    )
    embed.add_field(
        name="Submitted:",
        value='\n'.join([str(n) for n in s10])
    )
    await ctx.send(embed=embed)

# update highscores