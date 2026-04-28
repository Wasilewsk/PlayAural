"""Bot AI for Dead Man's Deck."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .game import DeadMansDeckCard, DeadMansDeckGame, DeadMansDeckPlayer


# Duplicated to keep bot.py independent from game.py at runtime and avoid
# circular imports while game.py imports bot_think.
RANK_JOKER = "joker"
PHASE_PLAYING = "playing"
MAX_CLAIM_CARDS = 3
CHAMBER_COUNT = 6
DECK_COUNTS = {
    "ace": 6,
    "king": 6,
    "queen": 6,
    RANK_JOKER: 2,
}


def bot_think(game: "DeadMansDeckGame", player: "DeadMansDeckPlayer") -> str | None:
    """Return the next legal bot action."""
    if game.phase != PHASE_PLAYING or player.eliminated:
        return None

    if game.last_claim and game.last_claim.player_id != player.id:
        if _should_challenge(game, player):
            return "call_liar"

    if not player.hand:
        return None

    player.selected_card_ids = [card.id for card in _choose_cards(game, player)]
    return "play_selected"


def _should_challenge(
    game: "DeadMansDeckGame",
    player: "DeadMansDeckPlayer",
) -> bool:
    if not game.last_claim:
        return False

    truthful_in_hand = sum(
        1 for card in player.hand if card.rank in {game.target_rank, RANK_JOKER}
    )
    possible_truthful_cards = DECK_COUNTS[game.target_rank] + DECK_COUNTS[RANK_JOKER]
    if truthful_in_hand + game.last_claim.count > possible_truthful_cards:
        return True

    base = {1: 0.10, 2: 0.22, 3: 0.38}.get(game.last_claim.count, 0.20)
    base += min(0.20, truthful_in_hand * 0.04)
    remaining_chambers = max(1, CHAMBER_COUNT - player.chamber_index)
    if remaining_chambers <= 2:
        base -= 0.12
    return random.random() < max(0.03, min(0.65, base))  # nosec B311


def _choose_cards(
    game: "DeadMansDeckGame",
    player: "DeadMansDeckPlayer",
) -> list["DeadMansDeckCard"]:
    truthful = [
        card for card in player.hand if card.rank in {game.target_rank, RANK_JOKER}
    ]
    bluff = [
        card for card in player.hand if card.rank not in {game.target_rank, RANK_JOKER}
    ]
    wants_truth = bool(truthful) and random.random() < 0.68  # nosec B311
    source = truthful if wants_truth else player.hand

    if not wants_truth and bluff:
        source = bluff if random.random() < 0.65 else player.hand  # nosec B311

    count = random.randint(1, min(MAX_CLAIM_CARDS, len(source)))  # nosec B311
    return random.sample(source, count)  # nosec B311
