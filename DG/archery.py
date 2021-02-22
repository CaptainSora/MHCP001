from discord import Embed
from json import load, dump
from random import choice, choices, random, triangular, uniform

def typeA(total):
    return len([i for i in [random() for _ in range(total)] if i <= 0.8])

def typeB(total):
    return choices(
        [total - i for i in range(1, 5)], cum_weights=[4, 7, 9, 10]
    )[0]

def typeC(total):
    return round(uniform(total-4, total))

def typeD(total):
    return round(triangular(total - 4, total, total - 2))

def get_score(total):
    func = choice([typeA, typeB, typeC, typeD])
    return func(total)

class Game:
    def __init__(self, total):
        self.mysets = 0
        self.compsets = 0
        self.total = total
        self.compfirst = choice([True, False])
        self.compscore = 0
        self.psets = 0
        self.history = []
    
    def scores(self, human):
        retstr = ""
        if human > self.total or human < 0:
            return "Invalid score, try again?"
        elif human == self.total:
            retstr += "Perfect set!\n"
            self.psets += 1
        if not self.is_compfirst():
            self.compscore = get_score(self.total)
            retstr += f"The opponent scored {self.compscore}. "
        self.history.append((human, self.compscore))
        if self.mysets >= 6 or self.compsets >= 6:
            retstr += "The game is already over."
        if human > self.compscore:
            self.mysets += 2
            retstr += "You won this set!"
        elif human < self.compscore:
            self.compsets += 2
            retstr += "You lost this set."
        else:
            retstr += "This set is drawn."
            if self.mysets != 5 or self.compsets != 5:
                self.mysets += 1
                self.compsets += 1
        return retstr
    
    def create_embed(self):
        embed = Embed(
            title='Disc Golf Archery',
            colour=0x0614d1
        )
        if self.mysets == 5 and self.compsets == 5:
            embed.description = "Sudden death! The next set wins!"
        setnums = [f"Set {i+1}" for i in range(len(self.history))]
        setnums.extend(['\u200b', '**Match**'])
        myscorelist = []
        compscorelist = []
        for h, c in self.history:
            if h < c:
                myscorelist.append(str(h))
                compscorelist.append(f"__{str(c)}__")
            elif h > c:
                myscorelist.append(f"__{str(h)}__")
                compscorelist.append(str(c))
            else:
                myscorelist.append(str(h))
                compscorelist.append(str(c))
        myscorelist.extend(['\u200b', f'**{self.mysets}**'])
        compscorelist.extend(['\u200b', f'**{self.compsets}**'])
        embed.add_field(
            name="\u200b",
            value='\n'.join(setnums),
            inline=True
        )
        embed.add_field(
            name="You",
            value='\n'.join(myscorelist),
            inline=True
        )
        embed.add_field(
            name="CPU",
            value='\n'.join(compscorelist),
            inline=True
        )
        return embed
  
    def winner(self):
        if self.mysets >= 6:
            return True
        elif self.compsets >= 6:
            return False
        else:
            return None
    
    def is_compfirst(self):
        if self.mysets == self.compsets:
            return self.compfirst
        else:
            return self.mysets > self.compsets
    
    def set_scores(self):
        # DEPRECATED
        retstr = f"The current set score is {self.mysets}-{self.compsets}."
        if self.mysets == 5 and self.compsets == 5:
            retstr += "\nSudden death! The next set wins!"
        return retstr
    
    def raw_scores(self):
        return (self.mysets, self.compsets)
    
    def begin_set(self):
        retstr = ""
        if self.is_compfirst():
            self.compscore = get_score(self.total)
            retstr += f"The opponent scored {self.compscore}."
            if (self.compscore < self.total and (self.mysets == 4 or 
                    (self.mysets == 5 and self.compsets == 5))):
                retstr += f" Score {self.compscore + 1} to win!"
            elif self.mysets == 5 and self.compsets < 5:
                retstr += f" Score {self.compscore} to win!"
            retstr += "\nYour turn:"
        else:
            retstr += f"You are first:"
        return retstr

    def get_psets(self):
        return self.psets

CURRENT_GAME = None

async def dg_archery(channel, message):
    global CURRENT_GAME
    words = message.split()
    if words[0].lower() in ["start", "new", "game"]:
        if CURRENT_GAME is None:
            # Start new game
            total = 9
            if len(words) > 1 and words[1].isdecimal():
                total = int(words[1])
            CURRENT_GAME = Game(total)
            await channel.send((
                f"Started a new game with {total} throws per set.\n"
                f"First to 6 set points wins!"
            ))
            await channel.send(CURRENT_GAME.begin_set())
        else:
            await channel.send("A game is in progress!")
            await channel.send(embed=CURRENT_GAME.create_embed())
    elif words[0].isdecimal():
        if CURRENT_GAME is None:
            await channel.send("Please start a game.")
        else:
            await channel.send(CURRENT_GAME.scores(int(words[0])))
            win = CURRENT_GAME.winner()
            if win is None:
                await channel.send(embed=CURRENT_GAME.create_embed())
                await channel.send(CURRENT_GAME.begin_set())
            else:
                myscore, compscore = CURRENT_GAME.raw_scores()
                if win is True:
                    await channel.send((
                        f"You win with a set score of "
                        f"{myscore} to {compscore}! Good work!"
                    ))
                else:
                    await channel.send((
                        f"You lost with a set score of "
                        f"{myscore} to {compscore}! Try again!"
                    ))
                save_score(win, CURRENT_GAME.get_psets())
                CURRENT_GAME = None
    elif words[0].lower() in ["record", "score"]:
        with open('DG/archery_score.json', 'r') as jf:
            data = load(jf)
        await channel.send(
            f"Your record is {data['wins']} wins and {data['losses']} losses."
        )


def save_score(win, psets):
    with open('DG/archery_score.json', 'r') as jf:
        data = load(jf)
    if win:
        data['wins'] += 1
    else:
        data['losses'] += 1
    data['perfect_sets'] += psets
    with open('DG/archery_score.json', 'w') as jf:
        dump(data, jf)
