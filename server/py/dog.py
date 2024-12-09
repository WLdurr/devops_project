from typing import List, Optional, ClassVar
from enum import Enum
import random
from pydantic import BaseModel
from server.py.game import Game, Player


class Card(BaseModel):
    suit: str  # card suit (color)
    rank: str  # card rank


class Marble(BaseModel):
    pos: int       # position on board (0 to 95)
    is_save: bool  # true if marble was moved out of kennel and was not yet moved


class PlayerState(BaseModel):
    name: str                  # name of player
    list_card: List[Card]      # list of cards
    list_marble: List[Marble]  # list of marbles


class Action(BaseModel):
    card: Card                 # card to play
    pos_from: Optional[int]    # position to move the marble from
    pos_to: Optional[int]      # position to move the marble to
    card_swap: Optional[Card] = None # optional card to swap ()


class GamePhase(str, Enum):
    SETUP = 'setup'            # before the game has started
    RUNNING = 'running'        # while the game is running
    FINISHED = 'finished'      # when the game is finished


class GameState(BaseModel):

    LIST_SUIT: ClassVar[List[str]] = ['♠', '♥', '♦', '♣']  # 4 suits (colors)
    LIST_RANK: ClassVar[List[str]] = [
        '2', '3', '4', '5', '6', '7', '8', '9', '10',      # 13 ranks + Joker
        'J', 'Q', 'K', 'A', 'JKR'
    ]
    LIST_CARD: ClassVar[List[Card]] = [
        # 2: Move 2 spots forward
        Card(suit='♠', rank='2'), Card(suit='♥', rank='2'), Card(suit='♦', rank='2'), Card(suit='♣', rank='2'),
        # 3: Move 3 spots forward
        Card(suit='♠', rank='3'), Card(suit='♥', rank='3'), Card(suit='♦', rank='3'), Card(suit='♣', rank='3'),
        # 4: Move 4 spots forward or back
        Card(suit='♠', rank='4'), Card(suit='♥', rank='4'), Card(suit='♦', rank='4'), Card(suit='♣', rank='4'),
        # 5: Move 5 spots forward
        Card(suit='♠', rank='5'), Card(suit='♥', rank='5'), Card(suit='♦', rank='5'), Card(suit='♣', rank='5'),
        # 6: Move 6 spots forward
        Card(suit='♠', rank='6'), Card(suit='♥', rank='6'), Card(suit='♦', rank='6'), Card(suit='♣', rank='6'),
        # 7: Move 7 single steps forward
        Card(suit='♠', rank='7'), Card(suit='♥', rank='7'), Card(suit='♦', rank='7'), Card(suit='♣', rank='7'),
        # 8: Move 8 spots forward
        Card(suit='♠', rank='8'), Card(suit='♥', rank='8'), Card(suit='♦', rank='8'), Card(suit='♣', rank='8'),
        # 9: Move 9 spots forward
        Card(suit='♠', rank='9'), Card(suit='♥', rank='9'), Card(suit='♦', rank='9'), Card(suit='♣', rank='9'),
        # 10: Move 10 spots forward
        Card(suit='♠', rank='10'), Card(suit='♥', rank='10'), Card(suit='♦', rank='10'), Card(suit='♣', rank='10'),
        # Jake: A marble must be exchanged
        Card(suit='♠', rank='J'), Card(suit='♥', rank='J'), Card(suit='♦', rank='J'), Card(suit='♣', rank='J'),
        # Queen: Move 12 spots forward
        Card(suit='♠', rank='Q'), Card(suit='♥', rank='Q'), Card(suit='♦', rank='Q'), Card(suit='♣', rank='Q'),
        # King: Start or move 13 spots forward
        Card(suit='♠', rank='K'), Card(suit='♥', rank='K'), Card(suit='♦', rank='K'), Card(suit='♣', rank='K'),
        # Ass: Start or move 1 or 11 spots forward
        Card(suit='♠', rank='A'), Card(suit='♥', rank='A'), Card(suit='♦', rank='A'), Card(suit='♣', rank='A'),
        # Joker: Use as any other card you want
        Card(suit='', rank='JKR'), Card(suit='', rank='JKR'), Card(suit='', rank='JKR')
    ] * 2

    cnt_player: int = 4                # number of players (must be 4)
    phase: GamePhase                   # current phase of the game
    cnt_round: int                     # current round
    bool_card_exchanged: bool          # true if cards was exchanged in round
    idx_player_started: int            # index of player that started the round
    idx_player_active: int             # index of active player in round
    list_player: List[PlayerState]     # list of players
    list_card_draw: List[Card]         # list of cards to draw
    list_card_discard: List[Card]      # list of cards discarded
    card_active: Optional[Card]        # active card (for 7 and JKR with sequence of actions)
    steps_remaining_for_7: int = 0     # steps left for a 7 card move


