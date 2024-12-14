import pytest
from server.py.dog import Dog, RandomPlayer, Card, Marble, Action, GameState, GamePhase

@pytest.fixture
def game():
    """Fixture to create a new game instance for testing."""
    return Dog()

@pytest.fixture
def random_player():
    """Fixture to create a RandomPlayer instance for testing."""
    return RandomPlayer()

def test_initialization(game):
    """Test the game initializes with the correct default state."""
    state = game.get_state()
    assert state.phase == GamePhase.RUNNING
    assert state.cnt_round == 1
    assert len(state.list_card_discard) == 0
    assert len(state.list_card_draw) == 86  # Assuming 86 cards after dealing
    assert len(state.list_player) == 4
    assert state.idx_player_active >= 0
    assert state.idx_player_active < 4
    assert state.idx_player_started == state.idx_player_active
    assert state.card_active is None
    assert not state.bool_card_exchanged
    assert game.exchanges_done == []

def test_card_dealing(game):
    """Test that cards are dealt correctly to players."""
    for player in game.state.list_player:
        assert len(player.list_card) == 6  # Initial cards per player

def test_start_new_round(game):
    """Test starting a new round."""
    game.start_new_round()
    assert game.state.cnt_round == 2
    assert len(game.state.list_player[0].list_card) == 5  # Cards per player in round 2

def test_valid_moves_out_of_kennel(game):
    """Test that valid moves are identified correctly."""
    player_idx = game.state.idx_player_active
    player = game.state.list_player[player_idx]
    list_card = [Card(suit='♦', rank='A'), Card(suit='♥', rank='K'), Card(suit='', rank='JKR')]

    for card in list_card:
        player.list_card.clear()
        player.list_card.append(card)
        actions = game.get_list_action()
        assert len(actions) > 0  # Ensure there are valid actions available

def test_apply_action(game):
    """Test applying a valid action updates the game state."""
    player_idx = game.state.idx_player_active
    player = game.state.list_player[player_idx]

    # Assume the player has a card that can move a marble
    card_to_use = Card(suit='♠', rank='2')
    player.list_card.append(card_to_use)

    # Set a marble position of the active player
    player.list_marble[0].pos = 4
    player.list_marble[0].is_save = False

    # Find a marble to move
    marble = player.list_marble[0]
    initial_position = marble.pos
    new_position = (initial_position + 2) % 64

    # Create and apply the action
    action = Action(card=card_to_use, pos_from=initial_position, pos_to=new_position)
    game.apply_action(action)

    # Assert the marble's position has been updated
    assert marble.pos == new_position, "Marble should have moved to the new position"

def test_game_phase_transition(game):
    """Test the game transitions correctly between phases."""
    # Initially, the game should be in the RUNNING phase
    assert game.state.phase == GamePhase.RUNNING

    # Manually set the game phase to FINISHED and check
    game.state.phase = GamePhase.FINISHED
    assert game.state.phase == GamePhase.FINISHED, "Game phase should transition to FINISHED"

def test_card_exchange(game):
    """Test the card exchange process."""
    # Simulate card exchange
    player_idx = game.state.idx_player_active
    player = game.state.list_player[player_idx]

    # Assume the player has a card to exchange
    card_to_exchange = player.list_card[0]
    partner_idx = (player_idx + 2) % game.state.cnt_player
    partner = game.state.list_player[partner_idx]

    # Perform the exchange
    action = Action(card=card_to_exchange, pos_from=None, pos_to=None)
    game.apply_action(action)

    # Assert the card has been exchanged
    assert card_to_exchange in partner.list_card, "Card should be exchanged with partner"

def test_marble_swap(game):
    """Test swapping marbles with a Jack card."""
    player_idx = game.state.idx_player_active
    player = game.state.list_player[player_idx]

    # Assume the player has a Jack card
    jack_card = Card(suit='♠', rank='J')
    player.list_card.append(jack_card)

    # Find two marbles to swap
    marble_1 = player.list_marble[0]
    marble_2 = player.list_marble[1]
    initial_pos_1 = marble_1.pos
    initial_pos_2 = marble_2.pos

    # Create and apply the swap action
    action = Action(card=jack_card, pos_from=initial_pos_1, pos_to=initial_pos_2)
    game.apply_action(action)

    # Assert the marbles' positions have been swapped
    assert marble_1.pos == initial_pos_2, "Marble 1 should be at Marble 2's initial position"
    assert marble_2.pos == initial_pos_1, "Marble 2 should be at Marble 1's initial position"

