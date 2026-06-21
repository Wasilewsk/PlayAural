import json
from pathlib import Path
import re

from ..games.fivecarddraw.game import FiveCardDrawGame, FiveCardDrawOptions
from ..games.fivecarddraw.bot import _choose_discards
from ..game_utils.cards import Card
from ..messages.localization import Localization
from ..users.test_user import MockUser
from ..users.bot import Bot


LOCALES_DIR = Path(__file__).parent.parent / "locales"


def _touch_user(name: str) -> MockUser:
    user = MockUser(name)
    user.client_type = "web"
    return user


def _turn_menu_ids(user: MockUser) -> list[str]:
    return [
        item.id
        for item in user.menus["turn_menu"]["items"]
        if getattr(item, "id", None)
    ]


def test_draw_game_creation():
    game = FiveCardDrawGame()
    assert game.get_name() == "Five Card Draw"
    assert game.get_name_key() == "game-name-fivecarddraw"
    assert game.get_type() == "fivecarddraw"
    assert game.get_category() == "poker"
    assert game.get_min_players() == 2
    assert game.get_max_players() == 6


def test_draw_options_defaults():
    game = FiveCardDrawGame()
    assert game.options.starting_chips == 20000
    assert game.options.ante == 100
    assert game.options.raise_mode == "no_limit"
    assert game.options.draw_limit == "three_cards"
    assert game.relevant_preferences == []


def test_draw_rejects_ante_that_consumes_starting_stack():
    game = FiveCardDrawGame(options=FiveCardDrawOptions(starting_chips=100, ante=100))
    assert (
        "draw-error-ante-too-high",
        {"ante": 100, "chips": 100},
    ) in game.prestart_validate()


def test_draw_capped_raise_modes_require_a_nonzero_ante():
    for mode in ("pot_limit", "double_pot"):
        game = FiveCardDrawGame(options=FiveCardDrawOptions(ante=0, raise_mode=mode))
        assert (
            "draw-error-capped-mode-needs-ante",
            {"mode": mode},
        ) in game.prestart_validate()

    game = FiveCardDrawGame(options=FiveCardDrawOptions(ante=0, raise_mode="no_limit"))
    assert not any(
        error[0] == "draw-error-capped-mode-needs-ante"
        for error in game.prestart_validate()
        if isinstance(error, tuple)
    )


def test_draw_touch_info_actions_remain_available_outside_turn():
    game = FiveCardDrawGame()
    user1 = _touch_user("Alice")
    user2 = _touch_user("Bob")
    game.add_player("Alice", user1)
    game.add_player("Bob", user2)
    game.on_start()

    player = next(p for p in game.get_active_players() if p != game.current_player)
    visible_actions = {entry.action.id: entry for entry in game.get_all_visible_actions(player)}
    for action_id in ("call", "fold", "raise", "all_in"):
        assert action_id in visible_actions
        assert visible_actions[action_id].enabled is False
        assert visible_actions[action_id].disabled_reason == "action-not-your-turn"

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


def test_draw_clockwise_order_opener_and_final_draw_focus():
    game = FiveCardDrawGame()
    users = [_touch_user(name) for name in ("Alice", "Bob", "Carol")]
    for user in users:
        game.add_player(user.username, user)
    game.on_start()

    assert game.table_state.button_player_id == game.players[1].id
    assert game.current_player == game.players[2]
    assert game.phase == "bet1"

    game._action_call(game.players[2], "call")
    game._action_raise(game.players[0], "10", "raise")
    game._action_call(game.players[1], "call")
    game._action_call(game.players[2], "call")

    assert game.phase == "draw"
    assert game.current_player == game.players[2]
    assert game.first_round_opener_id == game.players[0].id

    users[2].clear_messages()
    users[0].clear_messages()
    game._action_draw_cards(game.players[2], "draw_cards")
    assert "You stand pat and keep all five cards." in users[2].get_spoken_messages()
    assert "Carol stands pat and keeps all five cards." in users[0].get_spoken_messages()

    game._action_draw_cards(game.players[0], "draw_cards")
    game._action_draw_cards(game.players[1], "draw_cards")
    game.flush_menus()

    assert game.phase == "bet2"
    assert game.current_player == game.players[0]
    assert users[1].menus["turn_menu"]["selection_id"] == "call"


