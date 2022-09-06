from random import shuffle

from discord import Embed

""" TODO
? Show which date the single chose (save, show at end)
? Remove the waiting for field when date is choosing
? Redraw all cards? Put unused cards back in the deck
? Add ending splash (best wingperson)
"""

GAME = None
RFCOLOR = 0xfc0011

class RedFlags:
    def __init__(self, players, dms, ctx, wait_fn, flags):
        # These objects share the same indexing:
        idxorder = list(range(len(players))) 
        shuffle(idxorder) # Shuffle players
        self.players = [ # List of User objects
            players[idxorder[i]] for i in range(len(players))]
        self.dms = [ # List of DMChannel objects
            dms[idxorder[i]] for i in range(len(players))]
        self.latest = [ # List of latest messages (for embed)
            None for _ in range(len(players))]
        self.whitecards = [[] for _ in self.players]
        self.redcards = [[] for _ in self.players]
        self.dates = [[] for _ in self.players]
        self.single = 0
        # Flags
        self.core = any([f in flags for f in ['-c', '-core']])
        self.shortgame = any([f in flags for f in ['-s', '-short']])
        # Cards
        with open("RedFlags/whitecards.txt") as f:
            self.whitedeck = f.read().strip().split("\n")
        with open("RedFlags/redcards.txt") as f:
            self.reddeck = f.read().strip().split("\n")
        if not self.core:
            with open("RedFlags/whitecards_custom.txt") as f:
                self.whitedeck += f.read().strip().split("\n")
            with open("RedFlags/redcards_custom.txt") as f:
                self.reddeck += f.read().strip().split("\n")
        for i in range(len(self.whitedeck)):
            self.whitedeck[i] = "🤍 " + self.whitedeck[i]
        for i in range(len(self.reddeck)):
            self.reddeck[i] = "💔 " + self.reddeck[i]
        shuffle(self.whitedeck)
        shuffle(self.reddeck)
        # Game values
        self.emoji = [
            "0️⃣", "1️⃣", "2️⃣", "3️⃣", "4️⃣",
            "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣"
        ]
        self.scoretarget = 7
        # Util
        self.wait_fn = wait_fn
        self.ctx = ctx
    
    async def wait_for(self, msg, reacts, check, player=False):
        """
        Adds reactions to the message and waits for a response.
        Returns the index of the response in self.emoji
        Requires len(reacts) > 0
        """
        for r in reacts:
            await msg.add_reaction(r)
        reaction, _ = await self.wait_fn(check)
        return self.emoji.index(str(reaction)) - int(player)
    
    async def send_embed(self, embed):
        """
        Sends the same embed to all players.
        """
        for i in range(len(self.players)):
            await self.dms[i].send(embed=embed)
    
    async def instructions(self):
        # Instructions for the players (guaranteed valid #)
        embed = self.get_embed()
        embed.title = f"Red Flags - Instructions"
        with open("RedFlags/instr.txt") as f:
            embed.description = f.read()
        # Valid game, start round
        embed.add_field(
            name="Players",
            value="\n".join([
                f"{p[0]}. {p[1].mention}" for p in enumerate(self.players, 1)
            ])
        )
        embed.add_field(
            name="Flags",
            value="\n".join([
                f"Core deck only (-c): {self.core}",
                f"Short game (-s): {self.shortgame}",
            ])
        )
        await self.send_embed(embed)
        await self.round_handler()
    
    async def setup(self):
        """
        Shuffles cards back into deck
        Deals new cards to each player
        """
        for i in range(len(self.players)):
            self.whitedeck.extend(self.whitecards[i])
            self.reddeck.extend(self.redcards[i])
            shuffle(self.whitedeck)
            shuffle(self.reddeck)
            self.whitecards[i] = []
            self.redcards[i] = []
            while len(self.whitecards[i]) < 4:
                self.whitecards[i].append(self.whitedeck.pop())
            while len(self.redcards[i]) < 3:
                self.redcards[i].append(self.reddeck.pop())
        # Start round
        await self.choose_white()

    async def round_handler(self): #
        """
        Iterates over game rounds and turns to prevent excessive recursion
        depth.
        """
        embed = self.get_embed()
        embed.title = "Game Over!"
        while True:
            points = [len(d) for d in self.dates]
            if self.shortgame and sum(points) >= 2 * len(self.players):
                # End short game
                winners = [
                    i for i in range(len(self.players))
                    if points[i] == max(points)
                ]
                embed.description = (
                    "The best wingpersons are:\n"
                    "\n".join([
                        self.players[i].mention + "! :tada:" for i in winners
                    ])
                )
                for i in winners:
                    embed.add_field(
                        name=f"Dates created by {self.players[i].name}:",
                        value="\n\n".join(self.dates[i])
                    )
                break
            elif max(points) >= self.scoretarget:
                # End regular game
                winner = points.index(max(points))
                embed.description = (
                    f"The best wingperson is: "
                    f"{self.players[winner].mention}! :tada:"
                )
                embed.add_field(
                    name=f"Dates created by {self.players[winner].name}:",
                    value="\n\n".join(self.dates[winner])
                )
                break
            # Deal cards and start round
            await self.setup()
        await self.send_embed(embed=embed)
        await delete_game(self.ctx)
    
    async def choose_white(self):
        # Show everyone their cards (if not single)
        for i in range(len(self.players)):
            embed = self.get_embed()
            if i == self.single:
                embed.title = "You are The Single! 💁"
                embed.description = (
                    "Please wait for all candidates to choose their white 🤍 "
                    "cards."
                )
            else:
                embed.description = "\n".join(
                    self.whitecards[i] + self.redcards[i]
                )
            # Show played cards
            cardlist = [
                "?" if j != self.single else "Single! 💁"
                for j in range(len(self.players))
            ]
            for j in range(len(self.players)):
                embed.add_field(
                    name=f"Player {j+1}: {self.players[j].name}",
                    value=cardlist[j],
                    inline=True
                )
            embed.add_field(
                name="Waiting for:",
                value="...",
                inline=False
            )
            self.latest[i] = await self.dms[i].send(embed=embed)
        # Turn counter
        turn = (self.single + 1) % len(self.players)
        # Check function
        def check(reaction, user):
            return all([
                self.dms[turn].recipient == user,
                reaction.message == msg,
                str(reaction) in reacts
            ])
        # Each candidate takes a turn
        while turn != self.single:
            # Display whose turn it is
            for i in range(len(self.players)):
                await self.latest[i].edit(embed=
                    self.latest[i].embeds[0].set_field_at(
                        len(self.players),
                        name="Waiting for:",
                        value=self.players[turn].mention
                    )
                )
            # Choose Card 1
            reacts = [self.emoji[i+1] for i in range(4)]
            msg = await self.dms[turn].send(
                "Please choose your first white 🤍 card."
            )
            card1 = await self.wait_for(msg, reacts, check)
            reacts.remove(self.emoji[card1])
            card1 = self.whitecards[turn][card1 - 1] # Convert index to str
            # Choose Card 2
            msg = await self.dms[turn].send(
                "Please choose your second white 🤍 card."
            )
            card2 = await self.wait_for(msg, reacts, check)
            card2 = self.whitecards[turn][card2 - 1] # Convert index to str
            # Remove from hand, resend embed
            self.whitecards[turn].remove(card1)
            self.whitecards[turn].remove(card2)
            turnembed = self.latest[turn].embeds[0]
            turnembed.description = "\n".join(
                self.whitecards[turn] + self.redcards[turn]
            )
            await self.latest[turn].delete()
            self.latest[turn] = await self.dms[turn].send(embed=turnembed)
            # Update all players with two cards
            for i in range(len(self.players)):
                await self.latest[i].edit(embed=
                    self.latest[i].embeds[0].set_field_at(
                        turn,
                        name=f"Player {turn+1}: {self.players[turn].name}",
                        value=f"{card1}\n{card2}"
                    )
                )
            turn = (turn + 1) % len(self.players)
        await self.choose_red()

    async def choose_red(self):
        # Select target candidates
        targets = [
            (i+1) % len(self.players)
            if (i+1) % len(self.players) != self.single
            else (i+2) % len(self.players)
            for i in range(len(self.players))
        ]
        # Modify embeds
        for i in range(len(self.players)):
            embed = self.latest[i].embeds[0]
            if i == self.single:
                embed.description = (
                    "Please wait for all candidates to choose their red 💔 "
                    "cards."
                )
            else:
                embed.description += (
                    f"\n\nYou are sabotaging Player {targets[i] + 1}: "
                    f"{self.players[targets[i]].mention}"
                )
            await self.latest[i].edit(embed=embed)
        # Turn counter
        turn = (self.single + 1) % len(self.players)
        # Check function
        def check(reaction, user):
            return all([
                self.dms[turn].recipient == user,
                reaction.message == msg,
                str(reaction) in reacts
            ])
        # Each candidate takes a turn
        while turn != self.single:
            # Display whose turn it is
            for i in range(len(self.players)):
                await self.latest[i].edit(embed=
                    self.latest[i].embeds[0].set_field_at(
                        len(self.players),
                        name="Waiting for:",
                        value=self.players[turn].mention
                    )
                )
            # Choose Card
            reacts = [self.emoji[i+1] for i in range(3)]
            msg = await self.dms[turn].send(
                "Please choose your red 💔 card." # TODO
            )
            card = await self.wait_for(msg, reacts, check)
            card = self.redcards[turn][card - 1] # Convert index to str
            # Remove from hand, resend embed
            self.redcards[turn].remove(card)
            turnembed = self.latest[turn].embeds[0]
            turnembed.description = "\n".join(
                self.whitecards[turn] + self.redcards[turn]
            )
            await self.latest[turn].delete()
            self.latest[turn] = await self.dms[turn].send(embed=turnembed)
            # Update all players with new card
            for i in range(len(self.players)):
                whites = self.latest[i].embeds[0].fields[targets[turn]].value
                # TODO
                await self.latest[i].edit(embed=
                    self.latest[i].embeds[0].set_field_at(
                        targets[turn],
                        name=(
                            f"Player {targets[turn]+1}: "
                            f"{self.players[targets[turn]].name}"
                        ),
                        value=f"{whites}\n{card}"
                    )
                )
            turn = (turn + 1) % len(self.players)
        await self.choose_date()

    async def choose_date(self):
        # Modify embeds
        for i in range(len(self.players)):
            embed = self.latest[i].embeds[0]
            if i == self.single:
                embed.description = (
                    "Time to pick your date!"
                )
            else:
                embed.title = "Dealbreaker or lovemaker?"
                embed.description = (
                    "Please wait for The Single to choose their date!"
                )
            embed.remove_field(len(self.players))
            await self.latest[i].edit(embed=embed)
        # Check function
        def check(reaction, user):
            return all([
                self.dms[self.single].recipient == user,
                reaction.message == msg,
                str(reaction) in reacts
            ])
        # Choose date
        reacts = [
            self.emoji[i+1] for i in range(len(self.players))
            if i != self.single
        ]
        msg = await self.dms[self.single].send(
            "Who are you going to date this round?"
        )
        date = await self.wait_for(msg, reacts, check, player=True)
        player = self.players[date].mention
        cards = self.latest[date].embeds[0].fields[date].value
        self.dates[date].append(cards)
        # Delete latest and send round end embed
        for i in range(len(self.players)):
            await self.latest[i].delete()
        embed = self.get_embed()
        embed.title = "And the round goes to..."
        embed.description = f"{player}! :tada:\n\n{cards}"
        embed.add_field(
            name="Players:",
            value="\n".join([
                self.players[i].mention for i in range(len(self.players))
            ])
        )
        embed.add_field(
            name="Points:",
            value="\n".join([
                "❤" * len(d) if len(d) > 0 else "⠀" for d in self.dates
            ])
        )
        await self.send_embed(embed=embed)
        # Increment turn counter
        self.single = (self.single + 1) % len(self.players)

    def get_embed(self):
        embed = Embed(
            title=f"Your Cards",
            description="",
            color=RFCOLOR
        )
        embed.set_footer(text="Red Flags by Jack Dire")
        return embed


async def game_starter(players, dms, ctx, wait_fn, flags):
    global GAME
    if GAME is None:
        GAME = RedFlags(players, dms, ctx, wait_fn, flags)
        await GAME.instructions()
    else:
        await ctx.send(
            "Game already in progress! Unfortunately, Yui can only handle "
            "one game instance at a time..."
        )


async def delete_game(ctx):
    global GAME
    GAME = None
    await ctx.message.delete()
