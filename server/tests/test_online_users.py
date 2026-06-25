from pathlib import Path

import pytest

from ..core.server import Server
from ..tables.manager import TableManager
from ..users.test_user import MockUser
from ..messages.localization import Localization

# Ensure games are registered for name lookups.
from .. import games  # noqa: F401


class DummyClient:
    def __init__(self, username: str):
        self.username = username


def _make_server() -> Server:
    Localization.init(Path(__file__).resolve().parents[1] / "locales")
    server = Server.__new__(Server)
    server._tables = TableManager()
    server._user_states = {}
    server._users = {}
    return server


def _menu_texts(user: MockUser, menu_id: str) -> list[str]:
    items = user.menus.get(menu_id, {}).get("items", [])
    texts: list[str] = []
    for item in items:
        texts.append(item.text if hasattr(item, "text") else item)
    return texts


@pytest.mark.asyncio
async def test_list_online_users_speaks_sorted_list() -> None:
    server = _make_server()
    alice = MockUser("Alice")
    bob = MockUser("Bob")
    server._users = {"Bob": bob, "Alice": alice}

    client = DummyClient("Alice")
    await server._handle_list_online(client)

    assert alice.messages[-1].data["text"] == "2 users: Alice and Bob"


def test_online_users_menu_formats_game_names() -> None:
    server = _make_server()
    viewer = MockUser("Viewer")
    bob = MockUser("Bob")
    alice = MockUser("Alice")
    carol = MockUser("Carol")
    server._users = {"Viewer": viewer, "Bob": bob, "Alice": alice, "Carol": carol}

    table = server._tables.create_table("crazyeights", "Bob", bob)
    table.add_member("Carol", carol, as_spectator=True)

    server._show_online_users_menu(viewer)

    texts = _menu_texts(viewer, "online_users")
    assert "Bob (User, Desktop, English): Waiting at Crazy Eights table" in texts
    assert "Carol (User, Desktop, English): Watching Crazy Eights table" in texts
    assert "Alice (User, Desktop, English): Main menu" in texts


def test_online_users_menu_renders_current_user_as_read_only() -> None:
    server = _make_server()
    viewer = MockUser("Viewer")
    alice = MockUser("Alice")
    server._users = {"Viewer": viewer, "Alice": alice}

    server._show_online_users_menu(viewer)

    items = viewer.get_current_menu_items("online_users") or []
    own_item = next(item for item in items if item.text.startswith("Viewer "))
    assert own_item.id == ""


def test_client_platform_sanitizer_bounds_untrusted_display_text() -> None:
    sanitized = Server._sanitize_client_platform("<Windows>\n<script>AMD64</script>" * 3)
    assert sanitized.startswith("Windows scriptAMD64/script")
    assert "<" not in sanitized
    assert ">" not in sanitized
    assert "\n" not in sanitized
    assert len(sanitized) == 40


def test_online_users_menu_includes_first_party_client_platforms() -> None:
    server = _make_server()
    viewer = MockUser("Viewer")
    desktop = MockUser("DesktopPlayer")
    web = MockUser("WebPlayer")
    mobile = MockUser("MobilePlayer")

    desktop.client_type = "python"
    desktop.client_platform = "Windows 11 AMD64"
    web.client_type = "web"
    web.client_platform = "Windows"
    mobile.client_type = "mobile"
    mobile.client_platform = "Android 16 (API 36)"
    server._users = {
        "Viewer": viewer,
        "DesktopPlayer": desktop,
        "WebPlayer": web,
        "MobilePlayer": mobile,
    }

    server._show_online_users_menu(viewer)

    texts = _menu_texts(viewer, "online_users")
    assert "DesktopPlayer (User, Desktop (Windows 11 AMD64), English): Main menu" in texts
    assert "WebPlayer (User, Web (Windows), English): Main menu" in texts
    assert "MobilePlayer (User, Mobile (Android 16 (API 36)), English): Main menu" in texts


def test_online_users_menu_distinguishes_playing_and_spectating() -> None:
    server = _make_server()
    viewer = MockUser("Viewer")
    bob = MockUser("Bob")
    alice = MockUser("Alice")
    server._users = {"Viewer": viewer, "Bob": bob, "Alice": alice}

    table = server._tables.create_table("crazyeights", "Bob", bob)
    table.add_member("Alice", alice, as_spectator=True)
    table.status = "playing"

    server._show_online_users_menu(viewer)

    texts = _menu_texts(viewer, "online_users")
    assert "Bob (User, Desktop, English): Playing Crazy Eights" in texts
    assert "Alice (User, Desktop, English): Spectating Crazy Eights" in texts

