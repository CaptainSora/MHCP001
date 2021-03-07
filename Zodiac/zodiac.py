from datetime import datetime
from json import dump, load

from Zodiac.dategen import random_day

def get_generation(userid):
    with open('Zodiac/prefs.json', 'r') as f:
        prefdict = load(f)
        return prefdict.get(userid, 7)

def set_generation(userid, gen):
    with open('Zodiac/prefs.json', 'r+') as f:
        prefdict = load(f)
        prefdict[userid] = gen
        dump(prefdict, f)

def valid_gen(genstr):
    return genstr.isdecimal() and int(genstr) >= 4 and int(genstr) <= 7

def parse_date(datestr):
    valid_formats = [
        '%b %d', '%b %d %Y', '%b %d, %Y',
        '%B %d', '%B %d %Y', '%B %d, %Y',
        '%m/%d', '%Y/%m/%d', '%d/%m/%Y', '%d/%m/%y'
    ]
    for datefmt in valid_formats:
        try:
            return datetime.strptime(datestr, datefmt)
        except ValueError:
            pass
    return None

async def zodiac_wrapper(ctx, args):
    await ctx.send("Nothing here yet...")
    datestr = None
    dateobj = None
    if len(args) == 0:
        pass # ERROR MESSAGE
    elif args[1].lower() in ['set', 'setgen', 'gen']:
        # set generation default
        if len(args) < 2 or not valid_gen(args[1]):
            pass # ERROR MESSAGE
        else:
            set_generation(ctx.author.user.id, args[1])
            pass # Confirmation message
    elif valid_gen(args[1]):
        # temp generation
        if len(args > 2):
            datestr = ' '.join(args[2:])
            gen = int(args[1])
            dateobj = parse_date(datestr)
    else:
        # default generation
        if len(args > 1):
            datestr = ' '.join(args[1:])
            gen = get_generation(ctx.author.user.id)
            dateobj = parse_date(datestr)
    # Parse date and call function
    if dateobj is not None:
        pass # Call function with gen and date
    elif datestr is not None:
        pass # Error, unparseable date
    else:
        pass # Call function with gen only
