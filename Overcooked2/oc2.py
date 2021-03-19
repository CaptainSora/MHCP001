from difflib import SequenceMatcher
from json import dump, load

from discord import Embed


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
        if "World" in stardict:
            for i in range(len(stardict['World'])):
                world = stardict['World'][i]
                starcount.append([f"World {i+1}", sum(world), 4 * len(world)])
        if "Kevin" in stardict:
            kevin = stardict['Kevin']
            starcount.append(["Kevin", sum(kevin), 4 * len(kevin)])
        if "Tutorial" in stardict:
            starcount.append(["Tutorial", stardict['Tutorial'], 4])
        if "Horde" in stardict:
            horde = stardict['Horde']
            starcount.append(["Horde", 3 * sum(horde), 3 * len(horde)])
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
