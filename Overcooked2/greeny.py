from datetime import date
from json import dump, load

from bs4 import BeautifulSoup
import requests

TRANSLATION = {
    "story": ["Story"],
    "surf-n-turf": ["Surf 'n' Turf"],
    "christmas": ["Seasonal Updates", "Kevin's Christmas Cracker"],
    "chinese-new-year": ["Seasonal Updates", "Chinese New Year"],
    "campfire-cook-off": ["Campfire Cook Off"],
    "night-of-the-hangry-horde": ["Night of the Hangry Horde"],
    "carnival-of-chaos": ["Carnival of Chaos"],
    "winter-wonderland": ["Seasonal Updates", "Winter Wonderland"],
    "spring-festival": ["Seasonal Updates", "Spring Festival"],
    "suns-out-buns-out": ["Seasonal Updates", "Sun's Out, Buns Out"],
    "moon-harvest": ["Seasonal Updates", "Moon Harvest"]
}

TEAM = "[Blank]"

def scrape_greeny(override=False):
    scrapedate = str(date.today())
    with open('Overcooked2/greeny2p.json', 'r') as f:
        greeny2p = load(f)
    if greeny2p['last-updated'] == scrapedate and not override:
        return
    greeny2p['last-updated'] = scrapedate
    # Begin scraping
    for world in greeny2p:
        if world == 'last-updated':
            continue
        for level in greeny2p[world]:
            r = requests.get(
                f"https://overcooked.greeny.dev/overcooked-2/{world}/{level}"
            )
            soup = BeautifulSoup(r.text, 'html.parser')
            tablelist = soup.find_all("table")
            twoplayerscores = tablelist[2].get_text().split('\n')
            twoplayerscores = [t.strip() for t in twoplayerscores if t.strip()]
            teams = twoplayerscores[6::5]
            if twoplayerscores[7].isdecimal():
                scores = [int(s) for s in twoplayerscores[7::5]]
            else:
                scores = twoplayerscores[7::5]
            greeny2p[world][level] = dict(zip(teams, scores))
            print(f"Scraped {world} {level}")
    with open('Overcooked2/greeny2p.json', 'w') as f:
        dump(greeny2p, f)
    print("Finished scraping!")

def time_lt(t1, t2):
    # expects mm:ss as duration
    # returns t1 < t2
    t1 = [int(t) for t in t1.split(':')]
    t2 = [int(t) for t in t2.split(':')]
    return t1[0] < t2[0] or (t1[0] == t2[0] and t1[1] < t2[1])

def time_int_sub(t1, t2):
    # Calculates t1 - t2
    if isinstance(t1, int):
        return t1 - t2
    else:
        t1 = [int(t) for t in t1.split(':')]
        t2 = [int(t) for t in t2.split(':')]
        diff_s = (60 * t1[0] + t1[1]) - (60 * t2[0] + t2[1])
        return f"{diff_s//60:02}:{diff_s%60:02}"

def get_rankings(override=False):
    # Refresh data
    scrape_greeny(override)
    # Load data
    with open('Overcooked2/greeny2p.json', 'r') as f:
        greeny2p = load(f)
    with open('Overcooked2/highscores.json', 'r') as f:
        highscores = load(f)
    # Return container
    rankings = {}
    for world in greeny2p:
        if world == 'last-updated':
            continue
        # Group header and container
        header = ' - '.join(TRANSLATION[world])
        values = []
        # Parallel access 2nd dictionary
        scores = highscores
        for path in TRANSLATION[world]:
            scores = scores[path]
        # Iterate over levels
        for level in greeny2p[world]:
            # Parallel access 2nd dictionary for high scores
            levelpath = level.split('-')
            levelscore = scores
            if level[0].isdecimal():
                levelscore = levelscore['World']
            for path in levelpath:
                if path.isdecimal():
                    levelscore = levelscore[int(path)-1]
                else:
                    levelscore = levelscore[path.title()]
            if isinstance(levelscore, list):
                levelscore = levelscore[0]
            # levelscore should be base type now (int, with 6-6 str)
            place = 1
            on_lb = TEAM in greeny2p[world][level]
            mismatch = on_lb and levelscore != greeny2p[world][level][TEAM]
            # Iterate over leaderboard
            first_score = None
            next_score = levelscore
            for team, score in greeny2p[world][level].items():
                # Get first score
                if first_score is None:
                    first_score = score
                # compare scores for story 6-6
                if world == 'story' and level == '6-6':
                    if time_lt(score, levelscore):
                        break
                # compare scores for all other levels
                elif score < levelscore:
                    break
                # check for own team
                if team == TEAM:
                    break
                # increment and update next score
                place += 1
                if score != levelscore:
                    next_score = score
            values.append([
                level, place, on_lb, mismatch,
                time_int_sub(first_score, levelscore),
                time_int_sub(next_score, levelscore),
                levelscore
            ])
        rankings[header] = values
    return rankings
