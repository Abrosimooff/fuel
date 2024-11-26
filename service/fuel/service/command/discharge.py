from dpt.cqrs import CommandHandler
from dpt.domain.fuel import BeginFuelDischargeCommand, FuelDischarge, BeginFuelDischargeEvent, EndFuelDischargeCommand, \
    EndFuelDischargeEvent, SetFuelDischargeCommand, DeleteFuelDischargeCommand
from dpt.domain.fuel.event.discharge import FuelDischargeModifiedEvent, CancelFuelDischargeEvent
from dpt.fuel.storage.interface import IFuelDischargeStorage
from dpt.monro.command.implements import MongoSetObjectMixin, MongoDeleteObjectMixin

__all__ = (
    "BeginFuelDischargeCommandHandler",
    "EndFuelDischargeCommandHandler",
    "SetFuelDischargeCommandHandler",
    "DeleteFuelDischargeCommandHandler",
)


class BeginFuelDischargeCommandHandler(MongoSetObjectMixin, CommandHandler[BeginFuelDischargeCommand]):
    """Обработчик начала слива (Возможно начался слив)"""
    model_class = FuelDischarge
    storage_class = IFuelDischargeStorage
    event_class = BeginFuelDischargeEvent


class EndFuelDischargeCommandHandler(MongoSetObjectMixin, CommandHandler[EndFuelDischargeCommand]):
    """Обработчик окончания слива (Зафиксирован слив)"""
    model_class = FuelDischarge
    storage_class = IFuelDischargeStorage
    event_class = EndFuelDischargeEvent


class SetFuelDischargeCommandHandler(MongoSetObjectMixin, CommandHandler[SetFuelDischargeCommand]):
    """Обработчик изменения слива (Слив продолжается) """
    model_class = FuelDischarge
    storage_class = IFuelDischargeStorage
    event_class = FuelDischargeModifiedEvent


class DeleteFuelDischargeCommandHandler(MongoDeleteObjectMixin, CommandHandler[DeleteFuelDischargeCommand]):
    """Обработчик удаления слива (Слив отменен (ложная тревога)) """
    model_class = FuelDischarge
    storage_class = IFuelDischargeStorage
    event_class = CancelFuelDischargeEvent
