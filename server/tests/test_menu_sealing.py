"""Tests for the sealed menu orchestrators and the record/flush contract.

The menu orchestrators in MenuManagementMixin are sealed: a game subclass
that overrides one must fail loudly at class-creation (i.e. import) time
with a message that names the offender and points at the sanctioned hooks.

These tests also pin the recording contract: game code records intent with
``refresh_menus()`` / ``request_menu_focus()`` and nothing is built or sent
until the framework flush (``flush_menus()``, called at the end of every
``handle_event`` and once per server tick). Focus intents are one-shot,
per-player, last-writer-wins.
"""

from pathlib import Path

import pytest

from ..game_utils.menu_management_mixin import SEALED_MENU_ORCHESTRATORS
from ..game_utils.action_context import ActionContext
from ..users.base import MenuItem
from ..users.network_user import NetworkUser
from ..games.pig.game import PigGame
from ..messages.localization import Localization
from ..users.test_user import MockUser

_locales_dir = Path(__file__).parent.parent / "locales"
Localization.init(_locales_dir)


def make_game(player_count: int = 2) -> PigGame:
    game = PigGame()
    game.setup_keybinds()
    for index in range(player_count):
        user = MockUser(f"Player{index + 1}", uuid=f"p{index + 1}")
        game.add_player(f"Player{index + 1}", user)
    game.host = "Player1"
    return game


def turn_menu_messages(user: MockUser) -> list:
    return [
        m
        for m in user.messages
        if m.type == "show_menu" and m.data.get("menu_id") == "turn_menu"
    ]


def status_box_messages(user: MockUser) -> list:
    return [
        m
        for m in user.messages
        if m.type == "show_menu" and m.data.get("menu_id") == "status_box"
    ]


def actions_menu_messages(user: MockUser) -> list:
    return [
        m
        for m in user.messages
        if m.type == "show_menu" and m.data.get("menu_id") == "actions_menu"
    ]


class TestSealedOrchestrators:
    @pytest.mark.parametrize("name", SEALED_MENU_ORCHESTRATORS)
    def test_override_raises_at_class_creation(self, name: str) -> None:
        with pytest.raises(TypeError) as excinfo:
            type("BadGame", (PigGame,), {name: lambda self, *a, **k: None})
        message = str(excinfo.value)
        assert "BadGame" in message
        assert name in message
        assert "sealed menu orchestrator" in message
        # The error must guide toward the fix, not just forbid.
        assert "before_menu_build" in message
        assert "build_menu_items" in message

    def test_hook_overrides_are_allowed(self) -> None:
        cls = type(
            "GoodGame",
            (PigGame,),
            {
                "before_menu_build": lambda self, player: None,
                "build_menu_items": lambda self, player, user: None,
            },
        )
        assert issubclass(cls, PigGame)

    def test_old_orchestrator_names_are_gone(self) -> None:
        # The phase-1 names were deleted, not aliased: a game calling them
        # must fail loudly, not silently repaint with stale semantics.
        game = make_game()
        for name in (
            "rebuild_player_menu",
            "update_player_menu",
            "rebuild_all_menus",
            "update_all_menus",
            "defer_next_rebuild_to_update",
        ):
            assert not hasattr(game, name)


