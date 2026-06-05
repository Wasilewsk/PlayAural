"""Tests for the space-to-describe option feature.

Pressing space while an option is focused in the lobby/options menu speaks the
option's OptionMeta.description; during play, space remains a game keybind.
"""

from pathlib import Path

from ..games.pusoydos.game import PusoyDosGame
from ..messages.localization import Localization
from ..users.test_user import MockUser


_locales_dir = Path(__file__).parent.parent / "locales"
Localization.init(_locales_dir)


def _make_game(locale: str = "en") -> tuple[PusoyDosGame, MockUser, object]:
    game = PusoyDosGame()
    user = MockUser("Alice")
    user._locale = locale
    player = game.add_player("Alice", user)
    game.status = "waiting"
    game.setup_player_actions(player)
    return game, user, player


def _space(game, player, menu_item_id) -> None:
    game.handle_event(
        player, {"type": "keybind", "key": "space", "menu_item_id": menu_item_id}
    )


def test_space_speaks_option_description_en() -> None:
    game, user, player = _make_game("en")
    _space(game, player, "set_game_mode")
    spoken = user.get_spoken_messages()
    assert spoken, "expected a description to be spoken"
    assert "Elimination" in spoken[-1]


def test_space_speaks_option_description_vi() -> None:
    game, user, player = _make_game("vi")
    _space(game, player, "toggle_instant_wins")
    spoken = user.get_spoken_messages()
    assert spoken, "expected a Vietnamese description to be spoken"
    # The Vietnamese description contains non-ASCII characters.
    assert any(ord(ch) > 127 for ch in spoken[-1])


def test_space_on_non_option_says_nothing() -> None:
    game, user, player = _make_game("en")
    _space(game, player, "some_unrelated_button")
    assert user.get_spoken_messages() == []


def test_space_during_play_is_not_hijacked_for_descriptions() -> None:
    game, user, player = _make_game("en")
    game.status = "playing"
    _space(game, player, "set_game_mode")
    # No description spoken; space is reserved for game keybinds during play.
    assert user.get_spoken_messages() == []
