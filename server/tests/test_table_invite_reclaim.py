import os
import tempfile
from types import SimpleNamespace

import pytest

from server.auth.auth import AuthManager
from server.core.server import Server
from server.games.pig.game import PigGame, PigOptions
from server.messages.localization import Localization
from server.persistence.database import Database
from server.users.bot import Bot
from server.users.test_user import MockUser


class TestTableInviteReclaim:
    def setup_method(self):
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_file.close()
        self.db = Database(self.temp_file.name)
        self.db.connect()
        self.server = Server(db_path=self.temp_file.name)
        self.server._db = self.db
        self.server._auth = AuthManager(self.db)

    def teardown_method(self):
        for invitee_name in list(self.server._pending_invites):
            self.server._cancel_invite(invitee_name)
        self.db.close()
        os.unlink(self.temp_file.name)

    def _create_online_user(self, username: str) -> MockUser:
        self.db.create_user(
            username,
            "Password123",
            approved=True,
            email=f"{username.lower()}@example.com",
        )
        record = self.db.get_user(username)
        assert record is not None
        user = MockUser(username, uuid=record.uuid)
        self.server._users[username] = user
        self.server._user_states[username] = {"menu": "main_menu"}
        return user

    def _create_started_table(
        self, host: MockUser, guest: MockUser
    ) -> tuple:
        table = self.server._tables.create_table("pig", host.username, host)
        game = PigGame(options=PigOptions(target_score=25))
        table.game = game
        game._table = table
        game.initialize_lobby(host.username, host)
        table.add_member(guest.username, guest, as_spectator=False)
        game.add_player(guest.username, guest)
        game.on_start()
        return table, game

    def _get_menu_action_ids(self, user: MockUser, menu_id: str) -> list[str]:
        items = user.get_current_menu_items(menu_id) or []
        return [item.id for item in items if hasattr(item, "id")]

    def _sound_names(self, user: MockUser) -> list[str]:
        return [message.data["name"] for message in user.messages if message.type == "play_sound"]

    def _add_named_bot(self, game: PigGame, name: str):
        bot_user = Bot(name)
        bot_player = game.create_player(bot_user.uuid, name, is_bot=True)
        game.players.append(bot_player)
        game.attach_user(bot_player.id, bot_user)
        game.setup_player_actions(bot_player)
        return bot_player

    @pytest.mark.asyncio
    async def test_new_table_created_sound_follows_new_table_notification_preference(self):
        host = self._create_online_user("Host")
        listener_on = self._create_online_user("ListenerOn")
        listener_off = self._create_online_user("ListenerOff")
        listener_off.preferences.notify_table_created = False

        await self.server._handle_tables_selection(
            host,
            "create_table",
            {"game_type": "pig", "game_name": "Pig"},
        )

        assert "table_created.ogg" in self._sound_names(listener_on)
        assert "table_created.ogg" not in self._sound_names(listener_off)
        assert listener_on.get_last_spoken() == Localization.get(
            listener_on.locale,
            "table-created-broadcast",
            host=host.username,
            game=Localization.get(listener_on.locale, "game-name-pig"),
        )
        assert listener_off.get_last_spoken() is None

    @pytest.mark.asyncio
    async def test_table_invite_always_plays_invite_notification_sound(self):
        host = self._create_online_user("Host")
        guest = self._create_online_user("Guest")
        table, _ = self._create_started_table(host, guest)

        guest.preferences.notify_table_created = False

        await self.server._send_table_invite(host, table, guest)

        assert "table_invite.ogg" in self._sound_names(guest)
        assert guest.get_last_spoken() == Localization.get(
            guest.locale,
            "table-invite-received",
            host=host.username,
            game=Localization.get(guest.locale, "game-name-pig"),
        )

    @pytest.mark.asyncio
    async def test_table_invite_waits_until_private_message_input_finishes(self):
        host = self._create_online_user("Host")
        guest = self._create_online_user("Guest")
        friend = self._create_online_user("Friend")
        table, _ = self._create_started_table(host, friend)

        self.db.send_friend_request(guest.uuid, friend.uuid)
        self.db.send_friend_request(friend.uuid, guest.uuid)

        self.server._user_states[guest.username] = {"menu": "friend_actions_menu", "target_username": friend.username}
        guest.show_editbox(
            "send_pm_input",
            Localization.get(guest.locale, "enter-pm-message", username=friend.username),
            multiline=True,
        )
        self.server._enter_input_state(guest, "send_pm_input", target_username=friend.username)

        await self.server._send_table_invite(host, table, guest)

        assert self.server._user_states[guest.username]["menu"] == "send_pm_input"
        assert self.server._pending_invites[guest.username]["deferred"] is True
        assert self.server._pending_invites[guest.username]["task"] is not None
        assert "table_invite_prompt" not in guest.menus
        assert guest.get_last_spoken() == Localization.get(
            guest.locale,
            "table-invite-queued",
            host=host.username,
            game=Localization.get(guest.locale, "game-name-pig"),
        )

        client = SimpleNamespace(username=guest.username, authenticated=True)
        await self.server._on_client_message(client, {"type": "editbox", "text": "hello"})

        state = self.server._user_states[guest.username]
        assert state["menu"] == "table_invite_prompt"
        assert state["prev_state"]["menu"] == "friend_actions_menu"
        assert state["prev_state"]["target_username"] == friend.username
        assert self.server._pending_invites[guest.username]["deferred"] is False
        assert self.server._pending_invites[guest.username]["task"] is not None
        assert "table_invite_prompt" in guest.menus

        self.server._cancel_invite(guest.username)

    @pytest.mark.asyncio
    async def test_transient_private_message_input_escape_restores_parent_and_deferred_invite(self):
        host = self._create_online_user("Host")
        guest = self._create_online_user("Guest")
        friend = self._create_online_user("Friend")
        table, _ = self._create_started_table(host, friend)

        self.server._user_states[guest.username] = {
            "menu": "friend_actions_menu",
            "target_username": friend.username,
        }
        guest.show_editbox(
            "send_pm_input",
            Localization.get(guest.locale, "enter-pm-message", username=friend.username),
            multiline=True,
        )
        self.server._enter_input_state(guest, "send_pm_input", target_username=friend.username)

        await self.server._send_table_invite(host, table, guest)
        client = SimpleNamespace(username=guest.username, authenticated=True)
        await self.server._on_client_message(
            client,
            {"type": "escape", "menu_id": "send_pm_input"},
        )

        state = self.server._user_states[guest.username]
        assert state["menu"] == "table_invite_prompt"
        assert state["prev_state"]["menu"] == "friend_actions_menu"
        assert state["prev_state"]["target_username"] == friend.username
        assert self.server._pending_invites[guest.username]["deferred"] is False
        assert "table_invite_prompt" in guest.menus

        self.server._cancel_invite(guest.username)

    @pytest.mark.asyncio
    async def test_accepting_invite_reclaims_bot_replaced_seat(self):
        host = self._create_online_user("Host")
        guest = self._create_online_user("Guest")
        table, game = self._create_started_table(host, guest)

        guest_player = game.get_player_by_id(guest.uuid)
        assert guest_player is not None

        game._perform_leave_game(guest_player)
        table.remove_member(guest.username)

        replaced = game.get_player_by_id(guest.uuid)
        assert replaced is not None
        assert replaced.is_bot is True
        bot_name = replaced.name
        assert replaced.replaced_human_name == guest.username
        assert bot_name != guest.username

        await self.server._send_table_invite(host, table, guest)
        state = self.server._user_states[guest.username]
        host.clear_messages()
        guest.clear_messages()
        await self.server._handle_table_invite_selection(guest, "accept", state)

        reclaimed = game.get_player_by_id(guest.uuid)
        assert reclaimed is not None
        assert reclaimed.is_bot is False
        assert reclaimed.replaced_human is False
        assert reclaimed.is_spectator is False
        assert game.get_user(reclaimed) is guest
        assert table.get_user(guest.username) is guest
        assert self.server._tables.find_user_table(guest.username) is table
        assert sum(1 for member in table.members if member.username == guest.username) == 1
        assert sum(1 for player in game.players if player.name == guest.username) == 1
        expected = Localization.get(
            guest.locale,
            "player-reclaimed-from-bot",
            player=guest.username,
            bot=bot_name,
        )
        assert expected in host.get_spoken_messages()
        assert expected in guest.get_spoken_messages()
        assert "join.ogg" in self._sound_names(host)
        assert "join.ogg" in self._sound_names(guest)

    @pytest.mark.asyncio
    async def test_accepting_invite_reattaches_existing_table_member(self):
        host = self._create_online_user("Host")
        guest = self._create_online_user("Guest")
        table, game = self._create_started_table(host, guest)

        guest_player = game.get_player_by_id(guest.uuid)
        assert guest_player is not None

        game._replace_with_bot(guest_player)
        bot_name = guest_player.name
        table._users.pop(guest.username, None)
        self.server._tables._username_to_table.pop(guest.username, None)

        await self.server._send_table_invite(host, table, guest)
        state = self.server._user_states[guest.username]
        host.clear_messages()
        guest.clear_messages()
        await self.server._handle_table_invite_selection(guest, "accept", state)

        reclaimed = game.get_player_by_id(guest.uuid)
        assert reclaimed is not None
        assert reclaimed.is_bot is False
        assert reclaimed.replaced_human is False
        assert reclaimed.is_spectator is False
        assert game.get_user(reclaimed) is guest
        assert table.get_user(guest.username) is guest
        assert self.server._tables.find_user_table(guest.username) is table
        assert sum(1 for member in table.members if member.username == guest.username) == 1
        expected = Localization.get(
            guest.locale,
            "player-reclaimed-from-bot",
            player=guest.username,
            bot=bot_name,
        )
        assert expected in host.get_spoken_messages()
        assert expected in guest.get_spoken_messages()
        assert "join.ogg" in self._sound_names(host)
        assert "join.ogg" in self._sound_names(guest)

    def test_login_restore_reclaims_bot_replaced_seat_and_announces(self):
        host = self._create_online_user("Host")
        guest = self._create_online_user("Guest")
        table, game = self._create_started_table(host, guest)

        guest_player = game.get_player_by_id(guest.uuid)
        assert guest_player is not None

        game._replace_with_bot(guest_player)
        bot_name = guest_player.name
        table._users.pop(guest.username, None)
        host.clear_messages()
        guest.clear_messages()

        self.server._restore_user_state(guest, guest.username)

        reclaimed = game.get_player_by_id(guest.uuid)
        assert reclaimed is not None
        assert reclaimed.is_bot is False
        assert reclaimed.replaced_human is False
        assert reclaimed.is_spectator is False
        assert game.get_user(reclaimed) is guest
        assert table.get_user(guest.username) is guest
        assert self.server._tables.find_user_table(guest.username) is table
        assert self.server._user_states[guest.username] == {
            "menu": "in_game",
            "table_id": table.table_id,
        }
        expected = Localization.get(
            guest.locale,
            "player-reclaimed-from-bot",
            player=guest.username,
            bot=bot_name,
        )
        assert expected in host.get_spoken_messages()
        assert expected in guest.get_spoken_messages()
        assert "join.ogg" in self._sound_names(host)
        assert "join.ogg" in self._sound_names(guest)

    @pytest.mark.asyncio
    async def test_join_player_reclaims_bot_replaced_seat_before_menu_rebuild(self):
        host = self._create_online_user("Host")
        guest = self._create_online_user("Guest")
        table, game = self._create_started_table(host, guest)

        guest_player = game.get_player_by_id(guest.uuid)
        assert guest_player is not None

        game._perform_leave_game(guest_player)
        table.remove_member(guest.username)
        bot_name = game.get_player_by_id(guest.uuid).name
        host.clear_messages()
        guest.clear_messages()

        await self.server._handle_join_selection(
            guest,
            "join_player",
            {"table_id": table.table_id, "game_type": "pig"},
        )

        reclaimed = game.get_player_by_id(guest.uuid)
        assert reclaimed is not None
        assert reclaimed.is_bot is False
        assert reclaimed.replaced_human is False
        assert reclaimed.is_spectator is False
        assert game.get_user(reclaimed) is guest
        assert table.get_user(guest.username) is guest
        assert self.server._user_states[guest.username] == {
            "menu": "in_game",
            "table_id": table.table_id,
        }
        expected = Localization.get(
            guest.locale,
            "player-took-over",
            player=guest.username,
            bot=bot_name,
        )
        assert expected in host.get_spoken_messages()
        assert expected in guest.get_spoken_messages()
        assert "join.ogg" in self._sound_names(host)
        assert "join.ogg" in self._sound_names(guest)

    @pytest.mark.asyncio
    async def test_join_player_rejects_name_matching_existing_bot(self):
        host = self._create_online_user("Host")
        entrant = self._create_online_user("Test")
        table = self.server._tables.create_table("pig", host.username, host)
        game = PigGame(options=PigOptions(target_score=25))
        table.game = game
        game._table = table
        game.initialize_lobby(host.username, host)
        self._add_named_bot(game, "Test")

        await self.server._handle_join_selection(
            entrant,
            "join_player",
            {"table_id": table.table_id, "game_type": "pig"},
        )

        assert self.server._tables.find_user_table(entrant.username) is None
        assert game.get_player_by_id(entrant.uuid) is None
        assert entrant.get_last_spoken() == Localization.get(
            entrant.locale,
            "table-name-already-used",
        )

    @pytest.mark.asyncio
    async def test_join_spectator_rejects_name_matching_existing_bot(self):
        host = self._create_online_user("Host")
        entrant = self._create_online_user("Test")
        table = self.server._tables.create_table("pig", host.username, host)
        game = PigGame(options=PigOptions(target_score=25))
        table.game = game
        game._table = table
        game.initialize_lobby(host.username, host)
        self._add_named_bot(game, "Test")

        await self.server._handle_join_selection(
            entrant,
            "join_spectator",
            {"table_id": table.table_id, "game_type": "pig"},
        )

        assert self.server._tables.find_user_table(entrant.username) is None
        assert game.get_player_by_id(entrant.uuid) is None
        assert entrant.get_last_spoken() == Localization.get(
            entrant.locale,
            "table-name-already-used",
        )

    def test_custom_bot_name_rejects_registered_account_name(self):
        host = self._create_online_user("Host")
        self._create_online_user("Test")
        table = self.server._tables.create_table("pig", host.username, host)
        game = PigGame(options=PigOptions(target_score=25))
        table.game = game
        game._table = table
        game.initialize_lobby(host.username, host)
        host.preferences.allow_custom_bot_names = True
        host_player = game.get_player_by_id(host.uuid)
        assert host_player is not None

        game.execute_action(host_player, "add_bot")
        game.handle_event(
            host_player,
            {
                "type": "editbox",
                "input_id": "action_input_editbox",
                "text": "Test",
            },
        )

        assert not any(player.name == "Test" and player.is_bot for player in game.players)
        assert host.get_last_spoken() == Localization.get(
            host.locale,
            "bot-name-registered-account",
        )

    def test_generated_bot_name_skips_registered_account_name(self, monkeypatch):
        host = self._create_online_user("Host")
        self._create_online_user("Pho Pixel")
        table = self.server._tables.create_table("pig", host.username, host)
        game = PigGame(options=PigOptions(target_score=25))
        table.game = game
        game._table = table
        game.initialize_lobby(host.username, host)
        host_player = game.get_player_by_id(host.uuid)
        assert host_player is not None
        monkeypatch.setattr(
            "server.game_utils.bot_names.random.choice",
            lambda options: options[0],
        )

        game.execute_action(host_player, "add_bot")

        bot_names = [player.name for player in game.players if player.is_bot]
        assert bot_names
        assert "Pho Pixel" not in bot_names

    def test_replacement_bot_name_skips_registered_account_name(self, monkeypatch):
        host = self._create_online_user("Host")
        guest = self._create_online_user("Guest")
        self._create_online_user("Pho Pixel")
        table, game = self._create_started_table(host, guest)
        guest_player = game.get_player_by_id(guest.uuid)
        assert guest_player is not None
        monkeypatch.setattr(
            "server.game_utils.bot_names.random.choice",
            lambda options: options[0],
        )

        game._replace_with_bot(guest_player)

        assert guest_player.is_bot is True
        assert guest_player.name != "Pho Pixel"

    def test_disconnect_replacement_bot_survives_stale_waiting_table_status(
        self, monkeypatch
    ):
        host = self._create_online_user("Host")
        guest = self._create_online_user("Guest")
        table, game = self._create_started_table(host, guest)
        table.status = "waiting"
        table._member_offline_since[guest.username] = 0.0

        guest_player = game.get_player_by_id(guest.uuid)
        assert guest_player is not None
        game.on_player_disconnect(guest.uuid)
        self.server._users.pop(guest.username, None)

        replacement = game.get_player_by_id(guest.uuid)
        assert replacement is not None
        assert replacement.is_bot is True
        bot_name = replacement.name
        host.clear_messages()
        monkeypatch.setattr("server.tables.table.time.time", lambda: 20.0)

        table.on_tick()

        replacement = game.get_player_by_id(guest.uuid)
        assert table.status == "playing"
        assert replacement is not None
        assert replacement.is_bot is True
        assert replacement.name == bot_name
        assert replacement.replaced_human_name == guest.username
        assert any(member.username == guest.username for member in table.members)
        assert self.server._tables.get_table(table.table_id) is table
        assert Localization.get(
            host.locale,
            "player-kicked-offline",
            player=guest.username,
        ) not in host.get_spoken_messages()

    @pytest.mark.asyncio
    async def test_unexpected_disconnect_replacement_plays_table_leave_sound(self):
        host = self._create_online_user("Host")
        guest = self._create_online_user("Guest")
        table, game = self._create_started_table(host, guest)
        guest.connection = object()
        client = SimpleNamespace(username=guest.username, address="guest-client")
        host.clear_messages()

        await self.server._on_client_disconnect(client)

        replacement = game.get_player_by_id(guest.uuid)
        assert replacement is not None
        assert replacement.is_bot is True
        assert replacement.replaced_human_name == guest.username
        assert "leave.ogg" in self._sound_names(host)
        assert Localization.get(
            host.locale,
            "player-replaced-by-bot",
            player=guest.username,
            bot=replacement.name,
        ) in host.get_spoken_messages()

    def test_last_human_disconnect_survives_stale_waiting_table_status(
        self, monkeypatch
    ):
        host = self._create_online_user("Host")
        table = self.server._tables.create_table("pig", host.username, host)
        game = PigGame(options=PigOptions(target_score=25))
        table.game = game
        game._table = table
        game.initialize_lobby(host.username, host)
        game.on_start()
        table.status = "waiting"
        table._member_offline_since[host.username] = 0.0

        game.on_player_disconnect(host.uuid)
        self.server._users.pop(host.username, None)
        host.clear_messages()
        monkeypatch.setattr("server.tables.table.time.time", lambda: 20.0)

        table.on_tick()

        host_player = game.get_player_by_id(host.uuid)
        assert table.status == "playing"
        assert host_player is not None
        assert host_player.is_bot is False
        assert any(member.username == host.username for member in table.members)
        assert self.server._tables.get_table(table.table_id) is table
        assert Localization.get(
            host.locale,
            "player-kicked-offline",
            player=host.username,
        ) not in host.get_spoken_messages()

    def test_lobby_disconnected_player_becomes_reclaimable_bot_on_start(
        self, monkeypatch
    ):
        host = self._create_online_user("Host")
        guest = self._create_online_user("Guest")
        table = self.server._tables.create_table("pig", host.username, host)
        game = PigGame(options=PigOptions(target_score=25))
        table.game = game
        game._table = table
        game.initialize_lobby(host.username, host)
        table.add_member(guest.username, guest, as_spectator=False)
        game.add_player(guest.username, guest)
        table._member_offline_since[guest.username] = 0.0
        self.server._users.pop(guest.username, None)
        host_player = game.get_player_by_id(host.uuid)
        assert host_player is not None

        game.execute_action(host_player, "start_game")

        replacement = game.get_player_by_id(guest.uuid)
        assert replacement is not None
        assert game.status == "playing"
        assert table.status == "playing"
        assert replacement.is_bot is True
        assert replacement.replaced_human is True
        assert replacement.replaced_human_name == guest.username
        assert replacement.name != guest.username
        assert any(member.username == guest.username for member in table.members)
        assert Localization.get(
            host.locale,
            "player-replaced-by-bot",
            player=guest.username,
            bot=replacement.name,
        ) in host.get_spoken_messages()
        assert "leave.ogg" in self._sound_names(host)

        host.clear_messages()
        monkeypatch.setattr("server.tables.table.time.time", lambda: 20.0)
        table.on_tick()

        assert game.get_player_by_id(guest.uuid) is replacement
        assert any(member.username == guest.username for member in table.members)
        assert self.server._tables.get_table(table.table_id) is table
        assert Localization.get(
            host.locale,
            "player-kicked-offline",
            player=guest.username,
        ) not in host.get_spoken_messages()

    def test_lobby_disconnected_spectator_is_removed_before_start(self):
        host = self._create_online_user("Host")
        guest = self._create_online_user("Guest")
        spectator = self._create_online_user("Spectator")
        table = self.server._tables.create_table("pig", host.username, host)
        game = PigGame(options=PigOptions(target_score=25))
        table.game = game
        game._table = table
        game.initialize_lobby(host.username, host)
        table.add_member(guest.username, guest, as_spectator=False)
        game.add_player(guest.username, guest)
        table.add_member(spectator.username, spectator, as_spectator=True)
        game.add_spectator(spectator.username, spectator)
        table._member_offline_since[spectator.username] = 0.0
        self.server._users.pop(spectator.username, None)
        host_player = game.get_player_by_id(host.uuid)
        assert host_player is not None

        game.execute_action(host_player, "start_game")

        assert game.status == "playing"
        assert game.get_player_by_id(spectator.uuid) is None
        assert not any(
            member.username == spectator.username for member in table.members
        )
        assert spectator.username not in table._member_offline_since

    def test_table_reset_converts_replacement_bot_to_fresh_bot_identity(self):
        host = self._create_online_user("Host")
        guest = self._create_online_user("Guest")
        table, game = self._create_started_table(host, guest)

        guest_player = game.get_player_by_id(guest.uuid)
        assert guest_player is not None
        game._perform_leave_game(guest_player)
        table.remove_member(guest.username)

        replacement = game.get_player_by_id(guest.uuid)
        assert replacement is not None
        assert replacement.is_bot is True
        assert replacement.replaced_human is True
        replacement_name = replacement.name

        assert table.reset_game()
        assert table.game is not None
        fresh_bot = next(
            player
            for player in table.game.players
            if player.is_bot and player.name == replacement_name
        )
        assert fresh_bot.id != guest.uuid
        assert fresh_bot.replaced_human is False

    @pytest.mark.asyncio
    async def test_friend_join_reclaims_bot_replaced_seat(self):
        host = self._create_online_user("Host")
        guest = self._create_online_user("Guest")
        table, game = self._create_started_table(host, guest)

        guest_player = game.get_player_by_id(guest.uuid)
        assert guest_player is not None

        game._perform_leave_game(guest_player)
        table.remove_member(guest.username)
        bot_name = game.get_player_by_id(guest.uuid).name
        host.clear_messages()
        guest.clear_messages()

        await self.server._handle_friend_actions_selection(
            guest,
            "join_table",
            {"target_username": host.username},
        )

        reclaimed = game.get_player_by_id(guest.uuid)
        assert reclaimed is not None
        assert reclaimed.is_bot is False
        assert reclaimed.replaced_human is False
        assert reclaimed.is_spectator is False
        assert game.get_user(reclaimed) is guest
        assert table.get_user(guest.username) is guest
        assert self.server._tables.find_user_table(guest.username) is table
        assert sum(1 for member in table.members if member.username == guest.username) == 1
        expected = Localization.get(
            guest.locale,
            "player-reclaimed-from-bot",
            player=guest.username,
            bot=bot_name,
        )
        assert expected in host.get_spoken_messages()
        assert expected in guest.get_spoken_messages()
        assert "join.ogg" in self._sound_names(host)
        assert "join.ogg" in self._sound_names(guest)

    @pytest.mark.asyncio
    async def test_friend_join_switches_active_tables_via_leave_logic(self):
        host_a = self._create_online_user("HostA")
        mover = self._create_online_user("Mover")
        host_b = self._create_online_user("HostB")
        guest_b = self._create_online_user("GuestB")

        table_a, game_a = self._create_started_table(host_a, mover)
        table_b, game_b = self._create_started_table(host_b, guest_b)

        await self.server._handle_friend_actions_selection(
            mover,
            "join_table",
            {"target_username": host_b.username},
        )

        moved_from = game_a.get_player_by_id(mover.uuid)
        assert moved_from is not None
        assert moved_from.is_bot is True
        assert moved_from.replaced_human is True
        assert sum(1 for member in table_a.members if member.username == mover.username) == 0
        assert self.server._tables.find_user_table(mover.username) is table_b

        moved_to = game_b.get_player_by_id(mover.uuid)
        assert moved_to is not None
        assert moved_to.is_spectator is True
        assert moved_to.is_bot is False
        assert game_b.get_user(moved_to) is mover
        assert table_b.get_user(mover.username) is mover
        assert sum(1 for member in table_b.members if member.username == mover.username) == 1

    def test_private_tables_are_hidden_from_public_lists_and_friend_join(self):
        host = self._create_online_user("Host")
        public_host = self._create_online_user("PublicHost")
        member = self._create_online_user("Member")
        outsider = self._create_online_user("Outsider")

        private_table = self.server._tables.create_table("pig", host.username, host)
        private_game = PigGame(options=PigOptions(target_score=25))
        private_table.game = private_game
        private_game._table = private_table
        private_game.initialize_lobby(host.username, host)
        private_table.is_private = True
        private_table.add_member(member.username, member, as_spectator=False)
        private_game.add_player(member.username, member)

        public_table = self.server._tables.create_table(
            "pig", public_host.username, public_host
        )
        public_game = PigGame(options=PigOptions(target_score=25))
        public_table.game = public_game
        public_game._table = public_table
        public_game.initialize_lobby(public_host.username, public_host)

        game_items = self.server._get_tables_menu_items(outsider, "pig")
        active_items = self.server._get_active_tables_menu_items(outsider)
        outsider_table_ids = {item.id for item in game_items + active_items if hasattr(item, "id")}

        assert f"table_{private_table.table_id}" not in outsider_table_ids
        assert f"table_{public_table.table_id}" in outsider_table_ids

        self.server._show_friend_actions_menu(outsider, host.username)
        assert "join_table" not in self._get_menu_action_ids(outsider, "friend_actions_menu")

        member_game_items = self.server._get_tables_menu_items(member, "pig")
        member_ids = {item.id for item in member_game_items if hasattr(item, "id")}
        assert f"table_{private_table.table_id}" in member_ids

    @pytest.mark.asyncio
    async def test_stale_game_tables_menu_cannot_join_after_table_becomes_private(self):
        host = self._create_online_user("Host")
        outsider = self._create_online_user("Outsider")

        table = self.server._tables.create_table("pig", host.username, host)
        game = PigGame(options=PigOptions(target_score=25))
        table.game = game
        game._table = table
        game.initialize_lobby(host.username, host)

        self.server._show_tables_menu(outsider, "pig")
        menu_ids = self._get_menu_action_ids(outsider, "tables_menu")
        assert f"table_{table.table_id}" in menu_ids

        table.is_private = True

        await self.server._handle_tables_selection(
            outsider,
            f"table_{table.table_id}",
            self.server._user_states[outsider.username],
        )

        assert self.server._tables.find_user_table(outsider.username) is None
        assert outsider.get_last_spoken() == Localization.get(outsider.locale, "table-private-invite-only")
        refreshed_ids = self._get_menu_action_ids(outsider, "tables_menu")
        assert f"table_{table.table_id}" not in refreshed_ids

    @pytest.mark.asyncio
    async def test_stale_active_tables_menu_cannot_join_after_table_becomes_private(self):
        host = self._create_online_user("Host")
        outsider = self._create_online_user("Outsider")

        table = self.server._tables.create_table("pig", host.username, host)
        game = PigGame(options=PigOptions(target_score=25))
        table.game = game
        game._table = table
        game.initialize_lobby(host.username, host)

        self.server._show_active_tables_menu(outsider)
        menu_ids = self._get_menu_action_ids(outsider, "active_tables_menu")
        assert f"table_{table.table_id}" in menu_ids

        table.is_private = True

        await self.server._handle_active_tables_selection(
            outsider,
            f"table_{table.table_id}",
        )

        assert self.server._tables.find_user_table(outsider.username) is None
        assert outsider.get_last_spoken() == Localization.get(outsider.locale, "table-private-invite-only")
        refreshed_ids = self._get_menu_action_ids(outsider, "active_tables_menu")
        assert f"table_{table.table_id}" not in refreshed_ids