class TestRecordAndFlush:
    def test_refresh_records_without_painting(self) -> None:
        game = make_game()
        user1 = game.get_user(game.players[0])

        game.refresh_menus()
        assert turn_menu_messages(user1) == []

        game.flush_menus()
        assert len(turn_menu_messages(user1)) == 1

    def test_flush_without_refresh_paints_nothing(self) -> None:
        game = make_game()
        user1 = game.get_user(game.players[0])

        game.flush_menus()
        assert turn_menu_messages(user1) == []

    def test_per_player_refresh_scopes_the_paint(self) -> None:
        game = make_game()
        p1, p2 = game.players
        user1 = game.get_user(p1)
        user2 = game.get_user(p2)

        game.refresh_menus(p1)
        game.flush_menus()
        assert len(turn_menu_messages(user1)) == 1
        assert turn_menu_messages(user2) == []

    def test_flush_is_consumed(self) -> None:
        game = make_game()
        user1 = game.get_user(game.players[0])

        game.refresh_menus()
        game.flush_menus()
        game.flush_menus()
        assert len(turn_menu_messages(user1)) == 1

    def test_paint_always_uses_show_form(self) -> None:
        game = make_game()
        user1 = game.get_user(game.players[0])

        game.refresh_menus()
        game.flush_menus()
        game.refresh_menus()
        game.flush_menus()
        types = {m.type for m in user1.messages if m.data.get("menu_id") == "turn_menu"}
        assert types == {"show_menu"}

    def test_destroyed_game_flush_paints_nothing_and_clears(self) -> None:
        game = make_game()
        user1 = game.get_user(game.players[0])

        game.refresh_menus()
        game._destroyed = True
        game.flush_menus()
        assert turn_menu_messages(user1) == []
        assert not game._menu_dirty_all
        assert not game._menu_dirty

    def test_handle_event_flushes_synchronously(self) -> None:
        game = make_game()
        p1 = game.players[0]
        user1 = game.get_user(p1)

        # An executed action must leave the repainted menu visible without
        # any explicit flush: handle_event owns the flush.
        game.handle_event(
            p1,
            {"type": "menu", "menu_id": "turn_menu", "selection_id": "whos_at_table"},
        )
        assert len(turn_menu_messages(user1)) >= 1


class TestPersistentStartAction:
    def test_start_stays_visible_before_minimum_players_join(self) -> None:
        game = make_game(player_count=1)
        host = game.players[0]

        visible = {
            resolved.action.id: resolved
            for resolved in game.get_all_visible_actions(host)
        }

        assert "start_game" in visible
        assert visible["start_game"].enabled is True

    def test_non_host_sees_start_but_cannot_use_it(self) -> None:
        game = make_game()
        guest = game.players[1]

        visible = {
            resolved.action.id: resolved
            for resolved in game.get_all_visible_actions(guest)
        }

        assert "start_game" in visible
        assert visible["start_game"].disabled_reason == "action-not-host"

    def test_failed_start_reports_context_without_forcing_focus(self) -> None:
        game = make_game(player_count=1)
        host = game.players[0]
        user = game.get_user(host)
        assert isinstance(user, MockUser)

        game.refresh_menus()
        game.flush_menus()
        user.clear_messages()

        game.handle_event(
            host,
            {
                "type": "menu",
                "menu_id": "turn_menu",
                "selection_id": "start_game",
            },
        )

        assert game.status == "waiting"
        assert (
            "Cannot start. Active players: 1. Minimum required: 2."
            in user.get_spoken_messages()
        )
        assert turn_menu_messages(user)[-1].data["selection_id"] is None

    def test_failed_start_sends_no_redundant_network_menu_packet(self) -> None:
        game = PigGame()
        game.setup_keybinds()
        user = NetworkUser("Player1", "en", connection=None)
        host = game.add_player("Player1", user)
        game.host = host.name

        game.refresh_menus()
        game.flush_menus()
        user.get_queued_messages()

        game.handle_event(
            host,
            {
                "type": "menu",
                "menu_id": "turn_menu",
                "selection_id": "start_game",
            },
        )

        packets = user.get_queued_messages()
        assert any(packet.get("type") == "speak" for packet in packets)
        assert not any(packet.get("type") == "menu" for packet in packets)

    def test_validate_start_combines_count_and_game_errors(self) -> None:
        game = make_game(player_count=1)
        game.options.team_mode = "2v2"

        assert game.validate_start() == [
            (
                "action-start-needs-more-players",
                {"current": 1, "minimum": 2},
            ),
            "game-error-invalid-team-mode",
        ]