def test_set_state(game):
    """Test setting the game state."""
    # Create a new game state
    new_state = GameState(
        cnt_player=4,
        phase=GamePhase.RUNNING,
        cnt_round=2,
        bool_card_exchanged=False,
        idx_player_started=1,
        idx_player_active=1,
        list_player=game.state.list_player,
        list_card_draw=game.state.list_card_draw,
        list_card_discard=game.state.list_card_discard,
        card_active=None
    )

    # Set the new state
    game.set_state(new_state)

    # Assert the state has been updated
    assert game.state.cnt_round == 2
    assert game.state.idx_player_started == 1
    assert game.state.phase == GamePhase.RUNNING

    # Assert the active player index is rotated
    expected_active_player = (new_state.idx_player_started + new_state.cnt_round) % new_state.cnt_player
    assert game.state.idx_player_active == expected_active_player, "Active player index should be rotated"

def test_get_state(game):
    """Test getting the game state."""
    # Set up the game state with specific conditions
    game.state.cnt_round = 2
    game.state.idx_player_started = 1
    game.state.idx_player_active = 1

    # Get the state
    state = game.get_state()

    # Assert the state is returned correctly
    assert state.cnt_round == 2
    assert state.idx_player_started == 1

    # Assert the active player index is rotated
    expected_active_player = (state.idx_player_started + state.cnt_round) % state.cnt_player
    assert state.idx_player_active == expected_active_player, "Active player index should be rotated"

def test_print_state(game, capsys):
    """Test the print_state method outputs the correct game state."""
    # Set up a known state for testing
    game.state.cnt_round = 1
    game.state.idx_player_active = 0
    game.state.idx_player_started = 0
    game.state.bool_card_exchanged = False
    game.state.phase = GamePhase.RUNNING

    # Add some cards and marbles to the state for testing
    game.state.list_card_discard = []
    game.state.list_player[0].list_card = [Card(suit='♠', rank='A')]
    game.state.list_player[0].list_marble = [Marble(pos=0, is_save=True)]

    # Call the print_state method
    game.print_state()

    # Capture the output
    captured = capsys.readouterr()

    # Assert the captured output matches the expected output
    assert captured.out != " ", "Output should not be empty"

def test_deal_cards(game):
    """Test the deal_cards method deals the correct number of cards to each player."""
    num_cards_per_player = 6
    initial_deck_size = len(game.state.list_card_draw)

    # Deal cards to players
    game.deal_cards(num_cards_per_player)

    # Check each player has the correct number of cards
    for player in game.state.list_player:
        assert len(player.list_card) == num_cards_per_player, "Each player should have the correct number of cards"

    # Check the deck size is reduced correctly
    expected_deck_size = initial_deck_size - (num_cards_per_player * game.state.cnt_player)
    assert (len(game.state.list_card_draw) ==
            expected_deck_size), "Deck size should be reduced by the number of dealt cards"

    # Check that players' hands were cleared before dealing
    game.deal_cards(num_cards_per_player)
    for player in game.state.list_player:
        assert (len(player.list_card) ==
                num_cards_per_player), "Players' hands should be cleared before dealing new cards"

    # Check reshuffling logic
    game.state.list_card_draw.clear()  # Empty the draw pile to force reshuffle
    game.deal_cards(num_cards_per_player)
    assert (len(game.state.list_card_draw) ==
            len(GameState.LIST_CARD) - (num_cards_per_player * game.state.cnt_player)), \
        "Deck should be reshuffled if empty and have the correct number of cards after dealing"

def test_start_new_round_2(game):
    """Test the start_new_round method correctly initializes a new round."""
    initial_round = game.state.cnt_round
    initial_starting_player = game.state.idx_player_started

    # Call start_new_round
    game.start_new_round()

    # Check that the round number has incremented
    assert game.state.cnt_round == initial_round + 1, "Round number should increment"

    # Calculate expected number of cards per player
    expected_cards_per_player = 7 - ((game.state.cnt_round - 1) % 5 + 1)

    # Check each player has the correct number of cards
    for player in game.state.list_player:
        assert len(player.list_card) == expected_cards_per_player,\
            "Each player should have the correct number of cards"

    # Check that the starting player index has updated correctly
    expected_starting_player = (initial_starting_player + 1) % game.state.cnt_player
    assert game.state.idx_player_started == expected_starting_player, "Starting player index should update"

    # Check that the active player index is set to the starting player
    assert game.state.idx_player_active == expected_starting_player,\
        "Active player index should be set to starting player"

    # Check that the card exchange state is reset
    assert not game.state.bool_card_exchanged, "Card exchange state should be reset"

    # Check that the game phase is set to RUNNING
    assert game.state.phase == GamePhase.RUNNING, "Game phase should be set to RUNNING"

