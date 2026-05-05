"""Bot AI for Dead Man's Deck."""

from __future__ import annotations

from math import comb
import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .game import DeadMansDeckCard, DeadMansDeckGame, DeadMansDeckPlayer


# Duplicated to keep bot.py independent from game.py at runtime and avoid
# circular imports while game.py imports bot_think.
RANK_JOKER = "joker"
PHASE_PLAYING = "playing"
MAX_CLAIM_CARDS = 3
HAND_SIZE = 5
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
        if _must_challenge_to_avoid_forced_false_finish(game, player):
            return "call_liar"
        if _should_challenge(game, player):
            return "call_liar"

    if not player.hand:
        return None

    chosen_cards = _choose_cards(game, player)
    if not chosen_cards:
        return None
    player.selected_card_ids = [card.id for card in chosen_cards]
    return "play_selected"


def _should_challenge(
    game: "DeadMansDeckGame",
    player: "DeadMansDeckPlayer",
) -> bool:
    if not game.last_claim:
        return False

    truthful_in_hand = _truthful_count(player.hand, game.target_rank)
    possible_truthful_cards = DECK_COUNTS[game.target_rank] + DECK_COUNTS[RANK_JOKER]
    if truthful_in_hand + game.last_claim.count > possible_truthful_cards:
        return True

    bluff_probability = 1.0 - _estimated_truth_probability(
        game,
        player,
        truthful_in_hand,
    )
    probability = _challenge_probability(
        game,
        player,
        bluff_probability,
        _challenge_threshold(game, player, truthful_in_hand),
        truthful_in_hand,
    )
    return random.random() < probability  # nosec B311


def _estimated_truth_probability(
    game: "DeadMansDeckGame",
    player: "DeadMansDeckPlayer",
    truthful_in_hand: int,
) -> float:
    claim = game.last_claim
    if not claim or claim.count <= 0:
        return 1.0

    possible_truthful_cards = DECK_COUNTS[game.target_rank] + DECK_COUNTS[RANK_JOKER]
    unknown_truthful = max(0, possible_truthful_cards - truthful_in_hand)
    unknown_total = max(0, sum(DECK_COUNTS.values()) - len(player.hand))
    if claim.count > unknown_total:
        return 0.0
    if claim.count > unknown_truthful:
        return 0.0
    if unknown_total == 0:
        return 0.0
    return comb(unknown_truthful, claim.count) / comb(unknown_total, claim.count)


def _challenge_threshold(
    game: "DeadMansDeckGame",
    player: "DeadMansDeckPlayer",
    truthful_in_hand: int,
) -> float:
    claim = game.last_claim
    alive_count = max(2, len(game.alive_players))
    threshold = 0.58

    if alive_count == 2:
        threshold -= 0.07
    elif alive_count >= 4:
        threshold += 0.04

    if claim:
        threshold -= {1: 0.00, 2: 0.04, 3: 0.09}.get(claim.count, 0.05)
        accused = game.get_player_by_id(claim.player_id)
        if accused and not getattr(accused, "hand", []):
            threshold -= 0.12

    if truthful_in_hand == 0:
        threshold -= 0.10
    elif truthful_in_hand >= 3:
        threshold -= 0.05

    if len(player.hand) <= 2:
        threshold -= 0.06

    threshold += _roulette_risk(player) * 0.16
    return max(0.35, min(0.86, threshold))


def _challenge_probability(
    game: "DeadMansDeckGame",
    player: "DeadMansDeckPlayer",
    bluff_probability: float,
    threshold: float,
    truthful_in_hand: int,
) -> float:
    claim = game.last_claim
    alive_count = len(game.alive_players)
    margin = bluff_probability - threshold

    if margin <= -0.20:
        probability = 0.04
    elif margin >= 0.40:
        probability = 0.82
    else:
        probability = 0.04 + ((margin + 0.20) / 0.60) * 0.78

    if claim and _is_opening_claim(game):
        patience = {1: 0.25, 2: 0.45, 3: 0.62}.get(claim.count, 0.50)
        if alive_count >= 3:
            patience += 0.10
        probability *= min(0.85, patience)
        if claim.count == 3 and truthful_in_hand >= 4:
            probability += 0.10
    else:
        if alive_count == 2:
            probability += 0.06
        elif alive_count >= 4:
            probability -= 0.04

    if claim:
        accused = game.get_player_by_id(claim.player_id)
        if accused and not getattr(accused, "hand", []):
            probability += 0.18

    risk = _roulette_risk(player)
    if risk >= 0.5:
        probability *= 0.70
    elif risk <= (1.0 / CHAMBER_COUNT):
        probability *= 1.08

    if len(player.hand) <= 2:
        probability += 0.05

    return max(0.02, min(0.94, probability))


