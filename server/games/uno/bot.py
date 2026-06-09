"""Bot AI for UNO.

`bot_think_turn` drives the current player (via BotHelper.on_tick).
`bot_think_out_of_turn` drives non-current bots (UNO call-out now; interceptions
and straights are added in Phase 3) via per-bot BotHelper.process_bot_action.
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from . import cards
from .cards import UnoCard

if TYPE_CHECKING:
    from .game import UnoGame, UnoPlayer


def bot_choose_color(game: "UnoGame", player: "UnoPlayer") -> int:
    """Pick the color the bot holds most of (random if none)."""
    counts = {cards.RED: 0, cards.YELLOW: 0, cards.GREEN: 0, cards.BLUE: 0}
    for c in player.hand:
        if c.color in counts:
            counts[c.color] += 1
    best = max(counts.items(), key=lambda kv: kv[1])
    if best[1] == 0:
        return random.choice(cards.COLORS)
    return best[0]


def _evaluate_card(game: "UnoGame", player: "UnoPlayer", card: UnoCard) -> int:
    """Heuristic value of playing a card (higher = more attractive)."""
    score = 0
    hand = player.hand

    # With two cards, favor matching your other card's color.
    if len(hand) == 2:
        other = next((c for c in hand if c is not card), None)
        if other and card.color == other.color and card.color != cards.WILD:
            score += 1000

    score += cards.card_points(card) * 10

    if card.type in (cards.SKIP, cards.REVERSE):
        score += 100
    elif card.type == cards.DRAW_TWO:
        score += 150

    if card.type in cards.WILD_TYPES:
        score += 500 if len(hand) == 1 else -500

    if card.color == game.current_color and card.color != cards.WILD:
        score += 50

    # Hold onto a dominant color unless necessary.
    counts = {c: 0 for c in cards.COLORS}
    for c in hand:
        if c.color in counts:
            counts[c.color] += 1
    if card.color in counts and counts[card.color] >= 3 and counts[card.color] == max(counts.values()):
        score -= 30
    return score


def _choose_play(game: "UnoGame", player: "UnoPlayer") -> str | None:
    playable = [c for c in player.hand if game._is_card_playable(c)]
    if not playable:
        return None
    best = max(playable, key=lambda c: _evaluate_card(game, player, c))
    return f"play_card_{best.id}"


def _choose_swap_target(game: "UnoGame", player: "UnoPlayer") -> str | None:
    others = [p for p in game.alive_players if p.id != player.id]
    if not others:
        return None
    target = min(others, key=lambda p: len(p.hand))
    return f"swap_target_{target.id}"


def bot_think_turn(game: "UnoGame", player: "UnoPlayer") -> str | None:
    """Decision for the current player."""
    # Seven-swap target selection.
    if game.awaiting_swap_target and game.swap_player_id == player.id:
        return _choose_swap_target(game, player)

    # Choosing a wild color.
    if game.awaiting_wild_color and game.wild_color_player_id == player.id:
        return cards.color_action_id(bot_choose_color(game, player))

    if (
        game._is_wild_locked()
        or game.awaiting_swap_target
        or game.hand_wait_ticks > 0
        or game.intro_wait_ticks > 0
    ):
        return None
    if game.current_player != player:
        return None

    # Resolving a pending draw obligation (stack / challenge / accept).
    if game.cards_to_draw > 0:
        if game.bluff_challenge_available and random.random() < 0.3:
            return "bluff_challenge"
        play = _choose_play(game, player)  # only valid response cards are playable
        if play:
            return play
        return "draw"

    # After a draw, play the drawn card if it is playable (no pass exists).
    if player.turn_has_drawn:
        return _choose_play(game, player)

    play = _choose_play(game, player)
    if play:
        return play
    if game._can_draw(player):
        return "draw"
    # Nothing to do; the engine auto-skips a stuck player.
    return None


def bot_think_out_of_turn(game: "UnoGame", player: "UnoPlayer") -> str | None:
    """Decision for a bot when it is not the current player.

    Phase 1: announce a forgotten UNO and call out opponents who forgot theirs.
    Phase 3 extends this to interceptions and straights.
    """
    if player.is_spectator or player not in game.alive_players:
        return None

    # Choosing a seven-swap target after playing a seven out of turn (straight).
    if game.awaiting_swap_target and game.swap_player_id == player.id:
        return _choose_swap_target(game, player)

    # Continue a straight run we started.
    if game.options.straights and game.last_player_id == player.id:
        for c in player.hand:
            if game._oot_kind(player, c) == "straight":
                if random.random() < 0.95:
                    return f"play_card_{c.id}"

    # Intercept an exact match out of turn.
    if game.options.interceptions or game.options.super_interceptions:
        for c in player.hand:
            if game._oot_kind(player, c) in ("interception", "super"):
                if random.random() < 0.9:
                    return f"play_card_{c.id}"

    # Announce our own UNO if we forgot it.
    if len(player.hand) == 1 and not player.said_uno:
        return "uno"

    # Call out an opponent sitting in their open window.
    target = game._callable_target(player)
    if target and random.random() < 0.7:
        return "uno"

    return None
