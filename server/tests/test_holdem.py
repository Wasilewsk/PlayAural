import json
from pathlib import Path
import re

from ..games.holdem.game import HoldemGame, HoldemOptions
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


def test_holdem_game_creation():
    game = HoldemGame()
    assert game.get_name() == "Texas Hold'em"
    assert game.get_name_key() == "game-name-holdem"
    assert game.get_type() == "holdem"
    assert game.get_category() == "poker"
    assert game.get_min_players() == 2
    assert game.get_max_players() == 10


def test_holdem_options_defaults():
    game = HoldemGame()
    assert game.options.starting_chips == 20000
    assert game.options.big_blind == 200
    assert game.options.ante == 0
    assert game.relevant_preferences == []


def test_holdem_rejects_forced_bets_that_consume_starting_stack():
    big_blind_game = HoldemGame(options=HoldemOptions(starting_chips=100, big_blind=100))
    assert (
        "holdem-error-big-blind-too-high",
        {"blind": 100, "chips": 100},
    ) in big_blind_game.prestart_validate()

    forced_bet_game = HoldemGame(
        options=HoldemOptions(starting_chips=100, big_blind=80, ante=20, ante_start_level=0)
    )
    assert (
        "holdem-error-forced-bets-too-high",
        {"ante": 20, "blind": 80, "chips": 100},
    ) in forced_bet_game.prestart_validate()


def test_holdem_touch_info_actions_remain_available_outside_turn():
    game = HoldemGame()
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
    assert turn_set.get_action("speak_table") is None
    assert turn_set.get_action("check_button") is None

    standard_set = game.create_standard_action_set(player)
    expected_order = [
        "speak_hand",
        "speak_table",
        "speak_hand_value",
        "check_pot",
        "check_bet",
        "check_min_raise",
        "check_hand_players",
        "check_button",
        "check_position",
        "check_turn_timer",
        "check_blind_timer",
        "reveal_both",
        "reveal_first",
        "reveal_second",
        "check_scores",
        "whose_turn",
        "whos_at_table",
    ]
    assert standard_set._order[-len(expected_order):] == expected_order
    for action_id in expected_order:
        action = standard_set.get_action(action_id)
        assert action is not None
        resolved = standard_set.resolve_action(game, player, action)
        if action_id.startswith("reveal_"):
            assert resolved.enabled is False
        else:
            assert resolved.enabled
        assert resolved.visible or action_id.startswith("reveal_")


def test_holdem_between_hands_keeps_main_anchors_visible_without_focus_jump():
    game = HoldemGame()
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
        assert user.menus["turn_menu"]["selection_id"] is None


def test_holdem_eliminated_players_do_not_get_gameplay_menus_after_showdown():
    game = HoldemGame()
    users = [_touch_user("Alice"), _touch_user("Bob"), _touch_user("Carol")]
    for user in users:
        game.add_player(user.username, user)
    game.on_start()

    busted = game.players[0]
    busted.chips = 0
    busted.all_in = True
    busted.folded = False
    assert busted.hand

    game.phase = "showdown"
    game._queue_new_hand()
    game.flush_menus()

    ids = _turn_menu_ids(users[0])
    for action_id in (
        "call",
        "fold",
        "raise",
        "all_in",
        "speak_hand",
        "speak_hand_value",
        "reveal_both",
        "reveal_first",
        "reveal_second",
    ):
        assert action_id not in ids
    assert "check_pot" in ids


def test_holdem_eliminated_players_do_not_get_gameplay_menus_next_hand():
    game = HoldemGame()
    users = [_touch_user("Alice"), _touch_user("Bob"), _touch_user("Carol")]
    for user in users:
        game.add_player(user.username, user)
    game.on_start()

    busted = game.players[0]
    busted.chips = 0
    busted.all_in = True
    busted.folded = False
    assert busted.hand

    game._start_new_hand()
    game.flush_menus()

    ids = _turn_menu_ids(users[0])
    assert "call" not in ids
    assert "fold" not in ids
    assert "raise" not in ids
    assert "all_in" not in ids
    assert "speak_hand" not in ids
    assert "speak_hand_value" not in ids
    assert "check_pot" in ids
    assert busted.hand == []
    assert busted.folded is True
    assert busted.all_in is False


def test_holdem_serialization_round_trip():
    game = HoldemGame()
    user1 = MockUser("Alice")
    user2 = MockUser("Bob")
    game.add_player("Alice", user1)
    game.add_player("Bob", user2)
    game.on_start()
    json_str = game.to_json()
    data = json.loads(json_str)
    assert data["hand_number"] >= 1
    loaded = HoldemGame.from_json(json_str)
    assert loaded.hand_number == game.hand_number


def test_holdem_bot_game_completes():
    options = HoldemOptions(starting_chips=200, big_blind=200, ante=0)
    game = HoldemGame(options=options)
    for i in range(2):
        bot = Bot(f"Bot{i}")
        game.add_player(f"Bot{i}", bot)
    game.on_start()
    for _ in range(20000):
        if game.status == "finished":
            break
        game.on_tick()
    assert game.status == "finished"


def test_holdem_raise_too_large_rejected():
    game = HoldemGame()
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
    assert len(spoken_messages_after) > spoken_messages_before


