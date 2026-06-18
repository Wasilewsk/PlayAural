"""Tests for the Light Turret game."""

from pathlib import Path
import json
import random
import re
from unittest.mock import patch

from ..games.lightturret.game import (
    ACTION_SEQUENCE_ID,
    END_REASON_ALL_ELIMINATED,
    END_REASON_MAX_ROUNDS,
    RISK_CONFIRM_TICKS,
    UPGRADE_COST,
    LightTurretGame,
    LightTurretOptions,
    LightTurretPlayer,
)
from ..games.registry import GameRegistry
from ..messages.localization import Localization
from ..users.bot import Bot
from ..users.test_user import MockUser


_locales_dir = Path(__file__).parent.parent / "locales"
Localization.init(_locales_dir)


def make_game(
    *,
    player_count: int = 2,
    start: bool = False,
    bot_all: bool = False,
    mobile_first: bool = False,
    **option_overrides,
) -> LightTurretGame:
    game = LightTurretGame(options=LightTurretOptions(**option_overrides))
    game.setup_keybinds()
    for index in range(player_count):
        name = f"Player{index + 1}"
        if bot_all:
            user = Bot(name, uuid=f"p{index + 1}")
        else:
            user = MockUser(name, uuid=f"p{index + 1}")
            if mobile_first and index == 0:
                user.client_type = "mobile"
        game.add_player(name, user)
    game.host = "Player1"
    if start:
        game.on_start()
    return game


def advance_until(game: LightTurretGame, condition, max_ticks: int = 400) -> bool:
    for _ in range(max_ticks):
        if condition():
            return True
        game.on_tick()
    return condition()


def test_game_registered_defaults_and_metadata() -> None:
    assert GameRegistry.get("lightturret") is LightTurretGame
    game = LightTurretGame()
    assert game.get_name() == "Light Turret"
    assert game.get_type() == "lightturret"
    assert game.get_category() == "arcade"
    assert game.get_min_players() == 2
    assert game.get_max_players() == 4
    assert game.get_supported_leaderboards() == [
        "wins",
        "total_score",
        "high_score",
        "rating",
        "games_played",
    ]
    assert game.get_score_unit_key() == "game-score-unit-light"
    assert game.relevant_preferences == [
        "brief_announcements",
        "confirm_destructive_actions",
    ]
    assert game.options.starting_power == 10
    assert game.options.max_rounds == 50


def test_player_creation_and_start_state() -> None:
    game = make_game(start=True)
    player = game.players[0]

    assert isinstance(player, LightTurretPlayer)
    assert player.name == "Player1"
    assert player.is_bot is False
    assert player.alive is True
    assert player.power == 10
    assert player.light == 0
    assert player.coins == 0
    assert game.round == 1
    assert game.current_player == player


def test_prestart_validate_checks_option_ranges() -> None:
    low_power = make_game(starting_power=4)
    assert (
        "lightturret-error-starting-power-invalid",
        {"power": 4, "min": 5, "max": 30},
    ) in low_power.prestart_validate()

    high_rounds = make_game(max_rounds=201)
    assert (
        "lightturret-error-max-rounds-invalid",
        {"rounds": 201, "min": 10, "max": 200},
    ) in high_rounds.prestart_validate()


def test_serialization_preserves_polished_state_fields() -> None:
    game = make_game(start=True, starting_power=15)
    player = game.players[0]
    player.light = 7
    player.power = 18
    player.coins = 6
    player.pending_risky_action = "shoot:7:18:3"
    player.risky_confirm_ticks = 9
    game.round = 3
    game.end_reason = END_REASON_MAX_ROUNDS
    game.pending_action_player_id = player.id
    game.pending_action_kind = "shoot"
    game.pending_action_resolved = True

    data = json.loads(game.to_json())
    assert data["round"] == 3
    assert data["end_reason"] == END_REASON_MAX_ROUNDS
    assert data["players"][0]["pending_risky_action"] == "shoot:7:18:3"

    loaded = LightTurretGame.from_json(game.to_json())
    assert loaded.game_active is True
    assert loaded.round == 3
    assert loaded.end_reason == END_REASON_MAX_ROUNDS
    assert loaded.pending_action_player_id == player.id
    assert loaded.pending_action_kind == "shoot"
    assert loaded.pending_action_resolved is True
    assert loaded.players[0].light == 7
    assert loaded.players[0].power == 18
    assert loaded.players[0].coins == 6
    assert loaded.players[0].pending_risky_action == "shoot:7:18:3"
    assert loaded.players[0].risky_confirm_ticks == 9


