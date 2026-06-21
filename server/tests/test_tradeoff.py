"""
Tests for the Tradeoff game.
"""

import json
from pathlib import Path
import re

from ..games.tradeoff.game import (
    TradeoffGame,
    TradeoffPlayer,
    TradeoffOptions,
)
from ..games.tradeoff.bot import bot_think_taking
from ..games.tradeoff.scoring import (
    SET_DEFINITIONS,
    find_best_scoring,
    is_triple,
    is_group,
    is_mini_straight,
    is_double_triple,
    is_straight,
    is_double_group,
    is_all_groups,
    is_all_triplets,
)
from ..messages.localization import Localization
from ..users.preferences import DiceKeepingStyle
from ..users.test_user import MockUser
from ..users.bot import Bot


LOCALES_DIR = Path(__file__).parent.parent / "locales"


def _ftl_messages(text: str) -> dict[str, set[str]]:
    result: dict[str, set[str]] = {}
    current_key = None
    current_lines: list[str] = []
    for line in text.splitlines():
        if line and not line.startswith((" ", "\t")) and "=" in line:
            if current_key is not None:
                result[current_key] = set(
                    re.findall(r"\{\s*\$([a-zA-Z_][\w-]*)", "\n".join(current_lines))
                )
            current_key = line.split("=", 1)[0].strip()
            current_lines = [line]
        elif current_key is not None:
            current_lines.append(line)
    if current_key is not None:
        result[current_key] = set(
            re.findall(r"\{\s*\$([a-zA-Z_][\w-]*)", "\n".join(current_lines))
        )
    return result


def make_human_game(*, mobile_first: bool = False, target_score: int = 60) -> TradeoffGame:
    game = TradeoffGame(options=TradeoffOptions(target_score=target_score))
    game.setup_keybinds()
    for index, name in enumerate(("Alice", "Bob")):
        user = MockUser(name, uuid=f"tradeoff-{index + 1}")
        if mobile_first and index == 0:
            user.client_type = "mobile"
        game.add_player(name, user)
    game.host = "Alice"
    game.on_start()
    return game


