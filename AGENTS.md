# AGENTS.md - PlayAural AI Development Guide

Concise mandatory rules for AI agents working on PlayAural. `CLAUDE.md` is the
detailed source of truth; keep this file synchronized with it. If the two ever
conflict, follow `CLAUDE.md` and update `AGENTS.md`.

## Project

PlayAural is an audio-first multiplayer gaming platform for screen reader users.
It is GPL-licensed and has four first-party components:

- `server/`: Python 3.11 asyncio WebSocket server, games, auth, tables,
  persistence, localization, ratings, voice authorization.
- `client/`: Python wxPython desktop client with keyboard/screen-reader UX.
- `web_client/`: vanilla JS PWA with ARIA, browser audio, and web TTS.
- `mobile_client/`: Expo/React Native/TypeScript Android-first touch and
  self-voicing client.

All gameplay communication is WebSocket JSON packets. Table voice chat is
server-authorized but media flows through the separate LiveKit service. Never
merge voice media into gameplay WebSocket traffic. Voice membership is
runtime-only table state unless a future feature explicitly defines retention,
cleanup, and account-deletion behavior.

## Commands

Run server tests from the repo root through uv:

```bash
uv run --project server --extra dev python -m pytest server/tests -q
uv run --project server --extra dev python -m pytest server/tests/test_file.py::test_name
```

Run focused tests while iterating. Run the full suite before landing
cross-subsystem changes or features. Tests are parallel-safe with `-n auto`;
keep new tests deterministic and avoid RNG-dependent exact assertions.

Other common commands:

```bash
cd server && python -m server
python client/client.py
python -m http.server 8080 --directory web_client
cd mobile_client && cmd /c npm install && cmd /c npm run generate:sounds
cd mobile_client && cmd /c npm run typecheck && npx expo start
```

## Core Architecture

- `server/games/` currently registers 42 games. Categories are `cards`, `dice`,
  `board`, `poker`, `arcade`, and `misc`; user-facing category labels must be
  localized. The Play menu uses dynamic counts, not hardcoded category counts.
- Games are `@dataclass` classes registered with `@register_game`, inherit from
  `Game`, and may add utility mixins such as `GridGameMixin` or
  `TurnTimerMixin`.
- Persistent game state must be dataclass fields serialized safely by
  Mashumaro. Runtime-only state belongs in `__post_init__`.
- Use the canonical `Player` and `ActionContext` types from
  `server/game_utils/` or the `server/games/base.py` re-exports. Do not create
  duplicate base player/context classes.
- Every game implements metadata methods including `get_name`, `get_type`,
  `get_category`, player bounds, and `get_supported_leaderboards`.
- Use `get_active_players()` for gameplay, results, and winner logic. Do not
  iterate `self.players` for active-player decisions unless spectators/bots are
  deliberately included.
- `set_turn_players(players)` resets `turn_index` to 0. Do not call
  `advance_turn()` immediately afterward.
- `on_tick()` must call `super().on_tick()`, process scheduled sounds, process
  sequences, and gate bot logic when sequences pause bots.

## Timed Flows

Use `SequenceRunnerMixin` for delayed gameplay/audio flows that must survive
save/load: movement animations, reveals, captures, roulette, cutscenes, and any
legacy event-queue style flow.

Rules:

- Build explicit `SequenceBeat` lists with `sound_op`, `localized_sound_op`,
  and `callback_op`.
- State changes happen in callbacks, not because a sound played.
- Payloads must be Mashumaro-safe primitives, lists, dicts, or safe dataclasses.
- Prefer `SEQUENCE_LOCK_GAMEPLAY`; keep info/status actions available.
- Use `pause_bots=True` when bots must wait.
- Cancel stale tagged sequences when resetting a phase or round.

## Grid Games

For `GridGameMixin`, serialized fields must use exact safe types:

- `grid_cursors: dict[str, GridCursor]`
- `grid_row_labels: list[str]`
- `grid_col_labels: list[str]`

Do not store raw tuples or ad-hoc cursor dicts in serialized grid state.

## Actions, Menus, and Focus

Action sets resolve in this order: `turn -> lobby -> options -> standard`.

- Turn-menu gameplay actions use `show_in_actions_menu=False`.
- Game-specific info/status actions belong in `create_standard_action_set`, not
  the turn set.
- `Action.include_spectators` and matching keybind `include_spectators` must
  agree.
- Public information may use `include_spectators=True`; private or mutating
  gameplay actions normally must not.

