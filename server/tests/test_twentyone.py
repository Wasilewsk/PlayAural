"""Tests for 21 (Survival Rules)."""

from pathlib import Path

from ..game_utils.cards import Card, Deck
from ..game_utils.options import IntOption
from ..games.twentyone.game import (
    MODIFIER_BREAK,
    MODIFIER_DRAW_2,
    MODIFIER_DRAW_SILENCE,
    MODIFIER_TARGET_24,
    TwentyOneGame,
    TwentyOneOptions,
)
from ..messages.localization import Localization
from ..users.bot import Bot
from ..users.test_user import MockUser


_locales_dir = Path(__file__).parent.parent / "locales"
Localization.init(_locales_dir)


def make_game(**option_overrides) -> tuple[TwentyOneGame, MockUser, MockUser]:
    game = TwentyOneGame(options=TwentyOneOptions(**option_overrides))
    game.setup_keybinds()
    alice_user = MockUser("Alice", uuid="p1")
    bob_user = MockUser("Bob", uuid="p2")
    game.add_player("Alice", alice_user)
    game.add_player("Bob", bob_user)
    game.host = "Alice"
    return game, alice_user, bob_user


def make_started_game(**option_overrides) -> tuple[TwentyOneGame, MockUser, MockUser]:
    game, alice_user, bob_user = make_game(**option_overrides)
    alice, bob = game.players
    alice.hp = 10
    bob.hp = 10
    game.status = "playing"
    game.game_active = True
    game.phase = "turns"
    game.set_turn_players([alice, bob])
    return game, alice_user, bob_user


def speech_texts(user: MockUser) -> list[str]:
    return [message.data["text"] for message in user.messages if message.type == "speak"]


def test_twentyone_documented_options_are_host_configurable() -> None:
    metas = TwentyOneOptions().get_option_metas()

    expected_ranges = {
        "starting_health": (10, 1, 100),
        "base_bet": (1, 0, 50),
        "starting_modifiers_per_round": (1, 0, 10),
        "draw_modifier_chance_percent": (35, 0, 100),
        "deck_count": (1, 1, 10),
    }

    assert set(expected_ranges).issubset(metas)
    for option_name, (default, min_val, max_val) in expected_ranges.items():
        meta = metas[option_name]
        assert isinstance(meta, IntOption)
        assert meta.default == default
        assert meta.min_val == min_val
        assert meta.max_val == max_val


def test_prestart_validation_rejects_no_damage_source_setup() -> None:
    game, _, _ = make_game(
        base_bet=0,
        starting_modifiers_per_round=0,
        draw_modifier_chance_percent=0,
    )

    assert "twentyone-error-no-damage-source" in game.prestart_validate()


def test_break_effect_uses_listener_locale_for_removed_effect_name() -> None:
    game, alice_user, bob_user = make_started_game()
    bob_user._locale = "vi"
    alice, bob = game.players
    bob.table_modifiers = [MODIFIER_TARGET_24]
    alice_user.messages.clear()
    bob_user.messages.clear()

    game._resolve_modifier(alice, MODIFIER_BREAK)

    bob_speech = " ".join(speech_texts(bob_user))
    assert "mục tiêu 24" in bob_speech
    assert "target 24" not in bob_speech


def test_hit_uses_first_and_third_person_draw_messages() -> None:
    game, alice_user, bob_user = make_started_game(draw_modifier_chance_percent=0)
    alice = game.players[0]
    game.deck = Deck(cards=[Card(id=1, rank=5, suit=0)])
    alice_user.messages.clear()
    bob_user.messages.clear()

    game._action_hit(alice, "hit")

    assert any("You draw" in text for text in speech_texts(alice_user))
    assert any("Alice draws" in text for text in speech_texts(bob_user))


def test_hit_is_disabled_when_deck_is_empty() -> None:
    game, _, _ = make_started_game()
    alice = game.players[0]
    game.deck = Deck(cards=[])
    turn_set = game.create_turn_action_set(alice)
    hit_action = turn_set.get_action("hit")
    assert hit_action is not None

    resolved = turn_set.resolve_action(game, alice, hit_action)

    assert not resolved.enabled
    assert resolved.disabled_reason == "twentyone-deck-empty-must-stand"


def test_bot_stands_when_deck_is_empty() -> None:
    game = TwentyOneGame()
    game.setup_keybinds()
    bot_player = game.add_player("Bot", Bot("Bot", uuid="p1"))
    human = game.add_player("Human", MockUser("Human", uuid="p2"))
    bot_player.hp = 10
    human.hp = 10
    game.status = "playing"
    game.game_active = True
    game.phase = "turns"
    game.deck = Deck(cards=[])
    game.set_turn_players([bot_player, human])

    assert game.bot_think(bot_player) == "stand"


def test_change_card_menu_shows_blocked_cards_and_reports_reason() -> None:
    game, alice_user, _ = make_started_game()
    alice, bob = game.players
    alice.modifiers = [MODIFIER_DRAW_2]
    bob.table_modifiers = [MODIFIER_DRAW_SILENCE]
    game.deck = Deck(cards=[Card(id=2, rank=2, suit=0)])
    alice_user.messages.clear()

    options = game._options_for_play_modifier(alice)

    assert len(options) == 1
    assert "unavailable:" in options[0]
    assert game._is_play_modifier_enabled(alice) is None

    game._action_play_modifier(alice, options[0], "play_modifier")

    assert alice.modifiers == [MODIFIER_DRAW_2]
    speech = " ".join(speech_texts(alice_user))
    assert "You cannot play draw 2" in speech
    assert "draw-blocking effect" in speech


def test_change_card_menu_preserves_all_hand_indexes_with_unplayable_cards() -> None:
    game, alice_user, _ = make_started_game()
    alice, bob = game.players
    alice.modifiers = [MODIFIER_BREAK, MODIFIER_TARGET_24]
    bob.table_modifiers = []
    game.deck = Deck(cards=[Card(id=2, rank=2, suit=0)])
    alice_user.messages.clear()

    options = game._options_for_play_modifier(alice)

    assert len(options) == 2
    assert options[0].startswith("1:")
    assert "unavailable:" in options[0]
    assert options[1].startswith("2:")

    game._action_play_modifier(alice, options[0], "play_modifier")

    assert alice.modifiers == [MODIFIER_BREAK, MODIFIER_TARGET_24]
    assert any("no active table effects" in text for text in speech_texts(alice_user))
