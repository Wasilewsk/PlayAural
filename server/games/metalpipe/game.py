"""
Metal Pipe Game Implementation for PlayAural.

A joke game where one random player hits another with a metal pipe.
Supports single bonk (bonker wins) and multiple bonks (last alive wins).

The original PlayPalace implementation used the legacy ``event_queue`` /
``schedule_event`` API. PlayAural replaces that with the serialized
``SequenceRunnerMixin`` (already mixed into ``Game``), so the pre-computed
bonk schedule is expressed as a list of timed beats with callback ops.
"""

import random
from dataclasses import dataclass, field
from datetime import datetime

from ..base import Game, Player, GameOptions
from ..registry import register_game
from ...game_utils.game_result import GameResult, PlayerResult
from ...game_utils.options import BoolOption, option_field
from ...game_utils.sequence_runner_mixin import SequenceBeat, SequenceOperation
from ...messages.localization import Localization


@dataclass
class MetalPipePlayer(Player):
    """Player state for Metal Pipe game."""

    alive: bool = True


@dataclass
class MetalPipeOptions(GameOptions):
    """Options for Metal Pipe game."""

    multiple_bonks: bool = option_field(
        BoolOption(
            default=False,
            value_key="enabled",
            label="metalpipe-set-multiple-bonks",
            change_msg="metalpipe-option-changed-multiple-bonks",
        )
    )
    allow_self_bonk: bool = option_field(
        BoolOption(
            default=True,
            value_key="enabled",
            label="metalpipe-set-allow-self-bonk",
            change_msg="metalpipe-option-changed-allow-self-bonk",
        )
    )