def test_draw_action_returns_completed_player_to_main_anchors():
    game = FiveCardDrawGame()
    users = [_touch_user(name) for name in ("Alice", "Bob", "Carol")]
    for user in users:
        game.add_player(user.username, user)
    game.on_start()

    game._action_call(game.players[2], "call")
    game._action_raise(game.players[0], "10", "raise")
    game._action_call(game.players[1], "call")
    game._action_call(game.players[2], "call")
    assert game.phase == "draw"
    assert game.current_player == game.players[2]

    game._action_draw_cards(game.players[2], "draw_cards")
    game.flush_menus()

    completed_ids = _turn_menu_ids(users[2])
    assert completed_ids[:4] == ["call", "fold", "raise", "all_in"]
    assert "draw_cards" not in completed_ids
    assert "toggle_discard_1" not in completed_ids
    assert users[2].menus["turn_menu"]["selection_id"] == "call"

    current_drawer_ids = _turn_menu_ids(users[0])
    assert current_drawer_ids[:6] == [
        "toggle_discard_1",
        "toggle_discard_2",
        "toggle_discard_3",
        "toggle_discard_4",
        "toggle_discard_5",
        "draw_cards",
    ]
    assert "call" not in current_drawer_ids


def test_draw_between_hands_keeps_main_anchors_visible_without_focus_jump():
    game = FiveCardDrawGame()
    users = [_touch_user("Alice"), _touch_user("Bob")]
    for user in users:
        game.add_player(user.username, user)
    game.on_start()

    current = game.current_player
    assert current is not None
    game._action_fold(current, "fold")
    game.flush_menus()

    assert game._next_hand_wait_ticks > 0
    for user in users:
        ids = _turn_menu_ids(user)
        assert ids[:4] == ["call", "fold", "raise", "all_in"]
        assert "draw_cards" not in ids
        assert user.menus["turn_menu"]["selection_id"] is None


def test_draw_standard_limit_and_optional_four_card_ace_rule():
    hand = [
        Card(id=1, rank=1, suit=1),
        Card(id=2, rank=4, suit=2),
        Card(id=3, rank=7, suit=3),
        Card(id=4, rank=9, suit=4),
        Card(id=5, rank=12, suit=1),
    ]

    standard = FiveCardDrawGame()
    user = MockUser("Alice")
    standard.add_player("Alice", user)
    player = standard.players[0]
    player.hand = list(hand)
    for index in range(4):
        standard._set_discard(player, index, True)
    assert player.to_discard == {0, 1, 2}
    assert user.get_last_spoken() == (
        "You may exchange no more than 3 cards under the selected draw rule."
    )

    ace_rule = FiveCardDrawGame(
        options=FiveCardDrawOptions(draw_limit="four_with_ace")
    )
    ace_user = MockUser("Alice")
    ace_rule.add_player("Alice", ace_user)
    ace_player = ace_rule.players[0]
    ace_player.hand = list(hand)
    for index in range(1, 5):
        ace_rule._set_discard(ace_player, index, True)
    assert ace_player.to_discard == {1, 2, 3, 4}

    ace_player.to_discard = {0, 1, 2}
    ace_rule._set_discard(ace_player, 3, True)
    assert ace_player.to_discard == {0, 1, 2}
    assert ace_user.get_last_spoken() == (
        "Exchanging 4 cards requires you to keep at least one ace. "
        "Deselect an ace or exchange no more than 3 cards."
    )


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


def test_draw_rejects_all_in_and_oversized_raise_in_pot_limit():
    game = FiveCardDrawGame(
        options=FiveCardDrawOptions(starting_chips=1000, ante=100, raise_mode="pot_limit")
    )
    users = [MockUser("Alice"), MockUser("Bob")]
    for user in users:
        game.add_player(user.username, user)
    game.on_start()
    player = game.current_player
    assert player is not None
    user = game.get_user(player)
    assert user is not None
    chips_before = player.chips
    contribution_before = game.pot_manager.contributions[player.id]

    assert game._is_all_in_enabled(player) == "draw-all-in-unavailable-limit"
    game._action_all_in(player, "all_in")
    assert player.chips == chips_before
    assert game.pot_manager.contributions[player.id] == contribution_before
    assert "You cannot go all in" in user.get_last_spoken()

    game._action_raise(player, "201", "raise")
    assert player.chips == chips_before
    assert "largest raise available after calling is 200 chips" in user.get_last_spoken()

    game._action_raise(player, "200", "raise")
    assert player.chips == chips_before - 200
    assert game.betting is not None
    assert game.betting.current_bet == 200


