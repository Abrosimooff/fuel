from dataclasses import dataclass

from dpt.domain.fuel import FuelDischarge
from dpt.domain.identity import ModifiedEvent, DeletedEvent, FuelDischargeId

__all__ = (
    "BeginFuelDischargeEvent",
    "EndFuelDischargeEvent",
    "FuelDischargeModifiedEvent",
    "CancelFuelDischargeEvent"
)


@dataclass
class BeginFuelDischargeEvent(ModifiedEvent):
    """Слив начался"""
    object: FuelDischarge


@dataclass
class EndFuelDischargeEvent(ModifiedEvent):
    """Слив окончился"""
    object: FuelDischarge


@dataclass
class FuelDischargeModifiedEvent(ModifiedEvent):
    """Слив изменен"""
    object: FuelDischarge


@dataclass
class CancelFuelDischargeEvent(DeletedEvent):
    """Слив отменён"""
    object_id: FuelDischargeId
    """Идентификатор слива топлива"""
