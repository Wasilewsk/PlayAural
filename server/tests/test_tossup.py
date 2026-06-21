"""Tests for polished Toss Up mechanics, accessibility, and persistence."""

import json
from pathlib import Path
import random
import re
from unittest.mock import patch

import pytest

from ..games.registry import GameRegistry
from ..games.tossup.game import (
    RISK_CONFIRM_TICKS,
    TossUpGame,
    TossUpOptions,
    TossUpPlayer,
)
from ..messages.localization import Localization
from ..users.bot import Bot
from ..users.test_user import MockUser


LOCALES_DIR = Path(__file__).parent.parent / "locales"


def make_game(
    *,
    player_count: int = 2,
    start: bool = True,
    bot_all: bool = False,
    mobile_first: bool = False,
    **option_overrides,
) -> TossUpGame:
    game = TossUpGame(options=TossUpOptions(**option_overrides))
    game.setup_keybinds()
    for index in range(player_count):
        name = f"Player{index + 1}"
        user = (
            Bot(name, uuid=f"p{index + 1}")
            if bot_all
            else MockUser(name, uuid=f"p{index + 1}")
        )
        if mobile_first and index == 0:
            user.client_type = "mobile"
        game.add_player(name, user)
    game.host = "Player1"
    if start:
        game.on_start()
    return game


def roll_values(
    game: TossUpGame, player: TossUpPlayer, values: list[int]
) -> None:
    iterator = iter(values)

    def fixed_randint(low: int, high: int) -> int:
        if low == 1 and high in {3, 6}:
            return next(iterator)
        return low

    with patch("server.games.tossup.game.random.randint", side_effect=fixed_randint):
        game.execute_action(player, "roll")


def mark_safe_roll(player: TossUpPlayer) -> None:
    player.last_roll = {"green": 0, "yellow": 1, "red": 0}


def test_registration_metadata_defaults_and_preferences() -> None:
    game = TossUpGame()
    assert GameRegistry.get("tossup") is TossUpGame
    assert game.get_name() == "Toss Up"
    assert game.get_type() == "tossup"
    assert game.get_category() == "dice"
    assert game.get_min_players() == 2
    assert game.get_max_players() == 6
    assert game.get_supported_leaderboards() == [
        "wins",
        "total_score",
        "high_score",
        "rating",
        "games_played",
    ]
    assert game.relevant_preferences == [
        "brief_announcements",
        "confirm_destructive_actions",
    ]
    assert game.options == TossUpOptions(
        target_score=100,
        starting_dice=10,
        rules_variant="Standard",
    )


def test_player_and_game_state_round_trip() -> None:
    game = make_game(
        target_score=150,
        starting_dice=12,
        rules_variant="PlayAural",
    )
    player = game.players[0]
    game.round = 6
    game.tiebreaker_player_names = ["Player1", "Player2"]
    game._team_manager.teams[0].total_score = 78
    player.turn_points = 18
    player.dice_count = 4
    player.last_roll = {"green": 3, "yellow": 2, "red": 1}
    player.pending_risky_action = "roll:6:78:18:4:PlayAural"
    player.risky_confirm_ticks = 9

    data = json.loads(game.to_json())
    assert data["tiebreaker_player_names"] == ["Player1", "Player2"]
    assert data["players"][0]["pending_risky_action"].startswith("roll:6")

    loaded = TossUpGame.from_json(game.to_json())
    loaded_player = loaded.players[0]
    assert loaded.round == 6
    assert loaded.options == game.options
    assert loaded.tiebreaker_player_names == ["Player1", "Player2"]
    assert loaded.get_player_score(loaded_player) == 78
    assert loaded_player.turn_points == 18
    assert loaded_player.dice_count == 4
    assert loaded_player.last_roll == {"green": 3, "yellow": 2, "red": 1}
    assert loaded_player.risky_confirm_ticks == 9


def test_prestart_validation_reports_all_invalid_values() -> None:
    game = make_game(
        start=False,
        target_score=19,
        starting_dice=21,
        rules_variant="unknown",
    )
    errors = game.prestart_validate()
    assert (
        "tossup-error-target-out-of-range",
        {"value": 19, "min": 20, "max": 500},
    ) in errors
    assert (
        "tossup-error-dice-out-of-range",
        {"value": 21, "min": 5, "max": 20},
    ) in errors
    assert (
        "tossup-error-rules-variant",
        {"variant": "unknown"},
    ) in errors


