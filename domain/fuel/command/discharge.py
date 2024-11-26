from dataclasses import dataclass

from dpt.cqrs import Command
from dpt.domain.fuel import FuelDischarge
from dpt.domain.identity import FuelDischargeId, OrganizationId
from dpt.domain.identity.command import OrganizationIdMixin

__all__ = (
    "BeginFuelDischargeCommand",
    "EndFuelDischargeCommand",
    "SetFuelDischargeCommand",
    "DeleteFuelDischargeCommand"
)


@dataclass
class BeginFuelDischargeCommand(OrganizationIdMixin, Command):
    """Начать слив"""
    object: FuelDischarge


@dataclass
class EndFuelDischargeCommand(OrganizationIdMixin, Command):
    """Окончить слив"""
    object: FuelDischarge


@dataclass
class SetFuelDischargeCommand(OrganizationIdMixin, Command):
    """Изменить слив"""
    object: FuelDischarge


@dataclass
class DeleteFuelDischargeCommand(Command):
    """Удалить слив"""
    object_id: FuelDischargeId
    organization_id: OrganizationId


