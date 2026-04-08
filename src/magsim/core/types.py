from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

RacerName = Literal[
    "Alchemist",
    "Baba",
    "Banana",
    "Blimp",
    "Cheerleader",
    "Centaur",
    "Coach",
    "Lulu",
    "Ludomingo",
    "Duelist",
    "Cloudgirl",
    "FlipFlop",
    "ForbiddenBook",
    "Tabetha",
    "Gunk",
    "Gymnast",
    "Hare",
    "Halcyon",
    "Heckler",
    "HugeSable",
    "Hypnotist",
    "Inchworm",
    "Lackey",
    "Leaptoad",
    "Legs",
    "Lyrebird",
    "Magician",
    "Fate",
    "Mouth",
    "Dreamybird",
    "Romantic",
    "RocketScientist",
    "BedtimeStory",
    "Shoe",
    "Sisyphus",
    "Skipper",
    "Stickler",
    "Suckerfish",
    "ThirdWheel",
    "TreadmillBike",
    "Nina",
    "VanillaBean",
]

AbilityName = Literal[
    "AlchemistAlchemy",
    "BabaIsTrip",
    "BananaTrip",
    "BlimpModifierManager",
    "CentaurTrample",
    "CheerleaderSupport",
    "CoachAura",
    "CopyLead",
    "LudomingoRerollManager",
    "LudomingoDeal",
    "DuelistDuel",
    "CloudgirlCopy",
    "FlipFlopSwap",
    "ForbiddenBookIncinerate",
    "TabethaPrediction",
    "GunkSlime",
    "GymnastCartwheel",
    "HareHubris",
    "HalcyonModifierManager",
    "HecklerHeckle",
    "HugeSablePush",
    "HypnotistWarp",
    "InchwormCreep",
    "LackeyLoyalty",
    "LeaptoadJumpManager",
    "LongLegs",
    "LyrebirdBonus",
    "MagicalReroll",
    "FatePredict",
    "MouthSwallow",
    "DreamybirdBoostManager",
    "DreamyPull",
    "RomanticMove",
    "RocketScientistBoost",
    "SlipBy",
    "ShoeLaced",
    "SisyphusCurse",
    "SkipperTurn",
    "SticklerStrictFinishManager",
    "SuckerfishRide",
    "ThirdWheelJoin",
    "TreadmillBikeSpeedUp",
    "NinaCopy",
]

RacerModifierName = Literal[
    "BlimpModifier",
    "BlimpSpeed",
    "BlimpSlow",
    "CoachBoost",
    "ForbiddenBookStrikeOne",
    "ForbiddenBookStrikeTwo",
    "GunkSlimeModifier",
    "HareSpeed",
    "HalcyonModifier",
    "HugeSableBlocker",
    "LeaptoadJump",
    "FatePrediction",
    "DreamySelfBoost",
    "RocketScientistLiftoff",
    "SisyphusStumble",
    "ShoeSprint",
    "SticklerStrictFinish",
    "SuckerfishTarget",
    "TreadmillBoost"
]

BoardModifierName = Literal[
    "MoveDeltaTile",
    "TripTile",
    "VictoryPointTile",
    "EliminationTile",
]

BoardName = Literal["Standard", "WildWilds","Brutal","StandardLong"]

SystemSource = Literal["Board", "System"]
ModifierName = RacerModifierName | BoardModifierName
Source = AbilityName | ModifierName | SystemSource

ErrorCode = Literal[
    "CRITICAL_LOOP_DETECTED",
    "MINOR_LOOP_DETECTED",
    "MAX_TURNS_REACHED",
]
D6Values = Literal[1, 2, 3, 4, 5, 6]
D6VAlueSet = frozenset[D6Values]


@dataclass
class RacerStat:
    racer_name: RacerName
    speed: float = 0.0
    winrate: float = 0.0
    avg_vp: float = 0.0