def _choose_cards(
    game: "DeadMansDeckGame",
    player: "DeadMansDeckPlayer",
) -> list["DeadMansDeckCard"]:
    truthful = _truthful_cards(player.hand, game.target_rank)
    bluffs = _bluff_cards(player.hand, game.target_rank)
    alive_count = len(game.alive_players)

    if _truthful_finish_is_available(game, player, truthful):
        return truthful[: len(player.hand)]

    if _should_preserve_truthful_exit(game, player, truthful, bluffs, alive_count):
        return [_choose_low_value_bluff(bluffs)]

    if not truthful:
        return _choose_bluff_claim(game, player, bluffs)

    if not bluffs:
        return _choose_truthful_claim(game, player, truthful)

    if len(player.hand) <= MAX_CLAIM_CARDS and _would_force_challenge_after_play(
        game,
        player,
        len(player.hand),
    ):
        return _choose_mixed_hand_safe_claim(game, player, truthful, bluffs)

    if _should_bluff_with_mixed_hand(game, player, truthful, bluffs, alive_count):
        return [_choose_low_value_bluff(bluffs)]

    return _choose_truthful_claim(game, player, truthful)


def _truthful_finish_is_available(
    game: "DeadMansDeckGame",
    player: "DeadMansDeckPlayer",
    truthful: list["DeadMansDeckCard"],
) -> bool:
    return (
        len(player.hand) <= MAX_CLAIM_CARDS
        and len(truthful) == len(player.hand)
        and _would_force_challenge_after_play(game, player, len(player.hand))
    )


def _should_preserve_truthful_exit(
    game: "DeadMansDeckGame",
    player: "DeadMansDeckPlayer",
    truthful: list["DeadMansDeckCard"],
    bluffs: list["DeadMansDeckCard"],
    alive_count: int,
) -> bool:
    if (
        alive_count != 2
        or not truthful
        or not bluffs
        or len(player.hand) <= 1
        or len(player.hand) > MAX_CLAIM_CARDS
    ):
        return False
    if not _would_force_challenge_after_play(game, player, len(player.hand)):
        return False
    return True


def _choose_mixed_hand_safe_claim(
    game: "DeadMansDeckGame",
    player: "DeadMansDeckPlayer",
    truthful: list["DeadMansDeckCard"],
    bluffs: list["DeadMansDeckCard"],
) -> list["DeadMansDeckCard"]:
    if len(player.hand) == 1:
        return player.hand[:1]

    # If a full-hand claim would be forced and false, keep at least one card.
    # In two-player endings, spend a bluff first when a truthful exit card exists.
    if len(game.alive_players) == 2 and truthful and bluffs:
        return [_choose_low_value_bluff(bluffs)]

    max_count = min(MAX_CLAIM_CARDS, len(truthful), len(player.hand) - 1)
    if max_count >= 1:
        return random.sample(truthful, _weighted_truthful_count(max_count))  # nosec B311
    return [_choose_low_value_bluff(bluffs)]


def _choose_truthful_claim(
    game: "DeadMansDeckGame",
    player: "DeadMansDeckPlayer",
    truthful: list["DeadMansDeckCard"],
) -> list["DeadMansDeckCard"]:
    max_count = min(MAX_CLAIM_CARDS, len(truthful))
    if max_count <= 1:
        return truthful[:1]

    if (
        len(truthful) == len(player.hand)
        and len(player.hand) <= MAX_CLAIM_CARDS
        and _would_force_challenge_after_play(game, player, len(player.hand))
    ):
        return truthful[: len(player.hand)]

    count = _weighted_truthful_count(max_count)
    return random.sample(truthful, count)  # nosec B311


