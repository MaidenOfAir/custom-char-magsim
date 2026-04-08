from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, override

from magsim.core.mixins import ApproachHookMixin, LandingHookMixin
from magsim.core.modifiers import SpaceModifier
from magsim.engine.movement import push_move

from magsim.engine.flow import mark_finished

from magsim.core.events import RacerEliminatedEvent

if TYPE_CHECKING:
    from magsim.core.events import (
        GameEvent,
        Phase,
    )
    from magsim.core.state import RacerState
    from magsim.core.types import (
        AbilityName,
        BoardName,
        ModifierName,
    )
    from magsim.engine.game_engine import GameEngine, push_event


@dataclass(slots=True)
class Board:
    length: int
    static_features: dict[int, list[SpaceModifier]]
    second_turn: int = 15
    dynamic_modifiers: defaultdict[int, list[SpaceModifier]] = field(
        init=False,
        default_factory=lambda: defaultdict(list),
    )

    def register_modifier(
        self,
        tile: int,
        modifier: SpaceModifier,
        engine: GameEngine,
    ) -> None:
        modifiers = self.dynamic_modifiers[tile]

        # Manual deduplication for lists
        # Because eq=True, this prevents adding a second "identical" blocker
        if modifier not in modifiers:
            modifiers.append(modifier)
            engine.log_debug(
                f"BOARD: Registered {modifier.name} (owner={modifier.owner_idx}) at tile {tile}",
            )

    def unregister_modifier(
        self,
        tile: int,
        modifier: SpaceModifier,
        engine: GameEngine,
    ) -> None:
        modifiers = self.dynamic_modifiers.get(tile)

        # eq=True makes "in" work even for new instances
        if not modifiers or modifier not in modifiers:
            engine.log_warning(
                f"BOARD: Failed to unregister {modifier.name} from {tile} - not found.",
            )
            return

        modifiers.remove(modifier)
        engine.log_debug(
            f"BOARD: Unregistered {modifier.name} (owner={modifier.owner_idx}) from tile {tile}",
        )

        if not modifiers:
            self.dynamic_modifiers.pop(tile, None)

    def get_modifiers_at(self, tile: int) -> list[SpaceModifier]:
        static = self.static_features.get(tile, ())
        dynamic = self.dynamic_modifiers.get(tile, ())
        return sorted((*static, *dynamic), key=lambda m: m.priority)

    def resolve_position(
        self,
        target: int,
        moving_racer_idx: int,
        engine: GameEngine,
        event: GameEvent,
    ) -> int:
        visited: set[int] = set()
        current = target

        while current not in visited:
            visited.add(current)
            new_target = current

            for mod in (
                mod
                for mod in self.get_modifiers_at(current)
                if isinstance(mod, ApproachHookMixin)
            ):
                redirected = mod.on_approach(current, moving_racer_idx, engine, event)
                if redirected != current:
                    engine.log_info(
                        "%s redirected %s from %s -> %s",
                        mod.name,
                        engine.get_racer(moving_racer_idx).repr,
                        current,
                        redirected,
                    )
                    new_target = redirected
                    break

            if new_target == current:
                return current

            current = new_target

        engine.log_warning("resolve_position loop detected, settling on %s", current)
        return current

    def trigger_on_land(
        self,
        tile: int,
        racer_idx: int,
        phase: Phase,
        engine: GameEngine,
    ) -> None:
        for mod in (
            mod
            for mod in self.get_modifiers_at(tile)
            if isinstance(mod, LandingHookMixin)
        ):
            if not engine.get_racer(racer_idx).active:
                return
            current_pos = engine.get_racer_pos(racer_idx)
            if current_pos != tile:
                break
            mod.on_land(tile, racer_idx, phase, engine)

    def dump_state(self, engine: GameEngine):
        """Log the location of all dynamic modifiers currently on the board.

        Useful for debugging test failures.
        """
        engine.log_info("=== BOARD STATE DUMP ===")
        if not self.dynamic_modifiers:
            engine.log_info("  (Board is empty of dynamic modifiers)")
            return

        # Sort by tile index for readability
        active_tiles = sorted(self.dynamic_modifiers.keys())
        for tile in active_tiles:
            mods = self.dynamic_modifiers[tile]
            if mods:
                # Format each modifier as "Name(owner=ID)"
                mod_strs = [f"{m.name}(owner={m.owner_idx})" for m in mods]
                engine.log_info(f"  Tile {tile:02d}: {', '.join(mod_strs)}")
        engine.log_info("========================")


