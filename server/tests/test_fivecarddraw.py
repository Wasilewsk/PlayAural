import json

from ..games.fivecarddraw.game import FiveCardDrawGame, FiveCardDrawOptions
from ..users.test_user import MockUser
from ..users.bot import Bot


def _touch_user(name: str) -> MockUser:
    user = MockUser(name)
    user.client_type = "web"
    return user


def test_draw_game_creation():
    game = FiveCardDrawGame()
    assert game.get_name() == "Five Card Draw"
    assert game.get_name_key() == "game-name-fivecarddraw"
    assert game.get_type() == "fivecarddraw"
    assert game.get_category() == "poker"
    assert game.get_min_players() == 2
    assert game.get_max_players() == 5


def test_draw_options_defaults():
    game = FiveCardDrawGame()
    assert game.options.starting_chips == 20000
    assert game.options.ante == 100
    assert game.options.raise_mode == "no_limit"


def test_draw_rejects_ante_that_consumes_starting_stack():
    game = FiveCardDrawGame(options=FiveCardDrawOptions(starting_chips=100, ante=100))
    assert (
        "draw-error-ante-too-high",
        {"ante": 100, "chips": 100},
    ) in game.prestart_validate()


def test_draw_touch_info_actions_remain_available_outside_turn():
    game = FiveCardDrawGame()
    user1 = _touch_user("Alice")
    user2 = _touch_user("Bob")
    game.add_player("Alice", user1)
    game.add_player("Bob", user2)
    game.on_start()

    player = next(p for p in game.get_active_players() if p != game.current_player)
    turn_set = game.create_turn_action_set(player)
    assert turn_set.get_action("speak_hand") is None
    assert turn_set.get_action("check_dealer") is None

    standard_set = game.create_standard_action_set(player)
    expected_order = [
        "speak_hand",
        "speak_hand_value",
        "check_pot",
        "check_bet",
        "check_min_raise",
        "check_hand_players",
        "check_dealer",
        "check_position",
        "check_turn_timer",
        "check_scores",
        "whose_turn",
        "whos_at_table",
    ]
    assert standard_set._order[-len(expected_order):] == expected_order
    for action_id in expected_order:
        action = standard_set.get_action(action_id)
        assert action is not None
        resolved = standard_set.resolve_action(game, player, action)
        assert resolved.visible
        assert resolved.enabled


def test_draw_serialization_round_trip():
    game = FiveCardDrawGame()
    user1 = MockUser("Alice")
    user2 = MockUser("Bob")
    game.add_player("Alice", user1)
    game.add_player("Bob", user2)
    game.on_start()
    json_str = game.to_json()
    data = json.loads(json_str)
    assert data["hand_number"] >= 1
    loaded = FiveCardDrawGame.from_json(json_str)
    assert loaded.hand_number == game.hand_number


def test_draw_bot_game_completes():
    options = FiveCardDrawOptions(starting_chips=200, ante=100)
    game = FiveCardDrawGame(options=options)
    for i in range(2):
        bot = Bot(f"Bot{i}")
        game.add_player(f"Bot{i}", bot)
    game.on_start()
    for _ in range(40000):
        if game.status == "finished":
            break
        game.on_tick()
    if game.status != "finished":
        current = game.current_player.name if game.current_player else None
        betting = game.betting
        active_ids = game._active_betting_ids() if hasattr(game, "_active_betting_ids") else set()
        all_in_ids = game._all_in_ids() if hasattr(game, "_all_in_ids") else set()
        raise AssertionError(
            "Game did not finish. "
            f"status={game.status}, phase={getattr(game, 'phase', None)}, "
            f"hand={getattr(game, 'hand_number', None)}, "
            f"current={current}, "
            f"active={len(active_ids)}, all_in={len(all_in_ids)}, "
            f"betting_current={getattr(betting, 'current_bet', None)}, "
            f"betting_acted={len(getattr(betting, 'acted_since_raise', [])) if betting else None}, "
            f"bets={getattr(betting, 'bets', None)}"
        )


