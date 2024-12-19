from typing import List, Optional
from enum import Enum
import random
from dataclasses import dataclass
from server.py.game import Game, Player



class ActionType(str, Enum):
    SET_SHIP = 'set_ship'
    SHOOT = 'shoot'

@dataclass
class BattleshipAction:
    action_type: ActionType
    ship_name: Optional[str]  # Only for SET_SHIP actions
    location: List[str]


@dataclass
class Ship:
    name: str
    length: int
    location: Optional[List[str]] = None


@dataclass
class PlayerState:
    name: str
    ships: List[Ship]
    shots: List[str]
    successful_shots: List[str]


class GamePhase(str, Enum):
    SETUP = 'setup'            # before the game has started (including setting ships)
    RUNNING = 'running'        # while the game is running (shooting)
    FINISHED = 'finished'      # when the game is finished


@dataclass
class BattleshipGameState:
    idx_player_active: int
    phase: GamePhase
    winner: Optional[int]
    players: List[PlayerState]

class Battleship(Game):

    def __init__(self) -> None:
        """ Game initialization (set_state call not necessary) """
        # Define standard ship lengths
        ship_lengths = [2, 3, 3, 4, 5]

        # Create ships for both players
        player1_ships = [
            Ship(
                name=f"ship_{i+1}", length=length, location=None
            )
            for i, length in enumerate(ship_lengths)
        ]
        player2_ships = [
            Ship(
                name=f"ship_{i+1}", length=length, location=None
            )
            for i, length in enumerate(ship_lengths)
        ]

        # Create player states
        player1 = PlayerState(name="Player 1", ships=player1_ships, shots=[], successful_shots=[])
        player2 = PlayerState(name="Player 2", ships=player2_ships, shots=[], successful_shots=[])

        # Initialize the game state
        self.state = BattleshipGameState(
            idx_player_active=0,
            phase=GamePhase.SETUP,
            winner=None,
            players=[player1, player2]
        )

    def print_state(self) -> None:
        """ Set the game to a given state """
        if not self.state:
            print("No state set.")
            return
        for player in self.state.players:
            print(f"\nPlayer: {player.name}")
            print("  Ships:")
            for ship in player.ships:
                location = ship.location if ship.location else "Not Set"
                print(f"{ship.name} (Length: {ship.length}) - Location: {location}")
            print(f"Shots Fired: {player.shots}")
            print(f"Successful Shots: {player.successful_shots}")

    def get_state(self) -> BattleshipGameState:
        """ Get the complete, unmasked game state """
        if self.state is None:
            raise ValueError("Game state is not initialized.")
        return self.state

    def set_state(self, state: BattleshipGameState) -> None:
        """ Print the current game state """
        self.state = state

    def get_list_action(self) -> List[BattleshipAction]:
        """ Get a list of possible actions for the active player """
        if not self.state:
            return []

        actions = []
        active_player = self.state.players[self.state.idx_player_active]

        # Helper function to check for overlapping positions
        def is_overlapping(position: List[str]) -> bool:
            """
            Check if the given position overlaps with any already placed ships.
            """
            for player in self.state.players:
                for ship in player.ships:
                    if ship.location and any(coord in ship.location for coord in position):
                        return True
            return False

        # Helper function to generate actions for the SETUP phase
        def generate_setup_actions() -> List[BattleshipAction]:
            setup_actions = []
            all_rows = [chr(x) for x in range(ord('A'), ord('J') + 1)]  # Rows: A to J
            all_cols = [str(x) for x in range(1, 11)]  # Columns: 1 to 10

            for ship in active_player.ships:
                if ship.location is None:
                    # Horizontal placements
                    for row in all_rows:
                        for start_col in range(1, 12 - ship.length):
                            position = [row + str(col) for col in range(start_col, start_col + ship.length)]
                            if not is_overlapping(position):
                                setup_actions.append(BattleshipAction(
                                    action_type=ActionType.SET_SHIP,
                                    ship_name=ship.name,
                                    location=position,
                                ))

                    # Vertical placements
                    for col in all_cols:
                        for start_row in range(ord('A'), ord('K') - ship.length):
                            position = [chr(row) + col for row in range(start_row, start_row + ship.length)]
                            if not is_overlapping(position):
                                setup_actions.append(BattleshipAction(
                                    action_type=ActionType.SET_SHIP,
                                    ship_name=ship.name,
                                    location=position,
                                ))
            return setup_actions

        # Helper function to generate actions for the RUNNING phase
        def generate_running_actions() -> List[BattleshipAction]:
            running_actions = []
            all_locations = [chr(x) + str(y) for x in range(ord('A'), ord('J') + 1) for y in range(1, 11)]
            unshot_locations = set(all_locations) - set(active_player.shots)

            for location in unshot_locations:
                running_actions.append(BattleshipAction(
                    action_type=ActionType.SHOOT,
                    ship_name=None,
                    location=[location]
                ))
            return running_actions

        # Add actions based on the current game phase
        if self.state.phase == GamePhase.SETUP:
            actions.extend(generate_setup_actions())
        elif self.state.phase == GamePhase.RUNNING:
            actions.extend(generate_running_actions())

        return actions

    def apply_action(self, action: BattleshipAction) -> None:
        """ Apply the given action to the game """
        if not self.state:
            raise ValueError("Game state is not initialized.")

        # Get the active player based on the current state
        active_player = self.state.players[self.state.idx_player_active]

        # Handle SET_SHIP action
        if action.action_type == ActionType.SET_SHIP:
            if self.state.phase != GamePhase.SETUP:
                raise ValueError("SET_SHIP actions can only be performed in the SETUP phase.")

            def place_ship() -> bool:
                """
                Place the specified ship for the active player.
                Raises an error if the ship is already placed or doesn't exist.
                """
                for ship in active_player.ships:
                    if ship.name == action.ship_name:
                        if ship.location is not None:
                            raise ValueError(f"Ship '{action.ship_name}' is already placed.")
                        ship.location = action.location
                        return True  # Ship successfully placed
                raise ValueError(f"Ship '{action.ship_name}' does not exist.")

            # Place the ship and check if all ships are placed for the active player
            if place_ship() and all(ship.location is not None for ship in active_player.ships):
                # Move to the next player's turn
                self.state.idx_player_active = (self.state.idx_player_active + 1) % 2

                # If all players have placed their ships, transition to the RUNNING phase
                if self.state.idx_player_active == 0 and all(
                    all(ship.location is not None for ship in player.ships) for player in self.state.players
                ):
                    self.state.phase = GamePhase.RUNNING
            return  # Exit after handling SET_SHIP

        # Handle SHOOT action
        if action.action_type == ActionType.SHOOT:
            if self.state.phase != GamePhase.RUNNING:
                raise ValueError("SHOOT actions can only be performed in the RUNNING phase.")

            # Record the shot against the opposing player
            target_player = self.state.players[(self.state.idx_player_active + 1) % 2]
            active_player.shots.append(action.location[0])

            def process_shot() -> bool:
                """
                Check if the shot hits any ship of the target player.
                If a ship is hit, record it in the active player's successful shots.
                """
                for ship in target_player.ships:
                    if ship.location and action.location[0] in ship.location:
                        active_player.successful_shots.append(action.location[0])
                        return True  # Shot hit a ship
                return False  # Shot missed

            # Process the shot and determine if all ships of the target player are sunk
            process_shot()  # Call the function without assigning its return value
            all_sunk = all(
                all(location in active_player.successful_shots for location in ship.location)
                for ship in target_player.ships if ship.location
            )

            if all_sunk:
                self.state.phase = GamePhase.FINISHED
                self.state.winner = self.state.idx_player_active
            else:
                self.state.idx_player_active = (self.state.idx_player_active + 1) % 2

        # Handle unknown action types
        else:
            raise ValueError(f"Unknown action type: {action.action_type}")


    def get_player_view(self, idx_player: int) -> BattleshipGameState:
        """ Get the masked state for the active player (e.g. the oppontent's cards are face down)"""
        if not self.state:
            raise ValueError("Game state is not initialized.")

    # Copy the game state
        masked_players = []
        for i, player in enumerate(self.state.players):
            if i == idx_player:
                # Active player's view includes their full state
                masked_players.append(player)
            else:
                # Opponent's view: Ships' locations are hidden
                masked_ships = [
                    Ship(name=ship.name, length=ship.length, location=None) for ship in player.ships
                ]
                masked_players.append(PlayerState(
                    name=player.name,
                    ships=masked_ships,
                    shots=player.shots,
                    successful_shots=player.successful_shots
                ))

        # Return the masked game state
        return BattleshipGameState(
            idx_player_active=self.state.idx_player_active,
            phase=self.state.phase,
            winner=self.state.winner,
            players=masked_players
        )