@dataclass
class MoveDeltaTile(SpaceModifier, LandingHookMixin):
    """On landing, queue a move of +delta (forward) or -delta (backward)."""

    delta: int = 0
    priority: int = 5
    owner_idx: int | None = None
    name: AbilityName | ModifierName = "MoveDeltaTile"

    @property
    @override
    def display_name(self) -> str:
        return f"MoveDeltaTile({self.delta})"

    @override
    def on_land(
        self,
        tile: int,
        racer_idx: int,
        phase: Phase,
        engine: GameEngine,
    ) -> None:
        if self.delta == 0:
            return
        racer: RacerState = engine.get_racer(
            racer_idx,
        )  # uses existing GameEngine API.[file:1]
        engine.log_debug(
            f"{self.display_name}: Queuing {self.delta} move for {racer.repr}",
        )
        # New move is a separate event, not part of the original main move.[file:1]
        push_move(
            engine,
            self.delta,
            phase=phase,
            moved_racer_idx=racer_idx,
            source=self.name,
            responsible_racer_idx=None,
        )


@dataclass
class TripTile(SpaceModifier, LandingHookMixin):
    """On landing, trip the racer (they skip their next main move)."""

    name: AbilityName | ModifierName = "TripTile"
    priority: int = 5
    owner_idx: int | None = None

    @override
    def on_land(
        self,
        tile: int,
        racer_idx: int,
        phase: Phase,
        engine: GameEngine,
    ) -> None:
        racer = engine.get_racer(racer_idx)
        if racer.tripped:
            return
        racer.tripped = True
        engine.log_info(f"{self.name}: {racer.repr} is now tripped.")


@dataclass
class VictoryPointTile(SpaceModifier, LandingHookMixin):
    """On landing, grant +1 VP (or a configured amount)."""

    amount: int = 1
    priority: int = 5
    owner_idx: int | None = None
    name: AbilityName | ModifierName = "VictoryPointTile"

    @property
    @override
    def display_name(self) -> str:
        return f"VP(+{self.amount})"

    @override
    def on_land(
        self,
        tile: int,
        racer_idx: int,
        phase: Phase,
        engine: GameEngine,
    ) -> None:
        racer = engine.get_racer(racer_idx)
        racer.victory_points += self.amount
        engine.log_info(
            f"{self.display_name}: {racer.repr} gains +{self.amount} VP (now {racer.victory_points}).",
        )

@dataclass
class EliminationTile(SpaceModifier, LandingHookMixin):
#     On Landing, Eliminate player

    name: AbilityName | ModifierName = "EliminationTile"
    owner_idx: int | None = None
    priority: int = 0

    @override
    def on_land(
        self,
        tile: int,
        racer_idx: int,
        phase: Phase,
        engine: GameEngine,
    ) -> None:
        racer = engine.get_racer(racer_idx)
        # strip racer of all their abilities
        engine.clear_all_abilities(racer.idx)
        racer.eliminate()

        engine.log_info(
            f"{racer.repr} stepped on the wrong tile and EXPLODED!!!",
        )
        engine.push_event(
                RacerEliminatedEvent(
                    target_racer_idx=racer_idx,
                    responsible_racer_idx=None,
                    source=self.name,
                    phase=phase,
                ),
        )

        # Check for sudden game end (if only 1 racer left)
        active_count = sum(1 for r in engine.state.racers if r.active)
        if active_count == 1:
            last_racers = [r for r in engine.state.racers if r.active]
            last_racer = last_racers[0]
            rank = sum([1 for r in engine.state.racers if r.finished]) + 1
            if rank <= 2:
                engine.log_info(f"{last_racer.repr} is the last remaining racer.")
                mark_finished(engine, racer=last_racer, rank=rank)
            else:
                engine.log_error(
                    f"Unexpected state: {last_racer.repr} is the last remaining racer but more than one racer has finished.",
                )

def build_wild_wilds() -> Board:
    return Board(
        length=30,
        static_features={
            1: [VictoryPointTile(None, amount=1)],
            5: [TripTile(None)],
            7: [MoveDeltaTile(None, delta=3)],
            11: [MoveDeltaTile(None, delta=1)],
            13: [VictoryPointTile(None, amount=1)],
            16: [MoveDeltaTile(None, delta=-4)],
            17: [TripTile(None)],
            23: [MoveDeltaTile(None, delta=2)],
            24: [MoveDeltaTile(None, delta=-2)],
            26: [TripTile(None)],
        },
    )

def build_brutal() -> Board:
    return Board(
        length=25,
        static_features={
            5: [TripTile(None)],
            10: [TripTile(None)],
            11: [MoveDeltaTile(None, delta=-3)],
            13: [EliminationTile(None)],
            15: [TripTile(None)],
            19: [MoveDeltaTile(None, delta=-3)],
            21: [TripTile(None)],
            24: [MoveDeltaTile(None, delta=-2)],
        },
    )


BoardFactory = Callable[[], Board]

BOARD_DEFINITIONS: dict[BoardName, BoardFactory] = {
    "Standard": lambda: Board(
        length=30,
        static_features={},
    ),
    "StandardLong": lambda: Board(
        length=150,
        static_features={},
    ),
    "WildWilds": build_wild_wilds,
    "Brutal": build_brutal,
}
