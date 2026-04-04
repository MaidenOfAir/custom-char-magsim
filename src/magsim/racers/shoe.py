from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, override

from magsim.core.abilities import Ability
from magsim.core.events import (
    AbilityTriggeredEvent,
    GameEvent,
    Phase,
    TurnStartEvent,
    PostMoveEvent,
    PostWarpEvent,
)
from magsim.core.mixins import (
    LifecycleManagedMixin,
    RollModificationMixin,
)
from magsim.core.modifiers import RacerModifier
from magsim.core.state import ActiveRacerState, is_active
from magsim.engine.abilities import (
    add_racer_modifier,
    remove_racer_modifier,
)

from magsim.engine.movement import push_trip


if TYPE_CHECKING:
    from magsim.core.agent import Agent
    from magsim.core.events import MoveDistanceQuery
    from magsim.core.types import AbilityName, ModifierName
    from magsim.engine.game_engine import GameEngine


@dataclass
class ShoeSprint(RacerModifier, RollModificationMixin):
    name: AbilityName | ModifierName = "ShoeSprint"

    @override
    def modify_roll(
        self,
        query: MoveDistanceQuery,
        owner_idx: int | None,
        engine: GameEngine,
        rolling_racer_idx: int,
    ) -> list[AbilityTriggeredEvent]:
        if owner_idx is None:
            msg = f"owner_idx should never be None for {self.name}"
            raise ValueError(msg)

        owner = engine.get_racer(owner_idx)

        racers_ahead = 0
        for r in engine.state.racers:
            if r.position > owner.position:
                racers_ahead+=1


        # Bonus to main move
        query.modifiers.append(racers_ahead)
        query.modifier_sources.append((self.name, racers_ahead))

        return [
            AbilityTriggeredEvent(
                owner_idx,
                self.name,
                phase=Phase.ROLL_WINDOW,
                target_racer_idx=owner_idx,
            ),
        ]


@dataclass
class ShoeLaced(Ability, LifecycleManagedMixin):
    name: AbilityName = "ShoeLaced"
    triggers: tuple[type[GameEvent], ...] = (PostMoveEvent,PostWarpEvent,)

    @override
    def execute(
        self,
        event: GameEvent,
        owner: ActiveRacerState,
        engine: GameEngine,
        agent: Agent,
    ):
        if not isinstance(event, PostMoveEvent or PostWarpEvent):
            return "skip_trigger"

        # CASE 1: Shoe moved onto someone
        if event.target_racer_idx == owner.idx:
            engine.log_info(
                f"{owner.repr} moved onto {owner.position} and trips itself with {self.name}!",
            )
            push_trip(
                engine,
                phase=event.phase,
                tripped_racer_idx=owner.idx,
                source=self.name,
                responsible_racer_idx=owner.idx,
                emit_ability_triggered="after_resolution",
            )

        # CASE 2: Someone else moved onto shoe
        else:
            mover = engine.get_racer(event.target_racer_idx)
            if mover.active and mover.position == owner.position:
                if not owner.tripped:
                    # only log when actually tripping
                    engine.log_info(
                        f"{mover.repr} stepped onto {owner.repr} and trips up {owner.repr} due to {self.name}!",
                    )
                push_trip(
                    engine,
                    phase=event.phase,
                    tripped_racer_idx=owner.idx,
                    source=self.name,
                    responsible_racer_idx=owner.idx,
                    emit_ability_triggered="after_resolution",
                )

        return "skip_trigger"

    @override
    def on_gain(self, engine: GameEngine, owner_idx: int):
        add_racer_modifier(
            engine,
            owner_idx,
            ShoeSprint(owner_idx=owner_idx),
        )

    @override
    def on_loss(self, engine: GameEngine, owner_idx: int):
        remove_racer_modifier(
            engine,
            owner_idx,
            ShoeSprint(owner_idx=owner_idx),
        )