def _choose_bluff_claim(
    game: "DeadMansDeckGame",
    player: "DeadMansDeckPlayer",
    bluffs: list["DeadMansDeckCard"],
) -> list["DeadMansDeckCard"]:
    if not bluffs:
        return []
    if len(player.hand) == 1:
        return player.hand[:1]

    max_count = min(MAX_CLAIM_CARDS, len(bluffs), len(player.hand) - 1)
    if len(player.hand) <= MAX_CLAIM_CARDS and _would_force_challenge_after_play(
        game,
        player,
        len(player.hand),
    ):
        max_count = min(max_count, 1)
    if max_count <= 1:
        return [_choose_low_value_bluff(bluffs)]
    count = 1 if random.random() < 0.82 else 2  # nosec B311
    return random.sample(bluffs, min(count, max_count))  # nosec B311


def _should_bluff_with_mixed_hand(
    game: "DeadMansDeckGame",
    player: "DeadMansDeckPlayer",
    truthful: list["DeadMansDeckCard"],
    bluffs: list["DeadMansDeckCard"],
    alive_count: int,
) -> bool:
    if not bluffs or not truthful:
        return False
    if len(player.hand) <= 2 and alive_count == 2:
        return True

    chance = 0.22
    if alive_count == 2:
        chance += 0.14
    if len(bluffs) > len(truthful):
        chance += 0.12
    if _roulette_risk(player) >= 0.5:
        chance -= 0.08
    return random.random() < max(0.08, min(0.48, chance))  # nosec B311


def _must_challenge_to_avoid_forced_false_finish(
    game: "DeadMansDeckGame",
    player: "DeadMansDeckPlayer",
) -> bool:
    if not game.last_claim or not player.hand:
        return False
    if len(player.hand) > 1:
        return False
    if _is_truthful_card(player.hand[0], game.target_rank):
        return False
    return _would_force_challenge_after_play(game, player, 1)


def _would_force_challenge_after_play(
    game: "DeadMansDeckGame",
    player: "DeadMansDeckPlayer",
    selected_count: int,
) -> bool:
    alive_players = game.alive_players
    if len(alive_players) < 2:
        return False
    if selected_count <= 0:
        return False

    players_with_cards = 0
    for table_player in alive_players:
        if table_player.id == player.id:
            remaining = max(0, len(player.hand) - selected_count)
        else:
            remaining = len(table_player.hand)
        if remaining > 0:
            players_with_cards += 1
    return players_with_cards <= 1


def _is_opening_claim(game: "DeadMansDeckGame") -> bool:
    claim = game.last_claim
    alive_players = game.alive_players
    if not claim or not alive_players:
        return False
    remaining_cards = sum(len(player.hand) for player in alive_players)
    return remaining_cards + claim.count == HAND_SIZE * len(alive_players)


def _weighted_truthful_count(max_count: int) -> int:
    if max_count <= 1:
        return 1
    if max_count == 2:
        return 2 if random.random() < 0.58 else 1  # nosec B311
    roll = random.random()  # nosec B311
    if roll < 0.34:
        return 1
    if roll < 0.78:
        return 2
    return 3


def _choose_low_value_bluff(
    bluffs: list["DeadMansDeckCard"],
) -> "DeadMansDeckCard":
    return random.choice(bluffs)  # nosec B311


def _truthful_cards(
    cards: list["DeadMansDeckCard"],
    target_rank: str,
) -> list["DeadMansDeckCard"]:
    return [card for card in cards if _is_truthful_card(card, target_rank)]


def _bluff_cards(
    cards: list["DeadMansDeckCard"],
    target_rank: str,
) -> list["DeadMansDeckCard"]:
    return [card for card in cards if not _is_truthful_card(card, target_rank)]


def _truthful_count(cards: list["DeadMansDeckCard"], target_rank: str) -> int:
    return sum(1 for card in cards if _is_truthful_card(card, target_rank))


def _is_truthful_card(card: "DeadMansDeckCard", target_rank: str) -> bool:
    return card.rank in {target_rank, RANK_JOKER}


def _roulette_risk(player: "DeadMansDeckPlayer") -> float:
    remaining_chambers = max(1, CHAMBER_COUNT - player.chamber_index)
    return 1.0 / remaining_chambers