def test_classic_color_mapping_scores_green_and_keeps_yellow_red() -> None:
    game = make_game(starting_dice=5)
    actor, observer = game.players
    actor_user = game.get_user(actor)
    observer_user = game.get_user(observer)
    assert isinstance(actor_user, MockUser)
    assert isinstance(observer_user, MockUser)
    actor_user.clear_messages()
    observer_user.clear_messages()

    roll_values(game, actor, [1, 3, 4, 5, 6])

    assert actor.last_roll == {"green": 2, "yellow": 2, "red": 1}
    assert actor.turn_points == 2
    assert actor.dice_count == 3
    assert "You rolled 2 green, 2 yellow, and 1 red." in actor_user.get_spoken_messages()
    assert (
        "Player1 rolled 2 green, 2 yellow, and 1 red."
        in observer_user.get_spoken_messages()
    )


def test_classic_red_light_busts_without_green() -> None:
    game = make_game(starting_dice=2)
    actor = game.players[0]
    actor.turn_points = 9
    actor.dice_count = 2
    old_player = game.current_player

    roll_values(game, actor, [4, 6])

    assert actor.last_roll == {"green": 0, "yellow": 1, "red": 1}
    assert actor.turn_points == 0
    assert game.current_player is not old_player


def test_forgiving_rules_bust_only_when_every_die_is_red() -> None:
    game = make_game(starting_dice=2, rules_variant="PlayAural")
    actor = game.players[0]

    roll_values(game, actor, [2, 3])
    assert actor.last_roll == {"green": 0, "yellow": 1, "red": 1}
    assert game.current_player is actor

    actor.turn_points = 7
    roll_values(game, actor, [3, 3])
    assert actor.turn_points == 0
    assert game.current_player is game.players[1]


def test_all_yellow_first_roll_can_bank_zero_and_end_turn() -> None:
    game = make_game(starting_dice=2)
    actor = game.players[0]
    roll_values(game, actor, [4, 5])

    bank = {
        resolved.action.id: resolved
        for resolved in game.get_all_visible_actions(actor)
    }["bank"]
    assert bank.enabled is True
    assert actor.turn_points == 0

    game.execute_action(actor, "bank")
    assert game.current_player is game.players[1]
    assert game.get_player_score(actor) == 0


def test_all_green_awards_fresh_set_without_ending_turn() -> None:
    game = make_game(starting_dice=2)
    actor = game.players[0]

    roll_values(game, actor, [1, 2])

    assert actor.turn_points == 2
    assert actor.dice_count == 2
    assert game.current_player is actor
    assert "fresh set of 2 dice" in " ".join(
        game.get_user(actor).get_spoken_messages()
    )


def test_roll_and_bank_remain_visible_as_stable_controls() -> None:
    game = make_game()
    current, waiting = game.players
    current_actions = {
        resolved.action.id: resolved
        for resolved in game.get_all_visible_actions(current)
    }
    waiting_actions = {
        resolved.action.id: resolved
        for resolved in game.get_all_visible_actions(waiting)
    }

    assert current_actions["roll"].enabled is True
    assert current_actions["bank"].enabled is False
    assert current_actions["bank"].disabled_reason == "tossup-error-bank-roll-first"
    assert waiting_actions["roll"].disabled_reason == (
        "tossup-error-roll-not-your-turn",
        {"player": "Player1"},
    )
    assert waiting_actions["bank"].disabled_reason == (
        "tossup-error-bank-not-your-turn",
        {"player": "Player1"},
    )


def test_touch_focus_returns_to_roll_after_roll_and_bank() -> None:
    game = make_game(starting_dice=2, mobile_first=True)
    actor = game.players[0]
    user = game.get_user(actor)
    assert isinstance(user, MockUser)

    roll_values(game, actor, [1, 4])
    game.flush_menus()
    assert user.menus["turn_menu"]["selection_id"] == "roll"

    game.execute_action(actor, "bank")
    game.flush_menus()
    assert user.menus["turn_menu"]["selection_id"] == "roll"


def test_touch_focus_returns_to_roll_after_bust() -> None:
    game = make_game(starting_dice=2, mobile_first=True)
    actor = game.players[0]
    user = game.get_user(actor)
    assert isinstance(user, MockUser)
    actor.turn_points = 4

    roll_values(game, actor, [4, 6])
    game.flush_menus()

    assert game.current_player is game.players[1]
    assert user.menus["turn_menu"]["selection_id"] == "roll"


