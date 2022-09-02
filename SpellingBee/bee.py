from datetime import datetime, timezone
from json import dump, load
from random import sample, shuffle
from string import ascii_lowercase

from discord import Embed

WORDS = None

def load_words():
    global WORDS
    if WORDS is None:
        with open('SpellingBee/twl06.txt') as f:
            WORDS = set([w.lower() for w in f.read().split('\n')])

def num_valid_words(letters):
    valid = [w for w in WORDS if letters[0] in w and len(w) >= 4]
    valid = [w for w in valid if all([l in letters for l in w])]
    return(len(valid))


def todays_words():
    """
    Returns today's problem, and generates it as necessary.
    """
    # Returns a tuple of today's letters, answers, players, and date
    with open('SpellingBee/bee.json') as f:
        bee = load(f)
    today_str = datetime.now(tz=timezone.utc).strftime("%b %d, %Y")
    if today_str not in bee:
        letters = sample(ascii_lowercase, 7)
        while num_valid_words(letters) < 30:
            letters = sample(ascii_lowercase, 7)
        bee[today_str] = {
            'letters': letters,
            'answers': [],
            'players': [],
        }
        with open('SpellingBee/bee.json', 'w') as f:
            dump(bee, f)
    return (
        bee[today_str]['letters'],
        bee[today_str]['answers'],
        bee[today_str]['players'],
        today_str
    )

def add_word(date_str, word, player):
    # date_str must be an output of todays_words()
    # word will be assumed to be correct
    with open('SpellingBee/bee.json') as f:
        bee = load(f)
    bee[date_str]['answers'].append(word)
    bee[date_str]['players'].append(player)
    with open('SpellingBee/bee.json', 'w') as f:
        dump(bee, f)

async def spelling_bee(ctx, args):
    load_words()
    letters, answers, players, today_str = todays_words()
    players_str = [f"<@{i}>" for i in players]
    letters_copy = [*letters] # splat copy
    letters_copy[0] = f"__{letters_copy[0]}__"
    shuffle(letters_copy)
    embed=Embed(
        title=(
            "Today's letters: "
            f"{' '.join([l.upper() for l in letters_copy])}\n\n"
        ),
        color=0xfccf03 # Yellow
    )
    embed.set_author(
        name="Daily Spelling Bee",
        icon_url=(
            "https://cdn.discordapp.com/attachments/724693852228943954/"
            "838483537685774376/1.png"
        )
    )
    embed.set_footer(text=today_str)
    if not args:
        embed.description = (
            "To submit an answer:\n"
            ".bee [answer]\n\n"
            "Your answer must:\n"
            "1. Only use the letters povided\n"
            "   (You can reuse letters!)\n"
            "2. Include the underlined letter\n"
            "3. Be at least 4 letters long"
        )
    else:
        guess = args[0].lower().strip()
        embed.color = 0xd60606 # Red
        if guess in answers:
            embed.description = (
                "Your answer has already been submitted."
            )
        elif len(guess) < 4:
            embed.description = (
                "Your answer must be at least 4 letters long."
            )
        elif letters[0] not in guess:
            embed.description = (
                "Your answer must used the underlined letter."
            )
        elif not all([l in letters for l in guess]):
            embed.description = (
                "Your answer must only use the letters provided."
            )
        elif guess not in WORDS:
            embed.description = (
                "Your answer is not in the official Scrabble word list... "
                "Sorry!"
            )
        else:
            embed.color = 0xfccf03 # Yellow
            add_word(today_str, guess, ctx.message.author.id)
            answers.append(guess)
            players_str.append(f"<@{ctx.message.author.id}>")
            embed.description = (
                f"Submitted the word '{guess}'!"
            )
    if answers:
        maxlen = max([len(w) for w in answers])
        answers = [f"__{w}__" if len(w) == maxlen else w for w in answers]
        embed.add_field(
            name="Submitted:",
            value='\n'.join(answers[-30:])
        )
        embed.add_field(
            name="By:",
            value='\n'.join(players_str[-30:])
        )
        embed.add_field(
            name="Total:",
            value=str(len(answers)),
            inline=False
        )
    await ctx.send(embed=embed)

async def bee_leaderboards(ctx, args):
    embed=Embed(
        title=(
            "Leaderboard Archive"
        ),
        color=0xfccf03 # Yellow
    )
    embed.set_author(
        name="Daily Spelling Bee",
        icon_url=(
            "https://cdn.discordapp.com/attachments/724693852228943954/"
            "838483537685774376/1.png"
        )
    )
    # Check date
    if args:
        date = ' '.join(args)
    else:
        date = datetime.now(tz=timezone.utc).strftime("%b %d, %Y")
        embed.title = "Today's Leaderboard"
        embed.description = (
            "Enter a date to see that day's leaderboards!"
        )
    with open('SpellingBee/bee.json') as f:
        hist = load(f)
    if date not in hist:
        record_dates = list(hist.keys())
        if len(record_dates) > 10:
            record_dates = record_dates[:5] + ["..."] + record_dates[-5:]
        embed.description = (
            f"No records for '{date}'.\n"
            "Existing records:\n"
            f"{chr(10).join(record_dates)}"
        )
        await ctx.send(embed=embed)
        return
    embed.set_footer(text=date)
    answers = hist[date]['answers']
    players = hist[date]['players']
    if not answers:
        embed.add_field(
            name="No submissions yet!",
            value=""
        )
    else:
        player_dict = {}
        for i in range(len(answers)):
            if players[i] not in player_dict:
                player_dict[players[i]] = [0, 0]
            player_dict[players[i]][0] += 1
            player_dict[players[i]][1] = max(
                player_dict[players[i]][1], len(answers[i])
            )
        # Scoring
        player_dict = {k: v[0] + 2 * v[1] for k, v in player_dict.items()}
        player_dict = {
            f"<@{k}>": str(v) for k, v in sorted(
                player_dict.items(), key=lambda item: item[1], reverse=True)
        }
        # Add to embed
        embed.add_field(
            name="Players:",
            value='\n'.join(player_dict.keys())
        )
        embed.add_field(
            name="Score:",
            value='\n'.join(player_dict.values())
        )
    await ctx.send(embed=embed)