class TestTradeoffScoring:
    """Unit tests for Tradeoff scoring functions."""

    def test_is_triple(self):
        """Test triple detection."""
        assert is_triple([3, 3, 3]) is True
        assert is_triple([1, 1, 1]) is True
        assert is_triple([6, 6, 6]) is True
        assert is_triple([3, 3, 4]) is False
        assert is_triple([1, 2, 3]) is False
        assert is_triple([3, 3]) is False
        assert is_triple([3, 3, 3, 3]) is False

    def test_is_group(self):
        """Test group detection (5 of the same value)."""
        assert is_group([3, 3, 3, 3, 3]) is True
        assert is_group([1, 1, 1, 1, 1]) is True
        assert is_group([6, 6, 6, 6, 6]) is True
        assert is_group([3, 3, 3, 3, 4]) is False  # Not all same
        assert is_group([1, 2, 3, 4, 5]) is False  # All different
        assert is_group([3, 3, 3, 3]) is False  # Only 4 dice
        assert is_group([3, 3, 3, 3, 3, 3]) is False  # 6 dice

    def test_is_double_triple(self):
        """Test double triple detection."""
        assert is_double_triple([1, 1, 1, 2, 2, 2]) is True
        assert is_double_triple([3, 3, 3, 5, 5, 5]) is True
        assert is_double_triple([1, 1, 1, 1, 2, 2]) is False
        assert is_double_triple([1, 2, 3, 4, 5, 6]) is False
        assert is_double_triple([1, 1, 1, 2, 2]) is False

    def test_is_mini_straight(self):
        """Test mini straight detection (4 consecutive)."""
        assert is_mini_straight([1, 2, 3, 4]) is True
        assert is_mini_straight([2, 3, 4, 5]) is True
        assert is_mini_straight([3, 4, 5, 6]) is True
        assert is_mini_straight([4, 3, 2, 1]) is True  # Order doesn't matter
        assert is_mini_straight([1, 2, 3, 5]) is False  # Not consecutive
        assert is_mini_straight([1, 2, 3, 4, 5]) is False  # Too many dice
        assert is_mini_straight([1, 2, 3]) is False  # Too few dice

    def test_is_straight(self):
        """Test straight detection (5 consecutive)."""
        assert is_straight([1, 2, 3, 4, 5]) is True
        assert is_straight([2, 3, 4, 5, 6]) is True
        assert is_straight([5, 4, 3, 2, 1]) is True  # Order doesn't matter
        assert is_straight([1, 2, 3, 4, 6]) is False  # Not consecutive
        assert is_straight([1, 2, 3, 4, 5, 6]) is False  # Too many dice
        assert is_straight([1, 2, 3, 4]) is False  # Too few dice

    def test_is_double_group(self):
        """Test double group detection (5 of 2 kinds, 10 dice total)."""
        assert is_double_group([1, 1, 1, 1, 1, 2, 2, 2, 2, 2]) is True
        assert is_double_group([4, 4, 4, 4, 4, 6, 6, 6, 6, 6]) is True
        assert is_double_group([1, 1, 1, 1, 1, 2, 2, 2, 2, 3]) is False  # Not 5+5
        assert is_double_group([1, 1, 2, 2, 3, 3]) is False  # Only 6 dice
        assert is_double_group([1, 1, 1, 1, 1, 1, 1, 1, 1, 1]) is False  # All same

    def test_is_all_triplets(self):
        """Test all triplets detection (5 triples, 15 dice)."""
        # 5 triples: 1,1,1 + 2,2,2 + 3,3,3 + 4,4,4 + 5,5,5
        dice = [1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 4, 5, 5, 5]
        assert is_all_triplets(dice) is True

        # Not valid - only 4 different values
        dice = [1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 4, 4, 4, 4]
        assert is_all_triplets(dice) is False

        # Wrong count
        dice = [1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 4]
        assert is_all_triplets(dice) is False

    def test_is_all_groups(self):
        """Test all groups detection (3 groups of 5 same, 15 dice)."""
        # Valid: 3 values, each appearing 5 times
        dice = [1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3]
        assert is_all_groups(dice) is True

        # Different values work too
        dice = [4, 4, 4, 4, 4, 5, 5, 5, 5, 5, 6, 6, 6, 6, 6]
        assert is_all_groups(dice) is True

        # Not valid - only 2 different values
        dice = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2]
        assert is_all_groups(dice) is False

        # Not valid - 4 different values
        dice = [1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4]
        assert is_all_groups(dice) is False

        # Wrong count
        dice = [1, 1, 1, 1, 1, 2, 2, 2, 2, 2]
        assert is_all_groups(dice) is False

    def test_find_best_scoring_single_triple(self):
        """Test finding a single triple."""
        dice = [3, 3, 3]
        result = find_best_scoring(dice)
        assert len(result) == 1
        assert result[0][0] == "triple"
        assert result[0][2] == 3

    def test_find_best_scoring_single_group(self):
        """Test finding a single group (5 of same)."""
        dice = [4, 4, 4, 4, 4]
        result = find_best_scoring(dice)
        assert len(result) == 1
        assert result[0][0] == "group"
        assert result[0][2] == 8

    def test_find_best_scoring_prefers_higher_points(self):
        """Test that scoring prefers groups (8 pts) over triples (3 pts)."""
        # With 5 same dice, we can make either a triple + leftover or a group
        # Group (8 pts) should be preferred over triple (3 pts)
        dice = [2, 2, 2, 2, 2]
        result = find_best_scoring(dice)
        assert result[0][0] == "group"
        assert result[0][2] == 8

    def test_find_best_scoring_double_group(self):
        """Test finding a double group (5 of 2 kinds, 10 dice)."""
        dice = [1, 1, 1, 1, 1, 3, 3, 3, 3, 3]
        result = find_best_scoring(dice)
        assert len(result) == 1
        assert result[0][0] == "double_group"
        assert result[0][2] == 30

    def test_find_best_scoring_straight(self):
        """Test finding a straight (5 consecutive)."""
        dice = [1, 2, 3, 4, 5]
        result = find_best_scoring(dice)
        assert len(result) == 1
        assert result[0][0] == "straight"
        assert result[0][2] == 12

    def test_find_best_scoring_all_triplets(self):
        """Test finding all triplets (highest possible, 50 pts)."""
        dice = [1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 4, 5, 5, 5]
        result = find_best_scoring(dice)
        assert len(result) == 1
        assert result[0][0] == "all_triplets"
        assert result[0][2] == 50

    def test_find_best_scoring_multiple_sets(self):
        """Test finding multiple non-overlapping sets."""
        # 6 dice: double_triple (10 pts) vs 2 triples (6 pts)
        dice = [1, 1, 1, 2, 2, 2]
        result = find_best_scoring(dice)
        # Should prefer double_triple at 10 points
        assert sum(r[2] for r in result) == 10
        assert result[0][0] == "double_triple"

    def test_find_best_scoring_mini_straight(self):
        """Test finding a mini straight (4 consecutive)."""
        dice = [2, 3, 4, 5]
        result = find_best_scoring(dice)
        assert len(result) == 1
        assert result[0][0] == "mini_straight"
        assert result[0][2] == 7

    def test_find_best_scoring_prefers_straight_over_mini(self):
        """Test that straight (12 pts) is preferred over mini straight (7 pts)."""
        dice = [1, 2, 3, 4, 5]
        result = find_best_scoring(dice)
        assert result[0][0] == "straight"
        assert result[0][2] == 12

    def test_find_best_scoring_all_groups(self):
        """Test finding all groups (3 groups of 5 same, 50 pts)."""
        dice = [1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3]
        result = find_best_scoring(dice)
        assert len(result) == 1
        assert result[0][0] == "all_groups"
        assert result[0][2] == 50

    def test_find_best_scoring_empty(self):
        """Test with empty dice list."""
        result = find_best_scoring([])
        assert result == []