def test_get_player_view(game):
    """Test the get_player_view method provides the correct masked state."""
    # Assume each player has some cards
    for player in game.state.list_player:
        player.list_card = [Card(suit='♠', rank='A'), Card(suit='♥', rank='K')]

    idx_player = 0  # Test for player 1

    # Get the player view
    player_view = game.get_player_view(idx_player)

    # Check that the player's own cards are visible
    assert (player_view.list_player[idx_player].list_card ==
            [Card(suit='♠', rank='A'), Card(suit='♥', rank='K')]), \
        "Player's own cards should be visible"

def test_check_move_validity(game):
    """Test the check_move_validity method."""
    # Setup a scenario where a move is valid
    active_player_idx = 0
    marble_idx = 0
    marble_new_pos = 5
    game.state.list_player[active_player_idx].list_marble[marble_idx].pos = 0

    # Test a valid move
    assert game.check_move_validity(active_player_idx, marble_idx, marble_new_pos), \
        "Move should be valid"

    # Test move to a position occupied by a safe marble
    game.state.list_player[1].list_marble[0].pos = marble_new_pos
    game.state.list_player[1].list_marble[0].is_save = True
    assert not game.check_move_validity(active_player_idx, marble_idx, marble_new_pos), \
        "Move should be invalid due to safe marble"

    # Test move to a position outside the board
    assert not game.check_move_validity(active_player_idx, marble_idx, -1), \
        "Move should be invalid due to negative position"
    assert not game.check_move_validity(active_player_idx, marble_idx, 96), \
        "Move should be invalid due to position outside board"

def test_can_move_steps(game):
    """Test the can_move_steps method."""
    player_idx = 0
    marble_idx = 0
    steps = 3

    # Setup initial marble position
    game.state.list_player[player_idx].list_marble[marble_idx].pos = 0

    # Test valid move
    assert game.can_move_steps(player_idx, marble_idx, steps), \
        "Should be able to move steps"

    # Test invalid move due to occupied position
    game.state.list_player[1].list_marble[0].pos = 3
    game.state.list_player[1].list_marble[0].is_save = True
    assert not game.can_move_steps(player_idx, marble_idx, steps), \
        "Should not be able to move steps due to occupied position"

def test_compute_final_position(game):
    """Test the compute_final_position method."""
    player_idx = 0
    start_pos = 0
    steps = 5

    # Test normal circle move
    expected_pos = (start_pos + steps) % 64
    assert game.compute_final_position(start_pos, steps, player_idx) == expected_pos, \
        "Final position should be calculated correctly in normal circle"

    # Test finish lane move
    start_pos = 65
    steps = 3
    expected_pos = min(start_pos + steps, game.FINISH_POSITIONS[player_idx][-1])
    assert game.compute_final_position(start_pos, steps, player_idx) == expected_pos, \
        "Final position should be calculated correctly in finish lane"

def test_send_home_if_passed(game):
    """Test the send_home_if_passed method."""
    active_player_idx = 0
    pos = 5

    # Setup a marble to be overtaken
    game.state.list_player[1].list_marble[0].pos = pos

    # Call the method to send the overtaken marble home
    game.send_home_if_passed(pos, active_player_idx)

    # Check that the marble was sent home
    assert game.state.list_player[1].list_marble[0].pos == game.KENNEL_POSITIONS[1][0], \
        "Marble should be sent home"

def test_is_marble_protecting_start(game):
    """Test the is_marble_protecting_start method."""
    player_idx = 0
    marble_idx = 0

    # Setup a marble at the start position and safe
    game.state.list_player[player_idx].list_marble[marble_idx].pos = game.START_POSITION[player_idx]
    game.state.list_player[player_idx].list_marble[marble_idx].is_save = True

    # Test if the marble is protecting the start
    assert game.is_marble_protecting_start(player_idx, marble_idx), \
        "Marble should be protecting the start position"

    # Test if the marble is not protecting the start when not safe
    game.state.list_player[player_idx].list_marble[marble_idx].is_save = False
    assert not game.is_marble_protecting_start(player_idx, marble_idx), \
        "Marble should not be protecting the start position when not safe"

