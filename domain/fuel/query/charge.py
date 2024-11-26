from dataclasses import dataclass
from typing import Optional, List

from dpt.cqrs import Query
from dpt.domain.fuel import FuelCharge
from dpt.domain.identity import OrganizationId, ObjectId
from dpt.domain.telemetry import AnalyticEntityId
from dpt.utils import DateTimeInterval


__all__ = (
    "LastFuelChargeQuery",
    "FuelChargeQuery",
)


@dataclass
class LastFuelChargeQuery(Query[FuelCharge]):
    """Запрос последней заправки по объекту и баку """
    object_id: ObjectId
    """Идентификатор объекта"""
    analytic_entity_id: AnalyticEntityId
    """Идентификатор параметра (бака)"""
    organization_id: Optional[OrganizationId | List[OrganizationId]] = None
    """Идентификатор организации"""


@dataclass
class FuelChargeQuery(Query[List[FuelCharge]]):
    """Запрос заправок по объекту"""
    object_id: ObjectId
    """Идентификатор объекта"""
    interval: DateTimeInterval
    """Интервал заправок"""
    organization_id: Optional[OrganizationId] = None
    """Идентификатор организации"""
