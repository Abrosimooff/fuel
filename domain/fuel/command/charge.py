from dataclasses import dataclass

from dpt.cqrs import Command
from dpt.domain.fuel import FuelCharge
from dpt.domain.identity.command import OrganizationIdMixin

__all__ = (
    "BeginFuelChargeCommand",
    "EndFuelChargeCommand",
    "SetFuelChargeCommand"
)


@dataclass
class BeginFuelChargeCommand(OrganizationIdMixin, Command):
    """Начать заправку"""
    object: FuelCharge


@dataclass
class EndFuelChargeCommand(OrganizationIdMixin, Command):
    """Окончить заправку"""
    object: FuelCharge


@dataclass
class SetFuelChargeCommand(OrganizationIdMixin, Command):
    """Изменить заправку"""
    object: FuelCharge


