from dategen import random_day
from datetime import datetime


def pokeCalendar(gen): 

    randdate = random_day()

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

    day_of_year = randdate.timetuple().tm_yday
    curDate = daylist[day_of_year-1][2:]

    for reign in reignlist:
        reignEndDate = convertReignDate(reign[1], randdate)
        if randdate <= reignEndDate:
            curReign = reign[0]
            break
   
    for season in seasonlist:
        seasonEndDate = convertSeasonDate(season[1], randdate)
        if randdate <= seasonEndDate:
            curSeason = season[0]
            break

    # Feb 29 Check
    if randdate.day == 29 and randdate.month == 2:
        return "Feb 29: " + feb29[0][3:-1] + ", " + curSeason


    dateString = randdate.strftime("%b %d").replace(" 0"," ")
    curSeason = curSeason.title().replace(" Of ", " of ").replace(" The ", " the ")
    curReign = curReign.replace("The ", "")

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


async def zodiac_wrapper(ctx, args):
    await ctx.send("Nothing here yet...")


print(pokeCalendar(7))