def test_shoot_sequence_resolves_with_personal_and_public_messages() -> None:
    game = make_game(start=True)
    actor = game.players[0]
    observer = game.players[1]
    actor_user = game.get_user(actor)
    observer_user = game.get_user(observer)
    assert isinstance(actor_user, MockUser)
    assert isinstance(observer_user, MockUser)
    actor_user.clear_messages()
    observer_user.clear_messages()

    with patch("server.games.lightturret.game.random.randint", side_effect=[3, 1]):
        game.execute_action(actor, "shoot")

    assert game.has_active_sequence(sequence_id=ACTION_SEQUENCE_ID)
    assert actor.light == 0

    assert advance_until(
        game, lambda: not game.has_active_sequence(sequence_id=ACTION_SEQUENCE_ID)
    )
    assert actor.light == 3
    assert actor.coins == 6
    assert game.current_player == observer
    assert game.team_manager.get_team(actor.name).total_score == 3
    assert any("You fire and gain 3 light" in msg for msg in actor_user.get_spoken_messages())
    assert any(
        "Player1 fires and gains 3 light" in msg
        for msg in observer_user.get_spoken_messages()
    )


def test_action_sequence_lock_speaks_contextual_error() -> None:
    game = make_game(start=True)
    player = game.players[0]
    user = game.get_user(player)
    assert isinstance(user, MockUser)

    with patch("server.games.lightturret.game.random.randint", side_effect=[2, 1]):
        game.execute_action(player, "shoot")

    assert game.has_active_sequence(sequence_id=ACTION_SEQUENCE_ID)
    user.clear_messages()
    game.execute_action(player, "shoot")

    assert user.get_last_spoken() == Localization.get(
        "en", "lightturret-action-resolving"
    )


def test_waiting_touch_player_keeps_disabled_primary_action_anchors() -> None:
    game = make_game(start=True, mobile_first=True)
    waiting = game.players[1]
    user = game.get_user(waiting)
    assert isinstance(user, MockUser)
    user.client_type = "mobile"

    game.refresh_menus(waiting)
    game.flush_menus()

    visible_ids = [
        item.id
        for item in user.menus["turn_menu"]["items"]
        if getattr(item, "id", None)
    ]
    assert "shoot" in visible_ids
    assert "upgrade" in visible_ids

    user.clear_messages()
    game.handle_event(
        waiting,
        {"type": "menu", "menu_id": "turn_menu", "selection_id": "shoot"},
    )
    assert user.get_last_spoken() == Localization.get("en", "action-not-your-turn")


def test_risky_shot_requires_confirmation_when_enabled() -> None:
    game = make_game(start=True)
    player = game.players[0]
    user = game.get_user(player)
    assert isinstance(user, MockUser)
    user.preferences.confirm_destructive_actions = True
    player.light = 8
    player.power = 10
    user.clear_messages()

    game.execute_action(player, "shoot")

    assert not game.has_active_sequence(sequence_id=ACTION_SEQUENCE_ID)
    assert player.pending_risky_action == "shoot:8:10:1"
    assert player.risky_confirm_ticks == RISK_CONFIRM_TICKS
    assert "50% overload risk" in user.get_last_spoken()

    with patch("server.games.lightturret.game.random.randint", side_effect=[1, 1]):
        game.execute_action(player, "shoot")

    assert game.has_active_sequence(sequence_id=ACTION_SEQUENCE_ID)
    assert player.pending_risky_action == ""
    assert advance_until(
        game, lambda: not game.has_active_sequence(sequence_id=ACTION_SEQUENCE_ID)
    )
    assert player.light == 9


def test_risky_confirmation_expires_on_tick() -> None:
    game = make_game(start=True)
    player = game.players[0]
    user = game.get_user(player)
    assert isinstance(user, MockUser)
    user.preferences.confirm_destructive_actions = True
    player.light = 8
    player.power = 10

    game.execute_action(player, "shoot")
    assert player.risky_confirm_ticks == RISK_CONFIRM_TICKS

    for _ in range(RISK_CONFIRM_TICKS):
        game.on_tick()

    assert player.pending_risky_action == ""
    assert player.risky_confirm_ticks == 0


def test_upgrade_success_and_accident_overload_paths() -> None:
    success_game = make_game(start=True)
    success_player = success_game.players[0]
    success_user = success_game.get_user(success_player)
    assert isinstance(success_user, MockUser)
    success_player.coins = UPGRADE_COST
    success_user.clear_messages()

    with patch("server.games.lightturret.game.random.random", return_value=0.9), patch(
        "server.games.lightturret.game.random.randint", return_value=5
    ):
        success_game.execute_action(success_player, "upgrade")

    assert advance_until(
        success_game,
        lambda: not success_game.has_active_sequence(sequence_id=ACTION_SEQUENCE_ID),
    )
    assert success_player.coins == 0
    assert success_player.power == 15
    assert any("upgrade the core by 5 power" in msg for msg in success_user.get_spoken_messages())

    accident_game = make_game(start=True)
    accident_player = accident_game.players[0]
    accident_user = accident_game.get_user(accident_player)
    assert isinstance(accident_user, MockUser)
    accident_player.coins = UPGRADE_COST
    accident_player.light = 10
    accident_player.power = 10
    accident_user.clear_messages()

    with patch("server.games.lightturret.game.random.random", return_value=0.0), patch(
        "server.games.lightturret.game.random.randint", return_value=1
    ):
        accident_game.execute_action(accident_player, "upgrade")

    assert advance_until(
        accident_game,
        lambda: not accident_game.has_active_sequence(sequence_id=ACTION_SEQUENCE_ID),
    )
    assert accident_player.coins == 0
    assert accident_player.light == 11
    assert accident_player.alive is False
    assert any("core backfires and adds 1 light" in msg for msg in accident_user.get_spoken_messages())