def test_touch_bank_does_not_steal_next_players_menu_focus() -> None:
    game = make_game(start=False, starting_dice=2, mobile_first=True)
    next_user = game.get_user(game.players[1])
    assert isinstance(next_user, MockUser)
    next_user.client_type = "mobile"
    game.on_start()
    game.flush_menus()

    actor, next_player = game.players
    actor_user = game.get_user(actor)
    assert isinstance(actor_user, MockUser)
    actor_user.clear_messages()
    next_user.clear_messages()

    roll_values(game, actor, [1, 4])
    game.flush_menus()
    actor_user.clear_messages()
    next_user.clear_messages()
    game.execute_action(actor, "bank")
    game.flush_menus()

    assert game.current_player is next_player
    actor_updates = [
        message
        for message in actor_user.messages
        if message.type in {"show_menu", "update_menu"}
        and message.data.get("menu_id") == "turn_menu"
    ]
    next_updates = [
        message
        for message in next_user.messages
        if message.type in {"show_menu", "update_menu"}
        and message.data.get("menu_id") == "turn_menu"
    ]
    assert actor_updates[-1].data["selection_id"] == "roll"
    assert next_updates[-1].data["selection_id"] is None


def test_touch_standard_actions_start_with_game_status() -> None:
    game = make_game(mobile_first=True)
    player = game.players[0]
    action_ids = [
        resolved.action.id
        for resolved in game.get_all_visible_actions(player)
        if resolved.action.id
        in {"check_turn_status", "check_scores", "whose_turn", "whos_at_table"}
    ]
    assert action_ids == [
        "check_turn_status",
        "check_scores",
        "whose_turn",
        "whos_at_table",
    ]


def test_turn_status_has_actor_and_observer_context() -> None:
    game = make_game(starting_dice=2)
    actor, observer = game.players
    actor_user = game.get_user(actor)
    observer_user = game.get_user(observer)
    assert isinstance(actor_user, MockUser)
    assert isinstance(observer_user, MockUser)
    roll_values(game, actor, [1, 4])
    actor_user.clear_messages()
    observer_user.clear_messages()

    game.execute_action(actor, "check_turn_status")
    game.execute_action(observer, "check_turn_status")

    assert actor_user.get_last_spoken().startswith("Your last roll")
    assert observer_user.get_last_spoken().startswith("Player1 last rolled")


def test_spectators_receive_public_rolls_and_can_check_status() -> None:
    game = make_game(player_count=3, start=False, starting_dice=2)
    spectator = game.players[2]
    spectator.is_spectator = True
    spectator_user = game.get_user(spectator)
    assert isinstance(spectator_user, MockUser)
    game.on_start()
    spectator_user.clear_messages()

    roll_values(game, game.players[0], [1, 4])
    assert spectator_user.get_spoken_messages()[0].startswith("Player1 rolled")

    game.execute_action(spectator, "check_turn_status")
    assert spectator_user.get_last_spoken().startswith("Player1 last rolled")


def test_brief_announcements_are_selected_per_listener() -> None:
    game = make_game(starting_dice=2)
    actor, observer = game.players
    actor_user = game.get_user(actor)
    observer_user = game.get_user(observer)
    assert isinstance(actor_user, MockUser)
    assert isinstance(observer_user, MockUser)
    actor_user.preferences.brief_announcements = True
    actor_user.clear_messages()
    observer_user.clear_messages()

    roll_values(game, actor, [1, 4])

    assert actor_user.get_spoken_messages() == [
        "You: 1 green and 1 yellow; turn total 1; 1 left."
    ]
    assert len(observer_user.get_spoken_messages()) == 2
    assert observer_user.get_spoken_messages()[0].startswith("Player1 rolled")


