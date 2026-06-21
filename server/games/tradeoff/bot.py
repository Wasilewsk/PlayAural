"""
Bot AI logic for Tradeoff game.
"""

from typing import TYPE_CHECKING

from .scoring import find_best_scoring

if TYPE_CHECKING:
    from .game import TradeoffGame, TradeoffPlayer


def bot_think_trading(game: "TradeoffGame", player: "TradeoffPlayer") -> str | None:
    """
    Trading-phase AI.

    Strategy: keep dice that improve the current hand's set or straight
    potential; trade isolated dice back into the pool.

    All dice start marked for trading, so the bot toggles each desired-keep
    die off the trade list one at a time, then confirms.
    """
    if player.trades_confirmed:
        return None

    desired_keeps = _select_keep_indices(player.hand, player.rolled_dice)

    toggle_action = _next_trade_toggle(player.trading_indices, desired_keeps)
    if toggle_action:
        return toggle_action

    return "confirm_trades"


def bot_think_taking(game: "TradeoffGame", player: "TradeoffPlayer") -> str | None:
    """
    Taking-phase AI.

    Strategy: pick the pool die that most improves immediate score and near-set
    potential for the hand being built this round.
    """
    if game.taking_index >= len(game.taking_order):
        return None
    if game.taking_order[game.taking_index] != player.id:
        return None
    if player.dice_taken_count >= player.dice_traded_count:
        return None

    pool_counts = _count_dice(game.pool)
    best_value = _select_best_pool_value(player.hand, pool_counts)
    return f"take_{best_value}" if best_value is not None else None


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _count_dice(values: list[int]) -> dict[int, int]:
    counts: dict[int, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return counts


def _score_sets(values: list[int]) -> int:
    return sum(points for _, _, points in find_best_scoring(values))


def _straight_pressure(values: list[int], value: int) -> float:
    unique = set(values)
    pressure = 0.0
    for run in ([1, 2, 3, 4], [2, 3, 4, 5], [3, 4, 5, 6]):
        if value in run:
            present = sum(1 for die in run if die in unique)
            if present >= 3:
                pressure += present * 0.8
    for run in ([1, 2, 3, 4, 5], [2, 3, 4, 5, 6]):
        if value in run:
            present = sum(1 for die in run if die in unique)
            if present >= 4:
                pressure += present * 1.2
    return pressure


def _value_potential(values: list[int], value: int) -> float:
    counts = _count_dice(values)
    count = counts.get(value, 0)
    score = _score_sets(values) * 4.0
    if count >= 5:
        score += 18
    elif count == 4:
        score += 10
    elif count == 3:
        score += 8
    elif count == 2:
        score += 3
    score += _straight_pressure(values, value)
    return score


def _select_keep_indices(hand: list[int], rolled_dice: list[int]) -> list[int]:
    """Return rolled-die indices worth locking into the hand."""
    desired_keeps: list[int] = []
    combined = list(hand) + list(rolled_dice)
    for index, value in enumerate(rolled_dice):
        without_die = list(combined)
        without_die.remove(value)
        marginal = _value_potential(combined, value) - _value_potential(
            without_die, value
        )
        if marginal >= 2.5:
            desired_keeps.append(index)
    return desired_keeps


def _next_trade_toggle(trading_indices: list[int], desired_keeps: list[int]) -> str | None:
    """Return the next toggle action needed to remove a keep-die from the trade list."""
    for index in desired_keeps:
        if index in trading_indices:
            return f"toggle_trade_{index}"
    return None


def _select_best_pool_value(
    hand: list[int], pool_counts: dict[int, int]
) -> int | None:
    """Pick the pool die value that best matches the existing hand."""
    best_value = None
    best_score: tuple[float, int, int] | None = None
    for value, count in sorted(pool_counts.items()):
        if count <= 0:
            continue
        candidate = list(hand) + [value]
        score = (
            _value_potential(candidate, value),
            count,
            -value,
        )
        if best_score is None or score > best_score:
            best_score = score
            best_value = value
    return best_value
