from dataclasses import dataclass
from typing import List

from dpt.domain.identity import ObjectId, OrganizationEntity
from dpt.domain.telemetry import AnalyticEntityId

__all__ = (
    "ObjectFuelAnalyticEntity",
)


@dataclass
class ObjectFuelAnalyticEntity(OrganizationEntity):
    """Топливные аналитические параметры единицы техники"""
    id: ObjectId
    """Идентификатор объекта диспетчеризации"""
    analytic_entity_ids: List[AnalyticEntityId]
    """Идентификаторы параметров, отвечающих за топливо"""
