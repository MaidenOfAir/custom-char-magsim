from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, override

from magsim.core.abilities import Ability
from magsim.core.events import Phase, PostWarpEvent
from magsim.core.mixins import (
    LifecycleManagedMixin,
    MovementValidatorMixin,
)
from magsim.core.modifiers import RacerModifier
from magsim.engine.abilities import (
    add_racer_modifier,
    remove_racer_modifier,
)

if TYPE_CHECKING:
    from magsim.core.events import GameEvent
    from magsim.core.types import AbilityName, ModifierName
    from magsim.engine.game_engine import GameEngine


@dataclass(eq=False)
class ForbiddenBookStrikeOne(RacerModifier):
    """
    Applied the first time a racer other than stickler rolls a 6. Does nothing.
    """

    name: AbilityName | ModifierName = "ForbiddenBookStrikeOne"

@dataclass(eq=False)
class ForbiddenBookStrikeTwo(RacerModifier):
    """
    Applied the second time a racer other than stickler rolls a 6. Does nothing.
    """

    name: AbilityName | ModifierName = "ForbiddenBookStrikeTwo"


@dataclass
class ForbiddenBookIncinerate(Ability):
    name: AbilityName = "ForbiddenBookIncinerate"
    triggers: tuple[type[GameEvent], ...] = (RollResultEvent)

    @override
    def execute(
        self,
        event: GameEvent,
        owner: ActiveRacerState,
        agent: Agent,
    ) -> AbilityTriggeredEventOrSkipped:

        #Cancel ability if riggered at wrong time or on owner's turn'
        if (
            not isinstance(event, RollResultEvent)
            or event.target_racer_idx == owner.idx
        ):
            return "skip_trigger"

        #Check if racer rolled 5 or 6
        dice_val - engine.state.roll_state.dice_value
        if dice_val is None or dice_val not in (5,6):
            return "skip_trigger"

        #Check if racer has StrikeTwo, eliminate them if so
        mod = next(
            (m for m in event.target_racer_idx if isinstance(m, ForbiddenBookStrikeTwo)),
            None,
        )

        if mod:
            engine.log_info(
                f"{engine.get_racer(event.target_racer_idx).repr}... YOU'RE OUTTA HERE!",
            )

            engine.push_event(
                RacerEliminatedEvent(
                    target_racer_idx=event.target_racer_idx,
                    responsible_racer_idx=owner.idx,
                    source=self.name,
                    phase=event.phase,
                ),
            )

            #Check if all but one player has been eliminated, to activate instant game end
            active_count = sum(1 for r in engine.state.racers if r.active)
            if active_count == 1:
                rank = sum([1 for r in engine.state.racers if r.finished]) + 1
                if rank <= 2:
                    engine.log_info(f"{owner.repr} is the last remaining racer.")
                    mark_finished(engine, racer=owner, rank=rank)
                else:
                    engine.log_error(
                        f"Unexpected state: {owner.repr} is the last remaining racer but more than one racer has finished.",
                    )

            return AbilityTriggeredEvent(
                responsible_racer_idx=owner.idx,
                source=self.name,
                phase=event.phase,
                target_racer_idx=event.target_racer_idx,
            )

        #Check if racer has StrikeOne, Apply StrikeTwo if so
        mod = next(
            (m for m in event.target_racer_idx if isinstance(m, ForbiddenBookStrikeOne)),
            None,
        )

        if mod:
            engine.log_info(
                f"Careful {engine.get_racer(event.target_racer_idx).repr}, that's strike two...",
            )

            add_racer_modifier(engine, event.target_racer_idx, ForbiddenBookStrikeTwo(owner_idx=owner_idx))

            return AbilityTriggeredEvent(
                responsible_racer_idx=owner.idx,
                source=self.name,
                phase=event.phase,
                target_racer_idx=event.target_racer_idx,
            )

        #If racer did not have StrikeTwo or StrikeOne, apply StrikeOne
        add_racer_modifier(engine, event.target_racer_idx, ForbiddenBokStrikeOne(owner_idx=owner_idx))

        return AbilityTriggeredEvent(
            responsible_racer_idx=owner.idx,
            source=self.name,
            phase=event.phase,
            target_racer_idx=event.target_racer_idx)