class TestTradeoffPlayer:
    """Tests for TradeoffPlayer."""

    def test_player_defaults(self):
        """Test player default values."""
        player = TradeoffPlayer(id="123", name="Test")
        assert player.hand == []
        assert player.rolled_dice == []
        assert player.trading_indices == []
        assert player.trades_confirmed is False
        assert player.dice_traded_count == 0
        assert player.dice_taken_count == 0
        assert player.round_score == 0

    def test_player_is_bot(self):
        """Test bot player creation."""
        player = TradeoffPlayer(id="bot1", name="Bot", is_bot=True)
        assert player.is_bot is True


class TestTradeoffGameUnit:
    """Unit tests for Tradeoff game functions."""

    def test_game_creation(self):
        """Test creating a new Tradeoff game."""
        game = TradeoffGame()
        assert game.get_name() == "Tradeoff"
        assert game.get_type() == "tradeoff"
        assert game.get_category() == "dice"
        assert game.get_min_players() == 2
        assert game.get_max_players() == 8
        assert game.relevant_preferences == ["brief_announcements", "dice_keeping_style"]

    def test_player_creation(self):
        """Test creating a player with correct initial state."""
        game = TradeoffGame()
        user = MockUser("Alice")
        player = game.add_player("Alice", user)

        assert player.name == "Alice"
        assert player.is_bot is False
        assert isinstance(player, TradeoffPlayer)

    def test_options_defaults(self):
        """Test default game options."""
        game = TradeoffGame()
        assert game.options.target_score == 60

    def test_custom_options(self):
        """Test custom game options."""
        options = TradeoffOptions(target_score=50)
        game = TradeoffGame(options=options)
        assert game.options.target_score == 50

    def test_prestart_validation_reports_invalid_target(self):
        """Target score limits are enforced with contextual setup feedback."""
        game = TradeoffGame(options=TradeoffOptions(target_score=29))
        errors = game.prestart_validate()
        assert (
            "tradeoff-error-target-out-of-range",
            {"score": 29, "min": 30, "max": 500},
        ) in errors

    def test_serialization(self):
        """Test that game state can be serialized and deserialized."""
        game = TradeoffGame()
        user1 = MockUser("Alice")
        user2 = MockUser("Bob")
        game.add_player("Alice", user1)
        game.add_player("Bob", user2)

        game.on_start()

        # Serialize
        json_str = game.to_json()
        data = json.loads(json_str)

        # Verify structure
        assert len(data["players"]) == 2
        assert "hand" in data["players"][0]
        assert "rolled_dice" in data["players"][0]

        # Deserialize
        loaded_game = TradeoffGame.from_json(json_str)
        assert len(loaded_game.players) == 2


