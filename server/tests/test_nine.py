"""Tests for Nine rules and accessibility polish."""

from pathlib import Path
import re
from unittest.mock import patch

from ..game_utils.cards import Card, SUIT_CLUBS, SUIT_DIAMONDS, SUIT_HEARTS
from ..games.nine.game import (
    CARD_ACTION_PREFIX,
    NineGame,
    RANK_EIGHT,
    RANK_NINE,
    RANK_SEVEN,
    RANK_SIX,
    RANK_TEN,
    STARTING_NINE_SUIT,
)
from ..games.nine.state import SequenceState
from ..messages.localization import Localization
from ..users.test_user import MockUser


_locales_dir = Path(__file__).parent.parent / "locales"
Localization.init(_locales_dir)


def _add_players(game: NineGame, count: int) -> list:
    players = []
    for index in range(count):
        name = f"Player{index + 1}"
        players.append(game.add_player(name, MockUser(name, uuid=f"nine-player-{index + 1}")))
    return players


def _ftl_messages(text: str) -> dict[str, set[str]]:
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


def test_nine_metadata_uses_authentic_supported_counts_and_preferences() -> None:
    assert NineGame.get_min_players() == 3
    assert NineGame.get_max_players() == 6
    assert NineGame.relevant_preferences == ["brief_announcements"]


def test_invalid_player_count_returns_localizable_error_key() -> None:
    two_player_game = NineGame()
    _add_players(two_player_game, 2)

    five_player_game = NineGame()
    _add_players(five_player_game, 5)

    assert "nine-error-invalid-player-count" in two_player_game.validate_start()
    assert "nine-error-invalid-player-count" in five_player_game.validate_start()


def test_direct_start_with_invalid_player_count_refuses_without_finishing() -> None:
    game = NineGame()
    _add_players(game, 2)

    game.on_start()

    assert game.status != "finished"
    assert game.game_active is False


def test_starting_nine_is_diamonds_not_clubs() -> None:
    game = NineGame()
    alice, bob, charlie = _add_players(game, 3)
    alice.hand = [Card(id=1, rank=RANK_NINE, suit=SUIT_CLUBS)]
    bob.hand = [Card(id=2, rank=RANK_NINE, suit=SUIT_DIAMONDS)]
    charlie.hand = [Card(id=3, rank=RANK_SIX, suit=SUIT_HEARTS)]

    assert STARTING_NINE_SUIT == SUIT_DIAMONDS
    assert game._find_starting_nine_player() == bob.id


def test_first_play_requires_nine_of_diamonds_with_contextual_reason() -> None:
    game = NineGame()
    player = _add_players(game, 3)[0]
    game.status = "playing"
    game.current_player = player
    clubs_nine = Card(id=1, rank=RANK_NINE, suit=SUIT_CLUBS)
    diamonds_nine = Card(id=2, rank=RANK_NINE, suit=SUIT_DIAMONDS)
    player.hand = [clubs_nine, diamonds_nine]

    can_play_clubs, reason = game._can_play_card(player, clubs_nine)
    can_play_diamonds, _ = game._can_play_card(player, diamonds_nine)

    assert can_play_clubs is False
    assert reason == (
        "nine-reason-must-play-starting-nine",
        {"card": "9 of clubs", "starting_card": "9 of diamonds"},
    )
    assert can_play_diamonds is True


def test_invalid_card_attempt_speaks_specific_recovery_message() -> None:
    game = NineGame()
    user = MockUser("Alice", uuid="nine-invalid-play")
    player = game.add_player("Alice", user)
    _add_players(game, 2)
    game.status = "playing"
    game.set_turn_players(game.get_active_players())
    player.hand = [Card(id=1, rank=RANK_NINE, suit=SUIT_CLUBS)]

    game._action_play_card(player, f"{CARD_ACTION_PREFIX}1")

    assert user.get_last_spoken() == (
        "The first play must be the 9 of diamonds. "
        "9 of clubs cannot be played until the table is opened."
    )


def test_card_actions_use_stable_card_ids_and_report_stale_actions() -> None:
    game = NineGame()
    user = MockUser("Alice", uuid="nine-card-actions")
    player = game.add_player("Alice", user)
    _add_players(game, 2)
    game.setup_keybinds()
    game.status = "playing"
    game.set_turn_players(game.get_active_players())
    game.nine_state.nine_of_clubs_played = True
    game.nine_state.sequences = {
        SUIT_DIAMONDS: SequenceState(
            low_card=Card(id=100, rank=RANK_NINE, suit=SUIT_DIAMONDS),
            high_card=Card(id=100, rank=RANK_NINE, suit=SUIT_DIAMONDS),
        )
    }
    player.hand = [
        Card(id=12, rank=RANK_EIGHT, suit=SUIT_DIAMONDS),
        Card(id=42, rank=RANK_TEN, suit=SUIT_DIAMONDS),
    ]

    game._update_card_actions(player)
    turn_set = game.get_action_set(player, "turn")

    assert turn_set is not None
    assert f"{CARD_ACTION_PREFIX}12" in turn_set._order
    assert f"{CARD_ACTION_PREFIX}42" in turn_set._order
    assert "play_card_slot_1" not in turn_set._order

    user.clear_messages()
    game._action_play_card(player, f"{CARD_ACTION_PREFIX}999")

    assert user.get_last_spoken() == (
        "That card is no longer in your hand. Your hand menu has been refreshed."
    )


