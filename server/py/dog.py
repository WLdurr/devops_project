# pylint: disable=too-many-lines

''' This Code implement the game brandy dog'''
from typing import List, Optional, ClassVar, Tuple, Set
from enum import Enum
import random
from itertools import combinations
from dataclasses import dataclass
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

@dataclass
class ActionData:
    card: 'Card'
    pos_from: Optional[int]
    pos_to: Optional[int]


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
    steps_remaining_for_7: int = 7     # steps remaining for 7 card


class Dog(Game):
    KENNEL_POSITIONS = [
        [64, 65, 66, 67],   # Positions for player index 0
        [72, 73, 74, 75],   # Positions for player index 1
        [80, 81, 82, 83],   # Positions for player index 2
        [88, 89, 90, 91]    # Positions for player index 3
    ]

    # Define starting positions for each player
    START_POSITION = [0, 16, 32, 48]

    #Define Finish Position
    FINISH_POSITIONS = [
        [68, 69, 70, 71],  #  Positions for player index 0
        [76, 77, 78, 79],  #  Positions for player index 1
        [84, 85, 86, 87],  #  Positions for player index 2
        [92, 93, 94, 95],  #  Positions for player index 3
    ]

    def __init__(self) -> None:
        """ Game initialization (set_state call not necessary, we expect 4 players) """
        # Initialize the game state
        self.out_of_cards_counter:int = 0
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
        self.original_state_before_7: Optional[GameState] = None

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
        print(f"Phase: {self.state.phase}, Round: {self.state.cnt_round}")
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
        active_player_idx = self.state.idx_player_active
        start_position = self.START_POSITION[active_player_idx]

        # Handle actions for a 7 card with remaining steps
        if self._has_active_seven_card():
            return self._get_actions_for_seven_card(
                actions, seen_actions, active_player_idx,
            )

        # Handle setup phase actions
        if self._is_setup_phase():
            return self._get_setup_phase_actions(actions, seen_actions, self.state.list_player[active_player_idx])

        # Handle starting position logic
        if not self._is_start_position_occupied(active_player_idx):
            self._add_start_position_actions(
                actions, seen_actions, active_player_idx, start_position
            )

        # Handle card-specific actions
        if self.state.card_active is None:
            # If no card is active, the player can choose from any card in their hand
            possible_cards = self.state.list_player[active_player_idx].list_card
        else:
            # If there is an active card, restrict possible actions to this card
            possible_cards = [self.state.card_active]
        for card in possible_cards:
            self._handle_card_actions(
                actions, seen_actions, active_player_idx, card
            )

        partner_idx = (active_player_idx + 2) % self.state.cnt_player
        # Check if all marbles of the active player are in the finish
        marbles_finished = all(
            marble.pos in self.FINISH_POSITIONS[active_player_idx]
            for marble in self.state.list_player[active_player_idx].list_marble
        )

        # Allow actions for the partner's marbles if marbles are finished
        if marbles_finished:
            partner_idx = (active_player_idx + 2) % self.state.cnt_player  # Partner's index
            partner = self.state.list_player[partner_idx]

            # Generate actions for partner's marbles using the active player's card
            for card in self.state.list_player[active_player_idx].list_card:  # Use active player's cards for partner
                for marble_idx, marble in enumerate(partner.list_marble):
                    if marble.pos not in self.KENNEL_POSITIONS[partner_idx]:  # Partner's valid marbles
                        # Compute possible destinations
                        pos_to = self.compute_final_position(marble.pos, int(card.rank), partner_idx)
                        if self.check_move_validity(partner_idx, marble_idx, pos_to):
                            action_data = ActionData(card=card, pos_from=marble.pos, pos_to=pos_to)
                            self._add_unique_action(actions, seen_actions, action_data)

        return actions

    def apply_action(self, action: Action) -> None:
        """Apply the given action to the game."""
        active_player_index = self.state.idx_player_active

        if action is None:
            self._handle_no_action(active_player_index)
            return

        if self._is_card_exchange_action(action):
            self._handle_card_exchange(action)
            return

        if action.card.rank == "J":
            self._handle_jack_action(action)
        elif action.card.rank == "7":
            self._handle_seven_action(action, active_player_index)
            return
        elif action.card.rank == "JKR":
            self.state.card_active = action.card_swap
            if action.card in self.state.list_player[active_player_index].list_card:
                self.state.list_player[active_player_index].list_card.remove(action.card)
            return

        elif action.pos_from is not None and action.pos_to is not None:
            self._handle_normal_move(action, active_player_index)

        if action.card_swap is not None:
            self._handle_card_swap(action)

        # Move the played card to discard (if not part of a sequence)
        if self.state.card_active is None or self.state.card_active.rank != "7":
            self._move_card_to_discard(action, active_player_index)

        # Change active player unless in a 7 sequence
        if self.state.card_active is None:
            self._change_active_player()

        # Check if the game is finished
        self._check_game_finished()

    def get_player_view(self, idx_player: int) -> GameState:
        """ Get the masked state for the active player (e.g. the opponent's cards are face down)"""
        player_view = self.state.model_copy(deep = True)
        return player_view

    def check_move_validity(self, active_player_idx: int, marble_idx: int,
                             marble_new_pos: int) -> bool:
        """ Check if move is valid """
        marble = self.state.list_player[active_player_idx].list_marble[marble_idx]

        # check if the new position of the marble is occupied by another marble, that is safe or in the Finish
        for player_idx, player in enumerate(self.state.list_player):
            for other_marble_idx, other_marble in enumerate(player.list_marble):
                if other_marble.pos == marble_new_pos:
                    if (not (player_idx == active_player_idx and other_marble_idx == marble_idx)
                            and other_marble.is_save):
                        return False
                    if (not other_marble_idx == marble_idx) and marble_new_pos >= 68:
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
            for m_idx, marble in enumerate(player.list_marble):
                if marble.pos == pos:
                    # If it's the player's own marble
                    if p_idx == active_player_idx:
                        # Send home unless it is protecting the start
                        if not self.is_marble_protecting_start(p_idx, m_idx):
                            marble.pos = self.KENNEL_POSITIONS[p_idx][0]
                            marble.is_save = False
                    else:
                        # If it's an opponent's marble
                        marble.pos = self.KENNEL_POSITIONS[p_idx][0]
                        marble.is_save = False

    def is_marble_protecting_start(self, player_idx: int, marble_idx: int) -> bool:
        """If a marble is at start position and is safe, it protects it"""
        marble = self.state.list_player[player_idx].list_marble[marble_idx]
        return marble.is_save and marble.pos == self.START_POSITION[player_idx]

    def _get_actions_for_seven_card(self, actions: List['Action'],
            seen_actions: Set[Tuple[str, str, Optional[int], Optional[int]]],
            active_player_idx: int) -> List['Action']:
        """Generate actions for a 7 card."""
        card = self.state.card_active
        if not card:  # Ensure card is not None for mypy
            return actions

        for marble_idx, marble in enumerate(self.state.list_player[active_player_idx].list_marble):
            if (marble.pos not in self.KENNEL_POSITIONS[active_player_idx] and
                    marble.pos != self.FINISH_POSITIONS[active_player_idx][3]):
                for steps_to_move in range(1, self.state.steps_remaining_for_7 + 1):
                    des_dest = self._can_move_forward(active_player_idx, marble_idx, marble, steps_to_move)
                    if des_dest != -1:
                        action_data = ActionData(card=card, pos_from=marble.pos, pos_to=des_dest)
                        self._add_unique_action(actions, seen_actions, action_data)
        return actions

    def calculate_7_steps(self, pos_from: int | None, pos_to: int | None) -> int:
        """Calculate the number of steps for a 7 card move"""
        if pos_from is None or pos_to is None:
            raise ValueError("pos_from and pos_to must not be None")
        # if both positions are on the circular board (0-63)
        if pos_from < 64 and pos_to < 64:
            # normal circle move
            return (pos_to - pos_from + 64) % 64

        # if we move from the circle into the finish
        if pos_from < 64 <= pos_to:
            return ((pos_to - self.FINISH_POSITIONS[self.state.idx_player_active][0] + 1) +
                    (self.START_POSITION[self.state.idx_player_active] + 64 - pos_from)% 64)

        if pos_from >= 64 and pos_to >= 64:
            return abs(pos_to - pos_from)

        return 0

    def _has_active_seven_card(self) -> bool:
        """Check if the active card is a 7 with remaining steps."""
        return (
            self.state.card_active is not None
            and self.state.card_active.rank == '7'
            and self.state.steps_remaining_for_7 > 0
        )

    def _add_unique_action(self, actions: List['Action'],
                           seen_actions: Set[Tuple[str, str, Optional[int], Optional[int]]],
                           action_data: ActionData) -> None:
        """Add an action to the list if it's unique."""
        action_key = (action_data.card.suit, action_data.card.rank, action_data.pos_from, action_data.pos_to)
        if action_key not in seen_actions:
            seen_actions.add(action_key)
            actions.append(
                Action(
                    card=action_data.card,
                    pos_from=action_data.pos_from,
                    pos_to=action_data.pos_to,
                    card_swap=None,
                )
            )

    def _is_setup_phase(self) -> bool:
        """Check if the game is in the setup phase."""
        return self.state.cnt_round == 0 and not self.state.bool_card_exchanged

    def _get_setup_phase_actions(
        self,
        actions: List['Action'],
        seen_actions: Set[Tuple[str, str, Optional[int], Optional[int]]],
        active_player: 'PlayerState',
    ) -> List['Action']:
        """Generate actions for the setup phase."""
        for card in active_player.list_card:
            action_data = ActionData(card=card, pos_from=None, pos_to=None)
            self._add_unique_action(actions, seen_actions, action_data)
        return actions

    def _is_start_position_occupied(self, active_player_idx: int) -> bool:
        """Check if the start position is occupied."""
        start_position: int = self.START_POSITION[active_player_idx]
        return any(
            marble.pos == start_position
            for marble in self.state.list_player[active_player_idx].list_marble
        )

    def _add_start_position_actions(
        self,
        actions: List['Action'],
        seen_actions: Set[Tuple[str, str, Optional[int], Optional[int]]],
        active_player_idx: int,
        start_position: int
    ) -> None:
        """Add actions for moving a marble to the start position."""
        marbles_in_kennel = [
            marble
            for marble in self.state.list_player[active_player_idx].list_marble
            if marble.pos in self.KENNEL_POSITIONS[active_player_idx]
        ]
        marbles_in_kennel.sort(key=lambda x: x.pos)

        if self.state.card_active is None:
            # If no card is active, the player can choose from any card in their hand
            possible_cards = self.state.list_player[active_player_idx].list_card
        else:
            # If there is an active card, restrict possible actions to this card
            possible_cards = [self.state.card_active]

        for card in possible_cards:
            if card.rank in ['K', 'A', 'JKR'] and marbles_in_kennel:
                action_data = ActionData(
                    card=card,
                    pos_from=marbles_in_kennel[0].pos,
                    pos_to=start_position
                )
                self._add_unique_action(actions, seen_actions, action_data)

    def _handle_card_actions(
        self,
        actions: List['Action'],
        seen_actions: Set[Tuple[str, str, Optional[int], Optional[int]]],
        active_player_idx: int,
        card: 'Card',
    ) -> None:
        """Handle possible actions for a specific card."""
        if card.rank == 'JKR':
            self._handle_joker(actions, seen_actions, active_player_idx, card)
        elif card.rank == 'A':
            self._handle_ace(actions, seen_actions, active_player_idx, card)
            self._handle_normal_card(actions, seen_actions, active_player_idx, card)
        elif card.rank == '4':
            self._handle_four(actions, seen_actions, active_player_idx, card)
            self._handle_normal_card(actions, seen_actions, active_player_idx, card)
        elif card.rank == 'J':
            self._handle_jack(actions, active_player_idx, card)
        elif card.rank == '7':
            self._handle_seven(actions, seen_actions, active_player_idx, card)
        else:
            self._handle_normal_card(actions, seen_actions, active_player_idx, card)

    def _handle_normal_card(
        self,
        actions: List['Action'],
        seen_actions: Set[Tuple[str, str, Optional[int], Optional[int]]],
        active_player_idx: int,
        card: 'Card',
    ) -> None:
        """Handle actions for "normal" cards (e.g., numbered cards)."""
        num_moves = (
            13 if card.rank == 'K' else
            12 if card.rank == 'Q' else
            11 if card.rank == 'A' else
            int(card.rank)
        )
        for marble_idx, marble in enumerate(self.state.list_player[active_player_idx].list_marble):
            if marble.pos in self.KENNEL_POSITIONS[active_player_idx]:
                continue
            new_marble_pos = self._can_move_forward(active_player_idx, marble_idx, marble, num_moves)
            if new_marble_pos != -1:
                action_data = ActionData(card=card, pos_from=marble.pos, pos_to=new_marble_pos)
                self._add_action(actions, seen_actions, action_data)

    def _handle_joker(
            self,
            actions: List['Action'],
            seen_actions: Set[Tuple[str, str, Optional[int], Optional[int]]],
            active_player_idx: int,
            card: 'Card',
    ) -> None:
        """Handle actions for the Joker card."""
        self._use_joker_to_exit_kennel(actions, seen_actions, active_player_idx, card)
        self._use_joker_for_steps(actions, card)
        self._use_joker_as_jack(actions, active_player_idx, card)

    def _use_joker_to_exit_kennel(
            self,
            actions: List['Action'],
            seen_actions: Set[Tuple[str, str, Optional[int], Optional[int]]],
            active_player_idx: int,
            card: 'Card',
    ) -> None:
        """Use Joker to get out of the kennel."""
        marbles_in_kennel = [
            marble
            for marble in self.state.list_player[active_player_idx].list_marble
            if marble.pos in self.KENNEL_POSITIONS[active_player_idx]
        ]
        if marbles_in_kennel and not self._is_start_position_occupied(active_player_idx):
            marble = marbles_in_kennel[0]
            action_data = ActionData(
                card=card,
                pos_from=marble.pos,
                pos_to=self.START_POSITION[active_player_idx],
            )
            self._add_action(actions, seen_actions, action_data)
            for suit in self.state.LIST_SUIT:
                for rank in ['A', 'K']:
                    actions.append(
                        Action(
                            card=card,
                            pos_from=None,
                            pos_to=None,
                            card_swap=Card(suit=suit, rank=rank),
                        )
                    )

    def _use_joker_for_steps(
            self,
            actions: List['Action'],
            card: 'Card'
    ) -> None:
        """Use Joker to move between 1 and 13 steps."""
        for possible_card in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 13]:
            self._handle_joker_moves(actions, card, possible_card)

    def _use_joker_as_jack(
            self,
            actions: List['Action'],
            active_player_idx: int,
            card: 'Card'
    ) -> None:
        """Use Joker as Jack."""
        idx_other_players = [idx for idx in range(4) if idx != active_player_idx]
        exchange_possible = False

        for p1 in [active_player_idx]:
            for p2 in idx_other_players:
                if self._can_exchange_marbles(p1, p2):
                    exchange_possible = True

        if exchange_possible or not actions:
            for suit in self.state.LIST_SUIT:
                actions.append(
                    Action(
                        card=card,
                        pos_from=None,
                        pos_to=None,
                        card_swap=Card(suit=suit, rank="J"),
                    )
                )

    def _can_exchange_marbles(self, player1_idx: int, player2_idx: int) -> bool:
        """Check if marbles can be exchanged between two players."""
        for first_marble in self.state.list_player[player1_idx].list_marble:
            if first_marble.pos not in self.KENNEL_POSITIONS[player1_idx] and first_marble.pos not in \
                    self.FINISH_POSITIONS[player1_idx]:
                for other_marble in self.state.list_player[player2_idx].list_marble:
                    if other_marble.pos not in self.KENNEL_POSITIONS[player2_idx] and other_marble.pos not in \
                            self.FINISH_POSITIONS[player2_idx] and not other_marble.is_save:
                        return True
        return False

    def _handle_joker_moves(
        self,
        actions: List['Action'],
        card: 'Card',
        steps_to_move: int,
    ) -> None:
        """Handle moves for the Joker card."""
        active_player_idx = self.state.idx_player_active
        marbles = self.state.list_player[active_player_idx].list_marble
        joker_move_possible = False
        for marble_idx, marble in enumerate(marbles):
            if not marble.pos in self.KENNEL_POSITIONS[active_player_idx]:
                new_marble_pos = self._can_move_forward(active_player_idx, marble_idx, marble, steps_to_move)
                if new_marble_pos != -1:
                    joker_move_possible = True

        if joker_move_possible:
            for suit in self.state.LIST_SUIT:
                if steps_to_move == 1:
                    actions.append(
                        Action(
                            card=card,
                            pos_from=None,
                            pos_to=None,
                            card_swap=Card(suit=suit, rank='A'),
                        )
                    )
                elif steps_to_move == 12:
                    actions.append(
                        Action(
                            card=card,
                            pos_from=None,
                            pos_to=None,
                            card_swap=Card(suit=suit, rank='Q'),
                        )
                    )
                elif steps_to_move == 13:
                    actions.append(
                        Action(
                            card=card,
                            pos_from=None,
                            pos_to=None,
                            card_swap=Card(suit=suit, rank='K'),
                        )
                    )
                else:
                    actions.append(
                        Action(
                            card=card,
                            pos_from=None,
                            pos_to=None,
                            card_swap=Card(suit=suit, rank=str(steps_to_move)),
                        )
                    )

    def _add_action(
        self,
        actions: List['Action'],
        seen_actions: Set[Tuple[str, str, Optional[int], Optional[int]]],
        action_data: ActionData,
    ) -> None:
        """Add an action to the list if it is unique."""
        action_key = (action_data.card.suit, action_data.card.rank, action_data.pos_from, action_data.pos_to)
        if action_key not in seen_actions:
            seen_actions.add(action_key)
            actions.append(
                Action(
                    card=action_data.card,
                    pos_from=action_data.pos_from,
                    pos_to=action_data.pos_to,
                    card_swap=None,
                )
            )

    def _can_move_forward(
        self, active_player_idx: int, marble_idx: int, marble: Marble, num_moves: int
    ) -> int:
        """Check if a marble can move forward the specified number of steps."""
        new_pos = marble.pos
        for _ in range(num_moves):
            if new_pos == self.START_POSITION[active_player_idx] and not marble.is_save:
                new_pos = 64 + active_player_idx * 8 + 4
            elif new_pos < 64:
                new_pos = (new_pos + 1) % 64
            else:
                new_pos = new_pos + 1
            if not self.check_move_validity(active_player_idx, marble_idx, new_pos):
                return -1
        return new_pos

    def _handle_ace(
        self,
        actions: List['Action'],
        seen_actions: Set[Tuple[str, str, Optional[int], Optional[int]]],
        active_player_idx: int,
        card: 'Card',
    ) -> None:
        """Handle actions for the Ace card."""
        for marble_idx, marble in enumerate(self.state.list_player[active_player_idx].list_marble):
            if marble.pos in self.KENNEL_POSITIONS[active_player_idx]:
                continue  # Skip marbles in the kennel

            # Move forward 1 step, move 11 is handled in _handle_normal_card
            if marble.pos == self.START_POSITION[active_player_idx] and not marble.is_save:
                pos_to_1 = 64 + active_player_idx * 8 + 4
            elif marble.pos < 64:
                pos_to_1 = (marble.pos + 1) % 64
            else:
                pos_to_1 = marble.pos + 1
            if self.check_move_validity(active_player_idx, marble_idx, pos_to_1):
                action_data = ActionData(card=card, pos_from=marble.pos, pos_to=pos_to_1)
                self._add_action(actions, seen_actions, action_data)

    def _handle_four(
        self,
        actions: List['Action'],
        seen_actions: Set[Tuple[str, str, Optional[int], Optional[int]]],
        active_player_idx: int,
        card: 'Card',
    ) -> None:
        """Handle action of moving backwards for the Four card."""
        for marble_idx, marble in enumerate(self.state.list_player[active_player_idx].list_marble):
            if (marble.pos in self.KENNEL_POSITIONS[active_player_idx] or
                marble.pos in self.FINISH_POSITIONS[active_player_idx]):
                continue  # Skip marbles in the kennel or finish

            new_marble_pos = marble.pos
            move_backwards_allowed = True

            for _ in range(4):  # Try moving backwards step by step
                new_marble_pos = (new_marble_pos - 1 + 64) % 64
                if not self.check_move_validity(active_player_idx, marble_idx, new_marble_pos):
                    move_backwards_allowed = False
                    break

            if move_backwards_allowed:
                action_data = ActionData(card=card, pos_from=marble.pos, pos_to=new_marble_pos)
                self._add_action(actions, seen_actions, action_data)

    def _handle_jack(
        self,
        actions: List['Action'],
        active_player_idx: int,
        card: 'Card',
    ) -> None:
        """Handle actions for the Jack card."""
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
                                Action(card = card, pos_from = first_marble.pos,
                                    pos_to = other_marble.pos, card_swap = None)
                            )
                            actions.append(
                                Action(card = card, pos_from = other_marble.pos,
                                    pos_to = first_marble.pos, card_swap = None)
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

    def _handle_seven(
        self,
        actions: List['Action'],
        seen_actions: Set[Tuple[str, str, Optional[int], Optional[int]]],
        active_player_idx: int,
        card: 'Card',
    ) -> None:
        """Handle actions for the Seven card."""
        for marble_idx, marble in enumerate(self.state.list_player[active_player_idx].list_marble):
            if marble.pos >= 64:
                continue  # Skip marbles not on the board

            for steps_to_move in range(1, 8):  # Try moving between 1 and 7 steps
                if self.can_move_steps(active_player_idx, marble_idx, steps_to_move, direction=1):
                    new_marble_pos = (marble.pos + steps_to_move) % 64
                    action_data = ActionData(card=card, pos_from=marble.pos, pos_to=new_marble_pos)
                    self._add_action(actions, seen_actions, action_data)

    def deal_cards(self, num_cards_per_player: int) -> None:
        """Deal a specified number of cards to each player."""
        # total_cards_to_deal = num_cards_per_player * self.state.cnt_player

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

    def _handle_no_action(self, active_player_index: int) -> None:
        """Handle the case where no action is taken."""
        if (
            self.state.card_active is not None
            and self.state.card_active.rank == "7"
            and self.state.steps_remaining_for_7 > 0
        ):
            if self.original_state_before_7 is not None:
                self.state = self.original_state_before_7
            self.original_state_before_7 = None
            return

        # Discard player's cards and prepare for the next player
        self.state.list_card_discard.extend(
            self.state.list_player[active_player_index].list_card
        )
        self.state.list_player[active_player_index].list_card.clear()
        self.out_of_cards_counter += 1

        self._change_active_player()

        # Start a new round if all players are out of cards
        if all(not player.list_card for player in self.state.list_player) and self.out_of_cards_counter == 4:
            self.out_of_cards_counter = 0
            self.start_new_round()

    def _change_active_player(self) -> None:
        """Advance to the next active player."""
        self.state.idx_player_active = (self.state.idx_player_active + 1) % self.state.cnt_player

    def _handle_card_exchange(self, action: Action) -> None:
        """Handle card exchange at the beginning of the game."""
        card_owner_idx = self.state.idx_player_active
        partner_idx = (card_owner_idx + 2) % self.state.cnt_player
        self.state.list_player[card_owner_idx].list_card.remove(action.card)
        self.state.list_player[partner_idx].list_card.append(action.card)
        self.exchanges_done.append((card_owner_idx, action.card))

        # Mark card exchange as complete if all players have exchanged
        if len(self.exchanges_done) == self.state.cnt_player:
            self.state.bool_card_exchanged = True

        self._change_active_player()

    def _is_card_exchange_action(self, action: Action) -> bool:
        """Check if the action is a card exchange action at the beginning of the game."""
        return (
            action.pos_from is None
            and action.pos_to is None
            and action.card_swap is None
            and not self.state.bool_card_exchanged
        )

    def _handle_jack_action(self, action: Action) -> None:
        """Handle swapping of marbles for a Jack card."""
        marble_from, marble_to = None, None

        for player in self.state.list_player:
            for marble in player.list_marble:
                if marble.pos == action.pos_from:
                    marble_from = marble
                if marble.pos == action.pos_to:
                    marble_to = marble

        if marble_from and marble_to:
            marble_from.pos, marble_to.pos = marble_to.pos, marble_from.pos
        else:
            raise ValueError("Invalid marble positions for swapping.")

    def _handle_normal_move(self, action: Action, active_player_index: int) -> None:
        """Handle a normal card move."""
        moved = False
        possible_owners = [active_player_index, (active_player_index + 2) % self.state.cnt_player]

        for owner_idx in possible_owners:
            for marble in self.state.list_player[owner_idx].list_marble:
                if marble.pos == action.pos_from:
                    if action.pos_to is not None:
                        self._move_marble(marble, action.pos_to, owner_idx)
                    moved = True
                    break
            if moved:
                break

    def _move_marble(
        self, marble: Marble, pos_to: int, marble_owner_idx: int
    ) -> None:
        """Move a marble to a new position."""
        # Handle collisions
        for player_idx, player in enumerate(self.state.list_player):
            for other_marble in player.list_marble:
                if other_marble.pos == pos_to:
                    other_marble.pos = self.KENNEL_POSITIONS[player_idx][0]
                    other_marble.is_save = False

        marble.pos = pos_to
        # Only set is_save = True if the marble lands on its own start position
        if pos_to == self.START_POSITION[marble_owner_idx]:
            marble.is_save = True
        else:
            marble.is_save = False

    def _move_card_to_discard(self, action: Action, active_player_index: int) -> None:
        """Move the played card to the discard pile."""
        if action.card in self.state.list_player[active_player_index].list_card:
            self.state.list_player[active_player_index].list_card.remove(action.card)
            self.state.list_card_discard.append(action.card)

    def _handle_card_swap(self, action: Action) -> None:
        """Handle swapping of a card (e.g., Joker with Ace or King)."""
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

    def _handle_seven_action(self, action: Action, active_player_index: int) -> None:
        """Handle a 7 card action."""
        if self.state.card_active is None or self.state.steps_remaining_for_7 == 7:
            # Starting a new 7-sequence: backup the current state
            self.original_state_before_7 = self.state.model_copy(deep=True)
            self.state.card_active = action.card
            self.state.steps_remaining_for_7 = 7

        # Ensure only the same 7 card can be used
        if (
            self.state.card_active.suit != action.card.suit
            or self.state.card_active.rank != action.card.rank
        ):
            raise ValueError("Only actions with the same 7 card are allowed until the sequence ends.")

        # Validate move and calculate steps moved
        steps_moved = self.calculate_7_steps(action.pos_from, action.pos_to)
        if steps_moved <= 0 or steps_moved > self.state.steps_remaining_for_7:
            raise ValueError("Invalid number of steps for this 7-move action.")

        # Apply the movement
        marble_moved = False
        for marble in self.state.list_player[active_player_index].list_marble:
            if marble.pos == action.pos_from:
                # Handle each intermediate step
                for step in range(1, steps_moved + 1):
                    intermediate_pos = (marble.pos + step) % 64
                    self.send_home_if_passed(intermediate_pos, active_player_index)

                # Move the marble to its final position
                marble.pos = action.pos_to if action.pos_to is not None else 0
                marble_moved = True
                break

        if not marble_moved:
            raise ValueError("No marble found at the specified pos_from.")

        # Decrease steps remaining
        self.state.steps_remaining_for_7 -= steps_moved

        if self.state.steps_remaining_for_7 == 0:
            # End the 7-sequence
            self._end_seven_sequence(action, active_player_index)

    def _end_seven_sequence(self, action: Action, active_player_index: int) -> None:
        """End a 7 card sequence by discarding the card and resetting the state."""
        # Discard the 7 card
        if action.card in self.state.list_player[active_player_index].list_card:
            self.state.list_player[active_player_index].list_card.remove(action.card)
            self.state.list_card_discard.append(action.card)

        # Reset the state and move to the next player
        self.state.card_active = None
        self.original_state_before_7 = None
        self._change_active_player()

    def _check_game_finished(self) -> None:
        """Check if the game is finished by verifying all marbles are in the finish."""
        teams = [
            [0, 2],  # Team 1: Player 0 and Player 2
            [1, 3]   # Team 2: Player 1 and Player 3
        ]

        for team in teams:
            for player_idx in team:
                # Check if all marbles of the team are in their respective finish positions
                team_finished = all(
                    marble.pos in self.FINISH_POSITIONS[player_idx]
                    for player_idx in team
                    for marble in self.state.list_player[player_idx].list_marble
                )

                if team_finished:
                    self.state.phase = GamePhase.FINISHED
                    return  # Stop checking once a team finishes


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
