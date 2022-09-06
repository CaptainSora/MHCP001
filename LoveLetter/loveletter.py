from random import shuffle

from discord import Embed

""" Future Plans
- More flags?
- Handle more than one instance at a time
- Help function (for bot commands/flags)
"""

GAME = None
LLCOLOR = 0xfc3858

class LoveLetter:
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
        self.cards = [-1 for _ in self.players]
        self.spy = [0 for _ in self.players]
        self.handmaid = [0 for _ in self.players]
        self.tokens = [0 for _ in self.players]
        self.turn = 0
        # Game values
        self.deck = []
        self.discard = []
        self.names = {
            -1: ":x:",
            0: ":zero: Spy",
            1: ":one: Guard",
            2: ":two: Priest",
            3: ":three: Baron",
            4: ":four: Handmaid",
            5: ":five: Prince",
            6: ":six: Chancellor",
            7: ":seven: King",
            8: ":eight: Countess",
            9: ":nine: Princess"
        }
        self.cardhelp = {
            0: "Play or discard for a chance at an extra token. 💌",
            1: "Guess another player's card.",
            2: "Look at another player's hand.",
            3: "Compare hands. The lower hand is eliminated. :x:",
            4: "Play to become untargetable 🚫 until your next turn.",
            5: "Choose any player to discard their hand.",
            6: "Draw the top two cards, and return two cards to the bottom.",
            7: "Trade hands with another player.",
            8: "Has no effect. Must be discarded if the other card is 5 or 7.",
            9: "If played or discarded, you are eliminated. :x:"
        }
        self.emoji = [
            "0️⃣", "1️⃣", "2️⃣", "3️⃣", "4️⃣",
            "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣",
            "🚫", "❔"
        ]
        targets = {2: 6, 3: 5, 4: 4, 5: 3, 6: 3}
        self.scoretarget = targets.get(len(players), 0)
        # Util
        self.wait_fn = wait_fn
        self.ctx = ctx
        # Flags
        self.deadinfo = any([f in flags for f in ['-di', '-deadinfo']])
    
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

    async def send_msg(self, msg):
        """
        Sends the same message to all players.
        """
        for i in range(len(self.players)):
            await self.dms[i].send(msg)
    
    async def send_embed(self, embed):
        """
        Sends the same embed to all players.
        """
        for i in range(len(self.players)):
            await self.dms[i].send(embed=embed)
    
    async def instructions(self):
        # Instructions for the players (guaranteed valid #)
        embed = self.get_embed()
        embed.title = f"Love Letter - Instructions"
        with open("LoveLetter/instr.txt") as f:
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
                f"Show cards when eliminated (-di): {self.deadinfo}",
            ])
        )
        await self.send_embed(embed)
        await self.round_handler()
    
    async def setup(self):
        """
        Sets up a new round (of the game)
        """
        # Create deck and discard piles
        self.deck = [
            0, 0, 1, 1, 1, 1, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 8, 9
        ]
        self.discard = ["?"]
        # Shuffle and discard
        shuffle(self.deck)
        self.hidden_card = self.deck.pop() # Discards one
        if len(self.players) == 2:
            for _ in range(3):
                self.discard.append(self.deck.pop())
        # Deal
        for i in range(len(self.players)):
            self.cards[i] = self.deck.pop()
            if self.latest[i] is not None:
                await self.latest[i].delete()
            self.latest[i] = None
            self.spy[i] = 0
            self.handmaid[i] = 0
            await self.dms[i].send(
                f"====================\n"
                f"A new round has begun! "
                f"You have been dealt: {self.names[self.cards[i]]}.")

    async def round_handler(self):
        """
        Iterates over game rounds and turns to prevent excessive recursion
        depth.
        """
        game_end = False
        while not game_end:
            round_end = False
            await self.setup()
            while not round_end:
                round_end = await self.start_turn()
            game_end = await self.round_end()
        await delete_game(self.ctx)

    async def start_turn(self):
        """
        Updates the game state for all players
        """
        # Reset handmaid status
        self.handmaid[self.turn] = 0
        # player icons
        playernum = [
            f"{i+1}." if self.cards[i] > -1 else ":x:"
            for i in range(len(self.players))
        ]
        spyicon = [":spy:" * s for s in self.spy]
        handmaidicon = [
            "" if h == 0 else ":no_entry_sign:" for h in self.handmaid
        ]
        turnicon = ["" for _ in self.players]
        turnicon[self.turn] = ":clock3:"
        # create embed for each player
        for i in range(len(self.players)):
            dm = self.dms[i]
            embed = self.get_embed()
            # Players
            embed.add_field(
                name="Players",
                value="\n".join([
                    " ".join([
                        playernum[i], self.players[i].mention,
                        spyicon[i], handmaidicon[i], turnicon[i]
                    ])
                    for i in range(len(self.players))
                ])
            )
            # Player cards (only shown to dead players)
            if self.deadinfo and self.cards[i] == -1:
                cardemojis = [
                    self.names[c].split()[0] if c > -1 else "⠀"
                    for c in self.cards
                ]
                cardemojis[self.turn] += self.names[self.deck[-1]].split()[0]
                embed.add_field(
                    name="Cards",
                    value="\n".join(cardemojis)
                )
            # Remaining cards
            embed.add_field(
                name="Deck",
                value=len(self.deck)-1
            )
            # Discard pile
            embed.add_field(
                name="Discard Pile",
                value=" ".join([str(c) for c in self.discard]),
                inline=False
            )
            # Current card(s)
            if i == self.turn:
                # Draw card
                oldcard = self.cards[i]
                newcard = self.deck[-1] # Do not draw yet
                hand = sorted([oldcard, newcard])
                embed.add_field(
                    name="Your cards:",
                    value="\n".join([self.names[c] for c in hand]),
                    inline=False
                )
            else:
                embed.add_field(
                    name="Your card:",
                    value=self.names.get(
                        self.cards[i], "You are out of the round."),
                    inline=False
                )
            # Delete and re-send game state message
            if self.latest[i] is not None:
                await self.latest[i].delete()
            self.latest[i] = await dm.send(embed=embed)
        return await self.exec_turn()
    
    async def exec_turn(self):
        """
        Handles player actions during their turn.
        """
        dm = self.dms[self.turn]
        oldcard = self.cards[self.turn]
        newcard = self.deck.pop() # Draw a card
        player_mention = self.players[self.turn].mention
        hand = sorted([oldcard, newcard])

        # Expected values for check()
        reacts = [self.emoji[hand[0]], self.emoji[hand[1]], self.emoji[11]]
        # Check not to discard King or Prince when Countess is discarded
        if hand[1] == 8 and hand[0] in [5, 7]:
            reacts = [self.emoji[8], self.emoji[11]]
        
        msg = await dm.send(
            f"{player_mention} Your turn! Which card would you like to play?"
        )

        def check(reaction, user):
            return all([
                dm.recipient == user,
                reaction.message == msg,
                str(reaction) in reacts
            ])
        
        # Select a card to play (help text)
        reaction = await self.wait_for(msg, reacts, check)
        if reaction == 11:
            cards = list(set(hand))
            await msg.edit(content=
                "\n".join([msg.content] + [
                    self.names[c] + ": " + self.cardhelp[c] for c in cards
                ])
            )
            await msg.remove_reaction(self.emoji[11], msg.author)
            reacts = reacts[:-1]
            reaction = await self.wait_for(msg, reacts, check)

        # Discard used card
        if reaction == oldcard: # old card
            self.discard.append(oldcard)
            self.cards[self.turn] = newcard
        else:
            self.discard.append(newcard)

        # self.turn is the index of the player taking the turn
        target = None # used for cards 1, 2, 3, 5, 7
        playermsg = "" # i.e. "You played [x] against @player and ..."
        targetmsg = "" # i.e. "@player played [x] against you and ..."
        othersmsg = "" # i.e. "@player1 played [x] against @player2 ..."

        # Util
        targetable = [ # Indices of targetable players (not including self)
            i + 1 for i in range(len(self.players))
            if i != self.turn and self.cards[i] > -1 and self.handmaid[i] == 0]
        guard_guessable = [self.emoji[0]] + self.emoji[2:10]

        # Card play handler
        if reaction == 0:
            self.spy[self.turn] += 1
            if sum(self.spy) == 1:
                playermsg = f"You played the first {self.names[0]} :spy:!"
                othersmsg = (
                    f"{player_mention} is the first player to play or discard "
                    f"a {self.names[0]} :spy:!"
                )
            elif len([s for s in self.spy if s > 0]) == 1:
                playermsg = "You played both :zero: Spies! :spy:"
                othersmsg = f"{player_mention} played both :zero: Spies! :spy:"
            else:
                playermsg = (
                    f"You are the second player to play or discard a "
                    f"{self.names[0]}. :spy: "
                    f"No spy tokens will be given this round."
                )
                othersmsg = (
                    f"{player_mention} is the second player to play or "
                    f"discard a {self.names[0]}. :spy: "
                    f"No spy tokens will be given this round."
                )
        elif reaction == 1:
            # Choose target
            reacts = [self.emoji[i] for i in targetable]
            if len(reacts) > 0:
                msg = await dm.send(
                    f"Who would you like to use {self.names[1]} on?"
                )
                target = await self.wait_for(msg, reacts, check, player=True)
                targetcard = self.cards[target]
                # Guess Card
                msg = await dm.send(
                    f"Which card would you like to guess? "
                    f"You cannot guess the Guard."
                )
                reacts = guard_guessable[:]
                guess = await self.wait_for(msg, reacts, check)
                # Evaluate
                if guess == targetcard:
                    self.discard.append(targetcard)
                    self.cards[target] = -1
                    playermsg = (
                        f"{self.players[target].mention}'s card is the "
                        f"{self.names[guess].split()[1]}, and they are "
                        f"eliminated! :x:"
                    )
                    targetmsg = (
                        f"{player_mention} played {self.names[1]} and "
                        f"correctly guessed your card as the "
                        f"{self.names[guess].split()[1]}, and you are "
                        f"eliminated! :x:"
                    )
                    othersmsg = (
                        f"{player_mention} played {self.names[1]} and "
                        f"correctly guessed "
                        f"{self.players[target].mention}'s card as the "
                        f"{self.names[guess].split()[1]}, and they are "
                        f"eliminated! :x:"
                    )
                else:
                    playermsg = (
                        f"{self.players[target].mention}'s card is not the "
                        f"{self.names[guess].split()[1]}."
                    )
                    targetmsg = (
                        f"{player_mention} played {self.names[1]} and "
                        f"incorrectly guessed your card as "
                        f"the {self.names[guess].split()[1]}."
                    )
                    othersmsg = (
                        f"{player_mention} played {self.names[1]} and "
                        f"incorrectly guessed "
                        f"{self.players[target].mention}'s card as the "
                        f"{self.names[guess].split()[1]}."
                    )
            else:
                playermsg = (
                    f"There are no targets for {self.names[1]}."
                )
                othersmsg = (
                    f"{player_mention}'s {self.names[1]} has no targets."
                )
        elif reaction == 2:
            reacts = [self.emoji[i] for i in targetable]
            if len(reacts) > 0:
                msg = await dm.send(
                    f"Who would you like to use {self.names[2]} on?"
                )
                target = await self.wait_for(msg, reacts, check, player=True)
                targetcard = self.cards[target]
                playermsg = (
                    f"{self.players[target].mention} is holding "
                    f"{self.names[targetcard]}. :eyes:"
                )
                targetmsg = (
                    f"{player_mention} played {self.names[2]} against you "
                    f"and saw your card! :eyes:"
                )
                othersmsg = (
                    f"{player_mention} played {self.names[2]} against "
                    f"{self.players[target].mention} and saw their card. "
                    f":eyes:"
                )
            else:
                playermsg = (
                    f"There are no targets for {self.names[2]}."
                )
                othersmsg = (
                    f"{player_mention}'s {self.names[2]} has no targets. "
                )
        elif reaction == 3:
            reacts = [self.emoji[i] for i in targetable]
            if len(reacts) > 0:
                msg = await dm.send(
                    f"Who would you like to use {self.names[3]} on?"
                )
                target = await self.wait_for(
                    msg, reacts, check, player=True
                )
                targetcard = self.cards[target]
                playercard = self.cards[self.turn]
                if playercard > targetcard:
                    self.discard.append(self.cards[target])
                    self.cards[target] = -1
                    playermsg = (
                        f"{self.players[target].mention} is holding "
                        f"{self.names[targetcard]} and is eliminated. :x:"
                        f"They discarded their {self.names[targetcard]}."
                    )
                    targetmsg = (
                        f"{player_mention} played {self.names[3]} against "
                        f"you! Their {self.names[playercard]} is higher than "
                        f"your {self.names[targetcard]} and you are "
                        f"eliminated! :x:"
                    )
                    othersmsg = (
                        f"{player_mention} played {self.names[3]} against "
                        f"{self.players[target].mention}. "
                        f"{self.players[target].mention} had the lower card "
                        f"and is eliminated. :x:"
                        f"They discarded their {self.names[targetcard]}."
                    )
                elif playercard < targetcard:
                    self.discard.append(self.cards[self.turn])
                    self.cards[self.turn] = -1
                    playermsg = (
                        f"{self.players[target].mention} is holding "
                        f"{self.names[targetcard]}. You are eliminated! :x:"
                    )
                    targetmsg = (
                        f"{player_mention} played {self.names[3]} against "
                        f"you! Their {self.names[playercard]} is lower than "
                        f"your {self.names[targetcard]} and they are "
                        f"eliminated. :x:"
                        f"They discarded their {self.names[playercard]}."
                    )
                    othersmsg = (
                        f"{player_mention} played {self.names[3]} against "
                        f"{self.players[target].mention}."
                        f"{self.players[self.turn].mention} had the lower "
                        f"card and is eliminated. :x:"
                        f"They discarded their {self.names[playercard]}."
                    )
                else:
                    playermsg = (
                        f"{self.players[target].mention} is also holding "
                        f"{self.names[targetcard]}. Nobody is eliminated."
                    )
                    targetmsg = (
                        f"{player_mention} played {self.names[3]} against "
                        f"you! They are also holding "
                        f"{self.names[playercard]}. Nobody is eliminated."
                    )
                    othersmsg = (
                        f"{player_mention} played {self.names[3]} against "
                        f"{self.players[target].mention}. "
                        f"They both hold the same card, and nobody is "
                        f"eliminated."
                    )
            else:
                playermsg = (
                    f"There are no targets for {self.names[3]}."
                )
                othersmsg = (
                    f"{player_mention}'s {self.names[3]} has no targets."
                )
        elif reaction == 4:
            self.handmaid[self.turn] = 1
            playermsg = (
                f"You played {self.names[4]}. You are untargetable 🚫 until "
                f"your next turn."
            )
            othersmsg = (
                f"{player_mention} played {self.names[4]}. They are "
                f"untargetable 🚫 until their next turn."
            )
        elif reaction == 5:
            # Ask player for target (yourself included)
            reacts = [
                self.emoji[i] for i in sorted(targetable + [self.turn + 1])
            ]
            msg = await dm.send(
                f"Who would you like to use {self.names[5]} on? You may use "
                f"it on yourself."
            )
            target = await self.wait_for(msg, reacts, check, player=True)
            d_cardname = self.names[self.cards[target]]
            # Evaluate
            if target == self.turn: # Target self
                playercard = self.cards[self.turn]
                playermsg = ""
                othersmsg = (
                    f"{player_mention} played {self.names[5]} on themself.\n"
                )
                if self.cards[target] == 9:
                    playermsg += (
                        f"You discarded your {self.cards[9]} and are "
                        f"eliminated! :x:"
                    )
                    othersmsg += (
                        f"They discarded their {self.cards[9]} and are "
                        f"eliminated! :x:"
                    )
                elif self.cards[target] == 0:
                    if sum(self.spy) == 1:
                        playermsg += (
                            f"You discarded the first {self.names[0]}! :spy:"
                        )
                        othersmsg += (
                            f"They discarded the first {self.names[0]}! :spy:"
                        )
                    elif len([s for s in self.spy if s > 0]) == 1:
                        playermsg += (
                            "You played or discarded both :zero: Spies! :spy:"
                        )
                        othersmsg += (
                            "They played or discarded both :zero: Spies! :spy:"
                        )
                    else:
                        playermsg = (
                            f"You are the second player to play or discard a "
                            f"{self.names[0]}. :spy: "
                            f"No spy tokens will be given this round."
                        )
                        othersmsg = (
                            f"{player_mention} is the second player to play "
                            f"or discard a {self.names[0]}. :spy: "
                            f"No spy tokens will be given this round."
                        )
                else:
                    playermsg += f"You discarded your {d_cardname}."
                    othersmsg += f"They discarded their {d_cardname}."
            else: # Target another
                playermsg = (
                    f"You forced {self.players[target].mention} to "
                    f"discard their hand.\n"
                )
                targetmsg = (
                    f"{player_mention} played {self.names[5]} on you and "
                    f"forced you to discard your hand.\n"
                )
                othersmsg = (
                    f"{player_mention} played {self.names[5]} on "
                    f"{self.players[target].mention} and forced them to "
                    f"discard their hand.\n"
                )
                if self.cards[target] == 9:
                    playermsg += (
                        f"They discarded {self.names[9]} and were eliminated! "
                        f":x:"
                    )
                    targetmsg += (
                        f"You discarded {self.names[9]} and were eliminated! "
                        f":x:"
                    )
                    othersmsg += (
                        f"They discarded {self.names[9]} and were eliminated! "
                        f":x:"
                    )
                elif self.cards[target] == 0:
                    if sum(self.spy) == 1:
                        playermsg += (
                            f"They discarded the first {self.names[0]}! :spy:"
                        )
                        targetmsg += (
                            f"You discarded the first {self.names[0]}! :spy:"
                        )
                        othersmsg += (
                            f"They discarded the first {self.names[0]}! :spy:"
                        )
                    elif len([s for s in self.spy if s > 0]) == 1:
                        playermsg += (
                            "They played or discarded both :zero: Spies! :spy:"
                        )
                        targetmsg += (
                            "You played or discarded both :zero: Spies! :spy:"
                        )
                        othersmsg += (
                            "They played or discarded both :zero: Spies! :spy:"
                        )
                    else:
                        playermsg += (
                            f"They discarded the second {self.names[5]}. "
                            f":spy: No spy tokens will be given this round."
                        )
                        targetmsg += (
                            f"You discarded the second {self.names[5]}. "
                            f":spy: No spy tokens will be given this round."
                        )
                        othersmsg += (
                            f"They discarded the second {self.names[5]}. "
                            f":spy: No spy tokens will be given this round."
                        )
                else:
                    playermsg += f"They discarded their {d_cardname}."
                    targetmsg += f"You discarded your {d_cardname}."
                    othersmsg += f"They discarded their {d_cardname}."
            # Discard and redraw (if not eliminated)
            self.discard.append(self.cards[target])
            if self.cards[target] == 9:
                self.cards[target] = -1
            else:
                if len(self.deck) > 0:
                    newcard = self.deck.pop()
                else:
                    newcard = self.hidden_card
                    self.discard.pop(0)
                self.cards[target] = newcard
                if target == self.turn:
                    playermsg += f"\nYou drew {self.names[newcard]}."
                else:
                    targetmsg += f"\nYou drew {self.names[newcard]}."
        elif reaction == 6:
            if len(self.deck) == 0:
                playermsg = (
                    "The deck is empty."
                )
                othersmsg = (
                    f"{player_mention} played {self.names[6]}. The deck "
                    f" is empty, and it had no effect."
                )
            elif len(self.deck) == 1:
                hand = [self.cards[self.turn], self.deck.pop()]
                await dm.send(
                    f"You played {self.names[6]}, and have drawn "
                    f"{self.names[hand[1]]} from the deck. The deck is now "
                    f"empty."
                )
                hand.sort()
                # First card
                msg = await dm.send(
                    f"Which of your two cards would you like to return to "
                    f"the deck?"
                )
                reacts = [self.emoji[i] for i in hand]
                card = await self.wait_for(msg, reacts, check)
                self.deck.insert(0, card)
                hand.remove(card)
                # Done
                self.cards[self.turn] = hand[0]
                playermsg = (
                    "You have returned one card to form the deck."
                )
                othersmsg = (
                    f"{player_mention} played {self.names[6]}. They have "
                    f"drawn the last remaining card from the deck, and "
                    f"returned one card to the deck."
                )
            else:
                hand = [
                    self.cards[self.turn], self.deck.pop(), self.deck.pop()
                ]
                deck_empty = 'The deck is now empty.'
                await dm.send(
                    f"You played {self.names[6]}, and have drawn "
                    f"{self.names[hand[1]]} and {self.names[hand[2]]} from "
                    f"the deck. {deck_empty * (len(self.deck) == 0)}"
                )
                hand.sort()
                # First card
                msg = await dm.send(
                    f"Which of your three cards would you like to return to "
                    f"the bottom of the deck first? Your next card will go "
                    f"below this card."
                )
                reacts = [self.emoji[i] for i in hand]
                card = await self.wait_for(msg, reacts, check)
                self.deck.insert(0, card)
                hand.remove(card)
                # Second card
                msg = await dm.send(
                    f"Which of your two cards would you like to return to the "
                    f"bottom of the deck?"
                )
                reacts = [self.emoji[i] for i in hand]
                card = await self.wait_for(msg, reacts, check)
                self.deck.insert(0, card)
                hand.remove(card)
                # Done
                self.cards[self.turn] = hand[0]
                playermsg = (
                    "You have placed two cards on the bottom of the deck."
                )
                othersmsg = (
                    f"{player_mention} played {self.names[6]}. They have "
                    f"drawn the top two cards from the deck, and returned two "
                    f"cards to the bottom of the deck."
                )
        elif reaction == 7:
            # Ask player for target
            reacts = [self.emoji[i] for i in targetable]
            if len(reacts) > 0:
                msg = await dm.send(
                    f"Who would you like to use {self.names[7]} on?"
                )
                target = await self.wait_for(msg, reacts, check, player=True)
                # Swap cards
                self.cards[target], self.cards[self.turn] = \
                    self.cards[self.turn], self.cards[target]
                # Send messages to both players with their new hand
                playermsg = (
                    f"You used {self.names[7]} on "
                    f"{self.players[target].mention} "
                    f"and swapped hands with them. They took your "
                    f"{self.names[self.cards[target]]} and gave you their "
                    f"{self.names[self.cards[self.turn]]}."
                )
                targetmsg = (
                    f"{player_mention} played {self.names[7]} on you and your "
                    f"hands were swapped. They took your "
                    f"{self.names[self.cards[self.turn]]} and gave you their "
                    f"{self.names[self.cards[target]]}."
                )
                othersmsg = (
                    f"{player_mention} played {self.names[7]} against "
                    f"{self.players[target].mention} and swapped hands with "
                    f"them."
                )
            else:
                playermsg = (
                    f"There are no targets for {self.names[7]}."
                )
                othersmsg = (
                    f"{player_mention}'s {self.names[7]} has no targets."
                )
        elif reaction == 8:
            playermsg = f"You played {self.names[8]}."
            othersmsg = f"{player_mention} played {self.names[8]}."
        elif reaction == 9:
            # Eliminate player
            self.discard.append(self.cards[self.turn])
            self.cards[self.turn] = -1
            playermsg = (
                f"You have discarded {self.names[9]} and are eliminated. :x:"
            )
            othersmsg = (
                f"{player_mention} has discarded {self.names[9]} and is "
                f"eliminated. :x:"
            )
        else:
            # AAAAAAAAAAAAAAAAAAAAAAAAAAA
            raise ValueError("SOMETHING BROKE HELP AAAAAAAAAAAAAAAA")
        
        # Send messages
        for i in range(len(self.players)):
            if i == self.turn:
                await self.dms[i].send(playermsg)
            elif i == target:
                await self.dms[i].send(targetmsg)
            else:
                await self.dms[i].send(othersmsg)
        
        return await self.end_turn()

    async def end_turn(self):
        """
        Checks if the round is over and increments the turn.
        """
        remain = [i for i in range(len(self.players)) if self.cards[i] > -1]
        if len(remain) < 2:
            # win by last player standing
            self.turn = remain[0]
            self.tokens[remain[0]] += 1 # Winner gets token
            await self.send_msg(
                f"{self.players[self.turn].mention} is the only player "
                f"remaining!\n"
                f"The round is now over!"
            )
            return True
        elif len(self.deck) == 0:
            # win by high card
            remain = [i for i in remain if self.cards[i] == max(self.cards)]
            while True:
                self.turn = (self.turn + 1) % len(self.players)
                if self.turn in remain:
                    break
            for i in remain:
                self.tokens[i] += 1 # Winners get token
            embed = self.get_embed()
            embed.description = "The deck has run out!"
            embed.add_field(
                name="Players",
                value="\n".join([
                    f"{i+1}. {self.players[i].mention}"
                    for i in range(len(self.players))
                ])
            )
            embed.add_field(
                name="Cards",
                value="\n".join([
                    self.names[c].split()[0] if c > -1 else ":x:"
                    for c in self.cards
                ])
            )
            await self.send_embed(embed)
            if len(remain) == 1:
                end_msg = (
                    f"{self.players[remain[0]].mention} "
                    f"has the highest card! :love_letter:"
                )
            elif len(remain) == 2:
                end_msg = (
                    f"{remain[0]} and {remain[1]} tie for the highest card! "
                    f":love_letter:"
                )
            else:
                end_msg = (
                    f"{', '.join(remain[:-1])}, and {remain[-1]} all tie for "
                    f"the highest card! :love_letter:")
            await self.send_msg(end_msg)
            return True
        else:
            while True:
                self.turn = (self.turn + 1) % len(self.players)
                if self.cards[self.turn] > -1:
                    break
            return False
    
    async def round_end(self):
        # Award spy token
        spies = [i for i in range(len(self.players)) if self.spy[i] > 0]
        if len(spies) == 1:
            self.tokens[spies[0]] += 1 # Spy winner gets token
            await self.send_msg(
                f"{self.players[spies[0]].mention} has earned a token "
                f":love_letter: for being the only player to play or discard "
                f"a Spy!"
            )
        embed = self.get_embed()
        embed.title = "Scores"
        embed.description = f"Target score: {self.scoretarget}"
        embed.add_field(
            name="Players:",
            value="\n".join([
                f"{p[0]}. {p[1].mention}" for p in enumerate(self.players, 1)
            ])
        )
        embed.add_field(
            name="Tokens",
            value="\n".join([
                "⠀" * (1 - bool(self.tokens[i]))
                + ":love_letter: " * self.tokens[i]
                for i in range(len(self.players))
            ])
        )
        await self.send_embed(embed)
        if max(self.tokens) < self.scoretarget:
            return False
        else:
            winners = [
                self.players[i].mention for i in range(len(self.players))
                if self.tokens[i] >= self.scoretarget
            ]
            end_msg = "The game is now over! "
            if len(winners) == 1:
                end_msg += f"{winners[0]} is the winner! :tada:"
            elif len(winners) == 2:
                end_msg += (
                    f"{winners[0]} and {winners[1]} are the winners! :tada:"
                )
            else:
                end_msg += (
                    f"{', '.join(winners[:-1])}, and {winners[-1]} are the "
                    f"winners! :tada:"
                )
            await self.send_msg(end_msg)
            return True
            
    def get_embed(self):
        embed = Embed(
            title=f"Game State",
            description="",
            color=LLCOLOR
        )
        embed.set_footer(text="Love Letter Second Edition © 2019 Z-Man Games")
        return embed


async def game_starter(players, dms, ctx, wait_fn, flags):
    global GAME
    if GAME is None:
        GAME = LoveLetter(players, dms, ctx, wait_fn, flags)
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
