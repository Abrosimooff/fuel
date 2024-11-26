from dataclasses import dataclass
from uuid import UUID

from dpt.cqrs import Command
from dpt.domain.fuel import ObjectFuelIntervalSettings, ObjectFuelIntervalSettingsId
from dpt.domain.fuel.entity import ObjectFuelSettings, ObjectFuelSettingsId
from dpt.domain.identity import OrganizationId
from dpt.domain.identity.command import OrganizationIdMixin


__all__ = (
    "SetObjectFuelSettingsCommand",
    "DeleteObjectFuelSettingsCommand",
    "RestoreObjectFuelSettingsCommand",

    "SetObjectFuelIntervalSettingsCommand",
    "DeleteObjectFuelIntervalSettingsCommand",
    "RestoreObjectFuelIntervalSettingsCommand",
)


@dataclass
class SetObjectFuelSettingsCommand(OrganizationIdMixin, Command):
    """Сохранение настроек заправок/сливов для объекта"""
    object: ObjectFuelSettings


@dataclass
class DeleteObjectFuelSettingsCommand(Command):
    """Удаление настроек заправок/сливов для объекта"""
    object_id: ObjectFuelSettingsId
    organization_id: OrganizationId


@dataclass
class RestoreObjectFuelSettingsCommand(Command):
    """Восстановление настроек заправок/сливов для объекта"""
    object_id: ObjectFuelSettingsId
    organization_id: OrganizationId


@dataclass
class SetObjectFuelIntervalSettingsCommand(OrganizationIdMixin, Command):
    """Сохранение настроек заправок/сливов для объекта на интервал времени"""
    object: ObjectFuelIntervalSettings


@dataclass
class DeleteObjectFuelIntervalSettingsCommand(Command):
    """Удаление настроек заправок/сливов для объекта на интервал времени"""
    object_id: ObjectFuelIntervalSettingsId
    organization_id: OrganizationId


@dataclass
class RestoreObjectFuelIntervalSettingsCommand(Command):
    """Восстановление настроек заправок/сливов для объекта на интервал времени"""
    object_id: ObjectFuelIntervalSettingsId
    organization_id: OrganizationId
