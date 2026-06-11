# Phase 2 Design: Centralized Menu Flush

Status: IMPLEMENTED, 2026-06-11. Rory ruled on section 6: Q1 confirmed (no
audible focus reset on same-menu refresh), Q2 no interleaving requirement,
Q3 remove `defer_next_rebuild_to_update`, Q4 rename now and delete the old
names (no aliases). Landed as three commits on main: the content-diff skip,
the recorder/flush conversion + rename, and the docs rewrite.

Deviations from the proposal as written:

- The flush runs at TWO framework-owned points, not one: per table at the
  end of the server tick (as designed), and additionally at the end of every
  `Game.handle_event()`. The event-end flush changes nothing on the wire
  (packets still queue until the tick, and the coalescer plus content-diff
  absorb duplicates) but keeps menu/action-set state synchronous with player
  actions — which the action-input flows and hundreds of tests rely on.
- The API shrank further than proposed: `refresh_menus(player=None)` has no
  focus parameter. `request_menu_focus(player, id)` is the single focus
  mechanism (it also marks the player dirty), replacing the
  focus/focus_player kwargs. "Explicit focus supersedes a queued intent"
  became simply "last writer wins on the per-player slot".
- `_should_rebuild_after_keybind` and its three game overrides (backgammon/
  senet `_nav_skip_rebuild`, blackjack `_suppress_keybind_rebuild`) were
  deleted along with `defer_next_rebuild_to_update`: suppressing repaints to
  protect focus is meaningless when repaints are focus-preserving and no-op
  repaints send no packet.
- One latent assumption surfaced during migration: code that reads its own
  action sets mid-event (e.g. to compute a focus target) now sees them stale
  until the flush; citadels' `_refresh_menus_for_focus` calls its own
  `before_menu_build` first. Documented in CLAUDE.md.
- Measured (scripts/measure_menu_traffic.py, senet bot game with one
  spectator, ~90s of play): menu packets 408 -> 2; builds unchanged at 407
  in this workload (build savings only appear when several repaints coalesce
  in one tick).

Original proposal follows.

Author: Claude (Fable 5), 2026-06-11. Phase 1 (sealed orchestrators) landed on
branch `menu-orchestrator-sealing`.

## 1. What the code actually does today (verified, with citations)

These facts were verified by direct reading, not assumed. Two of them
contradict the current CLAUDE.md doctrine.

### 1.1 The packet verb barely matters; menu identity is what matters

All three clients route `show_menu` and `update_menu` into the same handler
path and apply the same rule (desktop: client/ui/main_window.py:2856-2944;
web: web_client/game.js:2243 treats update as show; mobile:
mobile_client/src/app/PlayAuralApp.tsx:1887 same):

- Same menu_id as currently displayed: in-place diff. Cursor follows the
  focused item by IDENTITY; falls back to clamped index when that id is gone;
  an explicit `selection_id`/`position` overrides. No speech, no sound, no
  announcement happens on receipt of either packet form.
- Different menu_id (or the displayed list was empty): full reset, cursor to
  first item (or explicit position).

Consequence: the documented rule "rebuild_* resets focus, update_* preserves
it" is STALE. A `rebuild_player_menu` of an already-displayed turn_menu does
NOT reset the cursor on any first-party client. Focus resets come from menu
identity changes (turn_menu -> status_box -> turn_menu), from items leaving
the list (the backgammon anchor-break), and from explicit focus directives —
not from the verb. The only real wire difference: the show form carries
`multiletter_enabled`/`escape_behavior` and the update form omits them
(clients preserve existing values on same-id updates, main_window.py:2859-2869).

### 1.2 A packet-level coalescer already exists

server/users/network_user.py:98-158 `get_queued_messages()`: within one flush,
only the LAST menu packet per menu_id survives, and the batch's most recent
explicit focus directive is carried onto the surviving packet. So redundant
repaints inside one tick already collapse to one packet with the right focus.

### 1.3 Everything flushes on the tick, nothing flushes sooner

server/core/tick.py:39-49 ticks every 50ms; server/core/server.py:408-414 runs
`self._tables.on_tick()` then `self._flush_user_messages()` — and that flush
call is the ONLY one in the codebase. Client event handlers (menu selection,
keybinds, editboxes) queue packets that sit until the next tick boundary.
"Immediate" paints (reconnect, server.py:921; system-menu return,
server.py:5029) are immediate only into the queue, not onto the wire.

### 1.4 What is therefore genuinely wasteful or risky today

- BUILD COST: 239 `rebuild_all_menus` call sites (plus the sequence runner
  firing one on every sequence state change,
  server/game_utils/sequence_runner_mixin.py:152). Each call resolves the
  full action set and renders every label through Fluent for every human
  player — even when the coalescer then throws all but one result away.
  CPU-only waste, multiplied on the live server.
- CROSS-TICK NO-OP PACKETS: the coalescer dedups within a tick, but an
  unchanged menu still gets re-sent every time something repaints. Clients
  diff it away silently, but it's bandwidth and client work for nothing.
- VESTIGIAL VERB CHOICE: every call site still picks rebuild_* vs update_*,
  and CLAUDE.md teaches a distinction the clients no longer implement. The
  five-commit deadmanspoker saga was partly people reasoning about a
  difference that doesn't exist on the wire.

## 2. Proposed end state

Game code never paints. The sealed orchestrators RECORD intent; one flush
point per tick BUILDS and SENDS.

