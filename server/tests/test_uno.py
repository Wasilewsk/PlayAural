from ..games.uno.game import UnoGame, UnoOptions
from ..games.uno import cards
from ..games.uno.cards import UnoCard
from ..users.bot import Bot
from ..users.test_user import MockUser


def _card(cid, color, ctype, value=None):
    return UnoCard(id=cid, color=color, type=ctype, value=value)


# ---------------------------------------------------------------------------
# Metadata / options
# ---------------------------------------------------------------------------


def test_uno_game_creation():
    game = UnoGame()
    assert game.get_name() == "UNO"
    assert game.get_name_key() == "game-name-uno"
    assert game.get_type() == "uno"
    assert game.get_category() == "cards"
    assert game.get_min_players() == 2
    assert game.get_max_players() == 10


def test_uno_options_defaults():
    game = UnoGame()
    assert game.options.winning_score == 100
    assert game.options.scoring_mode == "first_to_limit"
    assert game.options.bluff is True
    assert game.options.free_draws == 0
    assert game.options.interceptions is False


def test_uno_deck_composition():
    deck = cards.build_deck()
    assert len(deck) == 108
    assert sum(1 for c in deck if c.type == cards.WILD_CARD) == 4
    assert sum(1 for c in deck if c.type == cards.WILD_DRAW_FOUR) == 4
    # One zero per color, two of each 1-9 per color.
    zeros = [c for c in deck if c.type == cards.NUMBER and c.value == 0]
    assert len(zeros) == 4
    fives = [c for c in deck if c.type == cards.NUMBER and c.value == 5]
    assert len(fives) == 8
    # Card ids are unique.
    assert len({c.id for c in deck}) == 108


# ---------------------------------------------------------------------------
# Scoring display
# ---------------------------------------------------------------------------


def test_spectator_excluded_from_uno_scores_after_start():
    game = UnoGame(options=UnoOptions(winning_score=500))
    alice_user = MockUser("Alice", uuid="p1")
    bob_user = MockUser("Bob", uuid="p2")
    watcher_user = MockUser("Watcher", uuid="p3")

    alice = game.add_player("Alice", alice_user)
    bob = game.add_player("Bob", bob_user)
    watcher = game.add_player("Watcher", watcher_user)
    watcher.is_spectator = True

    game.on_start()
    alice.score = 12
    bob.score = 4
    game._sync_team_scores()

    alice_user.clear_messages()
    game._action_check_scores(alice, "check_scores")

    spoken = alice_user.get_spoken_messages()
    assert any("Alice: 12/500" in m for m in spoken)
    assert any("Bob: 4/500" in m for m in spoken)
    assert all("Watcher" not in m for m in spoken)


# ---------------------------------------------------------------------------
# Core mechanics (deterministic)
# ---------------------------------------------------------------------------


def _two_player_game():
    game = UnoGame()
    game.setup_keybinds()
    alice = MockUser("Alice", uuid="p1")
    bob = MockUser("Bob", uuid="p2")
    first = game.add_player("Alice", alice)
    second = game.add_player("Bob", bob)
    game.status = "playing"
    game.game_active = True
    return game, first, second


def test_playing_wild_locks_until_color_then_advances():
    game, first, second = _two_player_game()
    game.discard_pile = [_card(100, cards.RED, cards.NUMBER, 5)]
    game.current_color = cards.RED
    first.hand = [
        _card(1, cards.WILD, cards.WILD_CARD),
        _card(2, cards.BLUE, cards.NUMBER, 9),
    ]
    second.hand = [_card(3, cards.GREEN, cards.NUMBER, 7)]
    game.set_turn_players([first, second])
    game.rebuild_all_menus()

    game.execute_action(first, "play_card_1")
    assert game.awaiting_wild_color is True
    assert [c.id for c in first.hand] == [2]

    game.execute_action(first, "color_green")
    assert game.awaiting_wild_color is False
    assert game.current_color == cards.GREEN
    assert game.wild_wait_ticks == 15


