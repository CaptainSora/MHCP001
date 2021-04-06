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

def scrape_greeny():
    scrapedate = str(date.today())
    with open('Overcooked2/greeny2p.json', 'r') as f:
        greeny2p = load(f)
    if greeny2p['last-updated'] == scrapedate:
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

def dump_rankings():
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
            # Score on leaderboards already
            if TEAM in greeny2p[world][level]:
                pass
            # Parallel access 2nd dictionary for high scores
            levelpath = level.split('-')
            levelscore = scores
            if level[0].isdecimal():
                levelscore = levelscore['World']
            for path in levelpath:
                if path.isdecimal():
                    scores = scores[int(path)-1]
            # levelscore should be base type now (int, with 6-6 str)