- `rebuild_player_menu` / `update_player_menu` / `rebuild_all_menus` /
  `update_all_menus` keep their signatures (zero churn at 297 call sites) but
  become recorders: they mark players dirty and merge any explicit focus into
  the per-player pending-focus slot (phase 1's `_pending_menu_focus`,
  generalized). The rebuild/update distinction dissolves server-side too.
- One flush boundary: in `Server._on_tick`, after `self._tables.on_tick()`
  and before `self._flush_user_messages()`, each table's game flushes its
  dirty set: per dirty player -> `before_menu_build` -> guards
  (`_is_menu_refresh_blocked`) -> `build_menu_items` -> send. Latency change:
  zero (section 1.3).
- Always send the show form (full packet with `multiletter_enabled` /
  `escape_behavior`); clients already treat same-id show as a focus-preserving
  diff (section 1.1).
- CONTENT-DIFF SKIP: NetworkUser compares the built payload against
  `_current_menus[menu_id]` (it already stores the last-sent items,
  network_user.py:250-258). Identical payload + no explicit focus directive =>
  no packet. Tracking is cleared on reconnect and system-menu return so a
  fresh client always gets a full paint.
- Finished games: a dirty flush while `status == "finished"` restores the end
  screen (current rebuild behavior). The content-diff makes repeat restores
  free.
- `defer_next_rebuild_to_update()` (added in phase 1, used only by
  deadmanspoker) becomes meaningless — a plain flush never moves focus — and
  is REMOVED along with its tests. `request_menu_focus` remains and becomes
  the single focus mechanism; an explicit focus argument still supersedes a
  queued intent (used-or-discarded, as pinned by test_menu_sealing.py).

## 3. Why this kills the remaining bug class

- "Forgot to repaint after mutating state": any code path can cheaply mark
  dirty; over-marking costs one set-insert, so the safe habit is also the
  cheap habit. (Later, mutation helpers can auto-mark.)
- "Repainted too much / stole focus": plain flushes never carry focus; only
  explicit intents move the cursor, they live in one slot per player, and
  they fire at most once. The deadmanspoker saga becomes inexpressible.
- "Painted over an overlay": guards run at the single flush point; there is
  no other paint path to forget them on.
- Sequence runner: its blanket repaint per state change becomes a no-op-cheap
  dirty mark, and delayed repaints can no longer jump the cursor.

## 4. Migration plan (each step lands green and independently revertable)

1. CONTENT-DIFF SKIP in NetworkUser + tracking clear on reconnect/system
   return. No game-visible change; pure packet reduction. (Smallest, safest,
   immediately measurable.)
2. RECORDER + FLUSH: convert the sealed orchestrators to dirty-marking;
   add `Game.flush_menus()`; call it from `Server._on_tick` per table.
   Out-of-game paint sites (reconnect, join, system-menu return) keep calling
   the same orchestrators — their marks flush within <=50ms, same as today's
   wire behavior. The sequence runner's repaint becomes a mark.
3. REMOVE `defer_next_rebuild_to_update` and the deadmanspoker call; update
   phase-1 tests.
4. DOCS: rewrite CLAUDE.md's "Menu Focus on Refresh and Turn Transitions" —
   the rebuild-vs-update doctrine is stale; the real rules are menu identity,
   item persistence, and explicit focus intents.
5. MEASURE: before/after profile of a bot-heavy senet/backgammon game
   (builds per tick, packets per minute) to confirm the build-cost claim and
   give the optimization a number.

## 5. Risks and mitigations

- PACKET REORDERING: menu packets will now always queue at end-of-tick, after
  any speech/sound queued by the same event. Clients don't speak menus on
  receipt, so the audible difference is limited to per-item highlight-sound
  timing on explicit focus jumps (desktop/web play the focused item's sound).
  Mitigation: none needed in theory; playtest explicit-focus flows (ninetynine
  draw, deadmanspoker exchange, sorry move slots) to confirm by ear.
- HIDDEN INTRA-TICK SEQUENCING: any game that mutates state, repaints, mutates
  again, and repaints within ONE event and relies on the client seeing both
  intermediate states is already broken today (the coalescer keeps only the
  last packet). The flush makes this de-jure; no known game does it.
- STALE TRACKING => SKIPPED REPAINT: if `_current_menus` ever disagrees with
  what the client shows, the content-diff would wrongly skip. Mitigation:
  tracking cleared on reconnect and on every cross-menu transition (those are
  full show paths anyway); the skip applies only to same-id refreshes.
- TESTS THAT COUNT PACKETS: tests asserting "exactly N menu messages" may see
  fewer after the diff-skip and will be updated to assert the surviving
  content, which is the better assertion anyway.

## 6. Open questions for Rory (the design holds on any answer; these are calls only you can make)

- Q1 (you are the oracle): from your NVDA time on the live build — does any
  same-menu in-play refresh audibly reset or re-announce focus today? The
  code says no on all three clients; if your ears agree, the stale-doctrine
  claim is confirmed and step 4's doc rewrite proceeds.
- Q2 (audio UX): is there any flow where a menu repaint must interleave
  BETWEEN two sounds/speech within a single 50ms tick? I found none, and the
  per-flush coalescer already forbids it in practice, but you know the
  cinematic flows better than the code does.
- Q3 (API hygiene): OK to remove `defer_next_rebuild_to_update()` one phase
  after shipping it? It was faithful absorption of deadmanspoker's flag in
  phase 1; phase 2 reveals the whole mechanism is vestigial. Alternative is
  to keep it as a deprecated no-op.
- Q4 (naming): with the verb distinction dead, do you want a single
  `refresh_menus(...)` name now (old names kept as sealed aliases), or defer
  renaming until the dust settles?