class TestTradeoffPlayTest:
    """Integration tests for complete game play."""

    def test_two_player_game_completes(self):
        """Test that a 2-player bot game completes."""
        game = TradeoffGame()
        game.options.target_score = 30  # Low target for fast test

        bot1 = Bot("Bot1")
        bot2 = Bot("Bot2")
        game.add_player("Bot1", bot1)
        game.add_player("Bot2", bot2)

        game.on_start()

        max_ticks = 5000
        for _ in range(max_ticks):
            if game.status == "finished":
                break
            game.on_tick()

        assert game.status == "finished"

    def test_three_player_game_completes(self):
        """Test that a 3-player bot game completes."""
        game = TradeoffGame()
        game.options.target_score = 30  # Low target for fast test

        for i in range(3):
            bot = Bot(f"Bot{i}")
            game.add_player(f"Bot{i}", bot)

        game.on_start()

        max_ticks = 5000
        for _ in range(max_ticks):
            if game.status == "finished":
                break
            game.on_tick()

        assert game.status == "finished"

    def test_eight_player_game_completes(self):
        """Test that an 8-player bot game completes."""
        game = TradeoffGame()
        game.options.target_score = 30  # Low target for fast test

        for i in range(8):
            bot = Bot(f"Bot{i}")
            game.add_player(f"Bot{i}", bot)

        game.on_start()

        max_ticks = 10000
        for _ in range(max_ticks):
            if game.status == "finished":
                break
            game.on_tick()

        assert game.status == "finished"


class TestTradeoffPersistence:
    """Tests for game persistence."""

    def test_full_state_preserved(self):
        """Test that full game state is preserved through save/load."""
        game = TradeoffGame(options=TradeoffOptions(target_score=50))
        user1 = MockUser("Alice")
        user2 = MockUser("Bob")
        game.add_player("Alice", user1)
        game.add_player("Bob", user2)

        game.on_start()

        # Modify some state
        alice: TradeoffPlayer = game.players[0]  # type: ignore
        alice.hand = [1, 2, 3, 4, 5]
        alice.dice_traded_count = 2

        game.pool = [6, 6]
        game.phase = "taking"

        # Save
        json_str = game.to_json()

        # Load
        loaded = TradeoffGame.from_json(json_str)
        loaded_alice: TradeoffPlayer = loaded.players[0]  # type: ignore

        # Verify state
        assert loaded.game_active is True
        assert loaded.options.target_score == 50
        assert loaded_alice.hand == [1, 2, 3, 4, 5]
        assert loaded_alice.dice_traded_count == 2
        assert loaded.pool == [6, 6]
        assert loaded.phase == "taking"

    def test_trading_state_preserved(self):
        """Test that trading phase state is preserved."""
        game = TradeoffGame()
        user1 = MockUser("Alice")
        user2 = MockUser("Bob")
        game.add_player("Alice", user1)
        game.add_player("Bob", user2)

        game.on_start()

        # Set up trading state
        alice: TradeoffPlayer = game.players[0]  # type: ignore
        alice.rolled_dice = [1, 2, 3, 4, 5]
        alice.trading_indices = [0, 2]
        alice.trades_confirmed = False

        # Save and load
        json_str = game.to_json()
        loaded = TradeoffGame.from_json(json_str)
        loaded_alice: TradeoffPlayer = loaded.players[0]  # type: ignore

        assert loaded_alice.rolled_dice == [1, 2, 3, 4, 5]
        assert loaded_alice.trading_indices == [0, 2]
        assert loaded_alice.trades_confirmed is False


