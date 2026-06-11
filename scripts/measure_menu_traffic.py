"""Measure menu build cost and packet traffic for a bot-heavy game.

Phase 2 of the centralized-menu-flush work promises a measurable drop in
redundant menu builds and no-op menu packets. This script provides the
number: it runs a senet game with two bots and one human spectator (the
live-server hot case) for a fixed number of ticks, simulating the server's
per-tick packet flush, and reports:

- builds:   calls to MenuManagementMixin.build_menu_items (action resolution
            + Fluent label rendering; the CPU cost)
- paints:   menu packets queued by NetworkUser (post any content-diff skip)
- sent:     menu packets that survive get_queued_messages coalescing (the
            wire cost)

Run from the repo root, before and after a change:
    python scripts/measure_menu_traffic.py
"""

import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from server.games.senet.game import SenetGame, SenetOptions
from server.messages.localization import Localization
from server.users.bot import Bot
from server.users.network_user import NetworkUser

TICKS = 2000
SEED = 421

Localization.init(Path(__file__).parent.parent / "server" / "locales")


def main() -> None:
    random.seed(SEED)

    counts = {"builds": 0, "paints": 0, "sent": 0}

    original_build = SenetGame.build_menu_items

    def counting_build(self, player, user):
        counts["builds"] += 1
        return original_build(self, player, user)

    SenetGame.build_menu_items = counting_build

    game = SenetGame(options=SenetOptions())
    game.setup_keybinds()
    game.add_player("Bot Alpha", Bot("Bot Alpha"))
    game.add_player("Bot Beta", Bot("Bot Beta"))
    watcher = NetworkUser("Watcher", "en", connection=None)
    game.add_spectator("Watcher", watcher)
    game.host = "Bot Alpha"
    game.on_start()

    ticks_run = 0
    for _ in range(TICKS):
        if game.status == "finished":
            break
        game.on_tick()
        if hasattr(game, "flush_menus"):
            game.flush_menus()
        queued = watcher._message_queue
        counts["paints"] += sum(1 for p in queued if p.get("type") == "menu")
        sent = watcher.get_queued_messages()
        counts["sent"] += sum(1 for p in sent if p.get("type") == "menu")
        ticks_run += 1

    SenetGame.build_menu_items = original_build

    print(f"ticks run:            {ticks_run}")
    print(f"game status:          {game.status}")
    print(f"menu builds:          {counts['builds']}")
    print(f"menu packets queued:  {counts['paints']}")
    print(f"menu packets sent:    {counts['sent']}")
    for label, value in counts.items():
        print(f"{label} per second of play: {value / (ticks_run / 20):.2f}")


if __name__ == "__main__":
    main()