def test_risky_roll_requires_second_press_and_preserves_state() -> None:
    game = make_game(starting_dice=5)
    actor = game.players[0]
    user = game.get_user(actor)
    assert isinstance(user, MockUser)
    actor.turn_points = 20
    actor.dice_count = 1
    mark_safe_roll(actor)
    before = dict(actor.last_roll)

    with patch("server.games.tossup.game.random.randint", return_value=1) as randint:
        game.execute_action(actor, "roll")
        assert randint.call_count == 0
        assert actor.turn_points == 20
        assert actor.last_roll == before
        assert actor.pending_risky_action.startswith("roll:")
        assert actor.risky_confirm_ticks == RISK_CONFIRM_TICKS
        assert "Press Roll again" in user.get_last_spoken()

        game.execute_action(actor, "roll")
        assert randint.call_count == 1

    assert actor.pending_risky_action == ""
    assert actor.turn_points == 21


def test_risky_confirmation_can_be_disabled_and_expires() -> None:
    game = make_game(starting_dice=5)
    actor = game.players[0]
    user = game.get_user(actor)
    assert isinstance(user, MockUser)
    actor.turn_points = 20
    actor.dice_count = 1
    mark_safe_roll(actor)
    user.preferences.confirm_destructive_actions = False

    with patch("server.games.tossup.game.random.randint", return_value=1):
        game.execute_action(actor, "roll")
    assert actor.turn_points == 21
    assert actor.pending_risky_action == ""

    actor.turn_points = 20
    actor.dice_count = 1
    mark_safe_roll(actor)
    user.preferences.confirm_destructive_actions = True
    game.execute_action(actor, "roll")
    actor.risky_confirm_ticks = 1
    game.on_tick()
    assert actor.pending_risky_action == ""
    assert actor.risky_confirm_ticks == 0


def test_low_value_reroll_does_not_interrupt_with_confirmation() -> None:
    game = make_game(starting_dice=5)
    actor = game.players[0]
    actor.turn_points = 4
    actor.dice_count = 1
    mark_safe_roll(actor)

    with patch("server.games.tossup.game.random.randint", return_value=1):
        game.execute_action(actor, "roll")

    assert actor.turn_points == 5
    assert actor.pending_risky_action == ""


def test_exact_target_does_not_trigger_game_end() -> None:
    game = make_game(target_score=20)
    first, second = game.players
    game._team_manager.teams[0].total_score = 19
    first.turn_points = 1
    mark_safe_roll(first)
    game.execute_action(first, "bank")

    mark_safe_roll(second)
    game.execute_action(second, "bank")

    assert game.status == "playing"
    assert game.get_player_score(first) == 20
    assert game.current_player is first
    assert game.round == 2


def test_last_player_crossing_threshold_finishes_the_round_immediately() -> None:
    game = make_game(target_score=20)
    first, second = game.players

    mark_safe_roll(first)
    game.execute_action(first, "bank")

    game._team_manager.teams[1].total_score = 20
    second.turn_points = 1
    mark_safe_roll(second)
    game.execute_action(second, "bank")

    assert game.status == "finished"
    assert game.get_player_score(second) == 21
    assert game.build_game_result().custom_data["winner_name"] == "Player2"


def test_only_remaining_players_receive_final_response_turns() -> None:
    game = make_game(player_count=3, target_score=20)
    first, trigger, responder = game.players

    mark_safe_roll(first)
    game.execute_action(first, "bank")

    game._team_manager.teams[1].total_score = 20
    trigger.turn_points = 1
    mark_safe_roll(trigger)
    game.execute_action(trigger, "bank")
    assert game.current_player is responder
    assert game.status == "playing"

    game._team_manager.teams[2].total_score = 20
    responder.turn_points = 2
    mark_safe_roll(responder)
    game.execute_action(responder, "bank")

    assert game.status == "finished"
    assert game.get_player_score(trigger) == 21
    assert game.get_player_score(responder) == 22
    assert game.build_game_result().custom_data["winner_name"] == "Player3"


def test_tiebreaker_filters_turns_without_mutating_player_roles() -> None:
    game = make_game(player_count=3, target_score=20)
    first, second, third = game.players
    game._team_manager.teams[0].total_score = 21
    game._team_manager.teams[1].total_score = 21
    game._team_manager.teams[2].total_score = 15

    game._on_round_end()

    assert game.tiebreaker_player_names == ["Player1", "Player2"]
    assert [player.name for player in game.turn_players] == ["Player1", "Player2"]
    assert all(not player.is_spectator for player in game.players)
    assert [p.player_name for p in game.build_game_result().player_results] == [
        "Player1",
        "Player2",
        "Player3",
    ]

    first.turn_points = 1
    mark_safe_roll(first)
    game.execute_action(first, "bank")
    mark_safe_roll(second)
    game.execute_action(second, "bank")
    assert game.status == "finished"
    assert game.build_game_result().custom_data["winner_name"] == "Player1"
    assert third.is_spectator is False


