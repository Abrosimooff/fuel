import datetime
from dataclasses import dataclass

from dpt.domain.identity import ObjectId, FuelChargeId, FuelDischargeId, OrganizationEntity
from dpt.domain.telemetry import AnalyticEntityId
from dpt.geojson import Point

__all__ = (
    "FuelCharge",
    "FuelDischarge",
)


@dataclass
class FuelChargeBase(OrganizationEntity):
    """Заправка/Слив"""
    id: FuelChargeId
    """"Идентификатор заправки/слива"""
    object_id: ObjectId
    """Идентификатор объекта диспетчеризации"""
    analytic_entity_id: AnalyticEntityId
    """Параметр (бак/цистерна)"""
    location: Point
    """Положение на начало заправки"""
    begin: datetime.datetime
    """Время начала заправки"""
    end: datetime.datetime
    """Время окончания заправки"""
    is_complete: bool
    """Заправка/слив завершено?"""
    volume: float
    """Общий объём заправки/слива"""
    volume_begin: float
    """Объём топлива на начало заправки"""
    volume_end: float
    """Объём топлива на окончание заправки"""


@dataclass
class FuelCharge(FuelChargeBase):
    """Заправка топлива"""
    id: FuelChargeId
    """"Идентификатор заправки/слива"""


@dataclass
class FuelDischarge(FuelChargeBase):
    """Слив топлива"""
    id: FuelDischargeId
    """"Идентификатор заправки/слива"""
