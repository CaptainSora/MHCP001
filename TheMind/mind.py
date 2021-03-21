from random import sample, shuffle

from discord import Embed

# 2p: 12 levels
# 3p: 10 levels
# 4p: 8 levels
# hard mode: face down cards

### TO DO:
# Channel recognition
# Game functionality
# Help text

GAME = None
MINDCOLOR = 0xd17e11

class Mind:
    def __init__(self, mind, players, dms, hardmode):
        # These objects share the same indexing:
        self.players = players # List of User objects
        self.ready = [False for _ in self.players] # Ready booleans
        self.dms = dms # List of DMChannel objects
        self.cards = [[] for _ in self.players] # List of list of ints
        self.use_stars = [] # Indexed only when requested
        # GAME VALUES
        self.bonus_lives = [3, 6, 9]
        self.bonus_stars = [2, 5, 8]
        self.asc_blind = [3, 6, 8, 10]
        self.desc_blind = [4, 6, 10, 12]
        # OTHER
        self.active = False
        self.stack = []
        self.top_discard = None
        self.mind = mind # the-mind text channel object
        self.lives = len(self.players)
        self.lives_lost = 0
        self.shurikens = 1
        self.shurikens_used = 0
        self.level = 1
        self.maxlevel = 8
        if len(self.players) == 3:
            self.maxlevel = 10
        elif len(self.players) == 2:
            self.maxlevel = 12
        self.hardmode = hardmode
        self.hardstr = " HARD MODE" if self.hardmode else ""
    
    async def instructions(self):
        # Instructions for the players
        embed = Embed(
            title=f"The Mind - Instructions",
            color=MINDCOLOR
        )
        with open('TheMind/instr.txt') as f:
            embed.description = f.read()
        # Validate number of players
        if len(self.players) < 2 or len(self.players) > 4:
            embed.add_field(
                name='Invalid number of players',
                value="Must be 2-4 players"
            )
            await self.mind.send(embed=embed)
            return -9
        # Valid game, start round
        embed.add_field(
            name='Mode',
            value=f'{len(self.players)}p{self.hardstr}'
        )
        embed.add_field(
            name='Players',
            value='\n'.join([p.mention for p in self.players])
        )
        await self.mind.send(embed=embed)
        await self.start()
        return 0
    
    async def already_started(self):
        embed = self.get_embed()
        embed.description = "Game already in progress."
        await self.mind.send(embed=embed)

    async def start(self):
        # reset
        self.active = False
        self.stack = []
        self.ready = [False for _ in self.players]
        # pick cards
        cards = sample(range(1, 101), k=len(self.players) * self.level)
        shuffle(cards)
        # send DMs
        embed = self.get_embed()
        for i in range(len(self.players)):
            playercards = sorted(cards[self.level*i:self.level*(i+1)])
            self.cards[i] = playercards
            # TESTING CODE BLOCK VS NORMAL
            embed.add_field(
                name="Your cards:",
                value=f"{'  '.join([str(c) for c in playercards])}"
            )
            # END TESTING
            await self.dms[i].send(embed=embed)
            embed.clear_fields()
        # send start message
        embed.add_field(
            name="All cards dealt.",
            value=(
                "Waiting for all players to type 'ready' or 'r'.\n"
                "Players may type 'pause' or 'p' at any point during the game "
                "to initiate a resynchronization."
            )
        )
        await self.mind.send(embed=embed)
    
    def get_user_index(self, user):
        for i in range(len(self.players)):
            if self.players[i] == user:
                return i
        return -1
  
    def hearts(self, num=None):
        heartemoji = ":heart:" if num is None else ":broken_heart:"
        if num is None:
            num = self.lives
        heartlist = [heartemoji for _ in range(max(0, num))]
        return ' '.join(heartlist)
    
    def stars(self, num=None):
        staremoji = ":stars:" if num is None else ":comet:"
        if num is None:
            num = self.shurikens
        starlist = [staremoji for _ in range(max(0, num))]
        return ' '.join(starlist)

    def get_embed(self):
        return Embed(
            title=f"The Mind: {len(self.players)}p{self.hardstr}",
            description=f"Level {self.level}: {self.hearts()} {self.stars()}",
            color=MINDCOLOR
        )

    async def request_resync(self, user, status=None):
        embed = self.get_embed()
        idx = self.get_user_index(user)
        if idx < 0 or not self.active:
            return -1
        if status is None:
            embed.description = "Resync requested.\n"
        elif status is False:
            embed.description = "Star use declined.\n"
        embed.description += (
            "Waiting for all players to type 'ready' or 'r' to continue."
        )
        embed.add_field(
            name='Players:',
            value='\n'.join([p.mention for p in self.players])
        )
        embed.add_field(
            name='Cards remaining:',
            value='\n'.join([
                ' '.join(["🂠" for _ in range(len(self.cards[i]))])
                for i in range(len(self.players))
            ])
        )
        self.active = False
        self.ready = [False for _ in self.players]
        await self.mind.send(embed=embed)
        return 0

    async def ready_handler(self, user):
        embed = self.get_embed()
        idx = self.get_user_index(user)
        if idx < 0 or self.active:
            # non-playing user or already active
            return -1
        self.ready[idx] = True # Add ready status to player
        if all(self.ready): # If final ready message
            if self.stack:
                if self.hardmode:
                    embed.description = "Continue!"
                elif self.top_discard is not None:
                    embed.description = f"Continue from {self.top_discard}."
                    self.top_discard = None
                else:
                    embed.description = f"Continue from {self.stack[-1]}."
            else:
                embed.description += ' **BEGIN!**'
            self.active = True
            await self.mind.send(embed=embed)
        return 0

    async def card_handler(self, message):
        idx = self.get_user_index(message.author)
        if idx < 0 or not self.cards[idx] or not self.active:
            # No user, user has no cards, or paused
            return -1
        # embed
        embed = self.get_embed()
        # played and skipped cards
        playedcard = self.cards[idx].pop(0)
        skippedcards = []
        # validate card number
        if not self.hardmode and int(message.content) != playedcard:
            # replace removed card
            self.cards[idx].insert(0, playedcard)
            return -1
        # skipped cards (normal mode only)
        if not self.hardmode:
            for cards in self.cards:
                while cards and cards[0] < playedcard:
                    skippedcards.append(cards.pop(0))
            skippedcards.sort()
            self.stack.extend(skippedcards)
            # lose lives
            if skippedcards:
                self.lives -= 1
                self.lives_lost += 1
                embed.description = (
                    f"{self.hearts()} {self.hearts(num=1)}\n"
                    "Missed card(s):\n"
                    f"{'  '.join([str(c) for c in skippedcards])}\n"
                    f"Continue from {playedcard}."
                )
                await self.mind.send(embed=embed)
                if self.lives == 0:
                    await self.defeat()
                    return -9
        # add played card to stack
        self.stack.append(playedcard)
        # check for round end
        if not any(self.cards):
            # skipped cards (hard mode only)
            if self.hardmode:
                skips = [
                    self.stack[i] for i in range(len(self.stack) - 1)
                    if self.stack[i] > min(self.stack[i+1:])
                    and self.stack[i] > max(self.stack[:i])
                ]
                # lose lives
                prev = self.lives
                self.lives -= len(skips)
                self.lives_lost += len(skips)
                # display cards played
                cards_played = [
                    f"{c}" if c not in skips else f"__{c}__"
                    for c in self.stack
                ]
                embed.description = (
                    f"{self.hearts()} "
                    f"{self.hearts(num=min(prev, len(skips)))}\n"
                    "Cards played:\n"
                    f"{'  '.join(cards_played)}"
                )
                await self.mind.send(embed=embed)
                if self.lives <= 0:
                    await self.defeat()
                    return -9
            # check last level
            if self.level == self.maxlevel:
                await self.victory()
                return -9
            # extra life/stars
            extra = []
            if self.level in self.bonus_lives:
                self.lives += 1
                extra.append(":heart:")
            if self.level in self.bonus_stars:
                self.shurikens += 1
                extra.append(":stars:")
            if extra:
                embed.description = f"Bonus {' '.join(extra)}!"
                await self.mind.send(embed=embed)
            # end round
            self.level += 1
            await self.start()
        return 0
    
    async def request_stars(self, user):
        embed = self.get_embed()
        idx = self.get_user_index(user)
        if idx < 0 or not self.active:
            return -1
        if self.shurikens == 0:
            embed.description = "No stars remaining."
            await self.mind.send(embed=embed)
            return 0
        self.use_stars = ['False' for _ in self.players]
        self.use_stars[idx] = True
        embed.description = (
            f"Star use requested by {self.players[idx].mention}. "
            "The game is paused.\n"
            "Use a star to discard the lowest card in each player's hand.\n"
            "Waiting for all other players to choose 'yes' or 'no' "
            "('y' or 'n') to continue."
        )
        self.active = False
        await self.mind.send(embed)
        return 0

    async def confirm_stars(self, user, ans):
        idx = self.get_user_index(user)
        if idx < 0 or self.active:
            return -1
        if not ans:
            self.use_stars = []
            await self.request_resync(user, status=False)
            return 0
        self.use_stars[idx] = True
        if all(self.use_stars):
            discard = [self.cards[i].pop(0) for i in range(len(self.players))]
            self.top_discard = max(discard)
            self.shurikens -= 1
            self.shurikens_used += 1
            embed = self.get_embed()
            embed.description = f"{self.stars()} {self.stars(num=1)}"
            embed.add_field(
                name='Players:',
                value='\n'.join([p.mention for p in self.players])
            )
            embed.add_field(
                name="Discarded:",
                value='\n'.join([str(c) for c in discard])
            )
            await self.mind.send(embed=embed)
        return 0

    async def victory(self):
        embed = self.get_embed()
        embed.description = (
            ":tada: :tada: **VICTORY!** :tada: :tada:\n\n"
            "Congratulations on beating The Mind!\n"
        )
        embed.add_field(
            name='Players:',
            value='\n'.join([p.mention for p in self.players]),
            inline=False
        )
        embed.add_field(
            name='Game Stats:',
            value=(
                f"Mode: {len(self.players)}p{self.hardstr}\n"
                f"Lives lost: {self.hearts(num=self.lives_lost)}"
                f"Stars used: {self.stars(num=self.shurikens_used)}"
            ),
            inline=False
        )
        await self.mind.send(embed=embed)
    
    async def defeat(self):
        embed = self.get_embed()
        embed.description = (
            ":skull: Game over! :skull:\n"
            f"You made it to level {self.level} of {self.maxlevel}.\n"
            "Please try again!"
        )
        await self.mind.send(embed=embed)
    
    async def quit(self, user):
        idx = self.get_user_index(user)
        if idx < 0:
            return -1
        embed = self.get_embed()
        embed.description = "Game terminated! See you next time!"
        await self.mind.send(embed=embed)
        return -9