Game code does not paint turn menus directly. It records turn-menu intent with:

- `refresh_menus(player=None)`: mark one player or everyone dirty.
- `request_menu_focus(player, action_id)`: one-shot focus jump for one player.

Status overlays are the sanctioned exception: use `status_box(...)` for static
snapshots and `live_status_box(...)` for dynamic state panels. Games still must
not call `user.show_menu()` / `user.update_menu()` directly.
Server navigation requested while a status box is open is deferred and replayed
after the box closes; active editbox/action-input states block navigation
without queuing it. In-game overlays such as Host Management must enter through
modal-aware server navigation, not direct show calls from game actions.

`flush_menus()` is sealed and framework-owned. Games must not override or call
menu flush internals except tests calling `flush_menus()` at production
boundaries after direct `execute_action`, `_action_*`, `on_start`, or `on_tick`.
Do not resurrect old `rebuild_*` / `update_*` patterns.

Customize painting through:

- `before_menu_build(player)`: idempotently sync dynamic action sets and order.
- `build_menu_items(player, user) -> MenuBuild`: custom item/grid layout.

Client focus doctrine:

- Same-menu repaint preserves focus by item id; `NetworkUser` skips identical
  same-menu repaints with no focus directive.
- Anchors break only when the focused item leaves the menu, the menu identity
  changes, or `selection_id` explicitly jumps focus.
- Keep disabled-but-visible persistent controls when they anchor touch or screen
  reader focus. Use `request_menu_focus` only for deliberate action-driven jumps.
- The Escape/actions menu auto-refreshes in place through sealed
  `flush_menus()`. Games must not repaint or block it manually.
- Framework Back/Cancel exits restore focus to the opener when possible:
  actions-menu Back, action-input Cancel, leave-confirmation No, and status-box
  close. Use stable action ids so this works.
- Use `status_box(player, lines)` for static snapshots/help/limited reveals.
  Use `live_status_box(player, box_id, builder, focus_id=None)` for dynamic
  state panels such as boards, standings, clocks, rosters, and detailed scores.
  Live builders return strings or `MenuItem`s, refresh only through the sealed
  flush after `refresh_menus()`, and must use stable semantic item ids whenever
  rows can reorder, appear, or disappear.

## Touch Clients

Use `server/game_utils/client_types.py` helpers (`is_touch_client`,
`is_touch_client_type`, `uses_self_voicing_settings`) instead of raw
`client_type` checks. Touch clients include web and mobile; mobile is not web.

Rules:

- Time-critical reaction actions must be visible in the turn menu during active
  windows for touch clients.
- Utility actions normally reached by desktop keybinds should be touch-visible
  when useful.
- Turn order for touch menus: reactions, primary card/tile/play actions,
  multi-select confirmation, utilities.
- Touch standard-action order: game-specific info, `check_scores` if supported,
  `whose_turn`, `whos_at_table`.
- Use `_order_touch_standard_actions(action_set, target_order)`; do not copy
  manual ordering loops. Keep desktop ordering separate.

## Keybinds

`setup_keybinds()` must call `super().setup_keybinds()` first. Gameplay
keybinds use `KeybindState.ACTIVE`; lobby-only actions use `IDLE`; truly global
actions use `ALWAYS`.

Reserved base/client keys: `enter`, `escape`, `b`, `shift+b`, `f3`, `t`, `s`,
`shift+s`, `ctrl+m`, `ctrl+q`, `ctrl+u`, `ctrl+s`, `ctrl+r`, `ctrl+i`,
`ctrl+f1`. Do not reuse them for game-specific actions unless deliberately
matching the standard behavior.

## Options

Use declarative `GameOptions` with `option_field()`.

- Every option must have working logic; no dead options.
- Every option needs a localized `change_msg` in EN and VI.
- `MenuOption` needs `choice_labels` for every raw value.
- `TeamModeOption` uses shared team-mode helpers.
- `prestart_validate()` must block invalid player counts, impossible deals,
  unsupported option combinations, and team-mode conflicts with clear localized
  errors.

## Audio and Accessibility

Audio-first is mandatory. Every important state change needs TTS and/or sound.

- Every `speak_l()` and `broadcast_l()` call must pass explicit `buffer=`.
- Buffers: `game` for gameplay, `system` for settings/connection/moderation,
  `chat` for chat only, `misc` for minor non-game informational output.
- Use `play_sound`, `user.play_sound`, `play_music`, ambience helpers, scheduled
  sounds, or sequences as appropriate.
