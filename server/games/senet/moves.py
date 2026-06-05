"""Move generation and application for Senet."""

from __future__ import annotations

from dataclasses import dataclass

from .state import (
    SenetGameState,
    NUM_SQUARES,
    HOUSE_HAPPINESS,
    HOUSE_WATER,
    EXACT_BEAROFF,
    SAFE_SQUARES,
    find_rebirth_square,
    has_blocking_line,
    is_protected,
    opponent_num,
)


@dataclass(frozen=True)
class SenetMove:
    source: int  # 0-29
    destination: int  # 0-29, or 30 for bear off
    is_swap: bool = False
    is_bear_off: bool = False
    water_dest: int | None = None  # Actual landing square when hitting water


def generate_legal_moves(
    state: SenetGameState, player_num: int, roll: int
) -> list[SenetMove]:
    """Generate all legal moves for a player given a stick throw result."""
    moves: list[SenetMove] = []
    opp = opponent_num(player_num)

    for src in range(NUM_SQUARES):
        if state.board[src] != player_num:
            continue

        # Locked squares: only exact bear-off allowed
        if src in EXACT_BEAROFF:
            if roll == EXACT_BEAROFF[src]:
                moves.append(SenetMove(source=src, destination=30, is_bear_off=True))
            continue

        target = src + roll

        # House of Happiness gate: pieces before it cannot jump over it
        if src < HOUSE_HAPPINESS and target > HOUSE_HAPPINESS:
            continue

        # Off the end of the board — only locked squares can bear off
        if target >= NUM_SQUARES:
            continue

        # 3+ consecutive opponent pieces block passage
        if has_blocking_line(state.board, src, target, player_num):
            continue

        occupant = state.board[target]

        if occupant == player_num:
            # Cannot land on own piece
            continue

        if occupant == opp:
            # Cannot capture protected pieces or pieces on safe squares
            if is_protected(state.board, target) or target in SAFE_SQUARES:
                continue
            # Swap move
            if target == HOUSE_WATER:
                # Swapping onto water: our piece goes to rebirth, opponent goes to source
                # Actually, the swap happens first (opponent to source), then we land on water
                # and get sent to rebirth. Treat as swap with water redirect.
                water_landing = find_rebirth_square(state.board)
                moves.append(
                    SenetMove(
                        source=src,
                        destination=target,
                        is_swap=True,
                        water_dest=water_landing,
                    )
                )
            else:
                moves.append(SenetMove(source=src, destination=target, is_swap=True))

        else:
            # Empty square
            if target == HOUSE_WATER:
                water_landing = find_rebirth_square(state.board)
                moves.append(
                    SenetMove(source=src, destination=target, water_dest=water_landing)
                )
            else:
                moves.append(SenetMove(source=src, destination=target))

    return moves


def apply_move(state: SenetGameState, move: SenetMove, player_num: int) -> None:
    """Apply a move to the game state (mutates in place)."""
    opp = opponent_num(player_num)

    # Remove piece from source
    state.board[move.source] = 0

    if move.is_bear_off:
        state.off[player_num] += 1
        return

    if move.is_swap:
        # Opponent piece goes to where we came from
        state.board[move.destination] = 0
        state.board[move.source] = opp

    # Place our piece at the effective destination
    if move.water_dest is not None:
        state.board[move.water_dest] = player_num
    else:
        state.board[move.destination] = player_num


def has_any_legal_move(state: SenetGameState, player_num: int, roll: int) -> bool:
    return len(generate_legal_moves(state, player_num, roll)) > 0