async def game_starter(mind, players, dms, hardmode):
    global GAME
    if GAME is None:
        GAME = Mind(mind, players, dms, hardmode)
        response = await GAME.instructions()
        if response == -9:
            GAME = None
    else:
        await GAME.already_started()


async def message_handler(message):
    """
    Guaranteed to not be triggered by dot commands.
    """
    global GAME
    if GAME is None:
        return
    elif (message.content.isdecimal() and not GAME.hardmode) or \
            (message.content.lower() == 'x' and GAME.hardmode):
        response = await GAME.card_handler(message)
    elif message.content.lower() in ['ready', 'r']:
        response = await GAME.ready_handler(message.author)
    elif message.content.lower() in ['pause', 'p']:
        response = await GAME.request_resync(message.author)
    elif message.content.lower() in ['star', 's']:
        response = await GAME.request_stars(message.author)
    elif message.content.lower() in ['yes', 'y']:
        response = await GAME.confirm_stars(message.author, True)
    elif message.content.lower() in ['no', 'n']:
        response = await GAME.confirm_stars(message.author, False)
    elif message.content.lower() in ['quit', 'exit']:
        response = await GAME.quit(message.author)
    else:
        response = -1
    # Handle response values
    if response == -1:
        await message.delete()
    elif response == -9:
        GAME = None
