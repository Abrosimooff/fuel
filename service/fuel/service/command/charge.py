from dpt.cqrs import CommandHandler
from dpt.domain.fuel import BeginFuelChargeCommand, FuelCharge, BeginFuelChargeEvent, EndFuelChargeCommand, \
    EndFuelChargeEvent, SetFuelChargeCommand
from dpt.domain.fuel.event.charge import FuelChargeModifiedEvent
from dpt.fuel.storage.interface import IFuelChargeStorage
from dpt.monro.command.implements import MongoSetObjectMixin


__all__ = (
    "BeginFuelChargeCommandHandler",
    "EndFuelChargeCommandHandler",
    "SetFuelChargeCommandHandler",
)


class BeginFuelChargeCommandHandler(MongoSetObjectMixin, CommandHandler[BeginFuelChargeCommand]):
    """Обработчик начала заправки"""
    model_class = FuelCharge
    storage_class = IFuelChargeStorage
    event_class = BeginFuelChargeEvent


class EndFuelChargeCommandHandler(MongoSetObjectMixin, CommandHandler[EndFuelChargeCommand]):
    """Обработчик окончания заправки"""
    model_class = FuelCharge
    storage_class = IFuelChargeStorage
    event_class = EndFuelChargeEvent


class SetFuelChargeCommandHandler(MongoSetObjectMixin, CommandHandler[SetFuelChargeCommand]):
    """Обработчик изменения заправки"""
    model_class = FuelCharge
    storage_class = IFuelChargeStorage
    event_class = FuelChargeModifiedEvent