def test_holdem_short_stack_raise_all_in():
    game = HoldemGame()
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


def test_holdem_short_all_in_does_not_reopen_betting():
    game = HoldemGame()
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


def test_holdem_underfunded_raise_goes_all_in():
    game = HoldemGame()
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


def test_holdem_pot_limit_raise_cap():
    options = HoldemOptions(starting_chips=1000, big_blind=100, raise_mode="pot_limit")
    game = HoldemGame(options=options)
    user1 = MockUser("Alice")
    user2 = MockUser("Bob")
    game.add_player("Alice", user1)
    game.add_player("Bob", user2)
    game.on_start()
    player = game.current_player
    assert player is not None
    user = game.get_user(player)
    assert user is not None
    chips_before = player.chips
    contribution_before = game.pot_manager.contributions[player.id]

    assert game._is_all_in_enabled(player) == "holdem-all-in-unavailable-limit"
    game._action_all_in(player, "all_in")
    assert player.chips == chips_before
    assert game.pot_manager.contributions[player.id] == contribution_before
    assert "You cannot go all in" in user.get_last_spoken()

    game._action_raise(player, "201", "raise")
    assert player.chips == chips_before
    assert "largest raise available after calling is 200 chips" in user.get_last_spoken()

    game._action_raise(player, "200", "raise")
    assert player.chips == chips_before - 250
    assert game.betting is not None
    assert game.betting.current_bet == 300


def test_holdem_reraise_announces_the_cumulative_bet():
    game = HoldemGame(options=HoldemOptions(big_blind=20))
    users = [MockUser("Alice"), MockUser("Bob")]
    for user in users:
        game.add_player(user.username, user)
    game.on_start()

    first = game.current_player
    assert first is not None
    second = next(p for p in game.players if p != first)
    first_user = game.get_user(first)
    second_user = game.get_user(second)
    assert first_user is not None and second_user is not None

    game._action_raise(first, "20", "raise")
    game._action_raise(second, "20", "raise")
    first_user.clear_messages()
    second_user.clear_messages()
    game._action_raise(first, "20", "raise")

    assert "You raise to 80 chips." in first_user.get_spoken_messages()
    assert f"{first.name} raises to 80 chips." in second_user.get_spoken_messages()
    assert game.betting is not None
    assert game.betting.current_bet == 80


def test_holdem_new_hand_clears_busted_players_runtime_state():
    game = HoldemGame()
    for name in ("Alice", "Bob", "Carol"):
        game.add_player(name, MockUser(name))
    game.on_start()

    busted = game.players[0]
    busted.chips = 0
    busted.all_in = True
    busted.folded = False
    assert busted.hand

    game._start_new_hand()

    assert busted.hand == []
    assert busted.all_in is False
    assert busted.folded is True
    assert busted.id not in game._active_betting_ids()
    assert busted.id not in game.turn_player_ids


def test_holdem_spectator_hears_public_bet_instead_of_personal_call_amount():
    game = HoldemGame()
    game.add_player("Alice", MockUser("Alice"))
    game.add_player("Bob", MockUser("Bob"))
    game.on_start()
    spectator_user = MockUser("Watcher")
    spectator = game.add_spectator("Watcher", spectator_user)
    assert game.betting is not None
    game.betting.current_bet = 25

    game._action_check_bet(spectator, "check_bet")

    assert spectator_user.get_last_spoken() == "The current table bet is 25 chips."


def test_holdem_reveal_actions_only_show_for_live_showdown_hands():
    game = HoldemGame()
    users = [_touch_user("Alice"), _touch_user("Bob"), _touch_user("Carol")]
    for user in users:
        game.add_player(user.username, user)
    game.on_start()
    live = game.players[0]
    folded = game.players[1]
    busted = game.players[2]
    folded.folded = True
    busted.hand = []
    busted.folded = True
    game.phase = "showdown"

    live_actions = {entry.action.id for entry in game.get_all_visible_actions(live)}
    folded_actions = {entry.action.id for entry in game.get_all_visible_actions(folded)}
    busted_actions = {entry.action.id for entry in game.get_all_visible_actions(busted)}

    assert {"reveal_both", "reveal_first", "reveal_second"}.issubset(live_actions)
    assert "reveal_both" not in folded_actions
    assert "reveal_both" not in busted_actions


def test_holdem_locale_key_and_variable_parity():
    en_text = (LOCALES_DIR / "en" / "holdem.ftl").read_text(encoding="utf-8")
    vi_text = (LOCALES_DIR / "vi" / "holdem.ftl").read_text(encoding="utf-8")

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
    assert Localization.get("vi", "game-name-holdem") == "Poker Texas Hold'em"


def test_holdem_vietnamese_manual_matches_localized_terminology():
    text = (
        Path(__file__).parent.parent
        / "documentation"
        / "content"
        / "vi"
        / "games"
        / "holdem.md"
    ).read_text(encoding="utf-8")
    for term in (
        "Poker Texas Hold'em",
        "Mù nhỏ",
        "Mù lớn",
        "Cược góp",
        "Xem",
        "Theo",
        "Tố",
        "Tất tay",
        "Ngửa bài",
        "Giới hạn theo hũ",
    ):
        assert term in text