def _three_player_game(options=None):
    game = UnoGame(options=options or UnoOptions())
    game.setup_keybinds()
    users = [MockUser(n, uuid=f"p{i}") for i, n in enumerate(["A", "B", "C"])]
    players = [game.add_player(n, users[i]) for i, n in enumerate(["A", "B", "C"])]
    game.status = "playing"
    game.game_active = True
    game.deck = cards.build_deck()
    game.discard_pile = [_card(100, cards.RED, cards.NUMBER, 5)]
    game.current_color = cards.RED
    game.set_turn_players(players)
    return game, players


def test_draw_two_keeps_turn_when_skip_after_draw_off():
    # Default rule: a forced draw-two makes the next player draw, but they keep
    # their turn unless skip-after-draw is enabled.
    game, (a, b, c) = _three_player_game()
    a.hand = [_card(1, cards.RED, cards.DRAW_TWO), _card(2, cards.BLUE, cards.NUMBER, 9)]
    b.hand = [_card(3, cards.GREEN, cards.NUMBER, 7)]
    c.hand = [_card(4, cards.YELLOW, cards.NUMBER, 3)]
    game.rebuild_all_menus()

    game.execute_action(a, "play_card_1")

    assert len(b.hand) == 3  # drew two
    assert game.current_player is b  # B keeps the turn (no skip)
    assert game.cards_to_draw == 0


def test_draw_two_skips_when_skip_after_draw_on():
    game, (a, b, c) = _three_player_game(UnoOptions(skip_after_draw=True))
    a.hand = [_card(1, cards.RED, cards.DRAW_TWO), _card(2, cards.BLUE, cards.NUMBER, 9)]
    b.hand = [_card(3, cards.GREEN, cards.NUMBER, 7)]
    c.hand = [_card(4, cards.YELLOW, cards.NUMBER, 3)]
    game.rebuild_all_menus()

    game.execute_action(a, "play_card_1")

    assert len(b.hand) == 3  # drew two
    assert game.current_player is c  # B skipped because skip-after-draw is on


def test_callout_forces_silent_player_to_draw_four():
    game, first, second = _two_player_game()
    game.deck = cards.build_deck()
    game.discard_pile = [_card(100, cards.RED, cards.NUMBER, 5)]
    game.current_color = cards.RED
    first.hand = [_card(1, cards.RED, cards.NUMBER, 1)]  # one card, silent
    first.said_uno = False
    first.uno_window_ticks = 10  # window open
    # second holds more than one card so its own UNO branch does not trigger.
    second.hand = [
        _card(2, cards.GREEN, cards.NUMBER, 7),
        _card(5, cards.GREEN, cards.NUMBER, 8),
    ]
    game.set_turn_players([first, second])
    game.rebuild_all_menus()

    game.execute_action(second, "uno")  # call out

    assert len(first.hand) == 5  # 1 + 4 penalty


def test_say_uno_protects_from_callout():
    game, first, second = _two_player_game()
    game.deck = cards.build_deck()
    game.discard_pile = [_card(100, cards.RED, cards.NUMBER, 5)]
    game.current_color = cards.RED
    first.hand = [_card(1, cards.RED, cards.NUMBER, 1)]
    first.uno_window_ticks = 10
    second.hand = [
        _card(2, cards.GREEN, cards.NUMBER, 7),
        _card(5, cards.GREEN, cards.NUMBER, 8),
    ]
    game.set_turn_players([first, second])
    game.rebuild_all_menus()

    game.execute_action(first, "uno")  # first announces UNO
    assert first.said_uno is True

    game.execute_action(second, "uno")  # call-out should now do nothing
    assert len(first.hand) == 1


# ---------------------------------------------------------------------------
# Full bot games (both scoring modes terminate)
# ---------------------------------------------------------------------------