class TestFocusIntent:
    def test_request_menu_focus_lands_once_and_only_for_target(self) -> None:
        game = make_game()
        p1, p2 = game.players
        user1 = game.get_user(p1)
        user2 = game.get_user(p2)

        game.request_menu_focus(p1, "some_item")
        game.refresh_menus()
        game.flush_menus()
        assert turn_menu_messages(user1)[-1].data["selection_id"] == "some_item"
        assert turn_menu_messages(user2)[-1].data["selection_id"] is None

        # Consumed: the next flush must not jump the cursor again.
        game.refresh_menus()
        game.flush_menus()
        assert turn_menu_messages(user1)[-1].data["selection_id"] is None

    def test_request_menu_focus_marks_player_dirty(self) -> None:
        game = make_game()
        p1, p2 = game.players
        user1 = game.get_user(p1)
        user2 = game.get_user(p2)

        # No separate refresh_menus call: requesting focus implies repaint.
        game.request_menu_focus(p1, "some_item")
        game.flush_menus()
        assert turn_menu_messages(user1)[-1].data["selection_id"] == "some_item"
        assert turn_menu_messages(user2) == []

    def test_last_focus_writer_wins(self) -> None:
        game = make_game()
        p1 = game.players[0]
        user1 = game.get_user(p1)

        game.request_menu_focus(p1, "stale_item")
        game.request_menu_focus(p1, "fresh_item")
        game.flush_menus()
        assert turn_menu_messages(user1)[-1].data["selection_id"] == "fresh_item"

        # The superseded intent is discarded, not deferred to fire stale.
        game.refresh_menus()
        game.flush_menus()
        assert turn_menu_messages(user1)[-1].data["selection_id"] is None


class TestStatusBoxes:
    def test_static_status_box_assigns_unique_line_ids(self) -> None:
        game = make_game()
        p1 = game.players[0]
        user1 = game.get_user(p1)

        game.status_box(p1, ["First", "Second", "Third"])

        items = user1.menus["status_box"]["items"]
        assert [item.id for item in items] == [
            "status_box:line:0",
            "status_box:line:1",
            "status_box:line:2",
        ]

    def test_live_status_box_refreshes_open_box_through_menu_flush(self) -> None:
        game = make_game()
        p1 = game.players[0]
        user1 = game.get_user(p1)
        value = {"count": 1}

        def build_status(player, user):
            return [
                MenuItem(
                    text=f"Count: {value['count']}",
                    id="count",
                )
            ]

        game.live_status_box(p1, "counter", build_status, focus_id="count")
        assert user1.menus["status_box"]["items"][0].text == "Count: 1"
        assert status_box_messages(user1)[-1].data["selection_id"] == "count"

        value["count"] = 2
        game.refresh_menus(p1)
        game.flush_menus()

        assert user1.menus["status_box"]["items"][0].text == "Count: 2"
        assert status_box_messages(user1)[-1].data["selection_id"] is None
        assert turn_menu_messages(user1) == []

    def test_live_status_box_close_clears_builder_and_restores_turn_menu(self) -> None:
        game = make_game()
        p1 = game.players[0]
        user1 = game.get_user(p1)

        game.live_status_box(
            p1,
            "single",
            lambda player, user: [MenuItem(text="Open", id="open")],
        )
        assert p1.id in game._status_box_open
        assert p1.id in game._live_status_boxes

        game.handle_event(
            p1,
            {
                "type": "menu",
                "menu_id": "status_box",
                "selection_id": "open",
            },
        )

        assert p1.id not in game._status_box_open
        assert p1.id not in game._live_status_boxes
        assert "status_box" not in user1.menus
        assert turn_menu_messages(user1)


