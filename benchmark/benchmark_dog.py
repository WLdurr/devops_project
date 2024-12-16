# runcmd: cd .. & venv\Scripts\python benchmark/benchmark_dog.py python dog.Dog

import os
import sys
import abc
import benchmark
import importlib
import json
import traceback

from pydantic import BaseModel
from typing import List, Optional, Dict

from server.py.dog import Card, Marble, PlayerState, Action, GameState, GamePhase

class DogBenchmark(benchmark.Benchmark):

    CNT_PLAYERS = 4
    CNT_STEPS = 64
    CNT_BALLS = 4

    # --- tests ---

    def test_initial_game_state_values(self):
        """Test 001: Validate values of initial game state (cnt_round=1) [5 points]"""
        self.game_server.reset()
        state = self.game_server.get_state()

        assert state.phase == GamePhase.RUNNING, f'{state}Error: "phase" must be gamePhase.RUNNING initially'
        assert state.cnt_round == 1, f'{state}Error: "cnt_round" must be 1 initially'
        assert len(state.list_card_discard) == 0, f'{state}Error: len("list_card_discard") must be 0 initially'
        assert len(state.list_card_draw) == 86, f'{state}Error: len("list_card_draw") must be 86 initially'
        assert len(state.list_player) == 4, f'{state}Error: len("list_player") must be 4'
        assert state.idx_player_active >= 0, f'{state}Error: "idx_player_active" must >= 0'
        assert state.idx_player_active < 4, f'{state}Error: "idx_player_active" must < 4'
        assert state.idx_player_started == state.idx_player_active, f'{state}Error: "idx_player_active" must be == "idx_player_started"'
        assert state.card_active is None, f'{state}Error: "card_active" must be None'
        assert not state.bool_card_exchanged, f'{state}Error: bool_card_exchangedmust be False'

        for player in state.list_player:
            assert len(player.list_card) == 6, f'{state}Error: len("list_player.list_card") must be 6 initially'
            assert len(player.list_marble) == 4, f'{state}Error: len("list_player.list_marble") must be 4 initially'

    def test_later_game_state_values(self):
        """Test 002: Validate values of later game state (cnt_round=2) [5 points]"""
        self.start_game_state_at_round_2()

        state = self.game_server.get_state()

        assert state.cnt_round > 0, f'{state}Error: "cnt_round" must be > 0'
        assert len(state.list_card_draw) < 86, f'{state}Error: len("list_card_draw") must be < 86'
        assert len(state.list_player) == 4, f'{state}Error: len("list_player") must be 4'
        assert state.idx_player_active >= 0, f'{state}Error: "idx_player_active" must >= 0'
        assert state.idx_player_active < 4, f'{state}Error: "idx_player_active" must < 4'
        assert state.idx_player_started != state.idx_player_active, f'{state}Error: "idx_player_active" must be != "idx_player_started"'

        for player in state.list_player:
            assert len(player.list_marble) == 4, f'{state}Error: len("list_player.list_marble") must be 4 initially'

    def test_get_list_action_without_start_cards(self):
        """Test 003: Test get_list_action without start-cards [1 point]"""
        self.game_server.reset()
        state = self.game_server.get_state()

        idx_player_active = 0
        state.cnt_round = 0
        state.idx_player_started = idx_player_active
        state.idx_player_active = idx_player_active
        state.bool_card_exchanged = True
        player = state.list_player[idx_player_active]
        player.list_card = [Card(suit='♣', rank='3'), Card(suit='♦', rank='9'), Card(suit='♣', rank='10'), Card(suit='♥', rank='Q'), Card(suit='♠', rank='7'), Card(suit='♣', rank='J')]
        self.game_server.set_state(state)
        str_state = str(state)

        list_action_found = self.game_server.get_list_action()
        list_action_expected = []

        hint = str_state
        hint += 'Error: "get_list_action" result is wrong'
        hint += f'\nExpected:'
        hint += f'\n{self.get_list_action_as_str(list_action_expected)}'
        hint += f'\nFound:'
        hint += f'\n{self.get_list_action_as_str(list_action_found)}'
        assert self.get_sorted_list_action(list_action_found) == self.get_sorted_list_action(list_action_expected), hint

    def test_get_list_action_with_one_start_card(self):
        """Test 004: Test get_list_action with one start-card [1 point]"""

        list_card = [Card(suit='♦', rank='A'), Card(suit='♥', rank='K'), Card(suit='', rank='JKR')]

        for card in list_card:
            self.game_server.reset()
            state = self.game_server.get_state()

            idx_player_active = 0
            state.cnt_round = 0
            state.idx_player_started = idx_player_active
            state.idx_player_active = idx_player_active
            state.bool_card_exchanged = True
            player = state.list_player[idx_player_active]
            player.list_card = [Card(suit='♣', rank='10'), Card(suit='♥', rank='Q'), Card(suit='♠', rank='7'), Card(suit='♣', rank='J'), card]
            self.game_server.set_state(state)
            str_state = str(state)

            list_action_found = self.game_server.get_list_action()
            action = Action(card=card, pos_from=64, pos_to=0)

            hint = str_state
            hint += f'Error: "get_list_action" must return an action to get out of kennel for {card}'
            hint += f'\nFound:'
            hint += f'\n{self.get_list_action_as_str(list_action_found)}'
            assert action in list_action_found, hint

    def test_get_list_action_with_three_start_cards(self):
        """Test 005: Test get_list_action with three start-cards [1 point]"""

        self.game_server.reset()
        state = self.game_server.get_state()

        idx_player_active = 0
        state.cnt_round = 0
        state.idx_player_started = idx_player_active
        state.idx_player_active = idx_player_active
        state.bool_card_exchanged = True
        player = state.list_player[idx_player_active]
        player.list_card = [Card(suit='♣', rank='10'), Card(suit='♦', rank='A'), Card(suit='♠', rank='2'), Card(suit='♥', rank='K'), Card(suit='♠', rank='7'), Card(suit='♥', rank='A')]
        self.game_server.set_state(state)
        str_state = str(state)

        list_action = self.game_server.get_list_action()
        list_action_found = self.get_sorted_list_action(list_action)
        list_action_expected = self.get_sorted_list_action([
            Action(card=Card(suit='♦', rank='A'), pos_from=64, pos_to=0),
            Action(card=Card(suit='♥', rank='K'), pos_from=64, pos_to=0),
            Action(card=Card(suit='♥', rank='A'), pos_from=64, pos_to=0)
        ])

        hint = str_state
        hint += f'Error 1: "get_list_action" must return {len(list_action_expected)} not {len(list_action_found)} actions'
        assert len(list_action_found) == len(list_action_expected), hint

        hint = str_state
        hint += 'Error 2: "get_list_action" list is wrong'
        hint += f'\nExpected:'
        hint += f'\n{self.get_list_action_as_str(list_action_expected)}'
        hint += f'\nFound:'
        hint += f'\n{self.get_list_action_as_str(list_action_found)}'
        assert self.get_sorted_list_action(list_action_found) == self.get_sorted_list_action(list_action_expected), hint

    def test_move_out_of_kennel_1(self):
        """Test 006: Test move out of kennel without marble on start [1 point]"""

        self.game_server.reset()
        state = self.game_server.get_state()

        idx_player_active = 0
        state.cnt_round = 0
        state.idx_player_started = idx_player_active
        state.idx_player_active = idx_player_active
        state.bool_card_exchanged = True
        player = state.list_player[idx_player_active]
        player.list_card = [Card(suit='♦', rank='A'), Card(suit='♣', rank='10')]
        self.game_server.set_state(state)
        str_state_1 = str(state)

        action = Action(card=Card(suit='♦', rank='A'), pos_from=64, pos_to=0)
        self.game_server.apply_action(action)
        str_action = f'Action: {action}\n'

        state = self.game_server.get_state()
        str_state_2 = str(state)

        marble_found = False
        marble_save = False
        player = state.list_player[idx_player_active]

        idx_marble = self.get_idx_marble(player=player, pos=0)
        if idx_marble != -1:
            marble_found = True
            marble_save = player.list_marble[idx_marble].is_save

        hint = str_state_1 + str_action + str_state_2
        hint += 'Error: Player 1 must end with a marble at pos=0'
        assert marble_found, hint
        hint = str_state_1 + str_action + str_state_2
        hint += 'Error: Status of marble at pos=0 must be "is_save"=True'
        assert marble_save, hint

    def test_move_out_of_kennel_2(self):
        """Test 007: Test move out of kennel with self-blocking on start [1 point]"""

        self.game_server.reset()
        state = self.game_server.get_state()

        idx_player_active = 0
        state.cnt_round = 0
        state.idx_player_started = idx_player_active
        state.idx_player_active = idx_player_active
        state.bool_card_exchanged = True
        player = state.list_player[idx_player_active]
        player.list_card = [Card(suit='♦', rank='A')]
        player.list_marble[0].pos = 0
        player.list_marble[0].is_save = True
        self.game_server.set_state(state)
        str_state = str(state)

        list_action = self.game_server.get_list_action()
        list_action_found = [action for action in list_action if action.pos_from >= 64 and action.pos_from < 68]
        list_action_expected = []

        hint = str_state
        hint += f'Error: "get_list_action" must return {len(list_action_expected)} not {len(list_action_found)} actions'
        hint += '\nHint: Player 1\'s marbel on start is blocking.'
        assert len(list_action_found) == len(list_action_expected), hint

    def test_move_out_of_kennel_3(self):
        """Test 008: Test move out of kennel with oponent on start [1 point]"""

        self.game_server.reset()
        state = self.game_server.get_state()

        idx_player_active = 0
        state.cnt_round = 0
        state.idx_player_started = idx_player_active
        state.idx_player_active = idx_player_active
        state.bool_card_exchanged = True
        player = state.list_player[idx_player_active]
        player.list_card = [Card(suit='♦', rank='A')]
        player2 = state.list_player[idx_player_active + 1]
        player2.list_marble[0].pos = 0
        player2.list_marble[0].is_save = False
        self.game_server.set_state(state)
        str_state_1 = str(state)

        list_action_found = self.game_server.get_list_action()
        action = Action(card=Card(suit='♦', rank='A'), pos_from=64, pos_to=0)
        list_action_expected = [action]

        hint = str_state_1
        hint += f'Error: "get_list_action" must return {len(list_action_expected)} not {len(list_action_found)} actions'
        assert len(list_action_found) == len(list_action_expected), hint

        self.game_server.apply_action(action)
        str_action = f'Action: {action}\n'

        state = self.game_server.get_state()
        str_state_2 = str(state)

        player = state.list_player[idx_player_active]
        found = self.get_idx_marble(player=player, pos=0) != -1
        hint = str_state_1 + str_action + str_state_2
        hint += 'Error: Player 1\'s marble must be on start (pos=0)'
        assert found, hint

        player2 = state.list_player[idx_player_active + 1]
        found = self.get_idx_marble(player=player2, pos=72) != -1
        hint = str_state_1 + str_action + str_state_2
        hint += 'Error: Player 2\'s marble must be back in kennel (pos=72)'
        assert found, hint

    def test_move_with_ACE_from_start(self):
        """Test 009: Test move with card ACE from start [1 point]"""

        list_test = [
            {'card': Card(suit='♣', rank='A'), 'list_steps': [1, 11]},
            {'card': Card(suit='♦', rank='A'), 'list_steps': [1, 11]},
            {'card': Card(suit='♥', rank='A'), 'list_steps': [1, 11]},
            {'card': Card(suit='♠', rank='A'), 'list_steps': [1, 11]},
        ]
        self.move_test(pos_from=0, list_test=list_test)

    def test_move_with_TWO_from_start(self):
        """Test 010: Test move with card TWO from start [1 point]"""

        list_test = [
            {'card': Card(suit='♣', rank='2'), 'list_steps': [2]},
            {'card': Card(suit='♦', rank='2'), 'list_steps': [2]},
            {'card': Card(suit='♥', rank='2'), 'list_steps': [2]},
            {'card': Card(suit='♠', rank='2'), 'list_steps': [2]},
        ]
        self.move_test(pos_from=0, list_test=list_test)

    def test_move_with_THREE_from_start(self):
        """Test 011: Test move with card THREE from start [1 point]"""

        list_test = [
            {'card': Card(suit='♣', rank='3'), 'list_steps': [3]},
            {'card': Card(suit='♦', rank='3'), 'list_steps': [3]},
            {'card': Card(suit='♥', rank='3'), 'list_steps': [3]},
            {'card': Card(suit='♠', rank='3'), 'list_steps': [3]},
        ]
        self.move_test(pos_from=0, list_test=list_test)

    def test_move_with_FOUR_from_start(self):
        """Test 012: Test move with card FOUR from start [1 point]"""

        list_test = [
            {'card': Card(suit='♣', rank='4'), 'list_steps': [4, -4]},
            {'card': Card(suit='♦', rank='4'), 'list_steps': [4, -4]},
            {'card': Card(suit='♥', rank='4'), 'list_steps': [4, -4]},
            {'card': Card(suit='♠', rank='4'), 'list_steps': [4, -4]},
        ]
        self.move_test(pos_from=0, list_test=list_test)

    def test_move_with_FIVE_from_start(self):
        """Test 013: Test move with card FIVE from start [1 point]"""

        list_test = [
            {'card': Card(suit='♣', rank='5'), 'list_steps': [5]},
            {'card': Card(suit='♦', rank='5'), 'list_steps': [5]},
            {'card': Card(suit='♥', rank='5'), 'list_steps': [5]},
            {'card': Card(suit='♠', rank='5'), 'list_steps': [5]},
        ]
        self.move_test(pos_from=0, list_test=list_test)

    def test_move_with_SIX_from_start(self):
        """Test 014: Test move with card SIX from start [1 point]"""

        list_test = [
            {'card': Card(suit='♣', rank='6'), 'list_steps': [6]},
            {'card': Card(suit='♦', rank='6'), 'list_steps': [6]},
            {'card': Card(suit='♥', rank='6'), 'list_steps': [6]},
            {'card': Card(suit='♠', rank='6'), 'list_steps': [6]},
        ]
        self.move_test(pos_from=0, list_test=list_test)

    def test_move_with_SEVEN_from_start(self):
        """Test 015: Test move with card SEVEN from start [1 point]"""

        list_test = [
            {'card': Card(suit='♣', rank='7'), 'list_steps': [1, 2, 3, 4, 5, 6, 7]},
            {'card': Card(suit='♦', rank='7'), 'list_steps': [1, 2, 3, 4, 5, 6, 7]},
            {'card': Card(suit='♥', rank='7'), 'list_steps': [1, 2, 3, 4, 5, 6, 7]},
            {'card': Card(suit='♠', rank='7'), 'list_steps': [1, 2, 3, 4, 5, 6, 7]},
        ]
        self.move_test(pos_from=0, list_test=list_test)

    def test_move_with_EIGHT_from_start(self):
        """Test 016: Test move with card EIGHT from start [1 point]"""

        list_test = [
            {'card': Card(suit='♣', rank='8'), 'list_steps': [8]},
            {'card': Card(suit='♦', rank='8'), 'list_steps': [8]},
            {'card': Card(suit='♥', rank='8'), 'list_steps': [8]},
            {'card': Card(suit='♠', rank='8'), 'list_steps': [8]},
        ]
        self.move_test(pos_from=0, list_test=list_test)

    def test_move_with_NINE_from_start(self):
        """Test 017: Test move with card NINE from start [1 point]"""

        list_test = [
            {'card': Card(suit='♣', rank='9'), 'list_steps': [9]},
            {'card': Card(suit='♦', rank='9'), 'list_steps': [9]},
            {'card': Card(suit='♥', rank='9'), 'list_steps': [9]},
            {'card': Card(suit='♠', rank='9'), 'list_steps': [9]},
        ]
        self.move_test(pos_from=0, list_test=list_test)

    def test_move_with_TEN_from_start(self):
        """Test 018: Test move with card TEN from start [1 point]"""

        list_test = [
            {'card': Card(suit='♣', rank='10'), 'list_steps': [10]},
            {'card': Card(suit='♦', rank='10'), 'list_steps': [10]},
            {'card': Card(suit='♥', rank='10'), 'list_steps': [10]},
            {'card': Card(suit='♠', rank='10'), 'list_steps': [10]},
        ]
        self.move_test(pos_from=0, list_test=list_test)

    def test_move_with_QUEEN_from_start(self):
        """Test 019: Test move with card QUEEN from start [1 point]"""

        list_test = [
            {'card': Card(suit='♣', rank='Q'), 'list_steps': [12]},
            {'card': Card(suit='♦', rank='Q'), 'list_steps': [12]},
            {'card': Card(suit='♥', rank='Q'), 'list_steps': [12]},
            {'card': Card(suit='♠', rank='Q'), 'list_steps': [12]},
        ]
        self.move_test(pos_from=0, list_test=list_test)

    def test_move_with_KING_from_start(self):
        """Test 020: Test move with card KING from start [1 point]"""

        list_test = [
            {'card': Card(suit='♣', rank='K'), 'list_steps': [13]},
            {'card': Card(suit='♦', rank='K'), 'list_steps': [13]},
            {'card': Card(suit='♥', rank='K'), 'list_steps': [13]},
            {'card': Card(suit='♠', rank='K'), 'list_steps': [13]},
        ]
        self.move_test(pos_from=0, list_test=list_test)

    def test_swap_with_JAKE_1(self):
        """Test 021: Test swap list_actions with card JAKE and oponents [1 point]"""

        list_card = [Card(suit='♣', rank='J'), Card(suit='♦', rank='J'), Card(suit='♥', rank='J'), Card(suit='♠', rank='J')]

        for card in list_card:
            self.game_server.reset()
            state = self.game_server.get_state()

            idx_player_active = 0
            state.cnt_round = 0
            state.idx_player_started = idx_player_active
            state.idx_player_active = idx_player_active
            state.bool_card_exchanged = True
            for idx_player, player in enumerate(state.list_player):
                if idx_player == idx_player_active:
                    player.list_card = [card]
                marble = player.list_marble[0]
                marble.pos = idx_player * 16
                marble.is_save = True  # save oponents cant be moved!
                marble = player.list_marble[1]
                marble.pos = idx_player * 16 + 1
                marble.is_save = False

            self.game_server.set_state(state)
            str_state = str(state)

            list_action_found = self.game_server.get_list_action()
            list_action_expected = [
                Action(card=card, pos_from=0, pos_to=17),
                Action(card=card, pos_from=0, pos_to=33),
                Action(card=card, pos_from=0, pos_to=49),
                Action(card=card, pos_from=1, pos_to=17),
                Action(card=card, pos_from=1, pos_to=33),
                Action(card=card, pos_from=1, pos_to=49),
                Action(card=card, pos_from=17, pos_to=0),
                Action(card=card, pos_from=33, pos_to=0),
                Action(card=card, pos_from=49, pos_to=0),
                Action(card=card, pos_from=17, pos_to=1),
                Action(card=card, pos_from=33, pos_to=1),
                Action(card=card, pos_from=49, pos_to=1)
            ]

            hint = str_state
            hint += f'Error 1: "get_list_action" must return {len(list_action_expected)} not {len(list_action_found)} actions'
            hint += f'\nExpected actions:'
            for action in list_action_expected:
                hint += f'\n - {action}'
            hint += f'\nFound actions:'
            for action in list_action_found:
                hint += f'\n - {action}'
            assert len(list_action_found) == len(list_action_expected), hint

            hint = str_state
            hint += 'Error 2: "get_list_action" result is wrong'
            hint += f'\nExpected:'
            hint += f'\n{self.get_list_action_as_str(self.get_sorted_list_action(list_action_expected))}'
            hint += f'\nFound:'
            hint += f'\n{self.get_list_action_as_str(self.get_sorted_list_action(list_action_found))}'
            hint += f'\nHint: Oponents that are save on start can not be swaped'
            assert self.get_sorted_list_action(list_action_found) == self.get_sorted_list_action(list_action_expected), hint

    def test_swap_with_JAKE_2(self):
        """Test 022: Test swap list_actions with card JAKE no oponents and no other actions [1 point]"""

        list_card = [Card(suit='♣', rank='J'), Card(suit='♦', rank='J'), Card(suit='♥', rank='J'), Card(suit='♠', rank='J')]

        for card in list_card:
            self.game_server.reset()
            state = self.game_server.get_state()

            idx_player_active = 0
            state.cnt_round = 0
            state.idx_player_started = idx_player_active
            state.idx_player_active = idx_player_active
            state.bool_card_exchanged = True
            for idx_player, player in enumerate(state.list_player):
                if idx_player == idx_player_active:
                    player.list_card = [card]
                    marble = player.list_marble[0]
                    marble.pos = idx_player * 16
                    marble.is_save = True
                    marble = player.list_marble[1]
                    marble.pos = idx_player * 16 + 1
                    marble.is_save = True

            self.game_server.set_state(state)
            str_state = str(state)

            list_action_found = self.game_server.get_list_action()

            # TODO: Remove list_action_expected_2 for next semester

            list_action_expected = []
            list_action_expected_2 = [  # acceped too, as we won't change the logic anymore
                Action(card=card, pos_from=0, pos_to=1),
                Action(card=card, pos_from=1, pos_to=0)
            ]

            hint = str_state
            hint +=f'Error 1: "get_list_action" must return {len(list_action_expected)} not {len(list_action_found)} actions'
            hint += f'\nExpected actions:'
            for action in list_action_expected:
                    hint += f'\n - {action}'
            hint += f'\nFound actions:'
            for action in list_action_found:
                    hint += f'\n - {action}'
            if len(list_action_found) == len(list_action_expected_2):
                print('WARNING')
                print(hint)
            else:
                assert len(list_action_found) == len(list_action_expected), hint

            hint = str_state
            hint += 'Error 2: "get_list_action" result is wrong'
            hint += f'\nExpected:'
            hint += f'\n{self.get_list_action_as_str(list_action_expected)}'
            hint += f'\nFound:'
            hint += f'\n{self.get_list_action_as_str(list_action_found)}'
            hint += f'\nHint: Own marbles can\'t be swapped'
            if len(list_action_found) == len(list_action_expected_2):
                print('WARNING')
                print(hint)
            else:
                assert self.get_sorted_list_action(list_action_found) == self.get_sorted_list_action(list_action_expected), hint


    def test_swap_with_JAKE_3(self):
        """Test 023: Test swap action with card JAKE and oponents [1 point]"""

        list_card = [Card(suit='♣', rank='J'), Card(suit='♦', rank='J'), Card(suit='♥', rank='J'), Card(suit='♠', rank='J')]

        for card in list_card:
            self.game_server.reset()
            state = self.game_server.get_state()

            idx_player_active = 0
            state.cnt_round = 0
            state.idx_player_started = idx_player_active
            state.idx_player_active = idx_player_active
            state.bool_card_exchanged = True
            for idx_player, player in enumerate(state.list_player):
                if idx_player == idx_player_active:
                    player.list_card = [card]
                marble = player.list_marble[0]
                marble.pos = idx_player * 16
                marble.is_save = True  # save oponents cant be moved!
                marble = player.list_marble[1]
                marble.pos = idx_player * 16 + 1
                marble.is_save = False

            self.game_server.set_state(state)
            str_state_1 = str(state)

            action = Action(card=card, pos_from=0, pos_to=17)
            self.game_server.apply_action(action)
            str_action = f'Action: {action}\n'

            state = self.game_server.get_state()
            str_state_2 = str(state)

            player1 = state.list_player[idx_player_active]
            player2 = state.list_player[idx_player_active + 1]
            is_swapped = self.get_idx_marble(player=player1, pos=17) != -1 and \
                self.get_idx_marble(player=player2, pos=0) != -1

            hint = str_state_1 + str_action + str_state_2
            hint += 'Error: Player 1\'s marble on pos=0 should be swapped with Player 2\'s marble on pos=17'
            assert is_swapped, hint

    def test_swap_with_JAKE_4(self):
        """Test 024: Test swap action with card JAKE and no oponent and no other actions [1 point]"""

        list_card = [Card(suit='♣', rank='J'), Card(suit='♦', rank='J'), Card(suit='♥', rank='J'), Card(suit='♠', rank='J')]

        for card in list_card:
            self.game_server.reset()
            state = self.game_server.get_state()

            idx_player_active = 0
            state.cnt_round = 0
            state.idx_player_started = idx_player_active
            state.idx_player_active = idx_player_active
            state.bool_card_exchanged = True
            for idx_player, player in enumerate(state.list_player):
                if idx_player == idx_player_active:
                    player.list_card = [card]
                    marble = player.list_marble[0]
                    marble.pos = idx_player * 16
                    marble.is_save = True
                    marble = player.list_marble[1]
                    marble.pos = idx_player * 16 + 1
                    marble.is_save = True

            self.game_server.set_state(state)
            str_state = str(state)

            list_action_found = self.game_server.get_list_action()
            action = Action(card=card, pos_from=0, pos_to=1)

            hint = str_state
            hint += 'Error: Player 1 should be able to use JAKE without any oponents and no other actions'
            assert action in list_action_found, hint

    def test_chose_card_with_JOKER_1(self):
        """Test 025: Test JOKER card at beginning [5 point]"""

        list_card = [Card(suit='', rank='JKR')]
        LIST_SUIT: List[str] = ['♠', '♥', '♦', '♣']

        for card in list_card:
            self.game_server.reset()
            state = self.game_server.get_state()

            idx_player_active = 0
            state.cnt_round = 0
            state.idx_player_started = idx_player_active
            state.idx_player_active = idx_player_active
            state.bool_card_exchanged = True
            player = state.list_player[idx_player_active]
            player.list_card = [Card(suit='', rank='JKR')]
            self.game_server.set_state(state)
            str_state = str(state)

            list_action_found = self.game_server.get_list_action()
            list_action_expected = [
                Action(card=Card(suit='', rank='JKR'), pos_from=64, pos_to=0),
            ]
            for suit in LIST_SUIT:
                list_action_expected.extend([
                    Action(card=Card(suit='', rank='JKR'), pos_from=None, pos_to=None, card_swap=Card(suit=suit, rank='A')),
                    Action(card=Card(suit='', rank='JKR'), pos_from=None, pos_to=None, card_swap=Card(suit=suit, rank='K')),
                ])

            hint = str_state
            hint += f'Error 1: "get_list_action" must return {len(list_action_expected)} not {len(list_action_found)} actions'
            assert len(list_action_found) == len(list_action_expected), hint

            hint = str_state
            hint += 'Error 2: "get_list_action" result is wrong'
            hint += f'\nExpected:'
            hint += f'\n{self.get_list_action_as_str(list_action_expected)}'
            hint += f'\nFound:'
            hint += f'\n{self.get_list_action_as_str(list_action_found)}'
            assert self.get_sorted_list_action(list_action_found) == self.get_sorted_list_action(list_action_expected), hint

    def test_chose_card_with_JOKER_2(self):
        """Test 026: Test JOKER card in later game [5 point]"""

        list_card = [Card(suit='', rank='JKR')]
        LIST_SUIT: List[str] = ['♠', '♥', '♦', '♣']

        for card in list_card:
            self.game_server.reset()
            state = self.game_server.get_state()

            idx_player_active = 0
            state.cnt_round = 0
            state.idx_player_started = idx_player_active
            state.idx_player_active = idx_player_active
            state.bool_card_exchanged = True
            for idx_player, player in enumerate(state.list_player):
                if idx_player == idx_player_active:
                    player.list_card = [card]
                marble = player.list_marble[0]
                marble.pos = idx_player * 16
                marble.is_save = True  # save oponents cant be moved!
                marble = player.list_marble[1]
                marble.pos = idx_player * 16 + 1
                marble.is_save = False
            self.game_server.set_state(state)
            str_state = str(state)

            list_action_found = self.game_server.get_list_action()
            list_action_expected = []
            for suit in LIST_SUIT:
                list_action_expected.extend([
                    Action(card=Card(suit='', rank='JKR'), pos_from=None, pos_to=None, card_swap=Card(suit=suit, rank='2')),
                    Action(card=Card(suit='', rank='JKR'), pos_from=None, pos_to=None, card_swap=Card(suit=suit, rank='3')),
                    Action(card=Card(suit='', rank='JKR'), pos_from=None, pos_to=None, card_swap=Card(suit=suit, rank='4')),
                    Action(card=Card(suit='', rank='JKR'), pos_from=None, pos_to=None, card_swap=Card(suit=suit, rank='5')),
                    Action(card=Card(suit='', rank='JKR'), pos_from=None, pos_to=None, card_swap=Card(suit=suit, rank='6')),
                    Action(card=Card(suit='', rank='JKR'), pos_from=None, pos_to=None, card_swap=Card(suit=suit, rank='7')),
                    Action(card=Card(suit='', rank='JKR'), pos_from=None, pos_to=None, card_swap=Card(suit=suit, rank='8')),
                    Action(card=Card(suit='', rank='JKR'), pos_from=None, pos_to=None, card_swap=Card(suit=suit, rank='9')),
                    Action(card=Card(suit='', rank='JKR'), pos_from=None, pos_to=None, card_swap=Card(suit=suit, rank='10')),
                    Action(card=Card(suit='', rank='JKR'), pos_from=None, pos_to=None, card_swap=Card(suit=suit, rank='A')),
                    Action(card=Card(suit='', rank='JKR'), pos_from=None, pos_to=None, card_swap=Card(suit=suit, rank='J')),
                    Action(card=Card(suit='', rank='JKR'), pos_from=None, pos_to=None, card_swap=Card(suit=suit, rank='K')),
                    Action(card=Card(suit='', rank='JKR'), pos_from=None, pos_to=None, card_swap=Card(suit=suit, rank='Q')),
                ])
            hint = str_state
            hint += f'Error 1: "get_list_action" must return {len(list_action_expected)} not {len(list_action_found)} actions'
            assert len(list_action_found) == len(list_action_expected), hint

            hint = str_state
            hint += 'Error 2: "get_list_action" result is wrong'
            hint += f'\nExpected:'
            hint += f'\n{self.get_list_action_as_str(list_action_expected)}'
            hint += f'\nFound:'
            hint += f'\n{self.get_list_action_as_str(list_action_found)}'
            assert self.get_sorted_list_action(list_action_found) == self.get_sorted_list_action(list_action_expected), hint

        list_card = [Card(suit='♦', rank='A'), Card(suit='♥', rank='K'), Card(suit='', rank='JKR')]

        for card in list_card:
            self.game_server.reset()
            state = self.game_server.get_state()

            idx_player_active = 0
            state.cnt_round = 0
            state.idx_player_started = idx_player_active
            state.idx_player_active = idx_player_active
            state.bool_card_exchanged = True
            player = state.list_player[idx_player_active]
            player.list_card = [Card(suit='♣', rank='10'), Card(suit='♥', rank='Q'), Card(suit='♠', rank='7'), Card(suit='♣', rank='J'), card]
            self.game_server.set_state(state)
            str_state = str(state)

            list_action_found = self.game_server.get_list_action()
            action = Action(card=card, pos_from=64, pos_to=0)

            hint = str_state
            hint += f'Error 3: "get_list_action" must return at least one action to get out of kennel for {card}'
            assert action in list_action_found, hint

    def test_chose_card_with_JOKER_3(self):
        """Test 027: Test JOKER card with swap action [3 point]"""

        card_swap = Card(suit='♥', rank='A')

        self.game_server.reset()
        state = self.game_server.get_state()

        idx_player_active = 0
        state.cnt_round = 0
        state.idx_player_started = idx_player_active
        state.idx_player_active = idx_player_active
        state.bool_card_exchanged = True
        player = state.list_player[idx_player_active]
        player.list_card = [Card(suit='', rank='JKR'), Card(suit='♠', rank='K')]
        self.game_server.set_state(state)
        str_state_1 = str(state)

        action = Action(card=Card(suit='', rank='JKR'), pos_from=None, pos_to=None, card_swap=card_swap)
        self.game_server.apply_action(action)
        str_action = f'Action: {action}\n'

        state = self.game_server.get_state()
        str_state_2 = str(state)

        hint = str_state_1 + str_action + str_state_2
        hint += f'Error 1: "card_active" must be set to "{card_swap}" after JKR was played for other card.'
        assert state.card_active == card_swap, hint

        hint = str_state_1 + str_action + str_state_2
        hint += f'Error 2: "idx_player_active" must be same after JKR was played for other card.'
        assert state.idx_player_active == idx_player_active, hint

        list_action_found = self.game_server.get_list_action()
        action = Action(card=Card(suit='♠', rank='K'), pos_from=64, pos_to=0)

        hint = str_state_1 + str_action + str_state_2
        hint += f'Error 3: "get_list_action" must return only options for replaced card "card_active" ({card_swap}).'
        assert action not in list_action_found, hint

    def test_chose_card_with_JOKER_4(self):
        """Test 028: Test with two JOKER cards [1 point]"""

        card_swap = Card(suit='♥', rank='A')

        self.game_server.reset()
        state = self.game_server.get_state()

        idx_player_active = 0
        state.cnt_round = 0
        state.idx_player_started = idx_player_active
        state.idx_player_active = idx_player_active
        state.bool_card_exchanged = True
        player = state.list_player[idx_player_active]
        player.list_card = [Card(suit='', rank='JKR'), Card(suit='', rank='JKR')]
        self.game_server.set_state(state)
        str_state_1 = str(state)

        action = Action(card=Card(suit='', rank='JKR'), pos_from=None, pos_to=None, card_swap=card_swap)
        self.game_server.apply_action(action)
        str_action = f'Action: {action}\n'

        state = self.game_server.get_state()
        str_state_2 = str(state)

        player = state.list_player[idx_player_active]
        cnt_jkr = len([card for card in player.list_card if card == Card(suit='', rank='JKR')])
        hint = str_state_1 + str_action + str_state_2
        hint += 'Error: Only one JOKER card should be replaced.'
        assert cnt_jkr == 1, hint

    def test_move_with_SEVEN_multiple_steps_1(self):
        """Test 029: Test move with card SEVEN from start [5 point]"""

        list_steps_split = [
            [1, 1, 1, 1, 1, 1, 1],
            [2, 1, 1, 1, 1, 1],
            [2, 2, 1, 1, 1],
            [2, 2, 2, 1],
            [3, 1, 1, 1, 1],
            [3, 2, 1, 1],
            [3, 2, 2],
            [3, 3, 1],
            [4, 1, 1, 1],
            [4, 2, 1],
            [4, 3],
            [5, 2],
            [6, 1],
        ]
        list_card = [Card(suit='♣', rank='7'), Card(suit='♦', rank='7'), Card(suit='♥', rank='7'), Card(suit='♠', rank='7')]

        for card in list_card:

            for steps_split in list_steps_split:

                self.game_server.reset()
                state = self.game_server.get_state()

                pos_from = 0
                card_seven_steps_remaining = 7
                card_active = card
                idx_player_active = 0
                state.cnt_round = 0
                state.idx_player_started = idx_player_active
                state.idx_player_active = idx_player_active
                state.bool_card_exchanged = True
                player = state.list_player[idx_player_active]
                player.list_card = [card, Card(suit='♠', rank='K')]
                marble = player.list_marble[0]
                marble.pos = pos_from
                marble.is_save = True
                self.game_server.set_state(state)
                str_states = str(state)

                for steps in steps_split:

                    if card_seven_steps_remaining < 7:
                        list_action_found = self.game_server.get_list_action()
                        is_okay = True
                        for action in list_action_found:
                            is_okay = is_okay and action.card in list_card
                        hint = str_states
                        hint += f'Error 1: While playing card SEVEN only actions with card SEVEN are allowed.'
                        assert is_okay, hint

                    pos_to = (pos_from + steps + self.CNT_STEPS) % self.CNT_STEPS
                    action = Action(card=card, pos_from=pos_from, pos_to=pos_to)
                    self.game_server.apply_action(action)
                    str_states += f'Action: {action}\n'

                    card_seven_steps_remaining -= steps

                    state = self.game_server.get_state()
                    str_states += str(state)

                    found = False
                    player = state.list_player[idx_player_active]
                    found = self.get_idx_marble(player=player, pos=pos_to) != -1
                    hint = str_states
                    hint += f'Error 2: Player 1\'s marble must be moved from pos={pos_from} to pos={pos_to} with card={card}'
                    assert found, hint

                    if card_seven_steps_remaining == 0:
                        idx_player_active += 1
                        card_active = None

                    hint = str_states
                    hint += f'Error 3: "idx_player_active" should be {idx_player_active} not {state.idx_player_active}'
                    assert state.idx_player_active == idx_player_active, hint

                    hint = str_states
                    hint +=f'Error 4: "card_active" must be set to "{card}" {"after" if card_active is None else "while"} steps of card SEVEN are moved.'
                    assert state.card_active == card_active, hint

                    pos_from += steps

    def test_move_with_SEVEN_multiple_steps_2(self):
        """Test 030: Test move with card SEVEN with multiple marbles [5 point]"""

        list_steps_split = [
            [1, 1, 1, 1, 1, 1, 1],
            [2, 1, 1, 1, 1, 1],
            [2, 2, 1, 1, 1],
            [2, 2, 2, 1],
            [3, 1, 1, 1, 1],
            [3, 2, 1, 1],
            [3, 2, 2],
            [3, 3, 1],
            [4, 1, 1, 1],
            [4, 2, 1],
            [4, 3],
            [5, 2],
            [6, 1],
        ]
        list_card = [Card(suit='♣', rank='7'), Card(suit='♦', rank='7'), Card(suit='♥', rank='7'), Card(suit='♠', rank='7')]

        for card in list_card:

            for steps_split in list_steps_split:

                self.game_server.reset()
                state = self.game_server.get_state()

                pos_from_1 = 0
                pos_from_2 = 12
                card_seven_steps_remaining = 7
                idx_player_active = 0
                state.cnt_round = 0
                state.idx_player_started = idx_player_active
                state.idx_player_active = idx_player_active
                state.bool_card_exchanged = True
                player = state.list_player[idx_player_active]
                player.list_card = [card]
                marble = player.list_marble[0]
                marble.pos = pos_from_1
                marble.is_save = True
                marble = player.list_marble[1]
                marble.pos = pos_from_2
                marble.is_save = False
                self.game_server.set_state(state)
                str_states = str(state)

                for i, steps in enumerate(steps_split):

                    pos_from = pos_from_1 if i % 2 == 0 else pos_from_2
                    pos_to = (pos_from + steps + self.CNT_STEPS) % self.CNT_STEPS
                    action = Action(card=card, pos_from=pos_from, pos_to=pos_to)
                    self.game_server.apply_action(action)
                    str_states += f'Action: {action}\n'

                    card_seven_steps_remaining -= steps

                    state = self.game_server.get_state()
                    str_states += str(state)

                    player = state.list_player[idx_player_active]
                    found = self.get_idx_marble(player=player, pos=pos_to) != -1
                    hint = str_states
                    hint += f'Error 1: Player 1\'s marble must be moved from pos={pos_from} to pos={pos_to} with card={card}'
                    assert found, hint

                    if card_seven_steps_remaining == 0:
                        card_seven_steps_remaining = 7
                        idx_player_active += 1

                    hint = str_states
                    hint += f'Error 2: "idx_player_active" should be {idx_player_active} not {state.idx_player_active}'
                    assert state.idx_player_active == idx_player_active, hint

                    if i % 2 == 0:
                        pos_from_1 += steps
                    else:
                        pos_from_2 += steps

    def test_move_with_SEVEN_multiple_steps_3(self):
        """Test 031: Test move with card SEVEN and kick out oponents [1 point]"""

        list_steps = [1, 2, 3, 4, 5, 6, 7]
        list_card = [Card(suit='♣', rank='7'), Card(suit='♦', rank='7'), Card(suit='♥', rank='7'), Card(suit='♠', rank='7')]

        for card in list_card:

            for steps in list_steps:

                self.game_server.reset()
                state = self.game_server.get_state()

                pos_from = 0
                pos_oponent = pos_from + steps - 1 if steps > 1 else pos_from + 1
                idx_player_active = 0
                state.cnt_round = 0
                state.idx_player_started = idx_player_active
                state.idx_player_active = idx_player_active
                state.bool_card_exchanged = True
                player = state.list_player[idx_player_active]
                player.list_card = [card]
                marble = player.list_marble[0]
                marble.pos = pos_from
                marble.is_save = True
                player = state.list_player[idx_player_active + 1]
                player.list_card = [Card(suit='♥', rank='K')]
                marble = player.list_marble[0]
                marble.pos = pos_oponent
                marble.is_save = False
                self.game_server.set_state(state)
                str_states = str(state)

                pos_to = (pos_from + steps + self.CNT_STEPS) % self.CNT_STEPS
                action = Action(card=card, pos_from=pos_from, pos_to=pos_to)
                self.game_server.apply_action(action)
                str_states += f'Action: {action}\n'

                state = self.game_server.get_state()
                str_states += str(state)

                player = state.list_player[idx_player_active]
                found = self.get_idx_marble(player=player, pos=pos_to) != -1
                hint = str_states
                hint += f'Error 1: Player 1\'s marble must be moved from pos={pos_from} to pos={pos_to} with card={card}'
                assert found, hint

                pos_from = pos_oponent
                pos_to = 72
                player = state.list_player[idx_player_active + 1]
                found = self.get_idx_marble(player=player, pos=pos_to) != -1
                hint = str_states
                hint += f'Error 2: Player 2\'s marble must be put back to kennel from pos={pos_from} to pos={pos_to}.'
                hint += f'\nHint: Player 2\'s marble was overtaken by a SEVEN move ({steps} steps).'
                assert found, hint

    def test_move_with_SEVEN_multiple_steps_4(self):
        """Test 032: Test move with card SEVEN and kick out own marbles [1 point]"""

        list_steps = [1, 2, 3, 4, 5, 6, 7]
        list_card = [Card(suit='♣', rank='7'), Card(suit='♦', rank='7'), Card(suit='♥', rank='7'), Card(suit='♠', rank='7')]

        for card in list_card:

            for steps in list_steps:

                self.game_server.reset()
                state = self.game_server.get_state()

                pos_from = 0
                pos_own = pos_from + steps - 1 if steps > 1 else pos_from + 1
                idx_player_active = 0
                state.cnt_round = 0
                state.idx_player_started = idx_player_active
                state.idx_player_active = idx_player_active
                state.bool_card_exchanged = True
                player = state.list_player[idx_player_active]
                player.list_card = [card]
                marble = player.list_marble[0]
                marble.pos = pos_from
                marble.is_save = True
                marble = player.list_marble[1]
                marble.pos = pos_own
                marble.is_save = False
                self.game_server.set_state(state)
                str_states = str(state)

                pos_to = (pos_from + steps + self.CNT_STEPS) % self.CNT_STEPS
                action = Action(card=card, pos_from=pos_from, pos_to=pos_to)
                self.game_server.apply_action(action)
                str_states += f'Action: {action}\n'

                state = self.game_server.get_state()
                str_states += str(state)

                player = state.list_player[idx_player_active]
                found = self.get_idx_marble(player=player, pos=pos_to) != -1
                hint = str_states
                hint += f'Error 1: Player 1\'s marble must be moved from pos={pos_from} to pos={pos_to} with card={card}'
                assert found, hint

                player = state.list_player[idx_player_active]
                cnt_in_kennel = 0
                for marble in player.list_marble:
                    if marble.pos >= 64:
                        cnt_in_kennel += 1
                found = cnt_in_kennel == 3
                hint = str_states
                hint += f'Error 2: Player 1\'s second marble must be put back to kennel.'
                hint += f'\nHint: Player 1\'s second marble was overtaken by a SEVEN move ({steps} steps).'
                assert found, hint

    def test_move_with_SEVEN_multiple_steps_5(self):
        """Test 033: Test move with card SEVEN and can not play all steps [10 point]"""

        list_steps = [1, 2, 3]
        list_card = [Card(suit='♣', rank='7'), Card(suit='♦', rank='7'), Card(suit='♥', rank='7'), Card(suit='♠', rank='7')]

        for card in list_card:

            self.game_server.reset()
            state = self.game_server.get_state()

            pos_blocked = 16
            pos_from = pos_blocked - sum(list_steps[:-1]) - 1
            idx_player_active = 0
            state.cnt_round = 0
            state.idx_player_started = idx_player_active
            state.idx_player_active = idx_player_active
            state.bool_card_exchanged = True
            player = state.list_player[idx_player_active]
            player.list_card = [card]
            marble = player.list_marble[0]
            marble.pos = pos_from
            marble.is_save = False
            player = state.list_player[idx_player_active + 1]
            marble = player.list_marble[0]
            marble.pos = pos_blocked
            marble.is_save = True
            marble = player.list_marble[1]
            marble.pos = pos_blocked - 1
            marble.is_save = False
            self.game_server.set_state(state)
            str_states = str(state)

            for i, steps in enumerate(list_steps):

                if i < len(list_steps) - 1:  # before last step
                    pos_to = (pos_from + steps + self.CNT_STEPS) % self.CNT_STEPS
                    action = Action(card=card, pos_from=pos_from, pos_to=pos_to)
                    self.game_server.apply_action(action)
                    str_states += f'Action: {action}\n'
                else:  # last step
                    list_action_found = self.game_server.get_list_action()

                    hint = str_states
                    hint += 'Error 1: "get_list_action" must be empty.'
                    hint += f'\nHint: Player 1 can not play all steps with card {card}.'
                    assert len(list_action_found) == 0, hint

                    self.game_server.apply_action(None)
                    str_states += f'Action: None\n'

                    state = self.game_server.get_state()
                    str_states += str(state)

                    # assert game state is reset
                    hint = str_states
                    hint += 'Error 2: Game State was not reset.'
                    hint += f'\nHint: "card_active" must be None.'
                    assert state.card_active is None, hint

                    pos_blocked = 16
                    pos_from = pos_blocked - sum(list_steps[:-1]) - 1

                    player = state.list_player[idx_player_active]
                    idx_marble = self.get_idx_marble(player=player, pos=pos_from)
                    hint = str_states
                    hint += 'Error 3: Game State was not reset.'
                    hint += f'\nHint: Player 1 must have a marble on pos {pos_from}.'
                    assert idx_marble != -1, hint

                    player = state.list_player[idx_player_active + 1]
                    idx_marble = self.get_idx_marble(player=player, pos=pos_blocked)
                    hint = str_states
                    hint += 'Error 4: Game State was not reset.'
                    hint += f'\nHint: Player 2 must have a marble on pos {pos_blocked}.'
                    assert idx_marble != -1, hint

                    idx_marble = self.get_idx_marble(player=player, pos=pos_blocked - 1)
                    hint = str_states
                    hint += 'Error 5: Game State was not reset.'
                    hint += f'\nHint: Player 2 must have a marble on pos {pos_blocked - 1}.'
                    assert idx_marble != -1, hint

                pos_from = pos_to

    def test_move_with_SEVEN_multiple_steps_6(self):
        """Test 034: Test move with card SEVEN into finish [5 point]"""

        steps_split = [5, 2]
        list_card = [Card(suit='♣', rank='7'), Card(suit='♦', rank='7'), Card(suit='♥', rank='7'), Card(suit='♠', rank='7')]

        for card in list_card:

            self.game_server.reset()
            state = self.game_server.get_state()

            pos_from = 13
            card_seven_steps_remaining = 7
            card_active = card
            idx_player_active = 1
            state.cnt_round = 0
            state.idx_player_started = idx_player_active
            state.idx_player_active = idx_player_active
            state.bool_card_exchanged = True
            player = state.list_player[idx_player_active]
            player.list_card = [card]
            marble = player.list_marble[0]
            marble.pos = pos_from
            marble.is_save = False
            self.game_server.set_state(state)
            str_states = str(state)

            for steps in steps_split:

                pos_to = 77 if steps == 5 else 79
                action = Action(card=card, pos_from=pos_from, pos_to=pos_to)
                self.game_server.apply_action(action)
                str_states += f'Action: {action}\n'

                card_seven_steps_remaining -= steps

                state = self.game_server.get_state()
                str_states += str(state)

                found = False
                player = state.list_player[idx_player_active]
                found = self.get_idx_marble(player=player, pos=pos_to) != -1
                hint = str_states
                hint += f'Error 1: Player 1\'s marble must be moved from pos={pos_from} to pos={pos_to} with card={card}'
                assert found, hint

                if card_seven_steps_remaining == 0:
                    idx_player_active += 1
                    card_active = None

                hint = str_states
                hint += f'Error 2: "idx_player_active" should be {idx_player_active} not {state.idx_player_active}'
                assert state.idx_player_active == idx_player_active, hint

                hint = str_states
                hint += f'Error 3: "card_active" must be set to "{card}" {"after" if card_active is None else "while"} steps of card SEVEN are moved.'
                assert state.card_active == card_active, hint

                pos_from = pos_to

    def test_move_with_SEVEN_multiple_steps_7(self):
        """Test 035: Test move with card SEVEN into finish [5 point]"""

        steps_split = [5, 2]
        list_card = [Card(suit='♣', rank='7'), Card(suit='♦', rank='7'), Card(suit='♥', rank='7'), Card(suit='♠', rank='7')]

        for card in list_card:

            self.game_server.reset()
            state = self.game_server.get_state()

            pos_from = 12
            card_seven_steps_remaining = 7
            idx_player_active = 1
            state.cnt_round = 0
            state.idx_player_started = idx_player_active
            state.idx_player_active = idx_player_active
            state.bool_card_exchanged = True
            player = state.list_player[idx_player_active]
            player.list_card = [card]
            marble = player.list_marble[0]
            marble.pos = pos_from
            marble.is_save = False
            self.game_server.set_state(state)
            str_states = str(state)

            for steps in steps_split:

                if steps == 2:
                    list_action_found = self.game_server.get_list_action()
                    hint = str_states
                    hint += f'Error: Too many steps possible in finish.'
                    assert len(list_action_found) == 2, hint

                pos_to = 76 if steps == 5 else 78
                action = Action(card=card, pos_from=pos_from, pos_to=pos_to)
                self.game_server.apply_action(action)
                str_states += f'Action: {action}\n'

                card_seven_steps_remaining -= steps

                state = self.game_server.get_state()
                str_states += str(state)

                pos_from = pos_to

    def test_overtake_save_marble_1(self) -> None:
        """Test 036: Test to overtake own marble on save start [1 point]"""

        self.game_server.reset()
        state = self.game_server.get_state()

        card = Card(suit='♣', rank='5')
        idx_player_active = 0
        state.cnt_round = 0
        state.idx_player_started = idx_player_active
        state.idx_player_active = idx_player_active
        state.bool_card_exchanged = True
        player = state.list_player[idx_player_active]
        player.list_card = [card]
        player.list_marble[0].pos = 63
        player.list_marble[0].is_save = False
        player.list_marble[1].pos = 0
        player.list_marble[1].is_save = True
        self.game_server.set_state(state)
        str_state = str(state)

        list_action_found = self.game_server.get_list_action()
        list_action_expected = [
            Action(card=Card(suit='♣', rank='5'), pos_from=0, pos_to=5)
        ]

        hint = str_state
        hint += 'Error: "get_list_action" result is wrong'
        hint += f'\nExpected:'
        hint += f'\n{self.get_list_action_as_str(list_action_expected)}'
        hint += f'\nFound:'
        hint += f'\n{self.get_list_action_as_str(list_action_found)}'
        hint += f'\nHint: Marbles on start with status "is_save"=True must be blocking.'
        assert self.get_sorted_list_action(list_action_found) == self.get_sorted_list_action(list_action_expected), hint

    def test_overtake_save_marble_2(self) -> None:
        """Test 037: Test to overtake oponents marble on save start [1 point]"""

        self.game_server.reset()
        state = self.game_server.get_state()

        card = Card(suit='♣', rank='5')
        idx_player_active = 0
        state.cnt_round = 0
        state.idx_player_started = idx_player_active
        state.idx_player_active = idx_player_active
        state.bool_card_exchanged = True
        player = state.list_player[idx_player_active]
        player.list_card = [card]
        player.list_marble[0].pos = 15
        player.list_marble[0].is_save = False
        player = state.list_player[idx_player_active + 1]
        player.list_marble[1].pos = 16
        player.list_marble[1].is_save = True
        self.game_server.set_state(state)
        str_state = str(state)

        list_action_found = self.game_server.get_list_action()
        list_action_expected = []

        hint = str_state
        hint += 'Error: "get_list_action" result is wrong'
        hint += f'\nExpected:'
        hint += f'\n{self.get_list_action_as_str(list_action_expected)}'
        hint += f'\nFound:'
        hint += f'\n{self.get_list_action_as_str(list_action_found)}'
        hint += f'\nHint: Marbles on start with status "is_save"=True must be blocking.'
        assert self.get_sorted_list_action(list_action_found) == self.get_sorted_list_action(list_action_expected), hint

    def test_send_home_with_simple_cards(self):
        """Test 038: Test send home with simple cards from start [1 point]"""

        list_test = [
            {'card': Card(suit='♣', rank='A'), 'list_steps': [1, 11]},
            {'card': Card(suit='♦', rank='A'), 'list_steps': [1, 11]},
            {'card': Card(suit='♥', rank='A'), 'list_steps': [1, 11]},
            {'card': Card(suit='♠', rank='A'), 'list_steps': [1, 11]},
            {'card': Card(suit='♣', rank='2'), 'list_steps': [2]},
            {'card': Card(suit='♦', rank='2'), 'list_steps': [2]},
            {'card': Card(suit='♥', rank='2'), 'list_steps': [2]},
            {'card': Card(suit='♠', rank='2'), 'list_steps': [2]},
            {'card': Card(suit='♣', rank='3'), 'list_steps': [3]},
            {'card': Card(suit='♦', rank='3'), 'list_steps': [3]},
            {'card': Card(suit='♥', rank='3'), 'list_steps': [3]},
            {'card': Card(suit='♠', rank='3'), 'list_steps': [3]},
            {'card': Card(suit='♣', rank='4'), 'list_steps': [4, -4]},
            {'card': Card(suit='♦', rank='4'), 'list_steps': [4, -4]},
            {'card': Card(suit='♥', rank='4'), 'list_steps': [4, -4]},
            {'card': Card(suit='♠', rank='4'), 'list_steps': [4, -4]},
            {'card': Card(suit='♣', rank='5'), 'list_steps': [5]},
            {'card': Card(suit='♦', rank='5'), 'list_steps': [5]},
            {'card': Card(suit='♥', rank='5'), 'list_steps': [5]},
            {'card': Card(suit='♠', rank='5'), 'list_steps': [5]},
            {'card': Card(suit='♣', rank='6'), 'list_steps': [6]},
            {'card': Card(suit='♦', rank='6'), 'list_steps': [6]},
            {'card': Card(suit='♥', rank='6'), 'list_steps': [6]},
            {'card': Card(suit='♠', rank='6'), 'list_steps': [6]},
            {'card': Card(suit='♣', rank='8'), 'list_steps': [8]},
            {'card': Card(suit='♦', rank='8'), 'list_steps': [8]},
            {'card': Card(suit='♥', rank='8'), 'list_steps': [8]},
            {'card': Card(suit='♠', rank='8'), 'list_steps': [8]},
            {'card': Card(suit='♣', rank='9'), 'list_steps': [9]},
            {'card': Card(suit='♦', rank='9'), 'list_steps': [9]},
            {'card': Card(suit='♥', rank='9'), 'list_steps': [9]},
            {'card': Card(suit='♠', rank='9'), 'list_steps': [9]},
            {'card': Card(suit='♣', rank='10'), 'list_steps': [10]},
            {'card': Card(suit='♦', rank='10'), 'list_steps': [10]},
            {'card': Card(suit='♥', rank='10'), 'list_steps': [10]},
            {'card': Card(suit='♠', rank='10'), 'list_steps': [10]},
            {'card': Card(suit='♣', rank='Q'), 'list_steps': [12]},
            {'card': Card(suit='♦', rank='Q'), 'list_steps': [12]},
            {'card': Card(suit='♥', rank='Q'), 'list_steps': [12]},
            {'card': Card(suit='♠', rank='Q'), 'list_steps': [12]},
            {'card': Card(suit='♣', rank='K'), 'list_steps': [13]},
            {'card': Card(suit='♦', rank='K'), 'list_steps': [13]},
            {'card': Card(suit='♥', rank='K'), 'list_steps': [13]},
            {'card': Card(suit='♠', rank='K'), 'list_steps': [13]},
        ]
        self.send_home_test(pos_from=0, list_test=list_test)

    def test_send_home_with_SEVEN_from_start(self):
        """Test 039: Test send home with card SEVEN from start [1 point]"""

        list_test = [
            {'card': Card(suit='♣', rank='7'), 'list_steps': [1, 2, 3, 4, 5, 6, 7]},
            {'card': Card(suit='♦', rank='7'), 'list_steps': [1, 2, 3, 4, 5, 6, 7]},
            {'card': Card(suit='♥', rank='7'), 'list_steps': [1, 2, 3, 4, 5, 6, 7]},
            {'card': Card(suit='♠', rank='7'), 'list_steps': [1, 2, 3, 4, 5, 6, 7]},
        ]
        self.send_home_test(pos_from=0, list_test=list_test)

    def test_overtake_with_simple_cards(self):
        """Test 040: Test overtake with simple cards from start [1 point]"""

        list_test = [
            {'card': Card(suit='♣', rank='A'), 'list_steps': [11]},
            {'card': Card(suit='♦', rank='A'), 'list_steps': [11]},
            {'card': Card(suit='♥', rank='A'), 'list_steps': [11]},
            {'card': Card(suit='♠', rank='A'), 'list_steps': [11]},
            {'card': Card(suit='♣', rank='2'), 'list_steps': [2]},
            {'card': Card(suit='♦', rank='2'), 'list_steps': [2]},
            {'card': Card(suit='♥', rank='2'), 'list_steps': [2]},
            {'card': Card(suit='♠', rank='2'), 'list_steps': [2]},
            {'card': Card(suit='♣', rank='3'), 'list_steps': [3]},
            {'card': Card(suit='♦', rank='3'), 'list_steps': [3]},
            {'card': Card(suit='♥', rank='3'), 'list_steps': [3]},
            {'card': Card(suit='♠', rank='3'), 'list_steps': [3]},
            {'card': Card(suit='♣', rank='4'), 'list_steps': [4, -4]},
            {'card': Card(suit='♦', rank='4'), 'list_steps': [4, -4]},
            {'card': Card(suit='♥', rank='4'), 'list_steps': [4, -4]},
            {'card': Card(suit='♠', rank='4'), 'list_steps': [4, -4]},
            {'card': Card(suit='♣', rank='5'), 'list_steps': [5]},
            {'card': Card(suit='♦', rank='5'), 'list_steps': [5]},
            {'card': Card(suit='♥', rank='5'), 'list_steps': [5]},
            {'card': Card(suit='♠', rank='5'), 'list_steps': [5]},
            {'card': Card(suit='♣', rank='6'), 'list_steps': [6]},
            {'card': Card(suit='♦', rank='6'), 'list_steps': [6]},
            {'card': Card(suit='♥', rank='6'), 'list_steps': [6]},
            {'card': Card(suit='♠', rank='6'), 'list_steps': [6]},
            {'card': Card(suit='♣', rank='8'), 'list_steps': [8]},
            {'card': Card(suit='♦', rank='8'), 'list_steps': [8]},
            {'card': Card(suit='♥', rank='8'), 'list_steps': [8]},
            {'card': Card(suit='♠', rank='8'), 'list_steps': [8]},
            {'card': Card(suit='♣', rank='9'), 'list_steps': [9]},
            {'card': Card(suit='♦', rank='9'), 'list_steps': [9]},
            {'card': Card(suit='♥', rank='9'), 'list_steps': [9]},
            {'card': Card(suit='♠', rank='9'), 'list_steps': [9]},
            {'card': Card(suit='♣', rank='10'), 'list_steps': [10]},
            {'card': Card(suit='♦', rank='10'), 'list_steps': [10]},
            {'card': Card(suit='♥', rank='10'), 'list_steps': [10]},
            {'card': Card(suit='♠', rank='10'), 'list_steps': [10]},
            {'card': Card(suit='♣', rank='Q'), 'list_steps': [12]},
            {'card': Card(suit='♦', rank='Q'), 'list_steps': [12]},
            {'card': Card(suit='♥', rank='Q'), 'list_steps': [12]},
            {'card': Card(suit='♠', rank='Q'), 'list_steps': [12]},
            {'card': Card(suit='♣', rank='K'), 'list_steps': [13]},
            {'card': Card(suit='♦', rank='K'), 'list_steps': [13]},
            {'card': Card(suit='♥', rank='K'), 'list_steps': [13]},
            {'card': Card(suit='♠', rank='K'), 'list_steps': [13]},
        ]
        self.overtake_test(pos_from=0, list_test=list_test)

    def test_move_to_empty_finish_with_simple_cards(self):
        """Test 041: Test move to finish with simple cards [5 point]"""

        list_test = [
            {'card': Card(suit='♣', rank='A'), 'list_steps': [1, 11]},
            {'card': Card(suit='♦', rank='A'), 'list_steps': [1, 11]},
            {'card': Card(suit='♥', rank='A'), 'list_steps': [1, 11]},
            {'card': Card(suit='♠', rank='A'), 'list_steps': [1, 11]},
            {'card': Card(suit='♣', rank='2'), 'list_steps': [2]},
            {'card': Card(suit='♦', rank='2'), 'list_steps': [2]},
            {'card': Card(suit='♥', rank='2'), 'list_steps': [2]},
            {'card': Card(suit='♠', rank='2'), 'list_steps': [2]},
            {'card': Card(suit='♣', rank='3'), 'list_steps': [3]},
            {'card': Card(suit='♦', rank='3'), 'list_steps': [3]},
            {'card': Card(suit='♥', rank='3'), 'list_steps': [3]},
            {'card': Card(suit='♠', rank='3'), 'list_steps': [3]},
            {'card': Card(suit='♣', rank='4'), 'list_steps': [4]},
            {'card': Card(suit='♦', rank='4'), 'list_steps': [4]},
            {'card': Card(suit='♥', rank='4'), 'list_steps': [4]},
            {'card': Card(suit='♠', rank='4'), 'list_steps': [4]},
            {'card': Card(suit='♣', rank='5'), 'list_steps': [5]},
            {'card': Card(suit='♦', rank='5'), 'list_steps': [5]},
            {'card': Card(suit='♥', rank='5'), 'list_steps': [5]},
            {'card': Card(suit='♠', rank='5'), 'list_steps': [5]},
            {'card': Card(suit='♣', rank='6'), 'list_steps': [6]},
            {'card': Card(suit='♦', rank='6'), 'list_steps': [6]},
            {'card': Card(suit='♥', rank='6'), 'list_steps': [6]},
            {'card': Card(suit='♠', rank='6'), 'list_steps': [6]},
            {'card': Card(suit='♣', rank='8'), 'list_steps': [8]},
            {'card': Card(suit='♦', rank='8'), 'list_steps': [8]},
            {'card': Card(suit='♥', rank='8'), 'list_steps': [8]},
            {'card': Card(suit='♠', rank='8'), 'list_steps': [8]},
            {'card': Card(suit='♣', rank='9'), 'list_steps': [9]},
            {'card': Card(suit='♦', rank='9'), 'list_steps': [9]},
            {'card': Card(suit='♥', rank='9'), 'list_steps': [9]},
            {'card': Card(suit='♠', rank='9'), 'list_steps': [9]},
            {'card': Card(suit='♣', rank='10'), 'list_steps': [10]},
            {'card': Card(suit='♦', rank='10'), 'list_steps': [10]},
            {'card': Card(suit='♥', rank='10'), 'list_steps': [10]},
            {'card': Card(suit='♠', rank='10'), 'list_steps': [10]},
            {'card': Card(suit='♣', rank='Q'), 'list_steps': [12]},
            {'card': Card(suit='♦', rank='Q'), 'list_steps': [12]},
            {'card': Card(suit='♥', rank='Q'), 'list_steps': [12]},
            {'card': Card(suit='♠', rank='Q'), 'list_steps': [12]},
            {'card': Card(suit='♣', rank='K'), 'list_steps': [13]},
            {'card': Card(suit='♦', rank='K'), 'list_steps': [13]},
            {'card': Card(suit='♥', rank='K'), 'list_steps': [13]},
            {'card': Card(suit='♠', rank='K'), 'list_steps': [13]},
        ]

        for idx_player in range(4):
            pos_finish = self.CNT_STEPS + idx_player * self.CNT_BALLS * 2 + self.CNT_BALLS
            for i in range(4):
                pos_to = pos_finish + i

                for test in list_test:
                    card = test['card']
                    for steps in test['list_steps']:
                        pos_start = idx_player * int(self.CNT_STEPS / self.CNT_PLAYERS)

                        if pos_to - steps < pos_finish:
                            pos_from = (pos_start - steps + (pos_to - pos_finish + 1) + self.CNT_STEPS) % self.CNT_STEPS
                        else:
                            pos_from = pos_to - steps

                        self.move_marble_to_finish(card=card, pos_from=pos_from, pos_to=pos_to, idx_player=idx_player, steps=steps)

    def test_move_to_empty_finish_with_negative_steps(self):
        """Test 042: Test that can not move to finish with negative steps [1 point]"""

        list_test = [
            {'card': Card(suit='♣', rank='4'), 'list_steps': [-4]},
            {'card': Card(suit='♦', rank='4'), 'list_steps': [-4]},
            {'card': Card(suit='♥', rank='4'), 'list_steps': [-4]},
            {'card': Card(suit='♠', rank='4'), 'list_steps': [-4]},
        ]

        for idx_player in range(4):
            pos_finish = self.CNT_STEPS + idx_player * self.CNT_BALLS * 2 + self.CNT_BALLS
            for i in range(3):
                pos_to = pos_finish + i

                for test in list_test:
                    card = test['card']
                    for steps in test['list_steps']:
                        pos_start = idx_player * int(self.CNT_STEPS / self.CNT_PLAYERS)

                        pos_from = (pos_start + abs(steps) - (pos_to - pos_finish + 1) + self.CNT_STEPS) % self.CNT_STEPS
                        self.move_marble_to_finish(card=card, pos_from=pos_from, pos_to=pos_to, idx_player=idx_player, steps=steps)

    def test_not_overtaking_in_finish(self):
        """Test 043: Test not overtaking in finish [5 point]"""

        list_test = [
            {'card': Card(suit='♣', rank='A'), 'list_steps': [1, 11]},
            {'card': Card(suit='♦', rank='A'), 'list_steps': [1, 11]},
            {'card': Card(suit='♥', rank='A'), 'list_steps': [1, 11]},
            {'card': Card(suit='♠', rank='A'), 'list_steps': [1, 11]},
            {'card': Card(suit='♣', rank='2'), 'list_steps': [2]},
            {'card': Card(suit='♦', rank='2'), 'list_steps': [2]},
            {'card': Card(suit='♥', rank='2'), 'list_steps': [2]},
            {'card': Card(suit='♠', rank='2'), 'list_steps': [2]},
            {'card': Card(suit='♣', rank='3'), 'list_steps': [3]},
            {'card': Card(suit='♦', rank='3'), 'list_steps': [3]},
            {'card': Card(suit='♥', rank='3'), 'list_steps': [3]},
            {'card': Card(suit='♠', rank='3'), 'list_steps': [3]},
            {'card': Card(suit='♣', rank='4'), 'list_steps': [4]},
            {'card': Card(suit='♦', rank='4'), 'list_steps': [4]},
            {'card': Card(suit='♥', rank='4'), 'list_steps': [4]},
            {'card': Card(suit='♠', rank='4'), 'list_steps': [4]},
            {'card': Card(suit='♣', rank='5'), 'list_steps': [5]},
            {'card': Card(suit='♦', rank='5'), 'list_steps': [5]},
            {'card': Card(suit='♥', rank='5'), 'list_steps': [5]},
            {'card': Card(suit='♠', rank='5'), 'list_steps': [5]},
            {'card': Card(suit='♣', rank='6'), 'list_steps': [6]},
            {'card': Card(suit='♦', rank='6'), 'list_steps': [6]},
            {'card': Card(suit='♥', rank='6'), 'list_steps': [6]},
            {'card': Card(suit='♠', rank='6'), 'list_steps': [6]},
            {'card': Card(suit='♣', rank='7'), 'list_steps': [1, 2, 3, 4, 5, 6, 7]},
            {'card': Card(suit='♦', rank='7'), 'list_steps': [1, 2, 3, 4, 5, 6, 7]},
            {'card': Card(suit='♥', rank='7'), 'list_steps': [1, 2, 3, 4, 5, 6, 7]},
            {'card': Card(suit='♠', rank='7'), 'list_steps': [1, 2, 3, 4, 5, 6, 7]},
            {'card': Card(suit='♣', rank='8'), 'list_steps': [8]},
            {'card': Card(suit='♦', rank='8'), 'list_steps': [8]},
            {'card': Card(suit='♥', rank='8'), 'list_steps': [8]},
            {'card': Card(suit='♠', rank='8'), 'list_steps': [8]},
            {'card': Card(suit='♣', rank='9'), 'list_steps': [9]},
            {'card': Card(suit='♦', rank='9'), 'list_steps': [9]},
            {'card': Card(suit='♥', rank='9'), 'list_steps': [9]},
            {'card': Card(suit='♠', rank='9'), 'list_steps': [9]},
            {'card': Card(suit='♣', rank='10'), 'list_steps': [10]},
            {'card': Card(suit='♦', rank='10'), 'list_steps': [10]},
            {'card': Card(suit='♥', rank='10'), 'list_steps': [10]},
            {'card': Card(suit='♠', rank='10'), 'list_steps': [10]},
            {'card': Card(suit='♣', rank='Q'), 'list_steps': [12]},
            {'card': Card(suit='♦', rank='Q'), 'list_steps': [12]},
            {'card': Card(suit='♥', rank='Q'), 'list_steps': [12]},
            {'card': Card(suit='♠', rank='Q'), 'list_steps': [12]},
            {'card': Card(suit='♣', rank='K'), 'list_steps': [13]},
            {'card': Card(suit='♦', rank='K'), 'list_steps': [13]},
            {'card': Card(suit='♥', rank='K'), 'list_steps': [13]},
            {'card': Card(suit='♠', rank='K'), 'list_steps': [13]},
        ]

        for idx_player in range(4):
            pos_finish = self.CNT_STEPS + idx_player * self.CNT_BALLS * 2 + self.CNT_BALLS
            for i in range(3):
                pos_to = pos_finish + i + 1

                for test in list_test:
                    card = test['card']
                    for steps in test['list_steps']:
                        pos_start = idx_player * int(self.CNT_STEPS / self.CNT_PLAYERS)

                        if pos_to - steps < pos_finish:
                            pos_from = (pos_start - steps + (pos_to - pos_finish + 1) + self.CNT_STEPS) % self.CNT_STEPS
                        else:
                            pos_from = pos_to - steps

                        self.move_marble_to_blocked_finish(card=card, pos_from=pos_from, pos_to=pos_to, idx_player=idx_player)

    def test_card_exchange_at_beginning_of_round_1(self):
        """Test 044: Test card exchange actions at beginning of round [1 point]"""

        self.game_server.reset()
        state = self.game_server.get_state()

        idx_player_active = 0
        state.cnt_round = 0
        state.idx_player_started = idx_player_active
        state.idx_player_active = idx_player_active
        self.game_server.set_state(state)
        str_state = str(state)

        list_action_found = self.game_server.get_list_action()
        list_action_expected = []

        player = state.list_player[idx_player_active]
        for card in player.list_card:
            action = Action(card=card, pos_from=None, pos_to=None)
            if action not in list_action_expected:
                list_action_expected.append(action)

        hint = str_state
        hint += 'Error: "get_list_action" result is wrong'
        hint += f'\nExpected:'
        hint += f'\n{self.get_list_action_as_str(self.get_sorted_list_action(list_action_expected))}'
        hint += f'\nFound:'
        hint += f'\n{self.get_list_action_as_str(self.get_sorted_list_action(list_action_found))}'
        assert self.get_sorted_list_action(list_action_found) == self.get_sorted_list_action(list_action_expected), hint

    def test_card_exchange_at_beginning_of_round_2(self):
        """Test 045: Test card exchange result at beginning of round [1 point]"""

        self.game_server.reset()
        state = self.game_server.get_state()

        idx_player_active = 0
        state.cnt_round = 0
        state.idx_player_started = idx_player_active
        state.idx_player_active = idx_player_active
        self.game_server.set_state(state)
        str_states = str(state)

        list_card = []
        for player in state.list_player:
            card = player.list_card[0]  # first card
            list_card.append(card)
            action = Action(card=card, pos_from=None, pos_to=None)
            self.game_server.apply_action(action)
            str_states += f'Action: {action}\n'

        self.game_server.set_state(state)
        str_states += str(state)

        is_okay = True
        for idx_player in range(self.CNT_PLAYERS):
            idx_player_partner = (idx_player + 2) % self.CNT_PLAYERS
            player = state.list_player[idx_player_partner]
            card = list_card[idx_player]

            is_okay = is_okay and card in player.list_card

        hint = str_states
        hint += 'Error: Card exchange had wrong result.'

        assert is_okay, hint

    def test_number_of_cards_in_round_1(self):
        """Test 046: Test number of cards dealt in round 1 [1 point]"""
        self.game_server.reset()
        state = self.game_server.get_state()
        str_state = str(state)
        for idx_player in range(self.CNT_PLAYERS):
            cnt_cards_found = len(state.list_player[idx_player].list_card)
            cnt_cards_expected = 6
            hint = str_state
            hint += f'Error: Expected {cnt_cards_expected} cards, found {cnt_cards_found} cards.'
            assert cnt_cards_found == cnt_cards_expected, hint

    def test_number_of_cards_in_round_2(self):
        """Test 047: Test number of cards dealt in round 2 [1 point]"""
        self.start_game_state_at_round_2()

        state = self.game_server.get_state()
        str_state = str(state)

        for idx_player in range(self.CNT_PLAYERS):
            cnt_cards_found = len(state.list_player[idx_player].list_card)
            cnt_cards_expected = 5
            hint = str_state
            hint += f'Error: Expected {cnt_cards_expected} cards, found {cnt_cards_found} cards.'
            assert cnt_cards_found == cnt_cards_expected, hint

    def test_number_of_cards_in_round_5(self):
        """Test 048: Test number of cards dealt in round 5 [1 point]"""
        self.game_server.reset()

        state = self.game_server.get_state()

        idx_player_active = 0
        state.cnt_round = 4
        state.idx_player_active = idx_player_active
        state.bool_card_exchanged = True
        for idx_player in range(self.CNT_PLAYERS):
            state.list_player[idx_player].list_card = []
        self.game_server.set_state(state)

        self.game_server.apply_action(None)
        self.game_server.apply_action(None)
        self.game_server.apply_action(None)
        self.game_server.apply_action(None)

        state = self.game_server.get_state()
        str_state = str(state)

        for idx_player in range(self.CNT_PLAYERS):
            cnt_cards_found = 0
            cnt_cards_found = len(state.list_player[idx_player].list_card)
            cnt_cards_expected = 2
            hint = str_state
            hint += f'Error: Expected {cnt_cards_expected} cards, found {cnt_cards_found} cards.'
            assert cnt_cards_found == cnt_cards_expected, hint

    def test_number_of_cards_in_round_6(self):
        """Test 049: Test number of cards dealt in round 6 [1 point]"""
        self.game_server.reset()

        state = self.game_server.get_state()

        idx_player_active = 0
        state.cnt_round = 5
        state.idx_player_active = idx_player_active
        state.bool_card_exchanged = True
        for idx_player in range(self.CNT_PLAYERS):
            state.list_player[idx_player].list_card = []
        self.game_server.set_state(state)

        self.game_server.apply_action(None)
        self.game_server.apply_action(None)
        self.game_server.apply_action(None)
        self.game_server.apply_action(None)

        state = self.game_server.get_state()
        str_state = str(state)

        for idx_player in range(self.CNT_PLAYERS):
            cnt_cards_found = 0
            cnt_cards_found = len(state.list_player[idx_player].list_card)
            cnt_cards_expected = 6
            hint = str_state
            hint += f'Error: Expected {cnt_cards_expected} cards, found {cnt_cards_found} cards.'
            assert cnt_cards_found == cnt_cards_expected, hint

    def test_stock_out_of_cards(self):
        """Test 050: Test re-shuffle if stock out of cards [1 point]"""
        self.game_server.reset()

        state = self.game_server.get_state()

        state.list_card_discard.extend(state.list_card_draw)
        state.list_card_discard.append(Card(suit='♥', rank='A'))  # additional card was discarded after JKR
        state.list_card_draw = []

        self.game_server.set_state(state)

        self.game_server.apply_action(None)
        self.game_server.apply_action(None)
        self.game_server.apply_action(None)
        self.game_server.apply_action(None)

        state = self.game_server.get_state()
        str_state = str(state)

        cnt_cards = len(state.list_card_draw)
        for player in state.list_player:
            cnt_cards += len(player.list_card)

        hint = str_state
        hint += f'Error 1: Sum of cards must remain 110 after re-shuffle.'
        assert cnt_cards == 110, hint

        hint = str_state
        hint += f'Error 2: "list_card_discard" should be empty after re-shuffle.'
        assert len(state.list_card_discard) == 0, hint

    def test_folding_cards(self):
        """Test 051: Test folding cards when no action possible [1 point]"""

        self.game_server.reset()
        state = self.game_server.get_state()

        idx_player_active = 0
        state.cnt_round = 0
        state.idx_player_started = idx_player_active
        state.idx_player_active = idx_player_active
        state.bool_card_exchanged = True
        player = state.list_player[idx_player_active]
        player.list_card = [Card(suit='♥', rank='2'), Card(suit='♠', rank='10'), Card(suit='♦', rank='4')]
        player = state.list_player[idx_player_active + 1]
        player.list_card = [Card(suit='♥', rank='A')]
        self.game_server.set_state(state)
        str_states = str(state)

        self.game_server.apply_action(None)
        str_states += f'Action: None\n'

        state = self.game_server.get_state()
        str_states += str(state)

        player = state.list_player[idx_player_active]

        hint = str_states
        hint += 'Error: Player 1 must fold cards without actions.'
        assert len(player.list_card) == 0, hint

    def test_support_partner_at_the_end(self):
        """Test 052: Test support partner at the end [1 point]"""

        card = Card(suit='♣', rank='5')
        for idx_player in range(4):

            self.game_server.reset()
            state = self.game_server.get_state()

            state.idx_player_started = idx_player
            state.idx_player_active = idx_player
            state.bool_card_exchanged = True

            pos_finish = self.CNT_STEPS + idx_player * self.CNT_BALLS * 2 + self.CNT_BALLS
            player = state.list_player[idx_player]
            player.list_card = [card]
            for i in range(4):
                player.list_marble[i].pos = pos_finish + i

            idx_partner = (idx_player + 2) % self.CNT_PLAYERS
            pos_start = idx_partner * int(self.CNT_STEPS / self.CNT_PLAYERS)
            player = state.list_player[idx_partner]
            player.list_marble[0].pos = pos_start
            player.list_marble[0].is_save = False

            self.game_server.set_state(state)
            str_states = str(state)

            list_action_found = self.game_server.get_list_action()

            hint = str_states
            hint += f'Error 1: Player {idx_player+1} must allowed to move with Player {idx_partner+1}\'s marbles'
            hint += f'\nafter placing his own marbles at the finish.'
            assert len(list_action_found) > 0, hint

            pos_to = pos_start + 5
            action = Action(card=card, pos_from=pos_start, pos_to=pos_to)
            self.game_server.apply_action(action)
            str_states += f'Action: None\n'

            state = self.game_server.get_state()
            str_states += str(state)

            player = state.list_player[idx_partner]
            idx_marble = self.get_idx_marble(player=player, pos=pos_to)

            hint = str_states
            hint += f'Error 2: Player {idx_player+1} should have moved Player {idx_partner+1}\'s marble'
            hint += f'\nfrom {pos_start} to {pos_to}.'
            assert idx_marble != -1, hint

    def test_unique_actions(self):
        """Test 053: Test if list_action contains unique actions [2 point]"""

        self.game_server.reset()
        state = self.game_server.get_state()

        idx_player_active = 0
        state.cnt_round = 0
        state.idx_player_started = idx_player_active
        state.idx_player_active = idx_player_active
        state.bool_card_exchanged = True

        player = state.list_player[idx_player_active]
        player.list_card = [Card(suit='♣', rank='5'), Card(suit='♣', rank='5')]
        player.list_marble[0].pos = 0

        self.game_server.set_state(state)
        str_state = str(state)

        list_action_found = self.game_server.get_list_action()

        hint = str_state
        hint += f'Error: List of actions contains duplicate actions.'
        assert len(list_action_found) == 1, hint

    def test_finish_game(self):
        """Test 054: Test finish game [1 point]"""

        self.game_server.reset()
        state = self.game_server.get_state()

        idx_player_active = 0
        state.cnt_round = 0
        state.idx_player_started = idx_player_active
        state.idx_player_active = idx_player_active
        state.bool_card_exchanged = True

        for idx_player in [0, 2]:
            pos_finish = self.CNT_STEPS + idx_player * self.CNT_BALLS * 2 + self.CNT_BALLS
            player = state.list_player[idx_player]
            for idx_marble in range(4):
                player.list_marble[idx_marble].pos = pos_finish + idx_marble

        player = state.list_player[idx_player_active]
        player.list_card = [Card(suit='♥', rank='A')]
        player.list_marble[0].pos = 0

        self.game_server.set_state(state)
        str_states = str(state)

        action = Action(card=Card(suit='♥', rank='A'), pos_from=0, pos_to=68)
        self.game_server.apply_action(action)
        str_states += f'Action: None\n'

        state = self.game_server.get_state()
        str_states += str(state)

        hint = str_states
        hint += 'Error: Game should be finished.'
        assert state.phase == GamePhase.FINISHED, hint

    # --- helper functions ---

    def get_idx_marble(self, player: PlayerState, pos: int) -> int:
        for idx_marble, marble in enumerate(player.list_marble):
            if marble.pos == pos:
                return idx_marble
        return -1

    def get_cnt_marbles_in_kennel(self, state: dict, idx_player: int) -> int:
        cnt_in_kennel = 0
        player = state.list_player[idx_player]
        for marble in player.list_marble:
            if marble.pos >= self.CNT_STEPS + idx_player * self.CNT_BALLS * 2 and \
                    marble.pos < self.CNT_STEPS + idx_player * self.CNT_BALLS * 2 + self.CNT_BALLS:
                cnt_in_kennel += 1
        return cnt_in_kennel

    def get_sorted_list_action(self, list_action):
        return sorted(list_action, key=lambda x: (
            str(x.card),
            -1 if x.pos_from is None else x.pos_from,
            -1 if x.pos_to is None else x.pos_to,
            str(x.card_swap))
        )

    def get_list_action_as_str(self, list_action):
        list_action = self.get_sorted_list_action(list_action)
        return json.dumps([str(action) for action in list_action], indent=4, ensure_ascii=False)

    def start_game_state_at_round_2(self):
        self.game_server.reset()

        state = self.game_server.get_state()

        idx_player_started = 0
        state.idx_player_started = idx_player_started
        state.idx_player_active = idx_player_started
        state.bool_card_exchanged = True
        for idx_player in range(self.CNT_PLAYERS):
            state.list_player[idx_player].list_card = []
        self.game_server.set_state(state)

        self.game_server.apply_action(None)
        self.game_server.apply_action(None)
        self.game_server.apply_action(None)
        self.game_server.apply_action(None)

    def move_marble(self, card: str, pos_from: int, pos_to: int) -> None:
        self.game_server.reset()
        state = self.game_server.get_state()

        idx_player_active = 0
        state.idx_player_started = idx_player_active
        state.idx_player_active = idx_player_active
        state.bool_card_exchanged = True
        player = state.list_player[idx_player_active]
        player.list_card = [card]
        player.list_marble[0].pos = pos_from
        player.list_marble[0].is_save = True
        self.game_server.set_state(state)
        str_states = str(state)

        action = Action(card=card, pos_from=pos_from, pos_to=pos_to)
        self.game_server.apply_action(action)
        str_states += f'Action: {action}\n'

        state = self.game_server.get_state()
        str_states += str(state)

        player = state.list_player[idx_player_active]
        found = self.get_idx_marble(player=player, pos=pos_to) != -1
        hint = str_states
        hint += f'Error: Player 1\'s marble must be moved from pos={pos_from} to pos={pos_to} with card={card}'
        assert found, hint

    def move_marble_to_finish(self, card: str, pos_from: int, pos_to: int, idx_player: int, steps: int) -> None:

        list_is_save = [True, False]  # on path
        if pos_from > self.CNT_STEPS:
            list_is_save = [False]  # inside finish

        for is_save in list_is_save:

            self.game_server.reset()
            state = self.game_server.get_state()

            state.idx_player_started = idx_player
            state.idx_player_active = idx_player
            state.bool_card_exchanged = True
            player = state.list_player[idx_player]
            player.list_card = [card]
            player.list_marble[0].pos = pos_from
            player.list_marble[0].is_save = is_save
            self.game_server.set_state(state)
            str_states = str(state)

            list_action_found = self.game_server.get_list_action()
            action = Action(card=card, pos_from=pos_from, pos_to=pos_to)

            if is_save:
                hint = str_states
                hint += 'Error 1: "get_list_action" result is wrong.'
                hint += f'\nAction not allowed: {action}'
                hint += f'\nHint: Player 1 can not move to finish directly from Start (is_save=True).'
                assert action not in list_action_found, hint

            else:
                if steps > 0:

                    hint = str_states
                    hint += 'Error 2: "get_list_action" result is wrong'
                    hint += f'\nAction missing: {action}'
                    assert action in list_action_found, hint

                    self.game_server.apply_action(action)
                    str_states += f'Action: {action}\n'

                    state = self.game_server.get_state()
                    str_states += str(state)

                    player = state.list_player[idx_player]
                    found = self.get_idx_marble(player=player, pos=pos_to) != -1
                    hint = str_states
                    hint += f'Error 3: Player {idx_player+1}\'s marble must be moved from pos={pos_from} to pos={pos_to} with card={card}'
                    assert found, hint

                else:
                    hint = str_states
                    hint += 'Error 4: "get_list_action" result is wrong.'
                    hint += f'\nAction not allowed: {action}'
                    hint += f'\nHint: Player 1 can not move backwards into finish.'
                    assert action not in list_action_found, hint

    def move_marble_to_blocked_finish(self, card: str, pos_from: int, pos_to: int, idx_player: int) -> None:
        self.game_server.reset()
        state = self.game_server.get_state()

        for offset in [0, 1]:
            state.idx_player_started = idx_player
            state.idx_player_active = idx_player
            state.bool_card_exchanged = True
            player = state.list_player[idx_player]
            player.list_card = [card]
            player.list_marble[0].pos = pos_from
            player.list_marble[0].is_save = False
            player.list_marble[1].pos = pos_to - offset
            player.list_marble[1].is_save = False
            self.game_server.set_state(state)
            str_state = str(state)

            list_action_found = self.game_server.get_list_action()
            action = Action(card=card, pos_from=pos_from, pos_to=pos_to - offset)

            hint = str_state
            hint += 'Error: "get_list_action" result is wrong.'
            hint += f'\nAction not allowed: {action}'
            if offset == 0:
                hint += f'\nHint: Player 1 can not kick out marbles in finish.'
            else:
                hint += f'\nHint: Player 1 can not overtake marbles in finish.'
            assert action not in list_action_found, hint

    def overtake_marble(self, card: str, pos_from: int, pos_to: int) -> None:
        self.game_server.reset()
        state = self.game_server.get_state()

        idx_player_active = 0
        state.idx_player_started = idx_player_active
        state.idx_player_active = idx_player_active
        state.bool_card_exchanged = True
        player = state.list_player[idx_player_active]
        player.list_card = [card]
        player.list_marble[0].pos = pos_from
        player.list_marble[0].is_save = True
        player = state.list_player[idx_player_active + 1]
        player.list_card = [card]
        player.list_marble[0].pos = pos_from + 1
        player.list_marble[0].is_save = False
        self.game_server.set_state(state)
        str_states = str(state)

        action = Action(card=card, pos_from=pos_from, pos_to=pos_to)
        self.game_server.apply_action(action)
        str_states += f'Action: {action}\n'

        state = self.game_server.get_state()
        str_states += str(state)

        player = state.list_player[idx_player_active + 1]
        found = self.get_idx_marble(player=player, pos=pos_from + 1) != -1
        hint = str_states
        hint += f'Error: Player 2\'s marble must be sent to kennel from pos={pos_from + 1}'
        assert found, hint

    def send_home_marble(self, card: str, pos_from: int, pos_to: int, is_own_marble: bool) -> None:
        self.game_server.reset()
        state = self.game_server.get_state()

        idx_player_active = 0
        state.idx_player_started = idx_player_active
        state.idx_player_active = idx_player_active
        state.bool_card_exchanged = True
        player = state.list_player[idx_player_active]
        player.list_card = [card]
        player.list_marble[0].pos = pos_from
        player.list_marble[0].is_save = True
        if is_own_marble:
            player.list_marble[1].pos = pos_to
            player.list_marble[1].is_save = False
        else:
            player = state.list_player[idx_player_active + 1]
            player.list_marble[0].pos = pos_to
            player.list_marble[0].is_save = False
        self.game_server.set_state(state)
        str_states = str(state)

        action = Action(card=card, pos_from=pos_from, pos_to=pos_to)
        self.game_server.apply_action(action)
        str_states += f'Action: {action}\n'

        state = self.game_server.get_state()
        str_states += str(state)

        if is_own_marble:
            cnt_in_kennel = self.get_cnt_marbles_in_kennel(state=state, idx_player=idx_player_active)
            found = cnt_in_kennel == 3
        else:
            cnt_in_kennel = self.get_cnt_marbles_in_kennel(state=state, idx_player=idx_player_active + 1)
            found = cnt_in_kennel == 4
        hint = str_states
        hint += f'Error: Player 2\'s marble must be sent home with card={card}'
        assert found, hint

    def move_test(self, pos_from: int, list_test: list[dict]) -> None:
        for test in list_test:
            card = test['card']
            for steps in test['list_steps']:
                pos_to = (pos_from + steps + self.CNT_STEPS) % self.CNT_STEPS
                self.move_marble(card=card, pos_from=pos_from, pos_to=pos_to)

    def overtake_test(self, pos_from: int, list_test: list[dict]) -> None:
        for test in list_test:
            card = test['card']
            for steps in test['list_steps']:
                pos_to = (pos_from + steps + self.CNT_STEPS) % self.CNT_STEPS
                self.overtake_marble(card=card, pos_from=pos_from, pos_to=pos_to)

    def send_home_test(self, pos_from: int, list_test: list[dict]) -> None:
        for test in list_test:
            card = test['card']
            for steps in test['list_steps']:
                pos_to = (pos_from + steps + self.CNT_STEPS) % self.CNT_STEPS
                for is_own_marble in [True, False]:
                    self.send_home_marble(card=card, pos_from=pos_from, pos_to=pos_to, is_own_marble=is_own_marble)


if __name__ == '__main__':

    if len(sys.argv) < 3:
        print("Error: Wrong number of arguments")
        print("Use: python benchmark_dog_copy.py python [dog.Dog]")
        print("  or python benchmark_dog_copy.py localhost [port]")
        print("  or python benchmark_dog_copy.py remote [host:port]")
        sys.exit()

    benchmark = DogBenchmark(argv=sys.argv)

    if True:  # Run all tests
        benchmark.run_tests()

    else:  # Run specific test(s)
        benchmark.test_chose_card_with_JOKER_1()