def _run_bot_game(scoring_mode: str) -> UnoGame:
    options = UnoOptions(winning_score=30, scoring_mode=scoring_mode)
    game = UnoGame(options=options)
    for i in range(3):
        game.add_player(f"Bot{i}", Bot(f"Bot{i}"))
    game.on_start()
    for _ in range(80000):
        if game.status == "finished":
            break
        game.on_tick()
    return game


def test_bot_game_completes_first_to_limit():
    game = _run_bot_game("first_to_limit")
    assert game.status == "finished"


def test_bot_game_completes_elimination():
    game = _run_bot_game("elimination")
    assert game.status == "finished"


# ---------------------------------------------------------------------------
# Phase 2: house rules
# ---------------------------------------------------------------------------


def _n_player_game(names, options=None):
    game = UnoGame(options=options or UnoOptions())
    game.setup_keybinds()
    players = []
    for i, n in enumerate(names):
        players.append(game.add_player(n, MockUser(n, uuid=f"p{i}")))
    game.status = "playing"
    game.game_active = True
    game.deck = cards.build_deck()
    game.discard_pile = [_card(900, cards.RED, cards.NUMBER, 5)]
    game.current_color = cards.RED
    game.set_turn_players(players)
    return game, players


def test_draw_two_stacking_accumulates():
    game, (a, b, c) = _n_player_game(["A", "B", "C"], UnoOptions(responses=True, bluff=False))
    a.hand = [_card(1, cards.RED, cards.DRAW_TWO), _card(2, cards.BLUE, cards.NUMBER, 9)]
    b.hand = [_card(3, cards.RED, cards.DRAW_TWO), _card(5, cards.BLUE, cards.NUMBER, 8)]
    c.hand = [_card(4, cards.YELLOW, cards.NUMBER, 3)]
    game.rebuild_all_menus()

    game.execute_action(a, "play_card_1")  # obligation 2 -> B
    assert game.cards_to_draw == 2
    assert game.current_player is b

    game.execute_action(b, "play_card_3")  # stack -> obligation 4 -> C auto-draws 4
    assert len(c.hand) == 5  # 1 + 4
    assert game.cards_to_draw == 0


def test_draw_two_auto_accept_when_no_response():
    game, (a, b, c) = _n_player_game(["A", "B", "C"], UnoOptions(responses=True, bluff=False))
    a.hand = [_card(1, cards.RED, cards.DRAW_TWO), _card(2, cards.BLUE, cards.NUMBER, 9)]
    b.hand = [_card(3, cards.GREEN, cards.NUMBER, 7)]  # no response
    c.hand = [_card(4, cards.YELLOW, cards.NUMBER, 3)]
    game.rebuild_all_menus()

    game.execute_action(a, "play_card_1")
    assert len(b.hand) == 3  # auto-drew 2
    assert game.current_player is b  # keeps turn (skip-after-draw off)
    assert game.cards_to_draw == 0


def _advance_through_wild(game, ticks=25):
    for _ in range(ticks):
        if game.wild_wait_ticks == 0:
            break
        game.on_tick()


def test_bluff_challenge_catches_bluffer():
    game, (a, b) = _n_player_game(["A", "B"], UnoOptions(responses=False, bluff=True))
    # A holds a red card (matching current color) yet plays Wild Draw Four -> bluff.
    a.hand = [_card(1, cards.WILD, cards.WILD_DRAW_FOUR), _card(2, cards.RED, cards.NUMBER, 5)]
    b.hand = [_card(3, cards.GREEN, cards.NUMBER, 7), _card(6, cards.GREEN, cards.NUMBER, 8)]
    game.rebuild_all_menus()

    game.execute_action(a, "play_card_1")
    assert game.awaiting_wild_color is True
    assert game.is_bluff is True
    game.execute_action(a, "color_blue")
    _advance_through_wild(game)
    assert game.current_player is b
    assert game.bluff_challenge_available is True

    game.execute_action(b, "bluff_challenge")
    assert len(a.hand) == 1 + 6  # red 5 + (4 stack + 2 penalty)
    assert game.cards_to_draw == 0


