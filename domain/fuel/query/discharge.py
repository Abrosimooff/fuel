from dataclasses import dataclass
from typing import Optional, List

from dpt.cqrs import Query
from dpt.domain.fuel import FuelDischarge
from dpt.domain.identity import OrganizationId, ObjectId
from dpt.domain.telemetry import AnalyticEntityId
from dpt.utils import DateTimeInterval


__all__ = (
    "LastFuelDischargeQuery",
    "FuelDischargeQuery",
)


@dataclass
class LastFuelDischargeQuery(Query[FuelDischarge]):
    """Запрос последнего слива по объекту и баку """
    object_id: ObjectId
    """Идентификатор объекта"""
    analytic_entity_id: AnalyticEntityId
    """Идентификатор параметра (бака)"""
    organization_id: Optional[OrganizationId | List[OrganizationId]] = None
    """Идентификатор организации"""


@dataclass
class FuelDischargeQuery(Query[List[FuelDischarge]]):
    """Запрос сливов по объекту"""
    object_id: ObjectId
    """Идентификатор объекта"""
    interval: DateTimeInterval
    """Интервал сливов"""
    organization_id: Optional[OrganizationId] = None
    """Идентификатор организации"""