class TestActionMenuFocus:
    def test_actions_menu_refreshes_in_place_when_marked_dirty(self) -> None:
        game = make_game()
        p1 = game.players[0]
        user1 = game.get_user(p1)

        game.execute_action(
            p1,
            "show_actions",
            context=ActionContext(menu_item_id="show_actions"),
        )
        assert p1.id in game._actions_menu_open
        assert actions_menu_messages(user1)

        user1.clear_messages()
        game.refresh_menus(p1)
        game.flush_menus()

        assert actions_menu_messages(user1)
        assert not turn_menu_messages(user1)
        assert p1.id in game._actions_menu_open

    def test_actions_menu_back_returns_focus_to_touch_anchor(self) -> None:
        game = make_game()
        p1 = game.players[0]
        user1 = game.get_user(p1)
        user1.client_type = "web"

        game.refresh_menus(p1)
        game.flush_menus()
        game.handle_event(
            p1,
            {
                "type": "menu",
                "menu_id": "turn_menu",
                "selection_id": "web_actions_menu",
            },
        )
        assert p1.id in game._actions_menu_open

        game.handle_event(
            p1,
            {
                "type": "menu",
                "menu_id": "actions_menu",
                "selection_id": "go_back",
            },
        )

        assert p1.id not in game._actions_menu_open
        assert turn_menu_messages(user1)[-1].data["selection_id"] == "web_actions_menu"

    def test_actions_menu_action_completion_returns_to_touch_anchor(self) -> None:
        game = make_game()
        p1 = game.players[0]
        user1 = game.get_user(p1)
        user1.client_type = "web"

        game.handle_event(
            p1,
            {
                "type": "menu",
                "menu_id": "turn_menu",
                "selection_id": "web_actions_menu",
            },
        )
        game.handle_event(
            p1,
            {
                "type": "menu",
                "menu_id": "actions_menu",
                "selection_id": "whos_at_table",
            },
        )

        assert turn_menu_messages(user1)[-1].data["selection_id"] == "web_actions_menu"

    def test_actions_menu_status_box_close_returns_to_touch_anchor(self) -> None:
        game = make_game()
        p1 = game.players[0]
        user1 = game.get_user(p1)
        user1.client_type = "web"

        game.handle_event(
            p1,
            {
                "type": "menu",
                "menu_id": "turn_menu",
                "selection_id": "web_actions_menu",
            },
        )
        game.handle_event(
            p1,
            {
                "type": "menu",
                "menu_id": "actions_menu",
                "selection_id": "game_info",
            },
        )
        assert p1.id in game._status_box_open

        game.handle_event(
            p1,
            {
                "type": "menu",
                "menu_id": "status_box",
                "selection_id": "status_box:line:0",
            },
        )

        assert turn_menu_messages(user1)[-1].data["selection_id"] == "web_actions_menu"

    def test_action_input_cancel_returns_focus_to_opener(self) -> None:
        game = make_game()
        p1 = game.players[0]
        user1 = game.get_user(p1)
        user1.preferences.allow_custom_bot_names = True

        game.refresh_menus(p1)
        game.flush_menus()
        game.handle_event(
            p1,
            {
                "type": "menu",
                "menu_id": "turn_menu",
                "selection_id": "add_bot",
            },
        )
        assert p1.id in game._pending_actions

        game.handle_event(
            p1,
            {
                "type": "editbox",
                "input_id": "action_input_editbox",
                "text": "",
                "cancelled": True,
            },
        )

        assert p1.id not in game._pending_actions
        assert turn_menu_messages(user1)[-1].data["selection_id"] == "add_bot"

    def test_leave_confirmation_no_returns_focus_to_touch_anchor(self) -> None:
        game = make_game()
        p1 = game.players[0]
        user1 = game.get_user(p1)
        user1.client_type = "mobile"

        game.refresh_menus(p1)
        game.flush_menus()
        game.handle_event(
            p1,
            {
                "type": "menu",
                "menu_id": "turn_menu",
                "selection_id": "web_leave_table",
            },
        )
        assert p1.id in game._pending_actions

        game.handle_event(
            p1,
            {
                "type": "menu",
                "menu_id": "leave_game_confirm",
                "selection_id": "no",
            },
        )

        assert p1.id not in game._pending_actions
        assert turn_menu_messages(user1)[-1].data["selection_id"] == "web_leave_table"