def test_bluff_challenge_wrong_punishes_challenger():
    game, (a, b) = _n_player_game(["A", "B"], UnoOptions(responses=False, bluff=True))
    # A has no red card -> Wild Draw Four is legitimate.
    a.hand = [_card(1, cards.WILD, cards.WILD_DRAW_FOUR), _card(2, cards.BLUE, cards.NUMBER, 9)]
    b.hand = [_card(3, cards.GREEN, cards.NUMBER, 7), _card(6, cards.GREEN, cards.NUMBER, 8)]
    game.rebuild_all_menus()

    game.execute_action(a, "play_card_1")
    assert game.is_bluff is False
    game.execute_action(a, "color_blue")
    _advance_through_wild(game)

    game.execute_action(b, "bluff_challenge")
    assert len(b.hand) == 2 + 6  # original 2 + (4 stack + 2 penalty)
    assert game.cards_to_draw == 0


def test_bluffer_cannot_call_own_bluff():
    game, (a, b) = _n_player_game(["A", "B"], UnoOptions(responses=False, bluff=True))
    a.hand = [_card(1, cards.WILD, cards.WILD_DRAW_FOUR), _card(2, cards.RED, cards.NUMBER, 5)]
    b.hand = [_card(3, cards.GREEN, cards.NUMBER, 7), _card(6, cards.GREEN, cards.NUMBER, 8)]
    game.rebuild_all_menus()

    game.execute_action(a, "play_card_1")
    game.execute_action(a, "color_blue")
    # During the wild-wait window A is still current and bluff is available, but
    # A must never be offered "Call bluff" on their own Wild Draw Four.
    assert game.bluff_challenge_available is True
    assert game.current_player is a
    assert game._is_bluff_enabled(a) is not None

    _advance_through_wild(game)
    assert game.current_player is b
    assert game._is_bluff_enabled(b) is None  # B may call bluff


def test_zero_rotates_hands():
    game, (a, b, c) = _n_player_game(["A", "B", "C"], UnoOptions(zero_seven_rule=True))
    a.hand = [_card(1, cards.RED, cards.NUMBER, 0), _card(2, cards.BLUE, cards.NUMBER, 9)]
    b.hand = [_card(3, cards.GREEN, cards.NUMBER, 7)]
    c.hand = [_card(4, cards.YELLOW, cards.NUMBER, 3)]
    game.rebuild_all_menus()

    game.execute_action(a, "play_card_1")
    # Hands rotate by +1: A<-B, B<-C, C<-A(remaining blue 9).
    assert [card.id for card in c.hand] == [2]
    assert [card.id for card in a.hand] == [3]


def test_seven_swaps_with_chosen_player():
    game, (a, b) = _n_player_game(["A", "B"], UnoOptions(zero_seven_rule=True))
    a.hand = [_card(1, cards.RED, cards.NUMBER, 7), _card(2, cards.BLUE, cards.NUMBER, 9)]
    b.hand = [_card(3, cards.GREEN, cards.NUMBER, 3), _card(5, cards.GREEN, cards.NUMBER, 4)]
    game.rebuild_all_menus()

    game.execute_action(a, "play_card_1")
    assert game.awaiting_swap_target is True

    game.execute_action(a, f"swap_target_{b.id}")
    assert game.awaiting_swap_target is False
    assert sorted(card.id for card in a.hand) == [3, 5]
    assert [card.id for card in b.hand] == [2]


def test_stuck_turn_auto_resolves():
    # A player who has drawn, has nothing playable, and cannot draw must have
    # their turn ended by the engine (no pass action exists). Guards against the
    # deadlock where an out-of-turn play makes a just-drawn card unplayable.
    game, a, b = _two_player_game()
    game.discard_pile = [_card(900, cards.RED, cards.NUMBER, 5)]
    game.current_color = cards.RED
    a.hand = [_card(1, cards.BLUE, cards.NUMBER, 9)]  # not playable on red 5
    a.turn_has_drawn = True
    b.hand = [_card(3, cards.GREEN, cards.NUMBER, 7)]
    game.deck = []  # cannot draw
    game.set_turn_players([a, b])
    game.rebuild_all_menus()
    assert game.current_player is a

    game.on_tick()
    assert game.current_player is b  # stuck turn auto-resolved