class Dog(Game):

    KENNEL_POSITIONS = [
        [64, 65, 66, 67],  # Positions for player index 0
        [72, 73, 74, 75],  # Positions for player index 1
        [80, 81, 82, 83],  # Positions for player index 2
        [88, 89, 90, 91]  # Positions for player index 3
    ]

    # Define starting positions for each player
    START_POSITION = [0, 16, 32, 48]

    #Define Finish Position
    FINISH_POSITIONS = [
        [71, 70, 69, 68],  #  Positions for player index 0
        [79, 78, 77, 76],  #  Positions for player index 1
        [87, 86, 85, 84],  #  Positions for player index 2
        [95, 94, 93, 92],  #  Positions for player index 3
    ]

    def __init__(self) -> None:
        """ Game initialization (set_state call not necessary, we expect 4 players) """
        # Initialize the game state
        self.state: GameState = GameState(
            cnt_player=4,
            phase=GamePhase.SETUP,
            cnt_round=1,
            bool_card_exchanged=False,
            idx_player_started=0,
            idx_player_active=0,
            list_player=[],
            list_card_draw=[],
            list_card_discard=[],
            card_active=None,
        )

        # Initialize the deck of cards
        self.state.list_card_draw = GameState.LIST_CARD.copy()
        random.shuffle(self.state.list_card_draw)

        # Initialize the players
        for idx in range(self.state.cnt_player):
            player_state: PlayerState = PlayerState(
                name = f"Player {idx + 1}",
                list_card=[],
                list_marble=[],
            )

            # Initialize player's marbles
            for marble_idx in range(4):  # 4 marbles per player
                marble = Marble(
                    pos = self.KENNEL_POSITIONS[idx][marble_idx],  # get the position from the kennel
                    is_save = False)
                player_state.list_marble.append(marble)

            # Add the player state to the game state
            self.state.list_player.append(player_state)

        # Randomly select starting player
        self.state.idx_player_started = random.randint(0, self.state.cnt_player - 1)
        self.state.idx_player_active = self.state.idx_player_started

        # Initialize the state of the card exchange
        self.state.bool_card_exchanged = False

        # Initialize the number of rounds
        # (Stefan) Is this necessary? we already initialized cnt_round to 1 in INIT
        self.state.cnt_round = 1

        # # TODO: deal cards as an action ?? -> probably make a separate function for this outside the init
        # num_cards_per_player = 6  # Number of cards per player in the first round
        # total_cards_to_deal = num_cards_per_player * self.state.cnt_player
        # assert len(self.state.list_card_draw) >= total_cards_to_deal, (
        #     f"Not enough cards to deal: required {total_cards_to_deal}, "
        #     f"but only {len(self.state.list_card_draw)} available."
        # )
        #
        # for _ in range(num_cards_per_player):
        #     for player_state in self.state.list_player:
        #         # Draw a card for the player
        #         card = self.state.list_card_draw.pop()
        #         player_state.list_card.append(card)
        self.state.phase = GamePhase.RUNNING

        # Deal initial cards for the first round (6 cards per player)
        self.deal_cards(num_cards_per_player=6)

    def set_state(self, state: GameState) -> None:
        """ Set the game to a given state """
        self.state = state

    def get_state(self) -> GameState:
        """ Get the complete, unmasked game state """
        return self.state

    def print_state(self) -> None:
        """ Print the current game state """
        if not self.state:
            print("No state set.")
            return

        print("\n--- Game State ---")
        print(f"Phase: {self.state.phase}")
        print(f"Round: {self.state.cnt_round}")
        print(f"Active Player: Player {self.state.idx_player_active + 1}")
        print(f"Started by: Player {self.state.idx_player_started + 1}")
        print(f"Cards Exchanged: {self.state.bool_card_exchanged}")
        print("\nDiscard Pile:")
        if self.state.list_card_discard:
            for card in self.state.list_card_discard:
                print(f"  {card.suit}{card.rank}")
        else:
            print("Empty")
        print("\nPlayers:")
        for idx, player in enumerate(self.state.list_player):
            print(f"Player {idx + 1} - {player.name}")
            print("Cards:")
            for card in player.list_card:
                print(f"{card.suit}{card.rank}")
            print("Marbles:")
            for marble in player.list_marble:
                print(f"Position: {marble.pos}, Safe: {marble.is_save}")

    def get_list_action(self) -> List[Action]:
        """ Get a list of possible actions for the active player """
        actions: List[Action] = []

        active_player_idx = self.state.idx_player_active
        active_player = self.state.list_player[active_player_idx]

        # If we are currently in the middle of a 7-card move
        if self.state.card_active and self.state.card_active.rank == '7':
            # Only allow moves with the same 7 card
            if self.state.steps_remaining_for_7 > 0:
                # We must offer actions that move a marble forward by 1 to steps_remaining_for_7
                # According to tests, we must ensure if no action is possible, return empty list.

                # We try each marble and each possible step from 1 to steps_remaining_for_7
                any_action_found = False
                for card in active_player.list_card:
                    if card == self.state.card_active:
                        # Check each marble
                        for m_idx, marble in enumerate(active_player.list_marble):
                            if not self.is_in_kennel(active_player_idx, marble):
                                # Try all step sizes from 1 to steps_remaining_for_7
                                for steps in range(1, self.state.steps_remaining_for_7 + 1):
                                    if self.can_move_steps(active_player_idx, m_idx, steps):
                                        # We can form a potential action. The final position:
                                        final_pos = self.compute_final_position(marble.pos, steps, active_player_idx)
                                        actions.append(Action(
                                            card=card,
                                            pos_from=marble.pos,
                                            pos_to=final_pos
                                        ))
                                        any_action_found = True
                if not any_action_found:
                    # No moves possible - return empty list
                    return []
                return actions
            else:
                # No steps remaining for a 7 card (should not happen here)
                return []
        else:
            start_position = self.START_POSITION[active_player_idx]

            # Check if the start position is unoccupied
            if not any(marble.pos == start_position
                    for marble in self.state.list_player[active_player_idx].list_marble):
                # Start position is unoccupied

                # Check if the player has any marbles in the kennel
                marbles_in_kennel = [
                    marble for marble in self.state.list_player[active_player_idx].list_marble
                    if marble.pos in self.KENNEL_POSITIONS[active_player_idx]
                ]
                marbles_in_kennel.sort(key=lambda x: x.pos)

                for card in active_player.list_card:
                    if card.rank in ['K', 'A', 'JKR']:
                        if marbles_in_kennel:
                            # Move the marble in the first kennel position to the start position
                            action = Action(
                                card = card,
                                pos_from = marbles_in_kennel[0].pos,
                                pos_to = start_position,
                                card_swap = None
                            )
                            actions.append(action)

        # Check possible move actions for each card in the player's hand
        for card in active_player.list_card:
            if card.rank not in ['7', 'J', 'A', 'JKR']:
                # "normal" Cards
                for marble_idx, marble in enumerate(active_player.list_marble):
                    if marble.pos not in self.KENNEL_POSITIONS[active_player_idx]:
                        # Total moves allowed by the card
                        if card.rank == 'K':
                            num_moves = 13
                        elif card.rank == 'Q':
                            num_moves = 12
                        else:
                            num_moves = int(card.rank)

                            # Set move to allowed (will be rechecked in following steps)
                            move_allowed = True

                            # Create test game state
                            new_marble_pos = marble.pos

                            for _ in range(num_moves):
                                new_marble_pos = (new_marble_pos + 1) % 64
                                validity = self.check_move_validity(active_player_idx, marble_idx, new_marble_pos)
                                if not validity:
                                    move_allowed = False
                                    break

                            if move_allowed:
                                actions.append(
                                    Action(
                                        card = card,
                                        pos_from = marble.pos,
                                        pos_to = new_marble_pos,
                                        card_swap = None
                                    )
                                )

                # --- Card 7 ---
                if card.rank == '7':
                    # The initial usage of 7 card - allow at least one move
                    can_start_7 = False
                    for m_idx, marble in enumerate(active_player.list_marble):
                        if not self.is_in_kennel(active_player_idx, marble):
                            if self.can_move_steps(active_player_idx, m_idx, 1):
                                final_pos = self.compute_final_position(marble.pos, 1, active_player_idx)
                                actions.append(Action(
                                    card=card,
                                    pos_from=marble.pos,
                                    pos_to=final_pos
                                ))
                                can_start_7 = True
                    # If we cannot move even 1 step with any marble, no action for 7 is added.

                # --- Joker ---
                if card.rank == 'JKR':
                    for possible_card in range(1, 14):
                        for marble in active_player.list_marble:
                            if marble.pos not in self.KENNEL_POSITIONS[active_player_idx]:
                                num_moves = possible_card
                                move_allowed = True
                                test_state = self.state.model_copy(deep=True)

                                for _ in range(num_moves):
                                    test_state.list_player[active_player_idx].list_marble[marble.pos].pos += 1
                                    validity = self.check_move_validity(
                                        test_state, active_player_idx, marble.pos)
                                    if not validity:
                                        move_allowed = False
                                        break

                            if move_allowed:
                                actions.append(
                                    Action(
                                        card=Card(suit='', rank=str(possible_card)),
                                        pos_from=marble.pos,
                                        pos_to=test_state.list_player[active_player_idx].list_marble[marble.pos].pos,
                                        card_swap=None
                                    )
                                )
                # --- Ass ---
                if card.rank == 'A':
                    for marble in active_player.list_marble:
                        if marble.pos not in self.KENNEL_POSITIONS[active_player_idx]:
                            # Move 1 forward
                            pos_to_1 = (marble.pos + 1) % 64
                            if self.check_move_validity(test_state=self.state, active_player_idx=active_player_idx, marble_idx=marble_idx, marble_new_pos=pos_to_1):
                                actions.append(
                                    Action(
                                        card=card,
                                        pos_from=marble.pos,
                                        pos_to=pos_to_1,
                                        card_swap=None
                                    )
                                )

                            # Move 11 forward
                            pos_to_11 = (marble.pos + 11) % 64  
                            if self.check_move_validity(test_state=self.state, active_player_idx=active_player_idx, marble_idx=marble.pos):
                                actions.append(
                                    Action(
                                        card=card,
                                        pos_from=marble.pos,
                                        pos_to=pos_to_11,
                                        card_swap=None
                                    )
                                )




                if card.rank == '4':
                    # Add action for backwards motion
                    for marble_idx, marble in enumerate(active_player.list_marble):
                        if (marble.pos not in self.KENNEL_POSITIONS[active_player_idx] and
                                marble.pos not in self.FINISH_POSITIONS[active_player_idx]):

                            # Set move to allowed (will be rechecked in following steps)
                            move_backwards_allowed = True

                            # Create test game state
                            new_marble_pos = marble.pos

                            for _ in range(4):
                                new_marble_pos = (new_marble_pos -1 + 64) % 64
                                validity = self.check_move_validity(active_player_idx, marble_idx, new_marble_pos)
                                if not validity:
                                    move_backwards_allowed = False
                                    break

                            if move_backwards_allowed:
                                actions.append(
                                    Action(
                                        card = card,
                                        pos_from = marble.pos,
                                        pos_to = new_marble_pos,
                                        card_swap = None
                                    )
                                )


                # --- Jack ---
                if card.rank == 'J':
                    idx_player = [active_player_idx]
                    idx_other_players = [idx for idx in range(4) if idx != active_player_idx]

                    # Generate combinations in both directions
                    player_exchange_combinations = [(p1, p2) for p1 in idx_player for p2 in idx_other_players]

                    for combination in player_exchange_combinations:
                        for first_marble in self.state.list_player[combination[0]].list_marble:
                            if (first_marble.pos not in self.KENNEL_POSITIONS[combination[0]]
                                    and first_marble.pos not in self.FINISH_POSITIONS[combination[0]]):
                                for other_marble in self.state.list_player[combination[1]].list_marble:
                                    if (other_marble.pos not in self.KENNEL_POSITIONS[combination[1]] and other_marble.pos
                                            not in self.FINISH_POSITIONS[combination[1]] and not other_marble.is_save):
                                        actions.append(
                                            Action(
                                                card = card,
                                                pos_from = first_marble.pos,
                                                pos_to = other_marble.pos,
                                                card_swap = None
                                            )
                                        )
                                        actions.append(
                                            Action(
                                                card = card,
                                                pos_from = other_marble.pos,
                                                pos_to = first_marble.pos,
                                                card_swap = None
                                            )
                                        )

                    if len(actions) == 0:
                        # If no actions are possible, swap marbles with yourself
                        for first_marble in self.state.list_player[active_player_idx].list_marble:
                            if (first_marble.pos not in self.KENNEL_POSITIONS[active_player_idx]
                                    and first_marble.pos not in self.FINISH_POSITIONS[active_player_idx]):
                                for other_marble in self.state.list_player[active_player_idx].list_marble:
                                    if (other_marble.pos not in self.KENNEL_POSITIONS[active_player_idx] and
                                            other_marble.pos not in self.FINISH_POSITIONS[active_player_idx]):
                                        actions.append(
                                            Action(
                                                card=card,
                                                pos_from=first_marble.pos,
                                                pos_to=other_marble.pos,
                                                card_swap=None
                                            )
                                        )

            return actions

    # (Stefan): deal cards as new action
    def deal_cards(self, num_cards_per_player: int) -> None:
        """Deal a specified number of cards to each player."""
        total_cards_to_deal = num_cards_per_player * self.state.cnt_player
        assert len(self.state.list_card_draw) >= total_cards_to_deal, (
            f"Not enough cards to deal: required {total_cards_to_deal}, "
            f"but only {len(self.state.list_card_draw)} available."
        )

        # Clear players' hands before dealing new cards
        for player_state in self.state.list_player:
            player_state.list_card.clear()

        # Deal the cards to each player
        for _ in range(num_cards_per_player):
            for player_state in self.state.list_player:
                card = self.state.list_card_draw.pop()  # Pop a card from the deck
                player_state.list_card.append(card)

        # If there aren't enough cards left to deal, reshuffle the discard pile into the draw pile
        if len(self.state.list_card_draw) < total_cards_to_deal:
            print("Not enough cards in draw pile. Reshuffling discard pile into draw pile.")
            self.state.list_card_draw.extend(self.state.list_card_discard)
            self.state.list_card_discard.clear()
            random.shuffle(self.state.list_card_draw)

    # (Stefan): I tested new round with a helper method start_new_round to simplify code in apply action.
    def start_new_round(self) -> None:
        """ Begin a new round by reshuffling and distributing cards. """
        # Increment round number
        self.state.cnt_round += 1
        if self.state.cnt_round > 5:
            self.state.cnt_round = 1  # Reset after round 5 to round 1

        # Set number of cards per player based on round
        if 1 <= self.state.cnt_round <= 5:
            num_cards_per_player = 7 - self.state.cnt_round  # 6, 5, 4, 3, 2 cards
        elif self.state.cnt_round == 6:
            num_cards_per_player = 6  # Reset to 6 cards
        else:
            num_cards_per_player = max(7 - ((self.state.cnt_round - 1) % 5 + 1), 2)

        # Deal the correct number of cards to each player for the current round
        self.deal_cards(num_cards_per_player)

        # Reset the exchange state and set active player
        self.state.bool_card_exchanged = False
        self.state.idx_player_active = 0

        # Set the game phase to RUNNING
        self.state.phase = GamePhase.RUNNING

    def apply_action(self, action: Action) -> None:
        """Apply the given action to the game."""
        active_player_index = self.state.idx_player_active

        # Handle the case where action is None (start a new round)
        # handles errors in benchmark file. all tests running without errors.
        if action is None:
            self.start_new_round()
            return

        # Check input of pos_from and pos_to
        if (action.pos_from is not None and action.pos_from != -1 and
                action.pos_to is not None and action.pos_to != -1):
            # Move a marble
            for idx_marble, marble in enumerate(self.state.list_player[active_player_index].list_marble):
                if marble.pos == action.pos_from:
                    self.state.list_player[active_player_index].list_marble[idx_marble].pos = action.pos_to

                    # Check if the marble is moved out of the kennel
                    if action.pos_from in self.KENNEL_POSITIONS[active_player_index]:
                        self.state.list_player[active_player_index].list_marble[idx_marble].is_save = True

        # Handle card swapping
        elif action.card_swap is not None:
            target_player_idx = (active_player_index + 2) % 4

            # Active player gives their card and the target player receives it
            self.state.list_player[active_player_index].list_card.remove(action.card)
            self.state.list_player[target_player_idx].list_card.append(action.card)

            # Target player gives a random card back
            self.state.list_player[target_player_idx].list_card.remove(action.card_swap)
            self.state.list_player[active_player_index].list_card.append(action.card_swap)

            self.state.bool_card_exchanged = True

        # move played card from hand to discard pile
        if action.card in self.state.list_player[active_player_index].list_card:
            self.state.list_player[active_player_index].list_card.remove(action.card)
            self.state.list_card_discard.append(action.card)

        # Check if all players have finished their hands (end of round)
        if all(len(player.list_card) == 0 for player in self.state.list_player):
            self.start_new_round()



    def get_player_view(self, idx_player: int) -> GameState:
        """ Get the masked state for the active player (e.g. the opponent's cards are face down)"""
        # TODO: implement this
        player_view = self.state.model_copy(deep = True)
        return player_view

    def check_move_validity(self, active_player_idx: int, marble_idx: int, marble_new_pos: int) -> bool:
        """ Check if move is valid """
        marble = self.state.list_player[active_player_idx].list_marble[marble_idx]

        # check if the new position of the marble is occupied by another marble, that is safe
        for player_idx, player in enumerate(self.state.list_player):
            for other_marble_idx, other_marble in enumerate(player.list_marble):
                if other_marble.pos == marble_new_pos and other_marble.is_save:
                    if not (player_idx == active_player_idx and other_marble_idx == marble_idx):
                        return False

        # Check that the Finish is implemented correctly
        start_pos = self.START_POSITION[active_player_idx]
        kennel_pos = self.KENNEL_POSITIONS[active_player_idx]
        finish_pos = self.FINISH_POSITIONS[active_player_idx]

        # Prevent moving out of the kennel if the start position is occupied by a safe marble
        if marble.pos in kennel_pos and marble_new_pos == start_pos:
            list_of_other_marbles = [self.state.list_player[active_player_idx].list_marble[idx]
                                     for idx in range(4) if idx != marble_idx]
            for other_marble in list_of_other_marbles:
                if other_marble.pos == start_pos and other_marble.is_save:
                    return False

        # Check that marbles do not go back in kennel
        if marble_new_pos in kennel_pos:
            return False

        # Do not allow positions outside the game
        if marble_new_pos < 0 or marble_new_pos >= 96:
            return False

        return True

    def is_in_kennel(self, player_idx: int, marble: Marble) -> bool:
        return marble.pos in self.KENNEL_POSITIONS[player_idx]
    
    def can_move_steps(self, player_idx: int, marble_idx: int, steps: int, direction: int = 1) -> bool:
        # simulate step-by-step move in a copy
        test_state = self.state.model_copy(deep=True)
        marble = test_state.list_player[player_idx].list_marble[marble_idx]
        for _ in range(abs(steps)):
            if marble.pos < 64:
                next_pos = (marble.pos + direction) % 64
            else:
                # In finish lanes or kennel:
                next_pos = marble.pos + direction

            if not self.check_move_validity(player_idx, marble_idx, next_pos):
                return False
            marble.pos = next_pos
        return True

    def compute_final_position(self, start_pos: int, steps: int, player_idx: int) -> int:
        # Simplified final pos calculation:
        if start_pos < 64:
            # normal circle
            new_pos = (start_pos + steps) % 64
        else:
            # finish or kennel
            new_pos = start_pos + steps
        return new_pos

    def move_marble_steps_with_bumping(self, player_idx: int, marble_idx: int, steps: int, direction: int = 1):
        marble = self.state.list_player[player_idx].list_marble[marble_idx]
        start_pos = marble.pos
        for _ in range(abs(steps)):
            # compute next step
            if marble.pos < 64:
                next_pos = (marble.pos + direction) % 64
            else:
                next_pos = marble.pos + direction

            # check again (should already be checked in can_move_steps)
            if not self.check_move_validity(player_idx, marble_idx, next_pos):
                # This should not happen if get_list_action and apply_action are consistent
                return
            marble.pos = next_pos
            # bump marbles
            self.send_home_if_passed(marble.pos, player_idx)

        # If starting from kennel and now on board, mark is_save = True
        if start_pos in self.KENNEL_POSITIONS[player_idx] and marble.pos not in self.KENNEL_POSITIONS[player_idx]:
            marble.is_save = True

    def send_home_if_passed(self, pos: int, active_player_idx: int):
        # If a marble is found at 'pos', send it home (unless it's the moved marble itself)
        for p_idx, player in enumerate(self.state.list_player):
            for m_idx, m in enumerate(player.list_marble):
                if m.pos == pos and not (p_idx == active_player_idx and m.is_save and m.pos == self.START_POSITION[p_idx]):
                    # The marble that got overtaken goes to its kennel
                    if not (p_idx == active_player_idx and self.is_marble_protecting_start(p_idx, m_idx)):
                        # Overtaken marble goes home
                        m.pos = self.KENNEL_POSITIONS[p_idx][0]
                        m.is_save = False

    def is_marble_protecting_start(self, player_idx: int, marble_idx: int) -> bool:
        # If a marble is at start position and is safe, it protects it
        marble = self.state.list_player[player_idx].list_marble[marble_idx]
        return marble.is_save and marble.pos == self.START_POSITION[player_idx]


class RandomPlayer(Player):

    def select_action(self, state: GameState, actions: List[Action]) -> Optional[Action]:
        """ Given masked game state and possible actions, select the next action """
        if len(actions) > 0:
            return random.choice(actions)
        return None


if __name__ == '__main__':

    game = Dog()