import pytest
import random
from server.py.dog import RandomPlayer, GameState, Action, Card

def test_select_action_with_non_empty_list(random_player):
    """Test that select_action returns a valid action from a non-empty list."""
    # Create valid Card instances
    card1 = Card(suit='♠', rank='A')
    card2 = Card(suit='♥', rank='K')

    # Create actions with valid cards
    actions = [
        Action(card=card1, pos_from=0, pos_to=1),
        Action(card=card2, pos_from=1, pos_to=2)
    ]
    selected_action = random_player.select_action(None, actions)

    assert selected_action in actions, "Selected action should be one of the provided actions"

def test_select_action_with_empty_list(random_player):
    """Test that select_action returns None when given an empty list."""
    actions = []
    selected_action = random_player.select_action(None, actions)

    assert selected_action is None, "Selected action should be None when no actions are available"

def test_get_player_type(random_player):
    """Test that get_player_type returns the correct player type."""
    player_type = random_player.get_player_type()

    assert player_type == "Random", "Player type should be 'Random'"

def setup_game_state_for_testing(game, card_rank, marble_positions, player_idx=0):
    """Helper function to set up the game state for testing."""
    game.state.idx_player_active = player_idx
    active_player = game.state.list_player[player_idx]
    active_player.list_card = [Card(suit='♠', rank=card_rank)]
    for marble, pos in zip(active_player.list_marble, marble_positions):
        marble.pos = pos

def test_get_list_action_ace(game):
    """Test actions generated for an Ace card."""
    setup_game_state_for_testing(game, 'A', [0, 64, 65, 66])
    actions = game.get_list_action()
    assert any(action.card.rank == 'A' for action in actions), "Should generate actions for Ace"

def test_get_list_action_king(game):
    """Test actions generated for a King card."""
    setup_game_state_for_testing(game, 'K', [0, 64, 65, 66])
    actions = game.get_list_action()
    assert any(action.card.rank == 'K' for action in actions), "Should generate actions for King"

def test_get_list_action_four(game):
    """Test actions generated for a Four card (backward move)."""
    setup_game_state_for_testing(game, '4', [10, 64, 65, 66])
    actions = game.get_list_action()
    assert any(action.card.rank == '4' for action in actions), "Should generate actions for Four"

def test_get_list_action_normal_card(game):
    """Test actions generated for a normal card (e.g., 5)."""
    setup_game_state_for_testing(game, '5', [0, 64, 65, 66])
    actions = game.get_list_action()
    assert any(action.card.rank == '5' for action in actions), "Should generate actions for normal card"

def test_apply_action_none(game):
    """Test the apply_action method when the action is None."""
    # Setup initial game state
    active_player_index = game.state.idx_player_active
    active_player = game.state.list_player[active_player_index]
    active_player.list_card = [Card(suit='♠', rank='A'), Card(suit='♥', rank='K')]

    # Store initial state for comparison
    initial_discard_pile_size = len(game.state.list_card_discard)
    initial_active_player_index = game.state.idx_player_active

    # Apply action with None
    game.apply_action(None)

    # Check that the player's cards have been added to the discard pile
    assert len(game.state.list_card_discard) == initial_discard_pile_size + 2, \
        "Discard pile should have increased by the number of cards in the player's hand"

    # Check that the player's hand is cleared
    assert len(active_player.list_card) == 0, "Player's hand should be cleared"

    # Check that the active player index has changed
    expected_active_player_index = (initial_active_player_index + 1) % game.state.cnt_player
    assert game.state.idx_player_active == expected_active_player_index, \
        "Active player index should have advanced to the next player"

    # Check if a new round starts when all players have played their cards
    # Simulate all players having empty hands
    for player in game.state.list_player:
        player.list_card.clear()

    # Set the active player back to the starting player
    game.state.idx_player_active = game.state.idx_player_started

    # Apply action with None again
    game.apply_action(None)

    # Check that a new round has started
    assert game.state.cnt_round == 1, "A new round should start when all players have played their cards"
