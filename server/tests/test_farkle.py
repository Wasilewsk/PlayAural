from pathlib import Path
import re

import pytest

from server.games.farkle.game import (
    FarkleGame,
    FarkleOptions,
    FarklePlayer,
    RISK_CONFIRM_TICKS,
)
from server.game_utils.actions import Visibility
from server.users.test_user import MockUser

@pytest.fixture
def mock_users():
    return [MockUser("player1"), MockUser("player2")]

@pytest.fixture
def farkle_game(mock_users):
    game = FarkleGame()
    game.add_player("player1", mock_users[0])
    game.add_player("player2", mock_users[1])

    game.on_start()
    game.flush_menus()
    return game

def test_farkle_game_initialization(farkle_game):
    assert len(farkle_game.players) == 2
    assert farkle_game.status == "playing"
    assert farkle_game.round == 1
    assert farkle_game.relevant_preferences == [
        "brief_announcements",
        "confirm_destructive_actions",
    ]

    player1 = farkle_game.get_player_by_name("player1")
    assert isinstance(player1, FarklePlayer)
    assert player1.score == 0
    assert player1.turn_score == 0

def test_minimal_entrance_score(farkle_game):
    # Set custom entrance score
    farkle_game.options.min_entrance_score = 100

    player = farkle_game.current_player
    assert player.score == 0

    # Try to bank with 0 score (should fail - already handled by can_bank check, but we want to test our specific condition)
    player.turn_score = 50
    # Add a mock dice so has_scoring_dice check passes or len(dice.values) == 0 passes
    player.dice.values = []

    # Check if bank is enabled - should fail due to entrance score
    assert farkle_game._is_bank_enabled(player) == (
        "farkle-must-reach-entrance-score",
        {"points": 100},
    )

    # Increase turn score to meet requirement
    player.turn_score = 100
    assert farkle_game._is_bank_enabled(player) is None

    # Increase turn score to exceed requirement
    player.turn_score = 150
    assert farkle_game._is_bank_enabled(player) is None

def test_minimal_bank_score(farkle_game):
    # Set custom scores
    farkle_game.options.min_entrance_score = 100
    farkle_game.options.min_bank_score = 30

    player = farkle_game.current_player
    # Player has already entered the game
    player.score = 200

    # Try to bank with less than bank score
    player.turn_score = 20
    player.dice.values = []

    # Should fail due to bank score
    assert farkle_game._is_bank_enabled(player) == (
        "farkle-must-reach-bank-score",
        {"points": 30},
    )

    # Increase turn score to meet requirement
    player.turn_score = 30
    assert farkle_game._is_bank_enabled(player) is None

    # Increase turn score to exceed requirement
    player.turn_score = 50
    assert farkle_game._is_bank_enabled(player) is None

def test_bot_think_entrance_score(farkle_game):
    farkle_game.options.min_entrance_score = 100

    bot_player = farkle_game.get_player_by_name("player2")
    bot_player.is_bot = True
    bot_player.score = 0
    bot_player.turn_score = 50
    bot_player.dice.values = []

    # Bot shouldn't bank yet, hasn't reached entrance score
    action = farkle_game.bot_think(bot_player)
    # The action could be "roll" or a scoring combo, but NOT "bank"
    assert action != "bank"

def test_bot_think_bank_score(farkle_game):
    farkle_game.options.min_bank_score = 30

    bot_player = farkle_game.get_player_by_name("player2")
    bot_player.is_bot = True
    bot_player.score = 100 # Already in
    bot_player.turn_score = 20
    bot_player.dice.values = []

    # Bot shouldn't bank yet, hasn't reached bank score
    action = farkle_game.bot_think(bot_player)
    assert action != "bank"


def test_bot_rolls_with_six_available_after_hot_dice(farkle_game):
    bot_player = farkle_game.current_player
    bot_player.is_bot = True
    bot_player.score = 100
    bot_player.turn_score = 250
    bot_player.banked_dice = [1, 2, 3, 4, 5, 6]
    bot_player.dice.values = []
    bot_player.has_taken_combo = True

    assert farkle_game._get_roll_dice_count(bot_player) == 6
    assert farkle_game._is_bank_enabled(bot_player) is None
    assert farkle_game.bot_think(bot_player) == "roll"


def test_bot_keeps_scoring_dice_before_banking(farkle_game):
    bot_player = farkle_game.current_player
    bot_player.is_bot = True
    bot_player.score = 100
    bot_player.turn_score = 150
    bot_player.dice.values = [1, 5]
    bot_player.has_taken_combo = True
    farkle_game.update_scoring_actions(bot_player)

    assert farkle_game._is_bank_enabled(bot_player) is None
    assert farkle_game.bot_think(bot_player) == "score_single_1_1"


def test_bot_prefers_future_rich_scoring_choice(farkle_game):
    bot_player = farkle_game.current_player
    bot_player.is_bot = True
    bot_player.turn_score = 0
    bot_player.dice.values = [1, 2, 2, 2, 6, 6]
    bot_player.has_taken_combo = False
    farkle_game.update_scoring_actions(bot_player)

    assert farkle_game.bot_think(bot_player) == "score_single_1_1"


