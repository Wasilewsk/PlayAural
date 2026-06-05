"""Serializable state models for Senet."""

from dataclasses import dataclass, field
import random


NUM_SQUARES = 30
PIECES_PER_PLAYER = 5

# Special square indices (0-based)
HOUSE_REBIRTH = 14  # Square 15
HOUSE_HAPPINESS = 25  # Square 26 — mandatory stop
HOUSE_WATER = 26  # Square 27 — sends piece to rebirth
HOUSE_THREE_TRUTHS = 27  # Square 28
HOUSE_RE_ATUM = 28  # Square 29

# Squares where pieces require an exact roll to bear off
EXACT_BEAROFF = {27: 3, 28: 2, 29: 1}

# Squares where pieces cannot be captured
SAFE_SQUARES = frozenset({HOUSE_THREE_TRUTHS, HOUSE_RE_ATUM, 29})

# Locale keys for special square names
SPECIAL_SQUARE_NAMES = {
    HOUSE_REBIRTH: "senet-house-rebirth",
    HOUSE_HAPPINESS: "senet-house-happiness",
    HOUSE_WATER: "senet-house-water",
    HOUSE_THREE_TRUTHS: "senet-house-three-truths",
    HOUSE_RE_ATUM: "senet-house-re-atum",
}


@dataclass
class SenetGameState:
    """Serializable game state for Senet."""

    board: list[int] = field(default_factory=lambda: [0] * NUM_SQUARES)
    # off[0] unused, off[1] = player 1, off[2] = player 2
    off: list[int] = field(default_factory=lambda: [0, 0, 0])
    current_player_num: int = 1
    turn_phase: str = "throwing"  # "throwing" | "moving"
    current_roll: int = 0  # 1-5, or 0 if not yet thrown
    bonus_turn: bool = False
    throws_this_turn: int = 0


def opponent_num(player_num: int) -> int:
    return 3 - player_num


def build_initial_state() -> SenetGameState:
    """Build starting state with pieces interleaved on squares 1-10."""
    state = SenetGameState()
    for i in range(10):
        state.board[i] = 1 if i % 2 == 0 else 2
    return state


def throw_sticks(rng: random.Random | None = None) -> tuple[int, bool]:
    """Throw 4 sticks. Returns (movement_value, grants_bonus_turn).

    Each stick lands colored-side-up or black-side-up with equal probability.
    """
    r = rng or random
    colored_up = sum(r.randint(0, 1) for _ in range(4))  # nosec B311
    if colored_up == 0:
        return (5, True)
    elif colored_up == 1:
        return (1, True)
    elif colored_up == 2:
        return (2, False)
    elif colored_up == 3:
        return (3, False)
    else:
        return (4, True)


def is_protected(board: list[int], index: int) -> bool:
    """Check if the piece at index has an adjacent ally (2+ group)."""
    piece = board[index]
    if piece == 0:
        return False
    if index > 0 and board[index - 1] == piece:
        return True
    if index < NUM_SQUARES - 1 and board[index + 1] == piece:
        return True
    return False


def has_blocking_line(board: list[int], from_idx: int, to_idx: int, player_num: int) -> bool:
    """Check if 3+ consecutive opponent pieces block the path between from and to."""
    opp = opponent_num(player_num)
    consecutive = 0
    for i in range(from_idx + 1, to_idx):
        if board[i] == opp:
            consecutive += 1
            if consecutive >= 3:
                return True
        else:
            consecutive = 0
    return False


def find_rebirth_square(board: list[int]) -> int:
    """Find the rebirth destination: square 15 if empty, else first empty before it."""
    if board[HOUSE_REBIRTH] == 0:
        return HOUSE_REBIRTH
    for i in range(HOUSE_REBIRTH - 1, -1, -1):
        if board[i] == 0:
            return i
    # Extremely unlikely: all squares before 15 occupied. Fall back to first empty anywhere.
    for i in range(HOUSE_REBIRTH + 1, NUM_SQUARES):
        if board[i] == 0:
            return i
    return HOUSE_REBIRTH  # Should never happen in a valid game


def pieces_remaining(state: SenetGameState, player_num: int) -> int:
    """Count pieces still on the board for a player."""
    return sum(1 for sq in state.board if sq == player_num)
