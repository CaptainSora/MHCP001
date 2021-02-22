import gspread
from datetime import date

gc = gspread.service_account(filename='GuardianTales/client_secret.json')
sh = gc.open("NyaNyaCafe")

async def sc_totals(ctx):
    values = sh.worksheet('SCTotal').row_values(1)
    elements = [
        'Basic: ',
        'Fire:  ',
        'Water: ',
        'Earth: ',
        'Light: ',
        'Dark:  '
    ]
    sctext = '\n'.join([elements[i] + values[i] for i in range(6)])
    await ctx.send(f"Stored SC values:\n```{sctext}```")


async def get_roster(ctx):
    rostersheet = sh.worksheet('Roster')
    rostersheet.sort((13, 'des'))
    values = rostersheet.col_values(1)
    members = len([item for item in values[1:] if item is not None])
    cur_date = date.today().strftime('%b %d').replace(" 0", " ")
    values[0] = f"__Member List as of {cur_date}: ({members}/30)__"
    await ctx.send("```" + '\n'.join(values) + "```")
