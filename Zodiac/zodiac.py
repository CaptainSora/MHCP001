from datetime import datetime
from json import dump, load

from discord import Embed

from Zodiac.dategen import random_day

### Shiro222
def pokeCalendar(gen, searchdate):

    # randdate = random_day()

    with open(f"Zodiac/gen{gen}.txt", "r", encoding = "utf-8") as f:
        megalist = f.read().strip().split("\n")
    
    daylist = []
    reignlist = []
    seasonlist = []
    feb29 = []

    for item in megalist:
        if item != "":
            if item[0] == "-":
                daylist.append(item)
            elif item[0] == "T":
                extracted = item[:-1].split(' (')
                extracted[1] = extracted[1].split('-')[1]
                reignlist.append(extracted)
            elif item[0] == "S":
                extracted = item[:-1].split(' (')
                extracted[1] = extracted[1].split(' - ')[1]
                seasonlist.append(extracted)
            else:
                feb29.append(item)

    day_of_year = searchdate.timetuple().tm_yday
    curDate = daylist[day_of_year-1][2:]

    for reign in reignlist:
        reignEndDate = convertReignDate(reign[1], searchdate)
        if searchdate <= reignEndDate:
            curReign = reign[0]
            break
   
    for season in seasonlist:
        seasonEndDate = convertSeasonDate(season[1], searchdate)
        if searchdate <= seasonEndDate:
            curSeason = season[0]
            break


    dateString = searchdate.strftime("%b %d").replace(" 0"," ")
    curSeason = curSeason.title().replace(" Of ", " of ").replace(" The ", " the ")
    curReign = curReign.replace("The ", "")

    # Feb 29 Check
    if searchdate.day == 29 and searchdate.month == 2 and gen == 5:
        return "Feb 29: " + feb29[0][3:-1] + ", " + curSeason
    elif searchdate.day == 29 and searchdate.month == 2 and gen == 4:
        return "Feb 29: Day of the Cloning"
    elif searchdate.day == 29 and searchdate.month == 2 and (gen == 6 or gen == 7):
        return "Feb 29: " + feb29[0][3:-1] + " in the " + curReign + ", " + curSeason

    return dateString + ": The " + curDate + " in the " + curReign + ", " + curSeason


def convertReignDate(date, refdate):
    dateObject = datetime.strptime("2000 " + date, "%Y %m/%d")
    try:
        return dateObject.replace(year=refdate.year)
    except ValueError:
        return datetime(refdate.year, 2, 28)


def convertSeasonDate(date, refdate):
    dateObject = datetime.strptime(date, "%B %d")
    return dateObject.replace(year=refdate.year)


### CapSora
def get_generation(userid):
    with open('Zodiac/prefs.json', 'r') as f:
        prefdict = load(f)
        return prefdict.get(str(userid), 7)

def set_generation(userid, gen):
    with open('Zodiac/prefs.json', 'r') as f:
        prefdict = load(f)
    prefdict[str(userid)] = int(gen)
    with open('Zodiac/prefs.json', 'w') as f:
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
    dateobj = datetime.today()
    embed = Embed(
        title='Pokémon Zodiac',
        color=0xcc0000
    )
    if len(args) == 0:
        # default generation, no custom date
        gen = get_generation(ctx.author.id)
    elif args[0].lower() in ['set', 'setgen', 'gen']:
        # set generation default
        if len(args) < 2 or not valid_gen(args[1]):
            # ERROR MESSAGE
            embed.description = (
                "Could not set default generation, missing or invalid "
                "generation number"
            )
            await ctx.send(embed=embed)
        else:
            # Confirmation message
            set_generation(ctx.author.id, args[1])
            embed.description = (
                f"Successfully set default generation to {args[1]} for "
                f"{ctx.author.mention}."
            )
            await ctx.send(embed=embed)
        return
    elif valid_gen(args[0]):
        # temp generation
        gen = int(args[0])
        if len(args) > 1:
            datestr = ' '.join(args[1:])
            dateobj = parse_date(datestr)
    else:
        # default generation with custom date
        gen = get_generation(ctx.author.id)
        datestr = ' '.join(args)
        dateobj = parse_date(datestr)
    
    # Parse date and call function
    if dateobj is not None:
        # Call function with gen and date
        embed.description = "**" + pokeCalendar(gen, dateobj) + "**"
        embed.set_footer(text=f"Gen {gen}")
        embed.set_image(
            url=(
                f"https://www.dragonflycave.com/zodiac/gen{gen}/image?"
                f"day={dateobj.day}&month={dateobj.strftime('%b')}"
            )
        )
    else:
        embed.description = (
            "Error, unparseable date"
        )
    await ctx.send(embed=embed)