- Provide information actions for state queries such as hand, board/table,
  counts, status, scores, and whose turn.

## Localization

All player-facing strings go through Fluent. No hardcoded English may reach
players.

- Use `speak_l`, `broadcast_l`, `broadcast_personal_l`, localized option/pref
  helpers, and localized sequence helpers.
- Pass raw data as kwargs and let Fluent format lists, plurals, and selects.
- Maintain EN/VI parity: same keys, variables, and plural/select arms.
- Agents author both EN and VI strings in this repo, but Vietnamese is
  provisional and should be flagged for native review when quality matters.
- Prefer writing locale keys before feature code so every announcement path is
  planned.

## Scores, Leaderboards, and Teams

- Only games with real leaderboard support should expose
  `get_supported_leaderboards()` entries.
- Scoreless games should not claim score support; score buttons are hidden and
  `s` / `shift+s` are ignored silently.
- Games using default score actions must keep `TeamManager` synchronized.
- Non-point units need a localized `score_unit_key` in shared `games.ftl` or the
  game locale when unique. Units are display only; stored stats remain numeric.
- Brief score checks speak one line per player/team in the `game` buffer.
- Detailed score checks normally use `live_status_box(...)` with one line per
  player/team.
- Team games use shared team arrangement. Call
  `_setup_team_manager_for_start(...)`; use `_get_team_turn_players(...)` when
  seating affects turn order. Do not build per-game team selection UI.

## Persistence and Data Lifecycle

Any persistent feature must define and test:

- what is stored and why
- lifespan/retention
- cleanup/pruning of stale data
- account-deletion behavior
- migration/backward compatibility when schemas or supported games change

Do not add database rows, tables, saved runtime state, notifications, chat logs,
tokens, invites, moderation records, or similar data without this lifecycle.

## Server, Web, Desktop, and Mobile Rules

- Server navigation uses `_nav_push`, `_nav_back`, `_nav_refresh`, and
  `_restore_frame`; action handlers should not call `_show_*()` directly.
  The stack remembers the opener item and restores focus on Back/cancel.
  Server-owned menu selections are validated against the active menu before
  dispatch; stale client packets and forged item ids are ignored.
- Use `_enter_input_state(...)` / `server.enter_input_state(...)` for editbox
  input state instead of mutating `_user_states`.
- Reconnect restoration and ghost cleanup must route through centralized restore
  code.
- Web client must never use `innerHTML` with server-controlled content.
- Web speech prefs are `speech_mode`, `speech_voice`, `speech_rate`.
- Mobile speech prefs are `mobile_tts_engine`, `mobile_tts_voice`,
  `mobile_tts_rate`; unavailable synced voices/engines must fall back safely.
- Mobile connects as `client: "mobile"`, is treated as touch, uses SecureStore
  for credentials, AsyncStorage for local prefs, and must enforce mandatory APK
  updates on version/sound-pack mismatch.
- Desktop passwords live only in OS keyring. Saved microphone devices must fall
  back to system default if unavailable.

## New Game Requirements

Files normally required:

- `server/games/<type>/__init__.py`
- `server/games/<type>/game.py`
- optional `server/games/<type>/bot.py`
- `server/locales/en/<type>.ftl`
- `server/locales/vi/<type>.ftl`
- `server/documentation/content/en/games/<type>.md`
- `server/documentation/content/vi/games/<type>.md`
- `server/tests/test_<type>.py`

Also register the game in `server/games/__init__.py`.

Documentation must follow established game docs: escaped markdown bold,
overview, gameplay, special mechanics, scoring, customizable options with
defaults/ranges, and game-specific keyboard shortcuts.

Tests should cover registration/default options, pre-start validation, core
mechanics, scoring/scoreless behavior, bot completion, touch visibility/order,
keybind collisions, sound/TTS paths, transitions, and game completion.

## Code Style

- Module-level imports only, except `main()` in `client/client.py` where CWD
  setup must happen first.
- Prefer existing helpers and local patterns over new abstractions.
- Keep edits scoped; do not refactor unrelated code.
- Game classes: `<Name>Game`; player classes: `<Name>Player`; options:
  `<Name>Options`; type ids lowercase without separators; action ids
  `snake_case`.
- Handler names: `_action_<id>`; visibility: `_is_<id>_hidden`; enabled:
  `_is_<id>_enabled`.
- Use structured parsers/APIs where available; avoid ad-hoc string parsing.
- Update `CLAUDE.md` and `README.md` when catalog counts or user-facing catalog
  data changes.