@dataclass
@register_game
class MetalPipeGame(Game):
    """
    Metal Pipe - a joke game.

    A random player hits another random player over the head with a metal pipe.
    In single bonk mode, the bonker wins (unless they bonked themselves, in which
    case everyone else wins). In multiple bonks mode, bonking continues until
    only one player remains.
    """

    players: list[MetalPipePlayer] = field(default_factory=list)
    options: MetalPipeOptions = field(default_factory=MetalPipeOptions)

    # Game state
    _winner_names: list[str] = field(default_factory=list)

    @classmethod
    def get_name(cls) -> str:
        return "Metal Pipe"

    @classmethod
    def get_type(cls) -> str:
        return "metalpipe"

    @classmethod
    def get_category(cls) -> str:
        return "misc"

    @classmethod
    def get_min_players(cls) -> int:
        return 2

    @classmethod
    def get_max_players(cls) -> int:
        return 8

    def create_player(
        self, player_id: str, name: str, is_bot: bool = False
    ) -> MetalPipePlayer:
        return MetalPipePlayer(id=player_id, name=name, is_bot=is_bot)

    def on_start(self) -> None:
        """Called when the game starts."""
        self.status = "playing"
        self._sync_table_status()
        self.game_active = True
        self.cancel_all_sequences()

        active_players = self.get_active_players()
        self._winner_names = []

        self._run_bonks(active_players)

    def _run_bonks(self, players: list[MetalPipePlayer]) -> None:
        """Pre-calculate all bonk outcomes and schedule them as a sequence."""
        single = not self.options.multiple_bonks
        alive_ids = [p.id for p in players]
        winner_names: list[str] = []
        beats: list[SequenceBeat] = []

        # Bonk beats fire every 5 ticks (delay_after_ticks=5 between them).
        while len(alive_ids) > 1:
            bonker_id = random.choice(alive_ids)  # nosec B311

            if self.options.allow_self_bonk:
                bonked_id = random.choice(alive_ids)  # nosec B311
            else:
                others = [pid for pid in alive_ids if pid != bonker_id]
                if not others:
                    break
                bonked_id = random.choice(others)  # nosec B311

            is_self = bonker_id == bonked_id

            beats.append(
                SequenceBeat(
                    ops=[
                        SequenceOperation.sound_op("lsmack.ogg"),
                        SequenceOperation.callback_op(
                            "bonk",
                            {
                                "bonker_id": bonker_id,
                                "bonked_id": bonked_id,
                                "is_self": is_self,
                            },
                        ),
                    ],
                    delay_after_ticks=5,
                )
            )

            alive_ids = [pid for pid in alive_ids if pid != bonked_id]

            if single:
                # Single bonk: bonker wins unless self-bonk
                if is_self:
                    winner_names = [
                        p.name for p in players if p.id != bonker_id
                    ]
                else:
                    bonker = self.get_player_by_id(bonker_id)
                    winner_names = [bonker.name] if bonker else []
                break

        # Multiple bonks: determine winner from last alive
        if not single and not winner_names:
            if len(alive_ids) == 1:
                winner_player = self.get_player_by_id(alive_ids[0])
                winner_names = [winner_player.name] if winner_player else []
            else:
                winner_names = []
                for pid in alive_ids:
                    p = self.get_player_by_id(pid)
                    if p:
                        winner_names.append(p.name)
                if len(winner_names) > 1:
                    winner_names = [random.choice(winner_names)]  # nosec B311

        # Winner beat: wait ~30 ticks after the final bonk, then resolve.
        if beats:
            beats[-1].delay_after_ticks = 30

        beats.append(
            SequenceBeat(
                ops=[
                    SequenceOperation.sound_op("gamewin.ogg"),
                    SequenceOperation.callback_op(
                        "winner",
                        {"winner_names": winner_names},
                    ),
                ]
            )
        )

        self.start_sequence(
            "bonks",
            beats,
            start_delay=5,
            tag="bonks",
            lock_scope=self.SEQUENCE_LOCK_GAMEPLAY,
            pause_bots=True,
        )

    def on_sequence_callback(
        self,
        sequence_id: str,
        callback_id: str,
        payload: dict,
    ) -> None:
        """Handle scheduled sequence callbacks."""
        _ = sequence_id
        if callback_id == "bonk":
            bonker = self.get_player_by_id(payload["bonker_id"])
            bonked = self.get_player_by_id(payload["bonked_id"])
            if not bonker or not bonked:
                return

            if isinstance(bonked, MetalPipePlayer):
                bonked.alive = False

            if payload["is_self"]:
                self.broadcast_l(
                    "metalpipe-hit-self", buffer="game", bonker=bonker.name
                )
            else:
                self.broadcast_l(
                    "metalpipe-hit-other",
                    buffer="game",
                    bonker=bonker.name,
                    bonked=bonked.name,
                )

        elif callback_id == "winner":
            self._winner_names = payload["winner_names"]
            self.finish_game()

    def on_tick(self) -> None:
        """Called every game tick."""
        super().on_tick()
        self.process_scheduled_sounds()
        self.process_sequences()

    def build_game_result(self) -> GameResult:
        """Build the game result."""
        all_players = [
            p
            for p in self.players
            if isinstance(p, MetalPipePlayer) and not p.is_spectator
        ]

        return GameResult(
            game_type=self.get_type(),
            timestamp=datetime.now().isoformat(),
            duration_ticks=self.sound_scheduler_tick,
            player_results=[
                PlayerResult(
                    player_id=p.id,
                    player_name=p.name,
                    is_bot=p.is_bot and not p.replaced_human,
                )
                for p in all_players
            ],
            custom_data={
                "winner_names": self._winner_names,
                "multiple_bonks": self.options.multiple_bonks,
                "allow_self_bonk": self.options.allow_self_bonk,
            },
        )

    def format_end_screen(self, result: GameResult, locale: str) -> list[str]:
        """Format the end screen."""
        winner_names = result.custom_data.get("winner_names", [])
        if winner_names:
            return [
                Localization.get(locale, "metalpipe-winner", player=name)
                for name in winner_names
            ]
        return []