class TestTradeoffPhases:
    """Tests for game phase transitions."""

    def test_game_starts_in_trading_phase(self):
        """Test that game starts in trading phase."""
        game = TradeoffGame()
        bot1 = Bot("Bot1")
        bot2 = Bot("Bot2")
        game.add_player("Bot1", bot1)
        game.add_player("Bot2", bot2)

        game.on_start()

        assert game.phase == "trading"
        assert game.iteration == 1

    def test_pool_starts_empty(self):
        """Test that pool starts empty."""
        game = TradeoffGame()
        bot1 = Bot("Bot1")
        bot2 = Bot("Bot2")
        game.add_player("Bot1", bot1)
        game.add_player("Bot2", bot2)

        game.on_start()

        assert game.pool == []

    def test_players_get_rolled_dice(self):
        """Test that players get rolled dice at start of iteration."""
        game = TradeoffGame()
        bot1 = Bot("Bot1")
        bot2 = Bot("Bot2")
        game.add_player("Bot1", bot1)
        game.add_player("Bot2", bot2)

        game.on_start()

        for p in game.players:
            tp: TradeoffPlayer = p  # type: ignore
            assert len(tp.rolled_dice) == 5
            assert all(1 <= d <= 6 for d in tp.rolled_dice)


class TestTradeoffPolish:
    """Regression tests for Tradeoff accessibility and rules polish."""

    def test_taking_number_key_takes_matching_pool_die(self):
        game = make_human_game()
        player: TradeoffPlayer = game.players[0]  # type: ignore
        user = game.get_user(player)
        assert isinstance(user, MockUser)
        user.preferences.dice_keeping_style = DiceKeepingStyle.VALUE_BASED

        game.phase = "taking"
        game.pool = [4, 5]
        game.taking_order = [player.id]
        game.taking_index = 0
        player.hand = []
        player.dice_traded_count = 2
        player.dice_taken_count = 0

        game.execute_action(player, "dice_key_4")

        assert player.hand == [4]
        assert game.pool == [5]
        assert player.dice_taken_count == 1

    def test_taking_number_key_reports_missing_pool_value(self):
        game = make_human_game()
        player: TradeoffPlayer = game.players[0]  # type: ignore
        user = game.get_user(player)
        assert isinstance(user, MockUser)
        user.clear_messages()

        game.phase = "taking"
        game.pool = [2]
        game.taking_order = [player.id]
        game.taking_index = 0
        player.dice_traded_count = 1
        player.dice_taken_count = 0

        game.execute_action(player, "dice_key_6")

        assert "There is no 6 in the shared pool right now." in user.get_last_spoken()
        assert player.hand == []

    def test_trade_reveal_uses_personal_and_observer_wording(self):
        game = make_human_game()
        alice: TradeoffPlayer = game.players[0]  # type: ignore
        bob: TradeoffPlayer = game.players[1]  # type: ignore
        alice_user = game.get_user(alice)
        bob_user = game.get_user(bob)
        assert isinstance(alice_user, MockUser)
        assert isinstance(bob_user, MockUser)
        alice_user.clear_messages()
        bob_user.clear_messages()

        alice.rolled_dice = [1, 2, 3, 4, 5]
        alice.trading_indices = [0, 2]
        bob.rolled_dice = [6, 6, 6, 6, 6]
        bob.trading_indices = []

        game.execute_action(alice, "confirm_trades")
        game.execute_action(bob, "confirm_trades")

        alice_messages = " ".join(alice_user.get_spoken_messages())
        bob_messages = " ".join(bob_user.get_spoken_messages())
        assert "You traded 2 dice into the pool" in alice_messages
        assert "Alice traded 2 dice into the pool" in bob_messages
        assert "You kept all five dice from this hand" in bob_messages

    def test_brief_trade_reveal_shortens_actor_message(self):
        game = make_human_game()
        alice: TradeoffPlayer = game.players[0]  # type: ignore
        bob: TradeoffPlayer = game.players[1]  # type: ignore
        alice_user = game.get_user(alice)
        bob_user = game.get_user(bob)
        assert isinstance(alice_user, MockUser)
        assert isinstance(bob_user, MockUser)
        alice_user.preferences.brief_announcements = True
        alice_user.clear_messages()

        alice.rolled_dice = [1, 2, 3, 4, 5]
        alice.trading_indices = [0, 1, 2]
        bob.rolled_dice = [6, 6, 6, 6, 6]
        bob.trading_indices = []

        game.execute_action(alice, "confirm_trades")
        game.execute_action(bob, "confirm_trades")

        assert "You traded 3 dice." in alice_user.get_spoken_messages()

    def test_scoring_uses_personal_and_observer_wording(self):
        game = make_human_game(target_score=500)
        alice: TradeoffPlayer = game.players[0]  # type: ignore
        bob: TradeoffPlayer = game.players[1]  # type: ignore
        alice_user = game.get_user(alice)
        bob_user = game.get_user(bob)
        assert isinstance(alice_user, MockUser)
        assert isinstance(bob_user, MockUser)
        alice_user.clear_messages()
        bob_user.clear_messages()

        alice.hand = [1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 4, 5, 5, 5]
        bob.hand = [1, 1, 1, 1, 1, 2, 2, 2, 3, 4, 5, 6, 4, 5, 6]

        game._do_scoring()

        assert any(
            message.startswith("You scored 50 points")
            for message in alice_user.get_spoken_messages()
        )
        assert any(
            message.startswith("Alice scored 50 points")
            for message in bob_user.get_spoken_messages()
        )

    def test_touch_standard_actions_use_tradeoff_info_order(self):
        game = make_human_game(mobile_first=True)
        player = game.players[0]
        action_ids = [
            resolved.action.id
            for resolved in game.get_all_visible_actions(player)
            if resolved.action.id
            in {
                "view_hand",
                "view_pool",
                "view_players",
                "check_scores",
                "whose_turn",
                "whos_at_table",
            }
        ]

        assert action_ids == [
            "view_hand",
            "view_pool",
            "view_players",
            "check_scores",
            "whose_turn",
            "whos_at_table",
        ]

    def test_touch_confirm_focuses_actor_without_stealing_observer_focus(self):
        game = make_human_game(mobile_first=True)
        alice: TradeoffPlayer = game.players[0]  # type: ignore
        bob = game.players[1]
        bob_user = game.get_user(bob)
        alice_user = game.get_user(alice)
        assert isinstance(alice_user, MockUser)
        assert isinstance(bob_user, MockUser)
        bob_user.client_type = "mobile"
        alice_user.clear_messages()
        bob_user.clear_messages()

        game.execute_action(alice, "confirm_trades")
        game.flush_menus()

        alice_updates = [
            message
            for message in alice_user.messages
            if message.type in {"show_menu", "update_menu"}
            and message.data.get("menu_id") == "turn_menu"
        ]
        bob_updates = [
            message
            for message in bob_user.messages
            if message.type in {"show_menu", "update_menu"}
            and message.data.get("menu_id") == "turn_menu"
        ]
        assert alice_updates[-1].data["selection_id"] == "view_hand"
        assert bob_updates[-1].data["selection_id"] is None

    def test_bot_taking_prefers_completing_group(self):
        game = TradeoffGame()
        player = TradeoffPlayer(id="bot", name="Bot", is_bot=True)
        player.hand = [4, 4, 4, 4]
        player.dice_traded_count = 1
        player.dice_taken_count = 0
        game.players = [player]
        game.phase = "taking"
        game.pool = [1, 4, 6]
        game.taking_order = [player.id]
        game.taking_index = 0

        assert bot_think_taking(game, player) == "take_4"

    def test_locale_key_and_variable_parity_and_vi_manual_terms(self):
        en_text = (LOCALES_DIR / "en" / "tradeoff.ftl").read_text(encoding="utf-8")
        vi_text = (LOCALES_DIR / "vi" / "tradeoff.ftl").read_text(encoding="utf-8")
        assert _ftl_messages(en_text) == _ftl_messages(vi_text)
        assert Localization.get("vi", "tradeoff-set-mini-straight", low=1, high=4) == (
            "sảnh ngắn 1-4"
        )

        manual = (
            Path(__file__).parent.parent
            / "documentation"
            / "content"
            / "vi"
            / "games"
            / "tradeoff.md"
        ).read_text(encoding="utf-8")
        assert "tay giữ" in manual
        assert "hũ chung" in manual
        assert "sảnh ngắn" in manual.lower()