def test_legacy_tiebreaker_spectator_flags_are_repaired_on_restore() -> None:
    game = make_game(player_count=3, target_score=20)
    first, second, third = game.players
    game._team_manager.teams[0].total_score = 21
    game._team_manager.teams[1].total_score = 21
    game._team_manager.teams[2].total_score = 15
    third.is_spectator = True
    game.tiebreaker_player_names = []

    loaded = TossUpGame.from_json(game.to_json())
    loaded.rebuild_runtime_state()

    assert loaded.tiebreaker_player_names == ["Player1", "Player2"]
    assert all(not player.is_spectator for player in loaded.players)
    assert [player.name for player in loaded._round_players()] == [
        "Player1",
        "Player2",
    ]


def test_finishing_clears_all_risky_confirmation_state() -> None:
    game = make_game(target_score=20)
    first, second = game.players
    first.pending_risky_action = "roll:first"
    first.risky_confirm_ticks = 50
    second.pending_risky_action = "roll:second"
    second.risky_confirm_ticks = 50
    game._team_manager.teams[0].total_score = 21

    game._on_round_end()

    assert game.status == "finished"
    assert all(not player.pending_risky_action for player in game.players)
    assert all(player.risky_confirm_ticks == 0 for player in game.players)


def test_bot_strategy_uses_risk_and_final_score_context() -> None:
    game = make_game(target_score=100)
    player, opponent = game.players
    player.turn_points = 20
    player.dice_count = 1
    mark_safe_roll(player)
    assert game.bot_think(player) == "bank"

    game._team_manager.teams[1].total_score = 105
    player.turn_points = 5
    player.dice_count = 1
    assert game.bot_think(player) == "roll"

    game._team_manager.teams[0].total_score = 104
    player.turn_points = 2
    assert game.bot_think(player) == "bank"


@pytest.mark.parametrize(
    ("player_count", "rules_variant"),
    [(2, "Standard"), (2, "PlayAural"), (6, "Standard")],
)
def test_bot_games_complete(
    player_count: int, rules_variant: str
) -> None:
    random.seed(2026 + player_count)
    game = make_game(
        player_count=player_count,
        bot_all=True,
        target_score=20,
        starting_dice=5,
        rules_variant=rules_variant,
    )

    for tick in range(15000):
        if game.status == "finished":
            break
        if tick and tick % 200 == 0:
            game = TossUpGame.from_json(game.to_json())
            for index in range(player_count):
                name = f"Player{index + 1}"
                game.attach_user(name, Bot(name, uuid=f"p{index + 1}"))
            game.rebuild_runtime_state()
            for player in game.players:
                game.setup_player_actions(player)
        game.on_tick()

    assert game.status == "finished"
    assert max(game.get_player_score(player) for player in game.players) > 20
    assert len(game.players) == player_count


def test_locale_key_and_variable_parity() -> None:
    en_text = (LOCALES_DIR / "en" / "tossup.ftl").read_text(encoding="utf-8")
    vi_text = (LOCALES_DIR / "vi" / "tossup.ftl").read_text(encoding="utf-8")

    def messages(text: str) -> dict[str, set[str]]:
        result: dict[str, set[str]] = {}
        current = ""
        for line in text.splitlines():
            match = re.match(r"^([a-z0-9-]+)\s*=", line)
            if match:
                current = match.group(1)
                result[current] = set()
            if current:
                result[current].update(
                    re.findall(r"\{\s*\$([a-z0-9_]+)", line)
                )
        return result

    assert messages(en_text) == messages(vi_text)
    assert Localization.get(
        "vi", "tossup-result-green", count=2
    ) == "2 mặt xanh"


def test_vietnamese_manual_matches_localized_terminology() -> None:
    text = (
        Path(__file__).parent.parent
        / "documentation"
        / "content"
        / "vi"
        / "games"
        / "tossup.md"
    ).read_text(encoding="utf-8")
    assert "mặt xanh" in text
    assert "mặt vàng" in text
    assert "mặt đỏ" in text
    assert "mất trắng" in text
    assert "chốt điểm" in text
    assert "vượt mốc" in text
    assert "nổ" not in text