def test_brief_announcements_are_per_listener() -> None:
    game = NineGame()
    actor_user = MockUser("Alice", uuid="nine-brief-actor")
    observer_user = MockUser("Bob", uuid="nine-brief-observer")
    third_user = MockUser("Charlie", uuid="nine-brief-third")
    actor_user.preferences.brief_announcements = True
    actor = game.add_player("Alice", actor_user)
    game.add_player("Bob", observer_user)
    game.add_player("Charlie", third_user)
    game.status = "playing"
    game.current_player = actor
    game.nine_state.nine_of_clubs_played = True
    game.nine_state.sequences = {
        SUIT_DIAMONDS: SequenceState(
            low_card=Card(id=100, rank=RANK_NINE, suit=SUIT_DIAMONDS),
            high_card=Card(id=100, rank=RANK_NINE, suit=SUIT_DIAMONDS),
        )
    }
    actor.hand = [Card(id=1, rank=RANK_EIGHT, suit=SUIT_DIAMONDS)]

    with patch.object(game, "_end_turn"):
        game._play_card(actor, 0, actor.hand[0])

    assert actor_user.get_last_spoken() == "You play 8 of diamonds on diamonds."
    assert observer_user.get_last_spoken() == (
        "Alice extends the diamonds sequence with the 8 of diamonds."
    )


def test_bot_opens_with_nine_of_diamonds() -> None:
    game = NineGame()
    bot = game.create_player("bot", "Bot", is_bot=True)
    game.players = [bot]
    game.set_turn_players([bot])
    bot.hand = [
        Card(id=1, rank=RANK_NINE, suit=SUIT_CLUBS),
        Card(id=2, rank=RANK_NINE, suit=SUIT_DIAMONDS),
    ]

    assert game.bot_think(bot) == f"{CARD_ACTION_PREFIX}2"


def test_bot_prefers_extension_that_unlocks_its_own_run() -> None:
    game = NineGame()
    bot = game.create_player("bot", "Bot", is_bot=True)
    game.players = [bot]
    game.set_turn_players([bot])
    game.nine_state.nine_of_clubs_played = True
    game.nine_state.sequences = {
        SUIT_DIAMONDS: SequenceState(
            low_card=Card(id=100, rank=RANK_NINE, suit=SUIT_DIAMONDS),
            high_card=Card(id=100, rank=RANK_NINE, suit=SUIT_DIAMONDS),
        )
    }
    bot.hand = [
        Card(id=1, rank=RANK_EIGHT, suit=SUIT_DIAMONDS),
        Card(id=2, rank=RANK_TEN, suit=SUIT_DIAMONDS),
        Card(id=3, rank=RANK_SEVEN, suit=SUIT_DIAMONDS),
    ]

    assert game.bot_think(bot) == f"{CARD_ACTION_PREFIX}1"


def test_nine_auto_skip_does_not_play_turn_sound_for_skipped_player() -> None:
    game = NineGame()
    game.setup_keybinds()
    alice_user = MockUser("Alice", uuid="nine-turn-1")
    bob_user = MockUser("Bob", uuid="nine-turn-2")
    alice = game.add_player("Alice", alice_user)
    bob = game.add_player("Bob", bob_user)

    game.status = "playing"
    game.game_active = True
    game.nine_state.nine_of_clubs_played = True
    game.nine_state.sequences = {
        SUIT_CLUBS: SequenceState(
            low_card=Card(id=100, rank=RANK_NINE, suit=SUIT_CLUBS),
            high_card=Card(id=100, rank=RANK_NINE, suit=SUIT_CLUBS),
        )
    }
    alice.hand = [Card(id=1, rank=RANK_SIX, suit=SUIT_DIAMONDS)]
    bob.hand = [Card(id=2, rank=RANK_EIGHT, suit=SUIT_CLUBS)]
    game.set_turn_players([alice, bob])
    alice_user.clear_messages()
    bob_user.clear_messages()

    game._start_turn()

    assert "turn.ogg" not in alice_user.get_sounds_played()
    assert bob_user.get_sounds_played() == ["turn.ogg"]


def test_nine_locale_key_and_variable_parity() -> None:
    en_text = (_locales_dir / "en" / "nine.ftl").read_text(encoding="utf-8")
    vi_text = (_locales_dir / "vi" / "nine.ftl").read_text(encoding="utf-8")

    assert _ftl_messages(en_text) == _ftl_messages(vi_text)
