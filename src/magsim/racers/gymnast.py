from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, override

from magsim.core.abilities import Ability
from magsim.core.events import (
    AbilityTriggeredEventOrSkipped,
    GameEvent,
    Phase,
    TripCmdEvent,
    TripRecoveryEvent,
    RollResultEvent,
)
from magsim.core.mixins import (

)
from magsim.core.state import ActiveRacerState
from magsim.engine.abilities import (
    )

from magsim.engine.movement import push_trip, push_move, push_untrip


if TYPE_CHECKING:
    from magsim.core.agent import Agent
    from magsim.core.events import
    from magsim.core.types import AbilityName
    from magsim.engine.game_engine import GameEngine



@dataclass
class GymnastCartwheel(Ability):
    name: AbilityName = "GymnastCartwheel"
    triggers: tuple[type[GameEvent], ...] = (TripCmdEvent, TripRecoveryEvent, RollResultEvent,)

    @override
    def execute(
        self,
        event: GameEvent,
        owner: ActiveRacerState,
        engine: GameEngine,
        agent: Agent,
    ) -> AbilityTriggeredEventOrSkipped:

        if not isinstance(event, TripCmdEvent or TripRecoveryEvent or RollResultEvent):
            return "skip_trigger"


#         When Gymnast stands up...
        if isinstance(event, TripRecoveryEvent) and event.target_racer_idx == owner_idx:


#             ...announce it and move forward 1
            engine.log_info(
                f"{owner.repr} finishes their {self.name} cartwheel!"
            )
            push_move(
                engine,
                distance=1,
                phase=event.phase,
                moved_racer_idx=owner.idx,
                source=self.name,
                responsible_racer_idx=owner.idx,
                emit_ability_triggered="after_resolution",
            )


#         When gymnast gets tripped...
        if isinstance(event, TripCmdEvent) and event.target_racer_idx == owner_idx:

#             Untrip them if they are tripped
            if owner.tripped:
                push_untrip(
                    engine,
                    phase=event.phase,
                    untripped_racer_idx=owner_idx,
                    source=self.name,
                    responsible_racer_idx=owner.idx,
                    emit_ability_triggered="after_resolution",
                )

#             Otherwise announce and move forward 1
            engine.log_info(
                f"{owner.repr} started a cartwheel due to {self.name}!"
            )
            push_move(
                engine,
                distance=1,
                phase=event.phase,
                moved_racer_idx=owner.idx,
                source=self.name,
                responsible_racer_idx=owner.idx,
                emit_ability_triggered="after_resolution",
            )

#         When Someone rolls...
        if isinstance(RollResultEvent):

#             Check if it is 3 or 4
            if event.dice_value == 3 or 4:

#                 If so, announce it
                engine.log_info(
                    f"{engine.get_racer(event.target_racer_idx).repr} rolled a {event.dice_value}, so {owner.repr} uses {self.name}",
                )

#                 and immediately push a trip for gymnast
                push_trip(
                    engine,
                    phase=event.phase,
                    tripped_racer_idx=owner_idx,
                    source=self.name,
                    responsible_racer_idx=owner.idx,
                    emit_ability_triggered="after_resolution",
                )


        return "skip_trigger"


