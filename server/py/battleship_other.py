from typing import List, Optional
from enum import Enum
import random
from server.py.game import Game, Player


class ActionType(str, Enum):
    SET_SHIP = 'set_ship'
    SHOOT = 'shoot'


class BattleshipAction:

    def __init__(self, action_type: ActionType, ship_name: Optional[str], location: List[str]) -> None:
        self.action_type = action_type
        self.ship_name = ship_name # only for set_ship actions
        self.location = location


class Ship:

    def __init__(self, name: str, length: int, location: Optional[List[str]]) -> None:
        self.name = name
        self.length = length
        self.location = location


class PlayerState:

    def __init__(self, name: str, ships: List[Ship], shots: List[str], successful_shots: List[str]) -> None:
        self.name = name
        self.ships = ships
        self.shots = shots
        self.successful_shots = successful_shots


class GamePhase(str, Enum):
    SETUP = 'setup'            # before the game has started (including setting ships)
    RUNNING = 'running'        # while the game is running (shooting)
    FINISHED = 'finished'      # when the game is finished


class BattleshipGameState:

    def __init__(self, idx_player_active: int, phase: GamePhase, winner: Optional[int], players: List[PlayerState]) -> None:
        self.idx_player_active = idx_player_active
        self.phase = phase
        self.winner = winner
        self.players = players


class Battleship(Game):

    def __init__(self):
        self.state: Optional[BattleshipGameState] = None

    def print_state(self) -> None:
        if not self.state:
            print("No state set.")
            return
        print(f"Phase: {self.state.phase}, Active Player: {self.state.idx_player_active}")
        for idx, player in enumerate(self.state.players):
            print(f"Player {idx + 1}: {player.name}")
            print("  Ships:")
            for ship in player.ships:
                print(f"    {ship.name} - Location: {ship.location}")
            print(f"  Shots: {player.shots}")
            print(f"  Successful Shots: {player.successful_shots}")


    def get_state(self) -> BattleshipGameState:
        """ Get the complete, unmasked game state """
        return self.state

    def set_state(self, state: BattleshipGameState) -> None:
        """ Print the current game state """
        self.state = state
    
    def get_list_action(self) -> List[BattleshipAction]:
        """ Get a list of possible actions for the active player """
        actions: List[BattleshipAction] = []
        
        active_player_idx = self.state.idx_player_active
        active_player = self.state.players[active_player_idx]

        def is_valid_ship_placement(self, locations: List[str], existing_ship_locations: List[str]) -> bool:
            """
            Validate that the proposed locations:
            - Do not overlap with any existing ship.
            - Do not touch (including diagonals) any existing ship.
            """
            # Create a set of all occupied cells, including adjacent cells
            occupied_cells = set()
            for loc in existing_ship_locations:
                row, col = ord(loc[0]), int(loc[1:])
                # Add the cell and its surrounding cells
                for r in range(row - 1, row + 2):
                    for c in range(col - 1, col + 2):
                        occupied_cells.add(f"{chr(r)}{c}")

            # Check if any of the proposed locations overlap or touch existing ships
            for loc in locations:
                if loc in occupied_cells:
                    return False

            return True

        if self.state.phase == GamePhase.SETUP:
            # Generate ship placement actions
            for ship in active_player.ships:
                if not ship.location:
                    board_size = 10
                    # Collect all existing ship locations
                    existing_ship_locations = [
                        loc for other_ship in active_player.ships if other_ship.location for loc in other_ship.location
                    ]
                    for row in range(board_size):
                        for col in range(board_size):
                            # Generate all possible horizontal and vertical placements
                            if col + ship.length <= board_size:
                                # Horizontal placement
                                locations = [f"{chr(65 + row)}{c + 1}" for c in range(col, col + ship.length)]
                                if self.is_valid_ship_placement(locations, existing_ship_locations):
                                    actions.append(BattleshipAction(ActionType.SET_SHIP, ship.name, locations))
                            if row + ship.length <= board_size:
                                # Vertical placement
                                locations = [f"{chr(65 + r)}{col + 1}" for r in range(row, row + ship.length)]
                                if self.is_valid_ship_placement(locations, existing_ship_locations):
                                    actions.append(BattleshipAction(ActionType.SET_SHIP, ship.name, locations))


        elif self.state.phase == GamePhase.RUNNING:
            # Generate shooting actions
            board_size = 10
            for row in range(board_size):
                for col in range(board_size):
                    location = f"{chr(65 + row)}{col + 1}"
                    if location not in active_player.shots:
                        actions.append(BattleshipAction(ActionType.SHOOT, None, [location]))

        return actions

    def apply_action(self, action: BattleshipAction) -> None:
        if action.action_type == ActionType.SET_SHIP:
            player = self.state.players[self.state.idx_player_active]
            for ship in player.ships:
                if ship.name == action.ship_name:
                    ship.location = action.location
            all_ships_set = all(ship.location for ship in player.ships)
            if all_ships_set:
                self.state.idx_player_active = (self.state.idx_player_active + 1) % 2
                if all(all(ship.location for ship in p.ships) for p in self.state.players):
                    self.state.phase = GamePhase.RUNNING

        elif action.action_type == ActionType.SHOOT:
            player = self.state.players[self.state.idx_player_active]
            opponent = self.state.players[(self.state.idx_player_active + 1) % 2]
            target = action.location[0]
            player.shots.append(target)
            if any(target in ship.location for ship in opponent.ships if ship.location):
                player.successful_shots.append(target)
                opponent.ships = [ship for ship in opponent.ships if target not in ship.location]
            if not opponent.ships:
                self.state.phase = GamePhase.FINISHED
                self.state.winner = self.state.idx_player_active
            else:
                self.state.idx_player_active = (self.state.idx_player_active + 1) % 2

    def get_player_view(self, idx_player: int) -> BattleshipGameState:
        players_copy = []
        for i, player in enumerate(self.state.players):
            if i == idx_player:
                players_copy.append(player)
            else:
                hidden_ships = [Ship(ship.name, ship.length, None) for ship in player.ships]
                players_copy.append(PlayerState(player.name, hidden_ships, player.shots, player.successful_shots))
        return BattleshipGameState(self.state.idx_player_active, self.state.phase, self.state.winner, players_copy)



class RandomPlayer(Player):

    def select_action(self, state: BattleshipGameState, actions: List[BattleshipAction]) -> Optional[BattleshipAction]:
        """ Given masked game state and possible actions, select the next action """
        if len(actions) > 0:
            return random.choice(actions)
        return None


if __name__ == "__main__":

    game = Battleship()
    Player1 = RandomPlayer()
    Player2 = RandomPlayer()

    while game.get_state().phase != GamePhase.FINISHED:
        state = game.get_player_view(game.get_state().idx_player_active)
        actions = game.get_list_action()
        action = Player1.select_action(state, actions) if state.idx_player_active == 0 else Player2.select_action(state, actions)
        if action:
            game.apply_action(action)
        game.print_state()

    print("\nGame Over!")
    winner = game.get_state().winner
    if winner is not None:
        print(f"Winner: {game.get_state().players[winner].name}")