class RandomPlayer(Player): # pylint: disable=too-few-public-methods

    def select_action(self, state: BattleshipGameState, actions: List[BattleshipAction]) -> Optional[BattleshipAction]:
        """ Given masked game state and possible actions, select the next action """
        if len(actions) > 0:
            return random.choice(actions)
        return None


if __name__ == "__main__":

    game = Battleship()
    Player1 = RandomPlayer()
    Player2 = RandomPlayer()

    # Define and set the initial game state
    standard_ship_lengths = [2, 3, 3, 4, 5]  # Standard ship lengths
    local_player1_ships = [
        Ship(
            name=f"ship_{i+1}", length=length, location=None
        )
        for i, length in enumerate(standard_ship_lengths)
    ]
    local_player2_ships = [
        Ship(
            name=f"ship_{i+1}", length=length, location=None
        )
        for i, length in enumerate(standard_ship_lengths)
    ]

    local_player1 = PlayerState(name="Player 1", ships=local_player1_ships, shots=[], successful_shots=[])
    local_player2 = PlayerState(name="Player 2", ships=local_player2_ships, shots=[], successful_shots=[])

    initial_state = BattleshipGameState(
        idx_player_active=0,
        phase=GamePhase.SETUP,
        winner=None,
        players=[local_player1, local_player2]
    )

    game.set_state(initial_state)

    # Run the game loop
    while game.get_state().phase != GamePhase.FINISHED:
        current_state = game.get_player_view(game.get_state().idx_player_active)
        available_actions = game.get_list_action()
        selected_action = (
            Player1.select_action(current_state, available_actions)
            if current_state.idx_player_active == 0
            else Player2.select_action(current_state, available_actions)
        )
        if selected_action:
            game.apply_action(selected_action)
        game.print_state()

    # Print the winner
    print("\nGame Over!")
    game_winner = game.get_state().winner
    if game_winner is not None:
        print(f"Winner: {game.get_state().players[game_winner].name}")