def test_free_draw_allowed_with_playable_card():
    game, (a, b) = _n_player_game(["A", "B"], UnoOptions(free_draws=2))
    a.hand = [_card(1, cards.RED, cards.NUMBER, 5)]  # playable on red top
    b.hand = [_card(3, cards.GREEN, cards.NUMBER, 7)]
    game.rebuild_all_menus()

    game.execute_action(a, "draw")
    assert a.free_draws_used == 1
    assert len(a.hand) == 2
    assert game.current_player is a  # still A's turn


def test_draw_unplayable_card_auto_skips_turn():
    game, (a, b) = _n_player_game(["A", "B"])
    a.hand = [_card(1, cards.BLUE, cards.NUMBER, 9)]  # not playable on red 5 top
    game.deck = [_card(50, cards.GREEN, cards.NUMBER, 3)]  # drawn card also unplayable
    b.hand = [_card(3, cards.GREEN, cards.NUMBER, 7)]
    game.rebuild_all_menus()

    game.execute_action(a, "draw")
    assert len(a.hand) == 2  # drew the card
    assert game.current_player is b  # turn auto-skipped (no pass action)


def test_skip_after_draw_passes_turn():
    game, (a, b) = _n_player_game(["A", "B"], UnoOptions(skip_after_draw=True))
    a.hand = [_card(1, cards.BLUE, cards.NUMBER, 9)]  # not playable on red top
    b.hand = [_card(3, cards.GREEN, cards.NUMBER, 7)]
    game.rebuild_all_menus()

    game.execute_action(a, "draw")
    assert len(a.hand) == 2
    assert game.current_player is b  # turn skipped after drawing


# ---------------------------------------------------------------------------
# Phase 3: interceptions / straights
# ---------------------------------------------------------------------------


def test_interception_steals_play_and_turn():
    game, (a, b, c) = _n_player_game(["A", "B", "C"], UnoOptions(interceptions=True))
    a.hand = [_card(1, cards.RED, cards.NUMBER, 5), _card(2, cards.BLUE, cards.NUMBER, 9)]
    b.hand = [_card(3, cards.GREEN, cards.NUMBER, 7)]
    c.hand = [_card(4, cards.RED, cards.NUMBER, 5), _card(6, cards.YELLOW, cards.NUMBER, 1)]
    game.rebuild_all_menus()

    game.execute_action(a, "play_card_1")  # in-turn -> B
    assert game.current_player is b

    game.execute_action(c, "play_card_4")  # C intercepts exact red 5 out of turn
    assert game.top_card.id == 4
    assert all(card.id != 4 for card in c.hand)
    assert game.current_player is c  # the interceptor takes the floor


def test_draw_two_interception_plays_as_own_turn():
    # Action-card interceptions resolve as if played on the interceptor's turn:
    # the player to their left draws two and is skipped, then play advances.
    game, (a, b, c) = _n_player_game(["A", "B", "C"], UnoOptions(interceptions=True))
    game.discard_pile = [_card(900, cards.RED, cards.DRAW_TWO)]
    game.current_color = cards.RED
    a.hand = [_card(1, cards.BLUE, cards.NUMBER, 9)]
    b.hand = [_card(4, cards.RED, cards.DRAW_TWO), _card(5, cards.BLUE, cards.NUMBER, 8)]
    c.hand = [_card(6, cards.GREEN, cards.NUMBER, 7)]
    game.turn_index = 2  # C is the current player; B intercepts out of turn
    game.rebuild_all_menus()

    game.execute_action(b, "play_card_4")
    assert game.top_card.id == 4
    assert len(c.hand) == 3  # the player to B's left drew two
    assert game.current_player is c  # C keeps the turn (skip-after-draw off)