def test_draw_raise_too_large_rejected():
    game = FiveCardDrawGame()
    user1 = MockUser("Alice")
    user2 = MockUser("Bob")
    game.add_player("Alice", user1)
    game.add_player("Bob", user2)
    game.on_start()
    player = game.current_player
    assert player is not None
    player.chips = 5
    pot_before = game.pot_manager.total_pot()
    bet_before = game.betting.bets.get(player.id, 0) if game.betting else 0

    # Track messages spoken to the user to verify private error routing
    user = game.get_user(player)
    spoken_messages_before = len(user.get_spoken_messages())

    game._action_raise(player, "10", "raise")
    assert game.pot_manager.total_pot() == pot_before
    assert game.betting.bets.get(player.id, 0) == bet_before

    # Ensure it didn't crash and the error message was sent privately
    spoken_messages_after = user.get_spoken_messages()
    # The message is translated, so we can't just check for "poker-raise-too-large".
    # Since MockUser just records the text passed to `speak`, and `speak_l` calls `speak` with the translated text.
    # We just need to verify a new message was spoken.
    assert len(spoken_messages_after) > spoken_messages_before


def test_draw_short_stack_raise_all_in():
    game = FiveCardDrawGame()
    user1 = MockUser("Alice")
    user2 = MockUser("Bob")
    game.add_player("Alice", user1)
    game.add_player("Bob", user2)
    game.on_start()
    player = game.current_player
    assert player is not None
    player.chips = 5
    if game.betting:
        game.betting.current_bet = 10
        game.betting.bets[player.id] = 0
    pot_before = game.pot_manager.total_pot()
    game._action_raise(player, "5", "raise")
    assert game.pot_manager.total_pot() == pot_before + 5
    if game.betting:
        assert game.betting.current_bet == 10


def test_draw_short_all_in_does_not_reopen_betting():
    game = FiveCardDrawGame()
    user1 = MockUser("Alice")
    user2 = MockUser("Bob")
    game.add_player("Alice", user1)
    game.add_player("Bob", user2)
    game.on_start()
    player = game.current_player
    assert player is not None
    player.chips = 15
    if game.betting:
        game.betting.current_bet = 10
        game.betting.last_raise_size = 10
        game.betting.bets[player.id] = 0
        game.betting.acted_since_raise = set()
    game._action_all_in(player, "all_in")
    if game.betting:
        assert game.betting.current_bet == 10
        assert game.betting.acted_since_raise == {player.id}


def test_draw_underfunded_raise_goes_all_in():
    game = FiveCardDrawGame()
    user1 = MockUser("Alice")
    user2 = MockUser("Bob")
    game.add_player("Alice", user1)
    game.add_player("Bob", user2)
    game.on_start()
    player = game.current_player
    assert player is not None
    player.chips = 100
    if game.betting:
        game.betting.current_bet = 90
        game.betting.last_raise_size = 20
        game.betting.bets[player.id] = 0
        game.betting.acted_since_raise = set()
    pot_before = game.pot_manager.total_pot()
    game._action_raise(player, "20", "raise")
    assert game.pot_manager.total_pot() == pot_before + 100
    assert player.all_in is True
    if game.betting:
        assert game.betting.current_bet == 90


def test_draw_all_in_still_draws():
    options = FiveCardDrawOptions(starting_chips=200, ante=100)
    game = FiveCardDrawGame(options=options)
    user1 = MockUser("Alice")
    user2 = MockUser("Bob")
    game.add_player("Alice", user1)
    game.add_player("Bob", user2)
    game.on_start()
    players = game.get_active_players()
    assert len(players) == 2
    for p in players:
        p.chips = 0
        p.all_in = True
    if game.betting:
        game.betting.current_bet = 100
        game.betting.last_raise_size = 100
        for p in players:
            game.betting.bets[p.id] = 100
        game.betting.acted_since_raise = {p.id for p in players}
    game.current_bet_round = 1
    game._after_action()
    assert game.phase == "draw"

