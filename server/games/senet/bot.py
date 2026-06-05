"""Bot AI for Senet."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from .moves import SenetMove, generate_legal_moves
from .state import (
    HOUSE_HAPPINESS,
    HOUSE_WATER,
    SAFE_SQUARES,
    is_protected,
    opponent_num,
)

if TYPE_CHECKING:
    from .game import SenetGame, SenetPlayer


def bot_think(game: SenetGame, player: SenetPlayer) -> str | None:
    gs = game.game_state
    if gs.current_player_num != player.player_num:
        return None

    if gs.turn_phase == "throwing":
        return "sq_0"  # Any square click triggers a throw

    if gs.turn_phase == "moving":
        return _pick_move(game, player)

    return None


def _pick_move(game: SenetGame, player: SenetPlayer) -> str | None:
    gs = game.game_state
    moves = generate_legal_moves(gs, player.player_num, gs.current_roll)
    if not moves:
        return None

    difficulty = game.options.bot_difficulty
    if difficulty == "random":
        move = random.choice(moves)  # nosec B311
    else:
        move = max(moves, key=lambda m: _score_move(gs, m, player.player_num))

    return f"sq_{move.source}"


def _score_move(gs, move: SenetMove, player_num: int) -> int:
    """Heuristic score for a move. Higher is better."""
    score = 0
    opp = opponent_num(player_num)

    if move.is_bear_off:
        score += 200

    # Landing on House of Happiness (mandatory stop — good to get it done)
    if move.destination == HOUSE_HAPPINESS:
        score += 100

    if move.is_swap:
        score += 80
        # Extra value if opponent gets sent far back via water
        if move.water_dest is not None:
            score += 30

    # Landing on a safe square
    if move.destination in SAFE_SQUARES:
        score += 60

    # Forming or extending a protective pair at the destination
    # Exclude the source square since that piece is the one moving
    if not move.is_bear_off and move.destination < 30:
        board = gs.board
        dest = move.water_dest if move.water_dest is not None else move.destination
        if dest > 0 and board[dest - 1] == player_num and (dest - 1) != move.source:
            score += 50
        if dest < 29 and board[dest + 1] == player_num and (dest + 1) != move.source:
            score += 50

    # Penalty for breaking own protection at source
    board = gs.board
    src = move.source
    # Check if leaving source breaks a pair
    if src > 0 and board[src - 1] == player_num:
        score -= 40
    if src < 29 and board[src + 1] == player_num:
        score -= 40

    # Penalty for landing alone near opponent pieces
    if not move.is_bear_off and move.destination < 30:
        dest = move.water_dest if move.water_dest is not None else move.destination
        if dest not in SAFE_SQUARES:
            nearby_opponents = sum(
                1 for i in range(max(0, dest - 3), min(30, dest + 4))
                if board[i] == opp
            )
            if nearby_opponents > 0:
                score -= 15 * nearby_opponents

    # General advancement tiebreaker
    score += move.source

    return score
