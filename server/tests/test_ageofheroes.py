"""Tests for Age of Heroes action visibility."""

from pathlib import Path

from ..game_utils.actions import Visibility
from ..games.ageofheroes.cards import Card, CardType, ResourceType
from ..games.ageofheroes import game as ageofheroes_game_module
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


def test_ageofheroes_uses_coup_background_music() -> None:
    game = make_started_game()

    assert game.current_music == "game_coup/music.ogg"


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


def test_deny_road_request_returns_human_builder_to_construction() -> None:
    """Denying a road request must not crash the construction flow."""
    game = make_started_game()
    active_players = game.get_active_players()
    builder = active_players[0]
    target = active_players[1]
    assert not builder.is_bot

    game.phase = GamePhase.PLAY
    game.sub_phase = PlaySubPhase.ROAD_PERMISSION
    game.set_turn_players(active_players)
    builder.hand = [
        Card(id=101, card_type=CardType.RESOURCE, subtype=ResourceType.STONE),
        Card(id=102, card_type=CardType.RESOURCE, subtype=ResourceType.STONE),
    ]
    builder.pending_road_targets = [(1, "right")]
    game.road_request_from = 0
    game.road_request_to = 1

    game._action_deny_road(target, "deny_road")

    assert game.road_request_from == -1
    assert game.road_request_to == -1
    assert builder.pending_road_targets == []
    assert builder.declined_road_targets == [1]
    assert game.sub_phase == PlaySubPhase.CONSTRUCTION


def test_deny_road_request_resumes_bot_builder_construction(monkeypatch) -> None:
    """Bot road denials should route through the same safe handler path."""
    game = make_started_game()
    active_players = game.get_active_players()
    builder = active_players[0]
    target = active_players[1]
    builder.is_bot = True

    resumed: list[object] = []

    def fake_bot_perform_construction(game_arg, player_arg) -> None:
        resumed.append((game_arg, player_arg))

    monkeypatch.setattr(
        ageofheroes_game_module.bot_ai,
        "bot_perform_construction",
        fake_bot_perform_construction,
    )

    game.phase = GamePhase.PLAY
    game.sub_phase = PlaySubPhase.ROAD_PERMISSION
    game.set_turn_players(active_players)
    builder.hand = [
        Card(id=201, card_type=CardType.RESOURCE, subtype=ResourceType.STONE),
        Card(id=202, card_type=CardType.RESOURCE, subtype=ResourceType.STONE),
    ]
    builder.pending_road_targets = [(1, "right")]
    game.road_request_from = 0
    game.road_request_to = 1

    game._action_deny_road(target, "deny_road")

    assert game.road_request_from == -1
    assert game.road_request_to == -1
    assert builder.pending_road_targets == []
    assert builder.declined_road_targets == [1]
    assert resumed == [(game, builder)]


def _make_lobby_game(player_count: int = 3) -> AgeOfHeroesGame:
    """Build a game with players seated but still in the lobby (not started)."""
    game = AgeOfHeroesGame()
    game.setup_keybinds()
    for index in range(player_count):
        name = f"Player{index + 1}"
        game.add_player(name, MockUser(name, uuid=f"p{index + 1}"))
    game.host = "Player1"
    return game


def test_roll_dice_hidden_before_game_starts() -> None:
    """Roll Dice must not surface in the lobby.

    ``phase`` defaults to ``GamePhase.SETUP`` while the table is still waiting,
    so without a status guard the Roll Dice button leaked into the lobby for
    touch clients before the game had started.
    """
    game = _make_lobby_game()
    player = game.players[0]

    # Sanity: the conditions that used to make this VISIBLE all hold.
    assert game.status != "playing"
    assert game.phase == GamePhase.SETUP
    assert player.id not in game.setup_rolls

    assert game._is_roll_dice_hidden(player) == Visibility.HIDDEN


def test_roll_dice_visible_in_setup_for_unrolled_player() -> None:
    """Once the game starts, a seated player who hasn't rolled sees Roll Dice."""
    game = make_started_game()
    player = game.get_active_players()[0]

    assert game.status == "playing"
    assert game.phase == GamePhase.SETUP
    assert player.id not in game.setup_rolls

    assert game._is_roll_dice_hidden(player) == Visibility.VISIBLE


def test_roll_dice_hidden_after_player_rolled() -> None:
    """Roll Dice disappears for a player who has already rolled in setup."""
    game = make_started_game()
    player = game.get_active_players()[0]
    game.setup_rolls[player.id] = 9

    assert game._is_roll_dice_hidden(player) == Visibility.HIDDEN


def test_roll_dice_hidden_for_spectator() -> None:
    """Spectators never see the gameplay-mutating Roll Dice button."""
    game = make_started_game()
    player = game.get_active_players()[0]
    player.is_spectator = True

    assert game._is_roll_dice_hidden(player) == Visibility.HIDDEN
