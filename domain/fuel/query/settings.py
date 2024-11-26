from dataclasses import dataclass
from typing import List, Optional

from dpt.cqrs import Query
from dpt.domain.fuel import ObjectFuelIntervalSettings, ObjectFuelIntervalSettingsId
from dpt.domain.fuel.entity import ObjectFuelSettings, ObjectFuelSettingsId, ObjectFuelAnalyticEntity
from dpt.domain.identity import OrganizationId, DeletionStatus

__all__ = (
    "ObjectFuelSettingsQuery",
    "ObjectFuelIntervalSettingsQuery",
    "ObjectFuelAnalyticEntityQuery"
)


@dataclass
class ObjectFuelSettingsQuery(Query[List[ObjectFuelSettings]]):
    """Запрос настроек определения заправок/сливов"""
    id: Optional[ObjectFuelSettingsId | List[ObjectFuelSettingsId]] = None
    organization_id: Optional[OrganizationId | List[OrganizationId]] = None
    deletion: DeletionStatus = DeletionStatus.PRESENT


@dataclass
class ObjectFuelIntervalSettingsQuery(Query[List[ObjectFuelIntervalSettings]]):
    """Запрос настроек определения заправок/сливов на интервал времени"""
    id: Optional[ObjectFuelIntervalSettingsId | List[ObjectFuelIntervalSettingsId]] = None
    organization_id: Optional[OrganizationId | List[OrganizationId]] = None
    deletion: DeletionStatus = DeletionStatus.PRESENT


@dataclass
class ObjectFuelAnalyticEntityQuery(Query[List[ObjectFuelAnalyticEntity]]):
    """Запрос доступных баков/цистерн у единиц техники"""
    id: Optional[ObjectFuelSettingsId | List[ObjectFuelSettingsId]] = None
    organization_id: Optional[OrganizationId | List[OrganizationId]] = None
