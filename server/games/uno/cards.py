"""Card model and helpers for UNO.

UNO does not fit the standard 52-card ``Card`` (two of each 1-9, a single 0,
colorless wilds, named action types), so it uses a dedicated dataclass. Plain
fields keep it Mashumaro-serializable as ``list[UnoCard]`` on the game/players.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from ...messages.localization import Localization

# Colors
RED = 1
YELLOW = 2
GREEN = 3
BLUE = 4
WILD = 5

COLORS = (RED, YELLOW, GREEN, BLUE)

# Types
NUMBER = "number"
SKIP = "skip"
REVERSE = "reverse"
DRAW_TWO = "draw_two"
WILD_CARD = "wild"
WILD_DRAW_FOUR = "wild_draw_four"

ACTION_TYPES = (SKIP, REVERSE, DRAW_TWO)
WILD_TYPES = (WILD_CARD, WILD_DRAW_FOUR)

_COLOR_KEY = {
    RED: "uno-color-red",
    YELLOW: "uno-color-yellow",
    GREEN: "uno-color-green",
    BLUE: "uno-color-blue",
    WILD: "uno-color-wild",
}

_COLOR_ACTION_ID = {
    RED: "color_red",
    YELLOW: "color_yellow",
    GREEN: "color_green",
    BLUE: "color_blue",
}

_COLOR_SOUND = {
    RED: "game_uno/red.ogg",
    YELLOW: "game_uno/yellow.ogg",
    GREEN: "game_uno/green.ogg",
    BLUE: "game_uno/blue.ogg",
}

# Sort ordering for hand display.
_TYPE_ORDER = {
    NUMBER: 0,
    SKIP: 1,
    REVERSE: 2,
    DRAW_TWO: 3,
    WILD_CARD: 4,
    WILD_DRAW_FOUR: 5,
}


@dataclass
class UnoCard:
    """A single UNO card."""

    id: int
    color: int  # 1=red 2=yellow 3=green 4=blue 5=wild
    type: str  # number|skip|reverse|draw_two|wild|wild_draw_four
    value: int | None = None  # 0-9 for number cards, else None


def build_deck() -> list[UnoCard]:
    """Build a standard 108-card UNO deck (unshuffled).

    Per color: one 0, two each of 1-9, two skip, two reverse, two draw-two.
    Plus four wild and four wild-draw-four.
    """
    deck: list[UnoCard] = []
    cid = 0
    for color in COLORS:
        deck.append(UnoCard(id=cid, color=color, type=NUMBER, value=0))
        cid += 1
        for value in range(1, 10):
            for _ in range(2):
                deck.append(UnoCard(id=cid, color=color, type=NUMBER, value=value))
                cid += 1
        for action in ACTION_TYPES:
            for _ in range(2):
                deck.append(UnoCard(id=cid, color=color, type=action))
                cid += 1
    for _ in range(4):
        deck.append(UnoCard(id=cid, color=WILD, type=WILD_CARD))
        cid += 1
    for _ in range(4):
        deck.append(UnoCard(id=cid, color=WILD, type=WILD_DRAW_FOUR))
        cid += 1
    return deck


def shuffle(deck: list[UnoCard]) -> None:
    """Shuffle a deck in place."""
    random.shuffle(deck)


def card_points(card: UnoCard) -> int:
    """Scoring value of a card (number=face, action=20, wild=50)."""
    if card.type == NUMBER:
        return card.value or 0
    if card.type in ACTION_TYPES:
        return 20
    return 50  # wild / wild draw four


def hand_points(hand: list[UnoCard]) -> int:
    """Total scoring value of a hand."""
    return sum(card_points(c) for c in hand)


def color_name(color: int, locale: str) -> str:
    """Localized color name."""
    return Localization.get(locale, _COLOR_KEY.get(color, "uno-color-wild"))


def color_action_id(color: int) -> str:
    """Action id for choosing a color (red/yellow/green/blue)."""
    return _COLOR_ACTION_ID.get(color, "color_red")


def color_from_action(action_id: str) -> int | None:
    """Inverse of color_action_id."""
    for color, aid in _COLOR_ACTION_ID.items():
        if aid == action_id:
            return color
    return None


def color_sound(color: int) -> str | None:
    """Sound played when a color is chosen."""
    return _COLOR_SOUND.get(color)


def format_card(card: UnoCard, locale: str) -> str:
    """Localized full card name (e.g. 'Red 7', 'Blue Skip', 'Wild Draw Four')."""
    if card.type == NUMBER:
        return Localization.get(
            locale, "uno-card-number", color=color_name(card.color, locale),
            value=card.value,
        )
    if card.type == SKIP:
        return Localization.get(
            locale, "uno-card-skip", color=color_name(card.color, locale)
        )
    if card.type == REVERSE:
        return Localization.get(
            locale, "uno-card-reverse", color=color_name(card.color, locale)
        )
    if card.type == DRAW_TWO:
        return Localization.get(
            locale, "uno-card-draw-two", color=color_name(card.color, locale)
        )
    if card.type == WILD_CARD:
        return Localization.get(locale, "uno-card-wild")
    if card.type == WILD_DRAW_FOUR:
        return Localization.get(locale, "uno-card-wild-four")
    return Localization.get(locale, "uno-card-wild")


def sort_key_by_color(card: UnoCard) -> tuple:
    """Sort key: color, then type, then value."""
    return (card.color, _TYPE_ORDER.get(card.type, 9), card.value or 0)


def sort_key_by_number(card: UnoCard) -> tuple:
    """Sort key: type, then value, then color."""
    return (_TYPE_ORDER.get(card.type, 9), card.value or 0, card.color)
