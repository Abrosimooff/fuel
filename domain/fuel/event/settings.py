from dataclasses import dataclass

from dpt.domain.fuel import ObjectFuelIntervalSettings, ObjectFuelIntervalSettingsId
from dpt.domain.fuel.entity import ObjectFuelSettings, ObjectFuelSettingsId
from dpt.domain.identity import ModifiedEvent, DeletedEvent

__all__ = (
    "ObjectFuelSettingsModifiedEvent",
    "ObjectFuelSettingsDeletedEvent",

    "ObjectFuelIntervalSettingsModifiedEvent",
    "ObjectFuelIntervalSettingsDeletedEvent",
)


@dataclass
class ObjectFuelSettingsModifiedEvent(ModifiedEvent):
    """Изменены настройки определения заправок/сливов"""
    object: ObjectFuelSettings


@dataclass
class ObjectFuelSettingsDeletedEvent(DeletedEvent):
    """Удалены настройки определения заправок/сливов"""
    object_id: ObjectFuelSettingsId


@dataclass
class ObjectFuelIntervalSettingsModifiedEvent(ModifiedEvent):
    """Изменены настройки определения заправок/сливов на интервал времени"""
    object: ObjectFuelIntervalSettings


@dataclass
class ObjectFuelIntervalSettingsDeletedEvent(DeletedEvent):
    """Удалены настройки определения заправок/сливов на интервал времени"""
    object_id: ObjectFuelIntervalSettingsId
