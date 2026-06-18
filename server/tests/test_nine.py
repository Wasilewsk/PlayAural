"""Tests for Nine turn flow polish."""

from pathlib import Path

from ..game_utils.cards import Card, SUIT_CLUBS, SUIT_DIAMONDS
from ..games.nine.game import NineGame, RANK_EIGHT, RANK_NINE, RANK_SIX
from ..games.nine.state import SequenceState
from ..messages.localization import Localization
from ..users.test_user import MockUser


_locales_dir = Path(__file__).parent.parent / "locales"
Localization.init(_locales_dir)


def test_invalid_player_count_returns_localizable_error_key() -> None:
    game = NineGame()
    for index in range(5):
        name = f"Player{index + 1}"
        game.add_player(name, MockUser(name, uuid=f"nine-player-{index + 1}"))

    assert "nine-error-invalid-player-count" in game.validate_start()


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
