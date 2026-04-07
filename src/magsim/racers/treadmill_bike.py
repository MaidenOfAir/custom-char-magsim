from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, override

from magsim.core.abilities import Ability
from magsim.core.events import (
    AbilityTriggeredEventOrSkipped,
    GameEvent,
    RollResultEvent,
)
from magsim.engine.movement import push_move

if TYPE_CHECKING:
    from magsim.core.agent import Agent
    from magsim.core.state import ActiveRacerState
    from magsim.core.types import AbilityName
    from magsim.engine.game_engine import GameEngine

@dataclass
class TreadmillBoost(RacerModifier, RollModificationMixin):
    name: AbilityName | ModifierName = "TreadmillBoost"

    boost_val: int = 0

    @override
    def modify_roll(
        self,
        query: MoveDistanceQuery,
        owner_idx: int | None,
        engine: GameEngine,
        rolling_racer_idx: int,
    ) -> list[AbilityTriggeredEvent]:
        if (
            rolling_racer_idx != owner_idx
            or owner_idx is None
            or (owner := engine.get_active_racer(owner_idx)) is None
        ):
            return []

        delta = boost_val
        source = TreadmillBoost

        if delta != 0:
            query.modifiers.append(delta)
            query.modifier_sources.append((source, delta))

            return [
                AbilityTriggeredEvent(
                    owner_idx,
                    self.name,
                    phase=Phase.ROLL_WINDOW,
                    target_racer_idx=rolling_racer_idx,
                ),
            ]
        else:
            return []



@dataclass
class AbilityTreadmillBikeSpeedUp(Ability):
    name: AbilityName = "TreadmillBikeSpeedUp"
    triggers: tuple[type[GameEvent], ...] = (RollResultEvent,)

    treadmill_bike_ready: bool = False

    @override
    def execute(
        self,
        event: GameEvent,
        owner: ActiveRacerState,
        engine: GameEngine,
        agent: Agent,
    ) -> AbilityTriggeredEventOrSkipped:
        if (
            not isinstance(event, RollResultEvent)
            or owner.idx
            != event.target_racer_idx  # only triggers on treadmill bike's turn
        ):
            return "skip_trigger"


#         if bike rolls 1 or 2
        if (event.dice_value == 1 or event.dice_value == 2:

#                 and is not ready
            if not self.treadmill_bike_ready:
                engine.log_info(
                    f"{owner.repr} rolled a {event.dice_value} and starts speeding up!",
                )


#                 set it to be ready
                self.treadmill_bike_ready = True
                return "skip_trigger"

#             if it is ready, though
            if self.treadmill_bike_ready:
                owner.modifiers.boost_val += 1
                return [
                    AbilityTriggeredEvent(
                        owner.idx,
                        self.name,
                        phase=eventphase,
                        target_racer_idx=owner.idx,
                    ),
                ]





        return "skip_trigger"

    @override
    def on_gain(self, engine: GameEngine, owner_idx: int):
        # Apply the TreadmillBikeSpeedUp modifier to treadmill bike
        add_racer_modifier(
            engine,
            owner_idx,
            TreadmillBoost(owner_idx=owner_idx),
        )

    @override
    def on_loss(self, engine: GameEngine, owner_idx: int):
        remove_racer_modifier(
            engine,
            owner_idx,
            TreadmillBoost(owner_idx=owner_idx),
        )
