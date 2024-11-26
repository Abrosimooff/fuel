import datetime
from dataclasses import dataclass
from datetime import timedelta
from typing import Optional, NewType
from uuid import UUID

from dpt.cqrs import DTO
from dpt.domain.identity import ObjectId, ObjectModelId, OrganizationEntity
from dpt.domain.telemetry import AnalyticEntityId
from dpt.utils import DateTimeInterval


__all__ = (
    "ObjectFuelSettingsId",
    "ObjectFuelIntervalSettingsId",

    "FuelChargeSettings",
    "FuelDischargeSettings",

    "ObjectFuelSettings",
    "ObjectFuelIntervalSettings",
)


ObjectFuelSettingsId = NewType("ObjectFuelSettingsId", UUID)
"""Идентификатор объекта настроек заправок/сливов"""

ObjectFuelIntervalSettingsId = NewType("ObjectFuelIntervalSettingsId", UUID)
"""Идентификатор объекта настроек заправок/сливов на интервал времени"""


@dataclass
class FuelChargeSettings(DTO):
    """Параметры определения заправки"""
    min_volume: float = 150.0
    """Минимальный объем заправки, л"""
    min_duration_in: timedelta = timedelta(seconds=30)
    """Мин. продолжительность для входа в заправку, с"""
    min_duration_out: timedelta = timedelta(seconds=5)
    """Мин. продолжительность для выхода из заправки, с"""
    min_duration_sudden: timedelta = timedelta(seconds=30)
    """Мин. продолжительность для определения внезапной заправки, с"""
    ignore_on_speed: bool = False
    """Игнорировать заправки в движении"""
    ignore_duration_begin_move: timedelta = timedelta(seconds=0)
    """Игнорировать сообщения после начала движения, с"""


@dataclass
class FuelDischargeSettings(DTO):
    """Параметры определения слива топлива"""
    min_volume: float = 100.0
    """Минимальный объем слива, л"""
    max_fuel_speed: float = 0.300
    """Макс. Скорость изменения уровня топлива, л/с"""
    min_stoppage_duration: timedelta = timedelta(seconds=30)
    """Минимальная продолжительность остановки для определения слива, с"""
    ignore_on_speed: bool = False
    """Игнорировать сливы в движении"""
    ignore_duration_begin_move: timedelta = timedelta(seconds=0)
    """Игнорировать сообщения после начала движения, с"""


@dataclass
class ObjectFuelSettings(OrganizationEntity):
    """Настройки определения заправок|сливов для техники"""
    id: ObjectFuelSettingsId
    """"Идентификатор объекта настроек"""
    model_id: ObjectModelId
    """Идентификатор модели объекта диспетчеризации"""
    analytic_entity_id: AnalyticEntityId
    """Идентификатор параметра, отвечающего за топливо"""
    charge: FuelChargeSettings
    """Параметры определения заправки"""
    discharge: FuelDischargeSettings
    """Параметры определения слива топлива"""
    object_id: Optional[ObjectId] = None
    """Идентификатор объекта диспетчеризации"""
    created_at: Optional[datetime.datetime] = None
    """Создано в"""
    deleted_at: Optional[datetime.datetime] = None
    """Удалено в"""


@dataclass(kw_only=True)
class ObjectFuelIntervalSettings(ObjectFuelSettings):
    """Настройки определения заправок|сливов для техники на интервал времени"""
    id: ObjectFuelIntervalSettingsId
    """"Идентификатор объекта настроек"""
    interval: DateTimeInterval
    """Интервал"""