def test_draw_reraise_announces_the_cumulative_bet():
    game = FiveCardDrawGame()
    users = [MockUser("Alice"), MockUser("Bob")]
    for user in users:
        game.add_player(user.username, user)
    game.on_start()

    game._action_raise(game.players[0], "10", "raise")
    game._action_raise(game.players[1], "10", "raise")
    users[0].clear_messages()
    users[1].clear_messages()
    game._action_raise(game.players[0], "10", "raise")

    assert "You raise to 30 chips." in users[0].get_spoken_messages()
    assert "Alice raises to 30 chips." in users[1].get_spoken_messages()
    assert game.betting is not None
    assert game.betting.current_bet == 30


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
    assert {p.id for p in players}.issubset(set(game.turn_player_ids))


def test_draw_new_hand_clears_busted_players_runtime_state():
    game = FiveCardDrawGame()
    for name in ("Alice", "Bob", "Carol"):
        game.add_player(name, MockUser(name))
    game.on_start()

    busted = game.players[0]
    busted.chips = 0
    busted.all_in = True
    busted.folded = False
    busted.to_discard = {0, 1}
    assert busted.hand

    game._start_new_hand()

    assert busted.hand == []
    assert busted.to_discard == set()
    assert busted.all_in is False
    assert busted.folded is True
    assert busted.id not in game._active_betting_ids()
    assert busted.id not in game.turn_player_ids


def test_draw_bot_protects_made_hands_and_draws_to_four_card_flushes():
    game = FiveCardDrawGame()
    player = game.create_player("bot", "Bot", is_bot=True)

    player.hand = [
        Card(id=1, rank=2, suit=3),
        Card(id=2, rank=5, suit=3),
        Card(id=3, rank=8, suit=3),
        Card(id=4, rank=13, suit=3),
        Card(id=5, rank=9, suit=4),
    ]
    assert _choose_discards(game, player) == {4}

    player.hand = [
        Card(id=6, rank=9, suit=1),
        Card(id=7, rank=10, suit=2),
        Card(id=8, rank=11, suit=3),
        Card(id=9, rank=12, suit=4),
        Card(id=10, rank=2, suit=1),
    ]
    assert _choose_discards(game, player) == {4}

    player.hand = [
        Card(id=11, rank=2, suit=1),
        Card(id=12, rank=3, suit=2),
        Card(id=13, rank=4, suit=3),
        Card(id=14, rank=5, suit=4),
        Card(id=15, rank=6, suit=1),
    ]
    assert _choose_discards(game, player) == set()


def test_draw_spectator_hears_public_bet_instead_of_personal_call_amount():
    game = FiveCardDrawGame()
    game.add_player("Alice", MockUser("Alice"))
    game.add_player("Bob", MockUser("Bob"))
    game.on_start()
    spectator_user = MockUser("Watcher")
    spectator = game.add_spectator("Watcher", spectator_user)
    assert game.betting is not None
    game.betting.current_bet = 25

    game._action_check_bet(spectator, "check_bet")

    assert spectator_user.get_last_spoken() == "The current table bet is 25 chips."


def test_draw_locale_key_and_variable_parity():
    en_text = (LOCALES_DIR / "en" / "fivecarddraw.ftl").read_text(encoding="utf-8")
    vi_text = (LOCALES_DIR / "vi" / "fivecarddraw.ftl").read_text(encoding="utf-8")

    def messages(text: str) -> dict[str, set[str]]:
        result: dict[str, set[str]] = {}
        current = ""
        for line in text.splitlines():
            match = re.match(r"^([a-z0-9-]+)\s*=", line)
            if match:
                current = match.group(1)
                result[current] = set()
            if current:
                result[current].update(re.findall(r"\{\s*\$([a-z0-9_]+)", line))
        return result

    assert messages(en_text) == messages(vi_text)
    assert Localization.get("vi", "game-name-fivecarddraw") == "Poker Rút năm lá"


def test_draw_vietnamese_manual_matches_localized_terminology():
    text = (
        Path(__file__).parent.parent
        / "documentation"
        / "content"
        / "vi"
        / "games"
        / "fivecarddraw.md"
    ).read_text(encoding="utf-8")
    for term in (
        "Poker Rút năm lá",
        "Cược góp",
        "Xem",
        "Theo",
        "Tố",
        "Tất tay",
        "Bỏ bài",
        "Giữ nguyên bài",
        "Giới hạn theo hũ",
    ):
        assert term in text

