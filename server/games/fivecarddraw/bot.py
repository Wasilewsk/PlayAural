"""Bot strategy for Five Card Draw."""

from __future__ import annotations

from collections import Counter
from typing import TYPE_CHECKING

from ...game_utils.poker_evaluator import best_hand

if TYPE_CHECKING:
    from ...game_utils.cards import Card
    from .game import FiveCardDrawGame, FiveCardDrawPlayer


STRAIGHT_RANK_SETS = [
    {14, 2, 3, 4, 5},
    *[set(range(low, low + 5)) for low in range(2, 11)],
]


def bot_think(game: "FiveCardDrawGame", player: "FiveCardDrawPlayer") -> str | None:
    if game.current_player != player:
        return None
    if game.phase == "draw":
        player.to_discard = _choose_discards(game, player)
        return "draw_cards"
    if not game.betting:
        return None
    return _decide_bet(game, player)


def _choose_discards(
    game: "FiveCardDrawGame",
    player: "FiveCardDrawPlayer",
) -> set[int]:
    if len(player.hand) != 5:
        return set()

    score, _ = best_hand(player.hand)
    category = score[0]
    ranks = [_rank_value(card) for card in player.hand]
    counts = Counter(ranks)

    if category >= 4:
        return set()
    if category == 3:
        return {index for index, rank in enumerate(ranks) if counts[rank] != 3}
    if category == 2:
        return {index for index, rank in enumerate(ranks) if counts[rank] != 2}
    if category == 1:
        return {index for index, rank in enumerate(ranks) if counts[rank] != 2}

    flush_discard = _four_card_flush_discard(player.hand)
    if flush_discard is not None:
        return {flush_discard}

    straight_discard = _four_card_straight_discard(ranks)
    if straight_discard is not None:
        return {straight_discard}

    if game.options.draw_limit == "four_with_ace" and 14 in ranks:
        ace_index = ranks.index(14)
        return {index for index in range(5) if index != ace_index}

    keep = set(sorted(range(5), key=lambda index: ranks[index], reverse=True)[:2])
    return {index for index in range(5) if index not in keep}


def _four_card_flush_discard(hand: list["Card"]) -> int | None:
    suit_counts = Counter(card.suit for card in hand)
    flush_suit = next((suit for suit, count in suit_counts.items() if count == 4), None)
    if flush_suit is None:
        return None
    return next(index for index, card in enumerate(hand) if card.suit != flush_suit)


def _four_card_straight_discard(ranks: list[int]) -> int | None:
    candidates: list[tuple[int, int, int]] = []
    for discard_index in range(5):
        kept = {rank for index, rank in enumerate(ranks) if index != discard_index}
        if len(kept) != 4:
            continue
        outs = sum(1 for sequence in STRAIGHT_RANK_SETS if kept < sequence)
        if outs:
            candidates.append((outs, sum(kept), discard_index))
    if not candidates:
        return None
    return max(candidates)[2]


def _decide_bet(game: "FiveCardDrawGame", player: "FiveCardDrawPlayer") -> str:
    if not game.betting or len(player.hand) != 5:
        return "call"

    score, _ = best_hand(player.hand)
    category, tiebreakers = score
    to_call = game.betting.amount_to_call(player.id)
    pot_after_call = game.pot_manager.total_pot() + to_call
    pot_odds = to_call / max(1, pot_after_call)
    can_raise = game._can_make_full_raise(player)
    final_round = game.current_bet_round == 2

    if to_call == 0:
        if can_raise and (category >= 2 or (final_round and category == 1)):
            return "raise"
        return "call"

    if category >= 6 and player.chips <= game.pot_manager.total_pot():
        if game._is_all_in_enabled(player) is None:
            return "all_in"
    if category >= 4:
        return "raise" if can_raise and pot_odds <= 0.35 else "call"
    if category == 3:
        return "raise" if can_raise and pot_odds <= 0.25 else "call"
    if category == 2:
        if can_raise and final_round and pot_odds <= 0.2:
            return "raise"
        return "call" if pot_odds <= 0.5 else "fold"
    if category == 1:
        pair_rank = tiebreakers[0]
        threshold = 0.32 if pair_rank >= 11 or final_round else 0.24
        return "call" if pot_odds <= threshold else "fold"

    drawing_to_strong_hand = len(_choose_discards(game, player)) == 1
    threshold = 0.18 if not final_round and drawing_to_strong_hand else 0.1
    return "call" if pot_odds <= threshold else "fold"


def _rank_value(card: "Card") -> int:
    return 14 if card.rank == 1 else card.rank
