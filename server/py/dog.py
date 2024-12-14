''' This Code implement the game brandy dog'''
from typing import List, Optional, ClassVar, Tuple
from enum import Enum
import random
from itertools import combinations
from pydantic import BaseModel
from server.py.game import Game, Player


class Card(BaseModel):
    """Card class"""
    suit: str  # card suit (color)
    rank: str  # card rank


class Marble(BaseModel):
    """Marble class"""
    pos: int       # position on board (0 to 95)
    is_save: bool  # true if marble was moved out of kennel and was not yet moved


class PlayerState(BaseModel):
    """Player state class"""
    name: str                  # name of player
    list_card: List[Card]      # list of cards
    list_marble: List[Marble]  # list of marbles


class Action(BaseModel):
    """Action class"""
    card: Card                 # card to play
    pos_from: Optional[int]    # position to move the marble from
    pos_to: Optional[int]      # position to move the marble to
    card_swap: Optional[Card] = None # optional card to swap ()


class GamePhase(str, Enum):
    """Game phase enumeration"""
    SETUP = 'setup'            # before the game has started
    RUNNING = 'running'        # while the game is running
    FINISHED = 'finished'      # when the game is finished


class GameState(BaseModel):
    """Game state class"""
    LIST_SUIT: ClassVar[List[str]] = ['♠', '♥', '♦', '♣']  # 4 suits (colors)
    LIST_RANK: ClassVar[List[str]] = [
        '2', '3', '4', '5', '6', '7', '8', '9', '10',      # 13 ranks + Joker
        'J', 'Q', 'K', 'A', 'JKR'
    ]
    LIST_CARD: ClassVar[List[Card]] = [
        # 2: Move 2 spots forward
        Card(suit='♠', rank='2'), Card(suit='♥', rank='2'), Card(suit='♦', rank='2'),
        Card(suit='♣', rank='2'),
        # 3: Move 3 spots forward
        Card(suit='♠', rank='3'), Card(suit='♥', rank='3'), Card(suit='♦', rank='3'),
        Card(suit='♣', rank='3'),
        # 4: Move 4 spots forward or back
        Card(suit='♠', rank='4'), Card(suit='♥', rank='4'), Card(suit='♦', rank='4'),
        Card(suit='♣', rank='4'),
        # 5: Move 5 spots forward
        Card(suit='♠', rank='5'), Card(suit='♥', rank='5'), Card(suit='♦', rank='5'),
        Card(suit='♣', rank='5'),
        # 6: Move 6 spots forward
        Card(suit='♠', rank='6'), Card(suit='♥', rank='6'), Card(suit='♦', rank='6'),
        Card(suit='♣', rank='6'),
        # 7: Move 7 single steps forward
        Card(suit='♠', rank='7'), Card(suit='♥', rank='7'), Card(suit='♦', rank='7'),
        Card(suit='♣', rank='7'),
        # 8: Move 8 spots forward
        Card(suit='♠', rank='8'), Card(suit='♥', rank='8'), Card(suit='♦', rank='8'),
        Card(suit='♣', rank='8'),
        # 9: Move 9 spots forward
        Card(suit='♠', rank='9'), Card(suit='♥', rank='9'), Card(suit='♦', rank='9'),
        Card(suit='♣', rank='9'),
        # 10: Move 10 spots forward
        Card(suit='♠', rank='10'), Card(suit='♥', rank='10'), Card(suit='♦', rank='10'),
        Card(suit='♣', rank='10'),
        # Jake: A marble must be exchanged
        Card(suit='♠', rank='J'), Card(suit='♥', rank='J'), Card(suit='♦', rank='J'),
        Card(suit='♣', rank='J'),
        # Queen: Move 12 spots forward
        Card(suit='♠', rank='Q'), Card(suit='♥', rank='Q'), Card(suit='♦', rank='Q'),
        Card(suit='♣', rank='Q'),
        # King: Start or move 13 spots forward
        Card(suit='♠', rank='K'), Card(suit='♥', rank='K'), Card(suit='♦', rank='K'),
        Card(suit='♣', rank='K'),
        # Ass: Start or move 1 or 11 spots forward
        Card(suit='♠', rank='A'), Card(suit='♥', rank='A'), Card(suit='♦', rank='A'),
        Card(suit='♣', rank='A'),
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
    steps_remaining_for_7: int = 0     # steps remaining for 7 card


class Dog(Game):
    """Dog game implementation"""   
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

         # Track all swap card exchanges
        self.exchanges_done: List[Tuple[int, Card]] = []

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
                    pos = self.KENNEL_POSITIONS[idx][marble_idx],
                    is_save = False)
                player_state.list_marble.append(marble)

            # Add the player state to the game state
            self.state.list_player.append(player_state)

        # Randomly select starting player
        self.state.idx_player_started = random.randint(0, self.state.cnt_player - 1)
        self.state.idx_player_active = self.state.idx_player_started

        # Initialize the state of the card exchange
        self.state.bool_card_exchanged = False

        self.state.phase = GamePhase.RUNNING

        # Deal initial cards for the first round (6 cards per player)
        self.deal_cards(num_cards_per_player=6)

    def set_state(self, state: GameState) -> None:
        """ Set the game to a given state """
        self.state = state
        if (self.state.cnt_round > 1
                and self.state.idx_player_active == self.state.idx_player_started):
            # Rotate idx_player_active based on cnt_round
            self.state.idx_player_active = (
                self.state.idx_player_started + self.state.cnt_round
            ) % self.state.cnt_player


    def get_state(self) -> GameState:
        """ Get the complete, unmasked game state """
        if (self.state.cnt_round > 1
                and self.state.idx_player_active == self.state.idx_player_started):
            self.state.idx_player_active = (
                self.state.idx_player_started + self.state.cnt_round
            ) % self.state.cnt_player
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
        seen_actions: set[tuple[str, str, Optional[int], Optional[int]]] = set()
        action_key: tuple[str, str, Optional[int], Optional[int]]

        active_player_idx = self.state.idx_player_active
        active_player = self.state.list_player[active_player_idx]

        start_position = self.START_POSITION[active_player_idx]

        # Check if the game is in the setup phase
        # ----- check
        if self.state.cnt_round == 0 and not self.state.bool_card_exchanged:
            for card in active_player.list_card:
                action = Action(card=card, pos_from=None, pos_to=None)
                action_key = (card.suit, card.rank, None, None)
                if action_key not in seen_actions:
                    seen_actions.add(action_key)
                    actions.append(action)
            return actions

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
                        action_key = (card.suit, card.rank, marbles_in_kennel[0].pos,
                                      start_position)
                        if action_key not in seen_actions:
                            seen_actions.add(action_key)
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
                            validity = self.check_move_validity(active_player_idx, marble_idx,
                                                                new_marble_pos)
                            if not validity:
                                move_allowed = False
                                break

                        if move_allowed:
                            action = Action(
                                    card = card,
                                    pos_from = marble.pos,
                                    pos_to = new_marble_pos,
                                    card_swap = None
                                )
                            action_key = (card.suit, card.rank, marble.pos, new_marble_pos)
                            if action_key not in seen_actions:
                                seen_actions.add(action_key)
                                actions.append(action)


            # --- Joker ---
            if card.rank == 'JKR':
                # Option 1: Joker als Ass verwenden, um eine Murmel aus dem Kennel zu holen
                marbles_in_kennel = [
                    m for m in active_player.list_marble
                    if m.pos in self.KENNEL_POSITIONS[active_player_idx]
                ]
                start_pos = self.START_POSITION[active_player_idx]

                # Option 2: Joker für 1 bis 13 Felder verwenden
                seen_actions = set()  # Set, um doppelte Aktionen zu vermeiden
                for possible_card in range(1, 14):
                    for marble in active_player.list_marble:
                        if marble.pos not in self.KENNEL_POSITIONS[active_player_idx]:
                            num_moves = possible_card
                            move_allowed = True
                            test_state = self.state.model_copy(deep=True)
                            for _ in range(num_moves):
                                # Berechne die neue Position
                                new_pos = test_state.list_player[active_player_idx].list_marble[marble_idx].pos
                                validity = self.check_move_validity(
                                    active_player_idx, marble_idx, new_pos
                                )
                                if not validity:
                                    move_allowed = False
                                    break

                            if move_allowed:
                                action = Action(
                                    card=Card(suit='', rank=str(possible_card)),
                                    pos_from=marble.pos,
                                    pos_to=test_state.list_player[active_player_idx].list_marble[marble.pos].pos,
                                    card_swap=None
                                )
                                action_key = (card.suit, card.rank, marble.pos, new_pos)
                                if action_key not in seen_actions:
                                    seen_actions.add(action_key)
                                    actions.append(action)

                # Option 3: Tauschaktionen mit Ass und König für jede Farbe
                for suit in self.state.LIST_SUIT:
                    # Tauschen mit einer Ass-Karte (A) - einmal pro Farbe
                    actions.append(
                        Action(
                            card=card,
                            pos_from=None,
                            pos_to=None,
                            card_swap=Card(suit=suit, rank='A')
                        )
                    )
                    # Tauschen mit einer König-Karte (K) - einmal pro Farbe
                    actions.append(
                        Action(
                            card=card,
                            pos_from=None,
                            pos_to=None,
                            card_swap=Card(suit=suit, rank='K')
                        )
                    )

            # --- Ass ---
            if card.rank == 'A':
                for marble_idx, marble in enumerate(active_player.list_marble):
                    if marble.pos not in self.KENNEL_POSITIONS[active_player_idx]:
                        # Move 1 forward
                        pos_to_1 = (marble.pos + 1) % 64
                        if self.check_move_validity(active_player_idx=active_player_idx,
                                                    marble_idx=marble_idx, marble_new_pos=pos_to_1):
                            action = Action(
                                    card=card,
                                    pos_from=marble.pos,
                                    pos_to=pos_to_1,
                                    card_swap=None
                                )
                            action_key = (card.suit, card.rank, marble.pos, pos_to_1)
                            if action_key not in seen_actions:
                                seen_actions.add(action_key)
                                actions.append(action)

                        # Move 11 forward
                        pos_to_11 = (marble.pos + 11) % 64
                        if self.check_move_validity(active_player_idx=active_player_idx,
                                                    marble_idx=marble_idx,
                                                    marble_new_pos=pos_to_11):
                            action = Action(
                                    card=card,
                                    pos_from=marble.pos,
                                    pos_to=pos_to_11,
                                    card_swap=None
                                )
                            action_key = (card.suit, card.rank, marble.pos, pos_to_11)
                            if action_key not in seen_actions:
                                seen_actions.add(action_key)
                                actions.append(action)


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
                            validity = self.check_move_validity(active_player_idx, marble_idx,
                                                                new_marble_pos)
                            if not validity:
                                move_backwards_allowed = False
                                break

                        if move_backwards_allowed:
                            action = Action(
                                    card = card,
                                    pos_from = marble.pos,
                                    pos_to = new_marble_pos,
                                    card_swap = None
                                )
                            action_key = (card.suit, card.rank, marble.pos, new_marble_pos)
                            if action_key not in seen_actions:
                                seen_actions.add(action_key)
                                actions.append(action)


            # --- Jack ---
            if card.rank == 'J':
                idx_player = [active_player_idx]
                idx_other_players = [idx for idx in range(4) if idx != active_player_idx]
                # Generate combinations in both directions
                player_exchange_combinations = [(p1, p2) for p1 in idx_player
                                                for p2 in idx_other_players]

                for combination in player_exchange_combinations:
                    for first_marble in self.state.list_player[combination[0]].list_marble:
                        if (first_marble.pos not in self.KENNEL_POSITIONS[combination[0]]
                                and first_marble.pos not in self.FINISH_POSITIONS[combination[0]]):
                            for other_marble in self.state.list_player[combination[1]].list_marble:
                                if (other_marble.pos not in self.KENNEL_POSITIONS[combination[1]]
                                    and other_marble.pos
                                        not in self.FINISH_POSITIONS[combination[1]]
                                        and not other_marble.is_save):
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
                    my_player_idx = active_player_idx
                    # Filter marbles that are on the board (not in kennel/finish)
                    my_marbles = [m for m in self.state.list_player[my_player_idx].list_marble
                                if m.pos not in self.KENNEL_POSITIONS[my_player_idx]
                                and m.pos not in self.FINISH_POSITIONS[my_player_idx]]

                    # Generate only swaps between distinct marbles
                    for marble_i, marble_j in combinations(my_marbles, 2):
                        actions.append(
                            Action(card=card, pos_from=marble_i.pos,
                                   pos_to=marble_j.pos, card_swap=None)
                        )
                        actions.append(
                            Action(card=card, pos_from=marble_j.pos,
                                   pos_to=marble_i.pos, card_swap=None)
                        )

        return actions

    def deal_cards(self, num_cards_per_player: int) -> None:
        """Deal a specified number of cards to each player."""
        total_cards_to_deal = num_cards_per_player * self.state.cnt_player

        # Clear players' hands before dealing new cards
        for player_state in self.state.list_player:
            player_state.list_card.clear()

        if not self.state.list_card_draw:
            # Reshuffle the deck if it is empty
            self.state.list_card_draw = GameState.LIST_CARD.copy()
            self.state.list_card_discard.clear()
            random.shuffle(self.state.list_card_draw)

        # Get list of indices of player in order of card dealing
        player_indices = (list(range(self.state.idx_player_active, self.state.cnt_player)) +
                          list(range(0, self.state.idx_player_active)))

        # Deal the cards to each player
        for _ in range(num_cards_per_player):
            for idx in player_indices:
                card = self.state.list_card_draw.pop()  # Pop a card from the deck
                self.state.list_player[idx].list_card.append(card)

                if not self.state.list_card_draw:
                    # Reshuffle the deck if it is empty
                    self.state.list_card_draw = GameState.LIST_CARD.copy()
                    self.state.list_card_discard.clear()
                    random.shuffle(self.state.list_card_draw)


    def start_new_round(self) -> None:
        """ Begin a new round by reshuffling and distributing cards. """
        # Increment round number
        self.state.cnt_round += 1
        num_cards_per_player = 7 - ((self.state.cnt_round - 1) % 5 + 1)

        # Have the next player start the round
        self.state.idx_player_started = (self.state.idx_player_started + 1) % self.state.cnt_player
        self.state.idx_player_active = self.state.idx_player_started

        # Deal the correct number of cards to each player for the current round
        self.deal_cards(num_cards_per_player)

        # Reset the exchange state and set active player
        self.state.bool_card_exchanged = False

        # Set the game phase to RUNNING
        self.state.phase = GamePhase.RUNNING

    def apply_action(self, action: Action) -> None:
        """Apply the given action to the game."""
        active_player_index = self.state.idx_player_active

        # Handle the case where action is None (start a new round). No player can do anything anymore.
        if action is None:
            # Add the player's cards to the discard pile
            for card in self.state.list_player[active_player_index].list_card:
                self.state.list_card_discard.append(card)

            # Clear the player's hand
            self.state.list_player[active_player_index].list_card.clear()

            # Change the active player
            self.state.idx_player_active = (self.state.idx_player_active + 1) % self.state.cnt_player

            # Check if all players have played all their cards
            if (all(players.list_card == [] for players in self.state.list_player) and
                    self.state.idx_player_active == self.state.idx_player_started):
                self.start_new_round()
            return

        # Handle card exchange at the beginning of the game
        if (action.pos_from is None and action.pos_to is None and
                action.card_swap is None and not self.state.bool_card_exchanged):
            # Find the player who currently owns the card
            card_owner_idx = self.state.idx_player_active

            # Determine the partner's index
            partner_idx = (card_owner_idx + 2) % self.state.cnt_player

            # Perform the card exchange
            self.state.list_player[card_owner_idx].list_card.remove(action.card)
            self.state.list_player[partner_idx].list_card.append(action.card)

            # Record the exchange
            self.exchanges_done.append((card_owner_idx, action.card))

            # Check if all players have exchanged cards
            if len(self.exchanges_done) == self.state.cnt_player:
                self.state.bool_card_exchanged = True

            # Change the active player
            self.state.idx_player_active = (self.state.idx_player_active + 1) % self.state.cnt_player

            return

        # Handle special actions (e.g., swaps or specific card ranks)
        if action.card.rank == 'J':
            # Swap two marbles
            marble_from = None
            marble_to = None

            for p_idx, player in enumerate(self.state.list_player):
                for m_idx, m in enumerate(player.list_marble):
                    if m.pos == action.pos_from:
                        marble_from = m
                    if m.pos == action.pos_to:
                        marble_to = m

            if marble_from and marble_to:
                marble_from.pos, marble_to.pos = marble_to.pos, marble_from.pos
            else:
                raise ValueError("Invalid marble positions for swapping.")

        # Normal card play
        elif action.pos_from is not None and action.pos_to is not None:
            # Handle marble movement
            for idx_marble, marble in enumerate(self.state.list_player[active_player_index].list_marble):
                if marble.pos == action.pos_from:
                    # Check if destination is occupied
                    for p_idx, player in enumerate(self.state.list_player):
                        for m_idx, m in enumerate(player.list_marble):
                            if m.pos == action.pos_to:
                                # Send occupant marble home
                                m.pos = self.KENNEL_POSITIONS[p_idx][0]
                                m.is_save = False

                    # Move the marble
                    marble.pos = action.pos_to

                    # Check if the marble is leaving the kennel
                    if action.pos_from in self.KENNEL_POSITIONS[active_player_index]:
                        marble.is_save = True

        # Handle card swapping
        if action.card_swap is not None:
            pass

        # Move played card to discard pile
        if action.card in self.state.list_player[active_player_index].list_card:
            self.state.list_player[active_player_index].list_card.remove(action.card)
            self.state.list_card_discard.append(action.card)

        # Change the active player
        self.state.idx_player_active = (self.state.idx_player_active + 1) % self.state.cnt_player


    def get_player_view(self, idx_player: int) -> GameState:
        """ Get the masked state for the active player (e.g. the opponent's cards are face down)"""
        player_view = self.state.model_copy(deep = True)
        return player_view

    def check_move_validity(self, active_player_idx: int, marble_idx: int,
                             marble_new_pos: int) -> bool:
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

    def can_move_steps(self, player_idx: int, marble_idx: int,
                       steps: int, direction: int = 1) -> bool:
        """simulate step-by-step move in a copy"""
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
        """Simplified final pos calculation:"""
        if start_pos < 64:
            # normal circle
            return (start_pos + steps) % 64
        # finish or kennel
        finish_positions = self.FINISH_POSITIONS[player_idx]
        finish_pos = start_pos + steps
        finish_pos = min(finish_pos, finish_positions[-1])
        return finish_pos

    def send_home_if_passed(self, pos: int, active_player_idx: int) -> None:
        """ Check if a marble is overtaken and send it home """
        # If a marble is found at 'pos', send it home (unless it's the moved marble itself)
        for p_idx, player in enumerate(self.state.list_player):
            for m_idx, m in enumerate(player.list_marble):
                if m.pos == pos and not (p_idx == active_player_idx and
                                         m.is_save and m.pos == self.START_POSITION[p_idx]):
                    # The marble that got overtaken goes to its kennel
                    if not (p_idx == active_player_idx and
                            self.is_marble_protecting_start(p_idx, m_idx)):
                        # Overtaken marble goes home
                        m.pos = self.KENNEL_POSITIONS[p_idx][0]
                        m.is_save = False

    def is_marble_protecting_start(self, player_idx: int, marble_idx: int) -> bool:
        """If a marble is at start position and is safe, it protects it"""
        marble = self.state.list_player[player_idx].list_marble[marble_idx]
        return marble.is_save and marble.pos == self.START_POSITION[player_idx]


class RandomPlayer(Player):
    """Random player that selects actions randomly"""

    def select_action(self, state: GameState, actions: List[Action]) -> Optional[Action]:
        """Given masked game state and possible actions, select the next action"""
        if len(actions) > 0:
            return random.choice(actions)
        return None

    def get_player_type(self) -> str:
        """Returns the player type."""
        return "Random"


if __name__ == '__main__':

    game = Dog()