def test_skip_interception_plays_as_own_turn():
    game, (a, b, c) = _n_player_game(["A", "B", "C"], UnoOptions(interceptions=True))
    game.discard_pile = [_card(900, cards.RED, cards.SKIP)]
    game.current_color = cards.RED
    a.hand = [_card(1, cards.BLUE, cards.NUMBER, 9)]
    b.hand = [_card(4, cards.RED, cards.SKIP), _card(5, cards.BLUE, cards.NUMBER, 8)]
    c.hand = [_card(6, cards.GREEN, cards.NUMBER, 7)]
    game.turn_index = 2  # C current; B intercepts
    game.rebuild_all_menus()

    game.execute_action(b, "play_card_4")
    assert game.top_card.id == 4
    assert game.current_player is a  # C (to B's left) skipped, play moves on


def test_super_interception_ignores_color():
    game, (a, b, c) = _n_player_game(
        ["A", "B", "C"], UnoOptions(interceptions=False, super_interceptions=True)
    )
    a.hand = [_card(1, cards.RED, cards.NUMBER, 5), _card(2, cards.BLUE, cards.NUMBER, 9)]
    b.hand = [_card(3, cards.GREEN, cards.NUMBER, 7)]
    c.hand = [_card(4, cards.YELLOW, cards.NUMBER, 5), _card(6, cards.GREEN, cards.NUMBER, 1)]
    game.rebuild_all_menus()

    game.execute_action(a, "play_card_1")
    game.execute_action(c, "play_card_4")  # yellow 5 onto red 5 (any color)
    assert game.top_card.id == 4
    assert game.current_color == cards.YELLOW


def test_invalid_interception_penalizes():
    game, (a, b, c) = _n_player_game(["A", "B", "C"], UnoOptions(interceptions=True))
    a.hand = [_card(1, cards.RED, cards.NUMBER, 5), _card(2, cards.BLUE, cards.NUMBER, 9)]
    b.hand = [_card(3, cards.GREEN, cards.NUMBER, 7)]
    c.hand = [_card(4, cards.GREEN, cards.NUMBER, 7)]  # not an exact match
    game.rebuild_all_menus()

    game.execute_action(a, "play_card_1")
    game.execute_action(c, "play_card_4")  # invalid out-of-turn play
    assert c.penalty_points == 3
    assert len(c.hand) == 1  # card not played


def test_straight_continues_same_player_same_color():
    game, (a, b) = _n_player_game(["A", "B"], UnoOptions(straights=True))
    game.discard_pile = [_card(900, cards.RED, cards.NUMBER, 4)]
    game.current_color = cards.RED
    a.hand = [
        _card(1, cards.RED, cards.NUMBER, 5),
        _card(2, cards.RED, cards.NUMBER, 6),
        _card(7, cards.BLUE, cards.NUMBER, 9),
    ]
    b.hand = [_card(3, cards.GREEN, cards.NUMBER, 7)]
    game.rebuild_all_menus()

    game.execute_action(a, "play_card_1")  # in-turn red 5 -> B
    assert game.current_player is b

    game.execute_action(a, "play_card_2")  # A straights red 6 out of turn
    assert game.top_card.id == 2
    assert all(card.id != 2 for card in a.hand)
    assert game.current_player is b  # turn pointer unchanged
    assert game.straight_dir == 1


def test_bot_game_completes_with_interceptions_and_straights():
    options = UnoOptions(
        winning_score=30,
        interceptions=True,
        super_interceptions=True,
        straights=True,
    )
    game = UnoGame(options=options)
    for i in range(4):
        game.add_player(f"Bot{i}", Bot(f"Bot{i}"))
    game.on_start()
    for _ in range(120000):
        if game.status == "finished":
            break
        game.on_tick()
    assert game.status == "finished"