def test_final_round_waits_for_every_surviving_player() -> None:
    game = make_game(start=True, max_rounds=10)
    first, second = game.players
    game.round = game.options.max_rounds
    game.turn_index = 0
    game.current_player = first

    game._on_turn_end()

    assert game.status == "playing"
    assert game.current_player == second

    game._on_turn_end()

    assert game.status == "finished"
    assert game.end_reason == END_REASON_MAX_ROUNDS


def test_tied_winners_are_recorded_without_single_winner_name() -> None:
    game = make_game(start=True)
    for player in game.players:
        player.light = 12
        player.power = 10
        player.alive = False
    game.end_reason = END_REASON_ALL_ELIMINATED

    result = game.build_game_result()

    assert set(result.custom_data["winner_ids"]) == {player.id for player in game.players}
    assert result.custom_data["winner_name"] is None
    assert result.custom_data["winner_light"] == 12
    end_screen = game.format_end_screen(result, "en")
    assert "First-place tie: Player1 and Player2 with 12 light." in end_screen


def test_winner_selector_uses_survived_branch() -> None:
    survived = Localization.get(
        "en",
        "lightturret-you-win",
        light=12,
        power=14,
        survived="true",
    )
    overloaded = Localization.get(
        "en",
        "lightturret-you-win",
        light=12,
        power=10,
        survived="false",
    )

    assert "Your turret survived." in survived
    assert "despite the overload." in overloaded


def test_live_status_box_uses_stable_rows_and_refreshes() -> None:
    game = make_game(start=True)
    player = game.players[0]
    user = game.get_user(player)
    assert isinstance(user, MockUser)

    game.execute_action(player, "check_stats")

    items = user.menus["status_box"]["items"]
    assert [item.id for item in items] == ["round", "player:p1", "player:p2"]
    assert "0 light" in items[1].text

    player.light = 4
    player.coins = 8
    game.refresh_menus(player)
    game.flush_menus()

    updated_items = user.menus["status_box"]["items"]
    assert [item.id for item in updated_items] == ["round", "player:p1", "player:p2"]
    assert "4 light" in updated_items[1].text
    assert "8 coins" in updated_items[1].text


def test_touch_standard_actions_use_platform_order() -> None:
    game = make_game(start=True, mobile_first=True)
    player = game.players[0]
    action_set = game.create_standard_action_set(player)

    assert action_set._order.index("check_stats") < action_set._order.index(
        "check_scores"
    )
    assert action_set._order.index("check_scores") < action_set._order.index(
        "whose_turn"
    )
    assert action_set._order.index("whose_turn") < action_set._order.index(
        "whos_at_table"
    )


def test_bot_game_completes_deterministically() -> None:
    random.seed(1234)
    game = make_game(player_count=4, start=True, bot_all=True, max_rounds=10)

    assert advance_until(game, lambda: game.status == "finished", max_ticks=15000)
    assert game.status == "finished"


def test_lightturret_locale_key_and_variable_parity() -> None:
    en_text = (_locales_dir / "en" / "lightturret.ftl").read_text(encoding="utf-8")
    vi_text = (_locales_dir / "vi" / "lightturret.ftl").read_text(encoding="utf-8")

    def messages(text: str) -> dict[str, set[str]]:
        result = {}
        current_key = None
        current_lines: list[str] = []
        for line in text.splitlines():
            if line and not line.startswith((" ", "\t")) and "=" in line:
                if current_key is not None:
                    result[current_key] = set(
                        re.findall(
                            r"\{\s*\$([a-zA-Z_][\w-]*)",
                            "\n".join(current_lines),
                        )
                    )
                current_key = line.split("=", 1)[0].strip()
                current_lines = [line]
            elif current_key is not None:
                current_lines.append(line)
        if current_key is not None:
            result[current_key] = set(
                re.findall(
                    r"\{\s*\$([a-zA-Z_][\w-]*)",
                    "\n".join(current_lines),
                )
            )
        return result

    assert messages(en_text) == messages(vi_text)


def test_vietnamese_documentation_uses_in_game_terms() -> None:
    doc_text = (
        Path(__file__).parent.parent
        / "documentation"
        / "content"
        / "vi"
        / "games"
        / "lightturret.md"
    ).read_text(encoding="utf-8")

    assert Localization.get("vi", "game-name-lightturret") in doc_text
    assert "quang năng" in doc_text
    assert "công suất" in doc_text
    assert "nâng cấp lõi" in doc_text