def test_prestart_validate_blocks_minimums_above_target():
    game = FarkleGame(options=FarkleOptions(target_score=500))
    game.options.min_entrance_score = 600
    game.options.min_bank_score = 700

    assert game.prestart_validate() == [
        (
            "farkle-error-entrance-above-target",
            {"entrance": 600, "target": 500},
        ),
        ("farkle-error-bank-above-target", {"bank": 700, "target": 500}),
    ]


def test_can_bank_after_keeping_one_combo_even_if_scoring_dice_remain(farkle_game):
    player = farkle_game.current_player
    player.score = 0
    player.turn_score = 50
    player.has_taken_combo = True
    player.dice.values = [2, 2, 2, 6, 6]

    assert farkle_game._is_bank_enabled(player) is None
    assert farkle_game._is_bank_hidden(player) == Visibility.VISIBLE


def test_risky_roll_confirmation_respects_preference(farkle_game, monkeypatch):
    player = farkle_game.current_player
    user = farkle_game.get_user(player)
    assert user is not None
    player.score = 100
    player.turn_score = 150
    player.has_taken_combo = True
    player.dice.values = [2, 3]

    def fixed_roll():
        player.dice.values = [1, 5]
        return player.dice.values

    monkeypatch.setattr(player.dice, "roll", fixed_roll)

    farkle_game._action_roll(player, "roll")

    assert player.pending_risky_action.startswith("roll:150")
    assert player.risky_confirm_ticks == RISK_CONFIRM_TICKS
    assert player.dice.values == [2, 3]
    assert "Rolling again risks losing them" in user.get_last_spoken()

    farkle_game._action_roll(player, "roll")

    assert player.pending_risky_action == ""
    assert player.dice.values == [1, 5]


def test_risky_roll_confirmation_can_be_disabled(farkle_game, monkeypatch):
    player = farkle_game.current_player
    user = farkle_game.get_user(player)
    assert user is not None
    user.preferences.confirm_destructive_actions = False
    player.score = 100
    player.turn_score = 150
    player.has_taken_combo = True
    player.dice.values = [2, 3]

    def fixed_roll():
        player.dice.values = [1, 5]
        return player.dice.values

    monkeypatch.setattr(player.dice, "roll", fixed_roll)

    farkle_game._action_roll(player, "roll")

    assert player.pending_risky_action == ""
    assert player.dice.values == [1, 5]


def test_brief_bank_announcement_is_personalized(farkle_game):
    actor, observer = farkle_game.players
    actor_user = farkle_game.get_user(actor)
    observer_user = farkle_game.get_user(observer)
    assert actor_user is not None
    assert observer_user is not None
    actor_user.preferences.brief_announcements = True
    actor.score = 50
    actor.turn_score = 100
    actor.has_taken_combo = True
    actor.dice.values = [2, 3]
    actor_user.clear_messages()
    observer_user.clear_messages()

    farkle_game._action_bank(actor, "bank")

    assert "You bank 100; total 150." in actor_user.get_spoken_messages()
    assert "player1 banks 100 points for a total of 150." in observer_user.get_spoken_messages()


def test_touch_bank_focuses_persistent_roll_anchor(farkle_game):
    actor, next_player = farkle_game.players
    actor_user = farkle_game.get_user(actor)
    assert actor_user is not None
    actor_user.client_type = "mobile"
    actor.score = 50
    actor.turn_score = 100
    actor.has_taken_combo = True
    actor.dice.values = [2, 3]

    farkle_game.execute_action(actor, "bank")
    farkle_game.flush_menus()

    assert farkle_game.current_player is next_player
    assert actor_user.menus["turn_menu"]["selection_id"] == "roll"


def test_tiebreaker_keeps_nonfinalists_in_final_results():
    users = [MockUser("p1"), MockUser("p2"), MockUser("p3")]
    game = FarkleGame()
    for user in users:
        game.add_player(user.username, user)
    game.on_start()
    p1, p2, p3 = game.players
    game.options.target_score = 500
    p1.score = 500
    p2.score = 500
    p3.score = 300

    game._on_round_end()

    assert p3.is_spectator is False
    assert game.tiebreaker_player_names == ["p1", "p2"]
    assert [player.name for player in game.turn_players] == ["p1", "p2"]
    result_names = [player.player_name for player in game.build_game_result().player_results]
    assert result_names == ["p1", "p2", "p3"]


def test_roll_focuses_first_scoring_action(farkle_game, monkeypatch):
    player = farkle_game.current_player
    user = farkle_game.get_user(player)
    assert user is not None

    def fixed_roll():
        player.dice.values = [1, 2, 3, 4, 6, 6]
        return player.dice.values

    monkeypatch.setattr(player.dice, "roll", fixed_roll)

    farkle_game._action_roll(player, "roll")
    farkle_game.flush_menus()

    menu = user.menus["turn_menu"]
    score_ids = [
        item.id
        for item in menu["items"]
        if getattr(item, "id", "").startswith("score_")
    ]
    assert score_ids
    assert menu["selection_id"] == score_ids[0]


def test_farkle_locale_key_and_variable_parity():
    root = Path(__file__).resolve().parents[1]
    en_text = (root / "locales" / "en" / "farkle.ftl").read_text(encoding="utf-8")
    vi_text = (root / "locales" / "vi" / "farkle.ftl").read_text(encoding="utf-8")

    def messages(text: str) -> dict[str, set[str]]:
        result = {}
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

    assert messages(en_text) == messages(vi_text)
