# runcmd: cd .. & venv\Scripts\python benchmark/benchmark_uno.py python uno.Uno
import os
import sys

import abc
import benchmark
import importlib
import json
import traceback
import copy

from pydantic import BaseModel
from typing import List, Optional

sys.path += '../'

from server.py.uno import Card, Action, PlayerState, GameState, GamePhase

LIST_COLOR = ['red', 'blue', 'yellow', 'green']
CNT_HAND_CARDS = 7


class UnoBenchmark(benchmark.Benchmark):

    # --- tests ---

    def test_initial_game_state_values(self):
        """Test 001: Validate values of initial game state (cnt_players=2) [5 points]"""

        self.game_server.reset()

        list_card_draw = []
        for i in range(4):
            for color in LIST_COLOR:
                for number in range(10):
                    card = Card(color=color, number=number, symbol=None)
                    if len(list_card_draw) < 108:
                        list_card_draw.append(card)

        state = GameState(
            cnt_player=2,
            list_card_draw=list_card_draw
        )
        self.game_server.set_state(state)
        self.game_server.get_state()
        str_state = f'GameState:\n{state}\n'

        cnt_cards = 108 - state.cnt_player * state.CNT_HAND_CARDS - 1
        hint = str_state
        hint += f'Error: len("list_card_draw") must be {cnt_cards} not {len(state.list_card_draw)} initially.'
        assert len(state.list_card_draw) == cnt_cards, hint
        hint = str_state
        hint += f'Error: len("list_card_draw") must be 1 initially.'
        assert len(state.list_card_discard) == 1, hint

        hint = str_state
        hint += f'Error: len("list_player") must be {state.cnt_player}.'
        assert len(state.list_player) == state.cnt_player, hint
        hint = str_state
        hint += f'Error: "idx_player_active" must >= 0.'
        assert state.idx_player_active >= 0, hint
        hint = str_state
        hint += f'Error: "idx_player_active" must < cnt_players.'
        assert state.idx_player_active < state.cnt_player, hint
        hint = str_state
        hint += f'Error: "direction" must be == 1.'
        assert state.direction == 1, hint

        for player in state.list_player:
            hint = str_state
            hint += f'Error: len("list_player.list_card") must be {state.CNT_HAND_CARDS} initially.'
            assert len(player.list_card) == state.CNT_HAND_CARDS, hint

    def is_card_valid(self, card: Card):
        okay = True
        okay = okay and card.number in [None, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        okay = okay and card.symbol in [None, 'skip', 'reverse', 'draw2', 'wild', 'wilddraw4']
        okay = okay and card.color in LIST_COLOR + ['any']
        if card.color == 'any':
            okay = okay and card.symbol in ['wild', 'wilddraw4']
        if card.symbol in ['skip', 'reverse', 'draw2']:
            okay = okay and card.color != 'any'
        return okay

    def get_idx_top(self, list_card_draw, cnt_player):
        # index of top card in list_card_draw after players get 7 cards
        idx_top = len(list_card_draw) - cnt_player * CNT_HAND_CARDS - 1
        return idx_top

    def test_card_values(self):
        """Test 002: Validate card values [1 points]"""

        self.game_server.reset()
        state = GameState(cnt_player=2)
        self.game_server.set_state(state)
        self.game_server.get_state()
        str_state = f'GameState:\n{state}\n'

        for card in state.list_card_draw + state.list_card_discard:
            hint = str_state
            hint += f'Error: Card values not valid {card}.'
            assert self.is_card_valid(card), hint

        for player in state.list_player:
            for card in player.list_card:
                hint = str_state
                hint += f'Error: Card values not valid {card}.'
                assert self.is_card_valid(card), hint

    def test_list_action_card_matching_1(self):
        """Test 003: Test player card matching with discard pile card - simple cards [3 points]"""

        for c, color in enumerate(LIST_COLOR):

            for number in range(10):

                self.game_server.reset()

                cnt_player = 2
                idx_player_active = 0

                list_card_draw = []
                for color2 in LIST_COLOR:
                    for number2 in range(10):
                        card = Card(color=color2, number=number2, symbol=None)
                        list_card_draw.append(card)

                card1 = Card(color=color, number=number, symbol=None)                               # same color, same number
                card2 = Card(color=color, number=(number + 1) % 10, symbol=None)                    # same color, different number
                card3 = Card(color=LIST_COLOR[(c + 1) % 4], number=number, symbol=None)             # different color, same number
                card4 = Card(color=LIST_COLOR[(c + 1) % 4], number=(number + 1) % 10, symbol=None)  # different color, different number

                idx_top = self.get_idx_top(list_card_draw, cnt_player)
                list_card_draw[idx_top] = card1

                state = GameState(
                    cnt_player=cnt_player,
                    idx_player_active=idx_player_active,
                    list_card_draw=list_card_draw
                )
                self.game_server.set_state(state)
                state = self.game_server.get_state()
                player = state.list_player[idx_player_active]
                player.list_card = [card1, card2, card3, card4]
                self.game_server.set_state(state)
                state = self.game_server.get_state()
                str_state = f'GameState:\n{state}\n'

                list_action_found = self.game_server.get_list_action()
                list_action_expected = []
                action = Action(card=card1, color=card1.color, draw=None)
                list_action_expected.append(action)
                action = Action(card=card2, color=card2.color, draw=None)
                list_action_expected.append(action)
                action = Action(card=card3, color=card3.color, draw=None)
                list_action_expected.append(action)
                action = Action(card=None, color=None, draw=1)
                list_action_expected.append(action)

                hint = str_state
                hint += 'Error: "get_list_action" result is wrong.\n'
                hint += '  - Expected:\n'
                hint += f'{self.get_list_action_as_str(list_action_expected)}\n'
                hint += '  - Found:\n'
                hint += f'{self.get_list_action_as_str(list_action_found)}'
                assert sorted(list_action_found) == sorted(list_action_expected), hint

    def test_list_action_card_matching_2(self):
        """Test 004: Test player card matching with discard pile card - special cards [3 points]"""

        LIST_SYMBOL = ['skip', 'reverse', 'draw2']

        for c, color in enumerate(LIST_COLOR):

            for s, symbol in enumerate(LIST_SYMBOL):

                self.game_server.reset()

                cnt_player = 2

                list_card_draw = []
                for color2 in LIST_COLOR:
                    for number2 in range(10):
                        card = Card(color=color2, number=number2, symbol=None)
                        list_card_draw.append(card)

                card1 = Card(color=color, number=None, symbol=symbol)                                      # same color, same symbol
                card2 = Card(color=color, number=None, symbol=LIST_SYMBOL[(s + 1) % 3])                    # same color, different symbol
                card3 = Card(color=LIST_COLOR[(c + 1) % 4], number=None, symbol=symbol)                    # different color, same symbol
                card4 = Card(color=LIST_COLOR[(c + 1) % 4], number=None, symbol=LIST_SYMBOL[(s + 1) % 3])  # different color, different symbol

                idx_top = self.get_idx_top(list_card_draw, cnt_player)
                list_card_draw[idx_top] = card1

                idx_player_active = 1 if card1.symbol == 'skip' else 0

                state = GameState(
                    cnt_player=cnt_player,
                    idx_player_active=idx_player_active,
                    list_card_draw=list_card_draw
                )
                self.game_server.set_state(state)
                state = self.game_server.get_state()
                player = state.list_player[state.idx_player_active]
                player.list_card = [card1, card2, card3, card4]
                self.game_server.set_state(state)
                state = self.game_server.get_state()
                str_state = f'GameState:\n{state}\n'

                list_action_found = self.game_server.get_list_action()
                list_action_expected = []
                draw = state.cnt_to_draw + 2 if card1.symbol == 'draw2' else None
                action = Action(card=card1, color=card1.color, draw=draw)
                list_action_expected.append(action)
                if state.cnt_to_draw == 0:
                    draw = state.cnt_to_draw + 2 if card2.symbol == 'draw2' else None
                    action = Action(card=card2, color=card2.color, draw=draw)
                    list_action_expected.append(action)
                draw = state.cnt_to_draw + 2 if card3.symbol == 'draw2' else None
                action = Action(card=card3, color=card3.color, draw=draw)
                list_action_expected.append(action)
                draw = state.cnt_to_draw if state.cnt_to_draw > 0 else 1
                action = Action(card=None, color=None, draw=draw)
                list_action_expected.append(action)

                hint = str_state
                hint += f'Error: "get_list_action" result is wrong for {symbol.upper()} card.\n'
                hint += '  - Expected:\n'
                hint += f'{self.get_list_action_as_str(list_action_expected)}\n'
                hint += '  - Found:\n'
                hint += f'{self.get_list_action_as_str(list_action_found)}'
                assert sorted(list_action_found) == sorted(list_action_expected), hint

    def test_list_action_card_matching_3(self):
        """Test 005: Test player card matching with discard pile card - black cards [2 points]"""

        for symbol in ['wilddraw4', 'wild']:

            self.game_server.reset()

            cnt_player = 2
            idx_player_active = 0

            list_card_draw = []
            for color in LIST_COLOR:
                for number in range(10):
                    card = Card(color=color, number=number, symbol=None)
                    list_card_draw.append(card)
            card = Card(color='red', number=1, symbol=None)

            idx_top = self.get_idx_top(list_card_draw, cnt_player)
            list_card_draw[idx_top] = card

            state = GameState(
                cnt_player=cnt_player,
                idx_player_active=idx_player_active,
                list_card_draw=list_card_draw
            )
            self.game_server.set_state(state)
            state = self.game_server.get_state()
            card = Card(color='any', number=None, symbol=symbol)
            player = state.list_player[idx_player_active]
            player.list_card = [card]
            self.game_server.set_state(state)
            state = self.game_server.get_state()
            str_state = f'GameState:\n{state}\n'

            list_action_found = self.game_server.get_list_action()
            list_action_expected = []
            for color in LIST_COLOR:
                draw = 4 if symbol == 'wilddraw4' else None
                action = Action(card=card, color=color, draw=draw)
                list_action_expected.append(action)
            action = Action(card=None, color=None, draw=1)
            list_action_expected.append(action)

            hint = str_state
            hint += 'Error: "get_list_action" result is wrong.\n'
            hint += '  - Expected:\n'
            hint += f'{self.get_list_action_as_str(list_action_expected)}\n'
            hint += '  - Found:\n'
            hint += f'{self.get_list_action_as_str(list_action_found)}'
            assert sorted(list_action_found) == sorted(list_action_expected), hint

    def test_set_up_1(self):
        """Test 006: Test case when first card on discard pile is DRAW 2 [1 points]"""

        self.game_server.reset()

        cnt_player = 2
        idx_player_active = 0

        list_card_draw = []
        for color in LIST_COLOR:
            for number in range(10):
                card = Card(color=color, number=number, symbol=None)
                list_card_draw.append(card)

        card = Card(color='red', number=None, symbol='draw2')
        idx_top = self.get_idx_top(list_card_draw, cnt_player)
        list_card_draw[idx_top] = card

        state = GameState(
            cnt_player=cnt_player,
            idx_player_active=idx_player_active,
            list_card_draw=list_card_draw
        )
        self.game_server.set_state(state)
        state = self.game_server.get_state()
        str_state = f'GameState:\n{state}\n'

        hint = str_state
        hint += f'Error: First player needs to draw 2 cards after DRAW 2 start card.'
        assert state.cnt_to_draw == 2, hint

    def test_set_up_2(self):
        """Test 007: Test case when first card on discard pile is WILD DRAW 4 [1 points]"""

        self.game_server.reset()

        cnt_player = 2
        idx_player_active = 0

        list_card_draw = []
        for color in LIST_COLOR:
            for number in range(10):
                card = Card(color=color, number=number, symbol=None)
                list_card_draw.append(card)

        card = Card(color='red', number=None, symbol='wilddraw4')
        idx_top = self.get_idx_top(list_card_draw, cnt_player) 
        list_card_draw[idx_top] = card

        state = GameState(
            cnt_player=cnt_player,
            idx_player_active=idx_player_active,
            list_card_draw=list_card_draw
        )
        self.game_server.set_state(state)
        state = self.game_server.get_state()
        str_state = f'GameState:\n{state}\n'

        hint = str_state
        hint += f'Error: First draw pile card can\'t be WILD DRAW 4 card.'
        assert state.list_card_discard[-1] != card, hint

    def test_set_up_3(self):
        """Test 008: Test case when first card on discard pile is REVERSE [1 points]"""

        self.game_server.reset()

        cnt_player = 2
        idx_player_active = 0

        list_card_draw = []
        for color in LIST_COLOR:
            for number in range(10):
                card = Card(color=color, number=number, symbol=None)
                list_card_draw.append(card)

        card = Card(color='red', number=None, symbol='reverse')
        idx_top = self.get_idx_top(list_card_draw, cnt_player) 
        list_card_draw[idx_top] = card

        state = GameState(
            cnt_player=cnt_player,
            idx_player_active=idx_player_active,
            list_card_draw=list_card_draw
        )
        self.game_server.set_state(state)
        state = self.game_server.get_state()
        str_state = f'GameState:\n{state}\n'

        hint = str_state
        hint += f'Error: Wrong direction after REVERSE start card.\n'
        hint += f'Hint: direction should be -1 not {state.direction}.'
        assert state.direction == -1, hint

    def test_set_up_4(self):
        """Test 009: Test case when first card on discard pile is SKIP [1 points]"""

        for cnt_player in [2, 3]:
            for idx_player_active in range(cnt_player):

                self.game_server.reset()

                list_card_draw = []
                for color in LIST_COLOR:
                    for number in range(10):
                        card = Card(color=color, number=number, symbol=None)
                        list_card_draw.append(card)

                card = Card(color='red', number=None, symbol='skip')
                idx_top = self.get_idx_top(list_card_draw, cnt_player) 
                list_card_draw[idx_top] = card

                state = GameState(
                    cnt_player=cnt_player,
                    idx_player_active=idx_player_active,
                    list_card_draw=list_card_draw
                )
                self.game_server.set_state(state)
                state = self.game_server.get_state()
                str_state = f'GameState:\n{state}\n'

                idx_player_next = (idx_player_active + 1) % cnt_player

                hint = str_state
                hint += f'Error: Wrong player after SKIP start card (cnt_player={cnt_player}).\n'
                hint += f'Hint: idx_player_active should be {idx_player_next} not {state.idx_player_active}.'
                assert state.idx_player_active == idx_player_next, hint

    def test_set_up_5(self):
        """Test 010: Test case when first card on discard pile is WILD [1 points]"""

        self.game_server.reset()

        cnt_player = 2
        idx_player_active = 0

        list_card_draw = []
        for color in LIST_COLOR:
            for number in range(10):
                card = Card(color=color, number=number, symbol=None)
                list_card_draw.append(card)

        card = Card(color='any', number=None, symbol='wild')
        idx_top = self.get_idx_top(list_card_draw, cnt_player) 
        list_card_draw[idx_top] = card

        state = GameState(
            cnt_player=cnt_player,
            idx_player_active=idx_player_active,
            list_card_draw=list_card_draw
        )
        self.game_server.set_state(state)
        state = self.game_server.get_state()
        player = state.list_player[idx_player_active]
        card = Card(color='blue', number=1, symbol=None)
        player.list_card = [card]
        self.game_server.set_state(state)
        state = self.game_server.get_state()
        str_state = f'GameState:\n{state}\n'

        list_action_found = self.game_server.get_list_action()
        list_action_expected = []
        action = Action(card=card, color=card.color, draw=None)
        list_action_expected.append(action)
        action = Action(card=None, color=None, draw=1)
        list_action_expected.append(action)

        hint = str_state
        hint += 'Error: "get_list_action" result is wrong.\n'
        hint += '  - Expected:\n'
        hint += f'{self.get_list_action_as_str(list_action_expected)}\n'
        hint += '  - Found:\n'
        hint += f'{self.get_list_action_as_str(list_action_found)}'
        assert sorted(list_action_found) == sorted(list_action_expected), hint


    def test_draw_1(self):
        """Test 011: Test draw 1 once [2 points]"""

        self.game_server.reset()

        cnt_player = 2
        idx_player_active = 0

        list_card_draw = []
        for color in ['red', 'blue', 'yellow']:  # no green cards
            for number in range(1, 10):  # no 0 cards
                card = Card(color=color, number=number, symbol=None)
                list_card_draw.append(card)

        card = Card(color='green', number=0, symbol=None)
        idx_top = self.get_idx_top(list_card_draw, cnt_player)
        list_card_draw[idx_top] = card

        state = GameState(
            cnt_player=cnt_player,
            idx_player_active=idx_player_active,
            list_card_draw=list_card_draw
        )
        self.game_server.set_state(state)
        state = self.game_server.get_state()
        player = state.list_player[idx_player_active]
        card = Card(color='red', number=1, symbol=None)
        card2 = Card(color='blue', number=7, symbol=None)
        player.list_card = [card, card2]
        card = Card(color='green', number=None, symbol='2')
        state.list_card_draw.append(card)
        self.game_server.set_state(state)
        state = self.game_server.get_state()
        str_state_1 = f'GameState:\n{state}\n'

        list_action_found = self.game_server.get_list_action()
        list_action_expected = []
        action = Action(card=None, color=None, draw=1)
        list_action_expected.append(action)

        hint = str_state_1
        hint += 'Error 1: "get_list_action" result is wrong.\n'
        hint += '  - Expected:\n'
        hint += f'{self.get_list_action_as_str(list_action_expected)}\n'
        hint += '  - Found:\n'
        hint += f'{self.get_list_action_as_str(list_action_found)}'
        assert sorted(list_action_found) == sorted(list_action_expected), hint

        self.game_server.apply_action(action)
        str_action_1 = f'Action: {action}\n'

        state = self.game_server.get_state()
        str_state_2 = f'GameState:\n{state}\n'

        hint = str_state_1
        hint += str_action_1
        hint += str_state_2
        hint += f'Error 2: Wrong player active.\n'
        hint += f'Player {idx_player_active} should be active, found Player {state.idx_player_active}.'
        assert state.idx_player_active == idx_player_active, hint

        list_action_found = self.game_server.get_list_action()
        list_action_expected = []
        action = Action(card=card, color=card.color, draw=None)
        list_action_expected.append(action)

        hint = str_state_1
        hint += str_action_1
        hint += str_state_2
        hint += 'Error 2: "get_list_action" result is wrong\n'
        hint += '  - Expected:\n'
        hint += f'{self.get_list_action_as_str(list_action_expected)}\n'
        hint += '  - Found:\n'
        hint += f'{self.get_list_action_as_str(list_action_found)}'
        assert sorted(list_action_found) == sorted(list_action_expected), hint

    def test_draw_two_1(self):
        """Test 012: Test draw two [2 points]"""

        self.game_server.reset()

        cnt_player = 2
        idx_player_active = 0

        list_card_draw = []
        for color in LIST_COLOR:
            for number in range(10):
                card = Card(color=color, number=number, symbol=None)
                list_card_draw.append(card)

        card = Card(color='green', number=None, symbol='draw2')
        idx_top = self.get_idx_top(list_card_draw, cnt_player) 
        list_card_draw[idx_top] = card

        state = GameState(
            cnt_player=cnt_player,
            idx_player_active=idx_player_active,
            list_card_draw=list_card_draw
        )
        self.game_server.set_state(state)
        state = self.game_server.get_state()
        player = state.list_player[idx_player_active]
        card = Card(color='red', number=1, symbol=None)
        player.list_card = [card]
        self.game_server.set_state(state)
        state = self.game_server.get_state()

        list_action_found = self.game_server.get_list_action()
        list_action_expected = []
        action = Action(card=None, color=None, draw=2)
        list_action_expected.append(action)

        hint = 'Error: "get_list_action" result is wrong.\n'
        hint += '  - Expected:\n'
        hint += f'{self.get_list_action_as_str(list_action_expected)}\n'
        hint += '  - Found:\n'
        hint += f'{self.get_list_action_as_str(list_action_found)}'
        assert sorted(list_action_found) == sorted(list_action_expected), hint

    def test_draw_two_2(self):
        """Test 013: Test draw two in sequence [2 points]"""

        self.game_server.reset()

        cnt_player = 2
        idx_player_active = 0

        list_card_draw = []
        for color in LIST_COLOR:
            for number in range(10):
                card = Card(color=color, number=number, symbol=None)
                list_card_draw.append(card)

        card = Card(color='green', number=None, symbol='draw2')
        idx_top = self.get_idx_top(list_card_draw, cnt_player)
        list_card_draw[idx_top] = card

        state = GameState(
            cnt_player=cnt_player,
            idx_player_active=idx_player_active,
            list_card_draw=list_card_draw
        )
        self.game_server.set_state(state)
        state = self.game_server.get_state()
        player = state.list_player[idx_player_active]
        card = Card(color='red', number=None, symbol='draw2')
        card2 = Card(color='red', number=1, symbol=None)
        card3 = Card(color='blue', number=7, symbol=None)
        player.list_card = [card, card2, card3]
        self.game_server.set_state(state)
        state = self.game_server.get_state()
        str_state_1 = f'GameState:\n{state}\n'

        list_action_found = self.game_server.get_list_action()
        list_action_expected = []
        action = Action(card=card, color=card.color, draw=4)
        list_action_expected.append(action)
        draw = state.cnt_to_draw if state.cnt_to_draw > 0 else 1
        action2 = Action(card=None, color=None, draw=draw)
        list_action_expected.append(action2)

        hint = str_state_1
        hint += 'Error 1: "get_list_action" result is wrong.\n'
        hint += '  - Expected:\n'
        hint += f'{self.get_list_action_as_str(list_action_expected)}\n'
        hint += '  - Found:\n'
        hint += f'{self.get_list_action_as_str(list_action_found)}'
        assert sorted(list_action_found) == sorted(list_action_expected), hint

        self.game_server.apply_action(action)
        str_action_1 = f'Action: {action}\n'

        state = self.game_server.get_state()
        str_state_2 = f'GameState:\n{state}\n'

        list_action_found = self.game_server.get_list_action()
        list_action_expected = []
        action = Action(card=None, color=None, draw=4)
        list_action_expected.append(action)

        hint = str_state_1
        hint += str_action_1
        hint += str_state_2
        hint += 'Error 2: "get_list_action" result is wrong\n'
        hint += '  - Expected:\n'
        hint += f'{self.get_list_action_as_str(list_action_expected)}\n'
        hint += '  - Found:\n'
        hint += f'{self.get_list_action_as_str(list_action_found)}'
        assert sorted(list_action_found) == sorted(list_action_expected), hint

        self.game_server.apply_action(action)
        str_action_2 = f'Action: {action}\n'

        state = self.game_server.get_state()
        str_state_3 = f'GameState:\n{state}\n'

        player = state.list_player[state.idx_player_active]
        hint = str_state_1
        hint += str_action_1
        hint += str_state_2
        hint += str_action_2
        hint += str_state_3
        hint += f'Error 3: Wrong number of drawn cards. {player.name} should have 11 cards.'
        assert len(player.list_card) == 11, hint

    def test_skip_card(self):
        """Test 014: Test SKIP card [4 points]"""

        for direction in [1, -1]:

            for cnt_player in [2, 3]:

                self.game_server.reset()

                idx_player_active = 0

                list_card_draw = []
                for color in LIST_COLOR:
                    for number in range(10):
                        card = Card(color=color, number=number, symbol=None)
                        list_card_draw.append(card)
        
                card = Card(color='green', number=1, symbol=None)
                idx_top = self.get_idx_top(list_card_draw, cnt_player) 
                list_card_draw[idx_top] = card

                state = GameState(
                    cnt_player=cnt_player,
                    idx_player_active=idx_player_active,
                    list_card_draw=list_card_draw,
                    direction=direction
                )
                self.game_server.set_state(state)
                state = self.game_server.get_state()
                player = state.list_player[idx_player_active]
                card = Card(color='green', number=None, symbol='skip')
                card2 = Card(color='blue', number=7, symbol=None)
                card3 = Card(color='blue', number=8, symbol=None)
                player.list_card = [card, card2, card3]
                self.game_server.set_state(state)
                state = self.game_server.get_state()
                str_state_1 = f'GameState:\n{state}\n'

                list_action_found = self.game_server.get_list_action()
                list_action_expected = []
                action = Action(card=card, color=card.color, draw=None)
                list_action_expected.append(action)
                action2 = Action(card=None, color=None, draw=1)
                list_action_expected.append(action2)

                hint = str_state_1
                hint += 'Error 1: "get_list_action" result is wrong.\n'
                hint += '  - Expected:\n'
                hint += f'{self.get_list_action_as_str(list_action_expected)}\n'
                hint += '  - Found:\n'
                hint += f'{self.get_list_action_as_str(list_action_found)}'
                assert sorted(list_action_found) == sorted(list_action_expected), hint

                self.game_server.apply_action(action)
                str_action = f'Action: {action}\n'

                state = self.game_server.get_state()
                str_state_2 = f'GameState:\n{state}\n'

                idx_player_next = (idx_player_active + 2 * direction + cnt_player) % cnt_player
                hint = str_state_1
                hint += str_action
                hint += str_state_2
                hint += f'Error 2: Wrong active player after SKIP card. idx_player_active should be {idx_player_next} (Player {idx_player_next + 1}).'
                assert state.idx_player_active == idx_player_next, hint

                list_action_found = self.game_server.get_list_action()

    def test_wild_draw_four_1(self):
        """Test 015: Test WILD DRAW 4 [2 points]"""

        self.game_server.reset()

        cnt_player = 2
        idx_player_active = 0

        list_card_draw = []
        for color in LIST_COLOR:
            for number in range(10):
                card = Card(color=color, number=number, symbol=None)
                list_card_draw.append(card)

        card = Card(color='green', number=1, symbol=None)
        idx_top = self.get_idx_top(list_card_draw, cnt_player) 
        list_card_draw[idx_top] = card

        state = GameState(
            cnt_player=cnt_player,
            idx_player_active=idx_player_active,
            list_card_draw=list_card_draw
        )
        self.game_server.set_state(state)
        state = self.game_server.get_state()
        player = state.list_player[idx_player_active]
        card = Card(color='green', number=2, symbol=None)
        card2 = Card(color='any', number=None, symbol='wilddraw4')
        card3 = Card(color='blue', number=7, symbol=None)
        player.list_card = [card, card2, card3]
        self.game_server.set_state(state)
        state = self.game_server.get_state()

        list_action_found = self.game_server.get_list_action()
        list_action_expected = []
        action = Action(card=card, color=card.color, draw=None)
        list_action_expected.append(action)
        action = Action(card=None, color=None, draw=1)
        list_action_expected.append(action)

        hint = f'GameState:\n{state}\n'
        hint += 'Error: "get_list_action" result is wrong.\n'
        hint += '  - Expected:\n'
        hint += f'{self.get_list_action_as_str(list_action_expected)}\n'
        hint += '  - Found:\n'
        hint += f'{self.get_list_action_as_str(list_action_found)}\n'
        hint += 'Hint: WILD DRAW 4 can only if no player has no other color matching card.'
        assert sorted(list_action_found) == sorted(list_action_expected), hint

    def test_uno_call_1(self):
        """Test 016: Test list_actions for second last card [2 points]"""

        self.game_server.reset()

        cnt_player = 2
        idx_player_active = 0

        list_card_draw = []
        for color in LIST_COLOR:
            for number in range(10):
                card = Card(color=color, number=number, symbol=None)
                list_card_draw.append(card)

        card = Card(color='green', number=1, symbol=None)
        idx_top = self.get_idx_top(list_card_draw, cnt_player) 
        list_card_draw[idx_top] = card

        state = GameState(
            cnt_player=cnt_player,
            idx_player_active=idx_player_active,
            list_card_draw=list_card_draw
        )
        self.game_server.set_state(state)
        state = self.game_server.get_state()
        player = state.list_player[idx_player_active]
        card = Card(color='green', number=2, symbol=None)
        card2 = Card(color='green', number=3, symbol=None)
        player.list_card = [card, card2]
        self.game_server.set_state(state)
        state = self.game_server.get_state()
        str_states = f'GameState:\n{state}\n'

        list_action_found = self.game_server.get_list_action()
        list_action_expected = []
        for card in player.list_card:
            action = Action(card=card, color=card.color, draw=None)
            list_action_expected.append(action)
            action = Action(card=card, color=card.color, draw=None, uno=True)
            list_action_expected.append(action)
        action = Action(card=None, color=None, draw=1)
        list_action_expected.append(action)

        hint = str_states
        hint += 'Error: "get_list_action" result is wrong.\n'
        hint += '  - Expected:\n'
        hint += f'{self.get_list_action_as_str(list_action_expected)}\n'
        hint += '  - Found:\n'
        hint += f'{self.get_list_action_as_str(list_action_found)}\n'
        hint += 'Hint: WILD DRAW 4 can only if no player has no other color matching card.'
        assert sorted(list_action_found) == sorted(list_action_expected), hint

    def test_uno_call_2(self):
        """Test 017: Test draw 4 cards after missed uno call [2 points]"""

        self.game_server.reset()

        cnt_player = 2
        idx_player_active = 0

        list_card_draw = []
        for color in LIST_COLOR:
            for number in range(10):
                card = Card(color=color, number=number, symbol=None)
                list_card_draw.append(card)

        card = Card(color='green', number=1, symbol=None)
        idx_top = self.get_idx_top(list_card_draw, cnt_player) 
        list_card_draw[idx_top] = card

        state = GameState(
            cnt_player=cnt_player,
            idx_player_active=idx_player_active,
            list_card_draw=list_card_draw
        )
        self.game_server.set_state(state)
        state = self.game_server.get_state()
        player = state.list_player[idx_player_active]
        card = Card(color='green', number=2, symbol=None)
        card2 = Card(color='green', number=3, symbol=None)
        player.list_card = [card, card2]
        self.game_server.set_state(state)
        state = self.game_server.get_state()
        str_states = f'GameState:\n{state}\n'

        card = Card(color='green', number=2, symbol=None)
        action = Action(card=card, color=card.color, draw=None)
        self.game_server.apply_action(action)
        str_states += f'Action: {action}\n'

        state = self.game_server.get_state()
        str_states += f'GameState:\n{state}\n'

        player = state.list_player[idx_player_active]
        hint = str_states
        hint += f'Error: Wrong number of cards for Player {idx_player_active+1}.\n'
        hint += 'Hint: Player needs to draw 4 cards after not calling UNO playing second last card.'
        assert len(player.list_card) == 5, hint


    def test_game_finished(self):
        """Test 018: Test game finish [2 points]"""

        self.game_server.reset()

        cnt_player = 2
        idx_player_active = 0

        list_card_draw = []
        for color in LIST_COLOR:
            for number in range(10):
                card = Card(color=color, number=number, symbol=None)
                list_card_draw.append(card)

        card = Card(color='green', number=1, symbol=None)
        idx_top = self.get_idx_top(list_card_draw, cnt_player) 
        list_card_draw[idx_top] = card

        state = GameState(
            cnt_player=cnt_player,
            idx_player_active=idx_player_active,
            list_card_draw=list_card_draw
        )
        self.game_server.set_state(state)
        state = self.game_server.get_state()
        player = state.list_player[idx_player_active]
        card = Card(color='green', number=2, symbol=None)
        player.list_card = [card]
        self.game_server.set_state(state)
        state = self.game_server.get_state()
        str_states = f'GameState:\n{state}\n'

        card = Card(color='green', number=2, symbol=None)
        action = Action(card=card, color=card.color, draw=None, uno=True)
        self.game_server.apply_action(action)
        str_states += f'Action: {action}\n'

        state = self.game_server.get_state()
        str_states += f'GameState:\n{state}\n'

        player = state.list_player[idx_player_active]
        hint = str_states
        hint += f'Error: Wrong final active player. Winner should be Player {idx_player_active+1}.\n'
        assert state.idx_player_active == idx_player_active, hint

        hint = str_states
        hint += f'Error: Wrong phase. Should be "{GamePhase.FINISHED}"".\n'
        assert state.phase == GamePhase.FINISHED, hint

    # --- helper functions ---

    def get_list_action_as_str(self, list_action):
        line = ''
        for action in list_action:
            line += f'    - {action}\n'
        if len(line) > 0:
            line = line[:-1]
        return line


if __name__ == '__main__':

    if len(sys.argv) < 3:
        print("Error: Wrong number of arguments")
        print("Use: python benchmark_dog.py python [dog.Dog]")
        print("  or python benchmark_dog.py localhost [port]")
        print("  or python benchmark_dog.py remote [host:port]")
        sys.exit()

    benchmark = UnoBenchmark(argv=sys.argv)

    if True:  # Run all tests
        benchmark.run_tests()

    else:  # Run specific test(s)
        benchmark.test_list_action_card_matching_1()
        benchmark.test_list_action_card_matching_2()
