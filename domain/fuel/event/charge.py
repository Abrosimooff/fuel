from dataclasses import dataclass

from dpt.domain.fuel import FuelCharge
from dpt.domain.identity import ModifiedEvent

__all__ = (
    "BeginFuelChargeEvent",
    "EndFuelChargeEvent",
    "FuelChargeModifiedEvent"
)


@dataclass
class BeginFuelChargeEvent(ModifiedEvent):
    """Заправка началась"""
    object: FuelCharge


@dataclass
class EndFuelChargeEvent(ModifiedEvent):
    """Заправка окончилась"""
    object: FuelCharge


@dataclass
class FuelChargeModifiedEvent(ModifiedEvent):
    """Заправка изменена"""
    object: FuelCharge
