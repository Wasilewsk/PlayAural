"""Tests for Age of Heroes action visibility."""

from pathlib import Path

from ..game_utils.actions import Visibility
from ..games.ageofheroes.cards import Card, CardType, ResourceType
from ..games.ageofheroes.game import AgeOfHeroesGame, ActionType, GamePhase, PlaySubPhase
from ..messages.localization import Localization
from ..users.test_user import MockUser


_locales_dir = Path(__file__).parent.parent / "locales"
Localization.init(_locales_dir)


def make_started_game(player_count: int = 3) -> AgeOfHeroesGame:
    game = AgeOfHeroesGame()
    game.setup_keybinds()
    for index in range(player_count):
        name = f"Player{index + 1}"
        game.add_player(name, MockUser(name, uuid=f"p{index + 1}"))
    game.host = "Player1"
    game.on_start()
    return game


def test_main_action_hidden_when_disabled() -> None:
    """A main action that is disabled for the player drops out of the menu.

    Construction with no affordable buildings used to linger as a disabled
    button; it should now be hidden, while a generally-available action such
    as tax collection stays visible.
    """
    game = make_started_game()
    player = game.get_active_players()[0]
    game.phase = GamePhase.PLAY
    game.sub_phase = PlaySubPhase.SELECT_ACTION
    game.set_turn_players([player])

    # A fresh player has no resources, so construction is unavailable.
    construction_id = f"action_{ActionType.CONSTRUCTION.value}"
    assert game._is_main_action_enabled(player, construction_id) == "ageofheroes-no-resources"
    assert game._is_main_action_hidden(player, construction_id) == Visibility.HIDDEN

    tax_id = f"action_{ActionType.TAX_COLLECTION.value}"
    assert game._is_main_action_enabled(player, tax_id) is None
    assert game._is_main_action_hidden(player, tax_id) == Visibility.VISIBLE


def test_build_action_hidden_when_unaffordable() -> None:
    """Unaffordable buildings are hidden from the construction menu."""
    game = make_started_game()
    player = game.get_active_players()[0]
    game.phase = GamePhase.PLAY
    game.sub_phase = PlaySubPhase.CONSTRUCTION
    game.set_turn_players([player])

    # Exactly the cost of an army (iron + grain + grain) and nothing else.
    player.hand = [
        Card(id=1, card_type=CardType.RESOURCE, subtype=ResourceType.IRON),
        Card(id=2, card_type=CardType.RESOURCE, subtype=ResourceType.GRAIN),
        Card(id=3, card_type=CardType.RESOURCE, subtype=ResourceType.GRAIN),
    ]

    assert game._is_build_enabled(player, "build_army") is None
    assert game._is_build_hidden(player, "build_army") == Visibility.VISIBLE

    # A fortress needs iron + wood + stone, which the player cannot cover.
    assert game._is_build_enabled(player, "build_fortress") == "ageofheroes-no-resources"
    assert game._is_build_hidden(player, "build_fortress") == Visibility.HIDDEN
