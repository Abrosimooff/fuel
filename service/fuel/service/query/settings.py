from typing import List

from dpt.component import inject
from dpt.cqrs import QueryHandler
from dpt.domain.fuel import ObjectFuelIntervalSettings
from dpt.domain.fuel.entity import ObjectFuelSettings, ObjectFuelAnalyticEntity
from dpt.domain.fuel.query.settings import ObjectFuelSettingsQuery, ObjectFuelAnalyticEntityQuery, \
    ObjectFuelIntervalSettingsQuery
from dpt.fuel.storage.interface import IObjectFuelSettingsStorage, IObjectFuelAnalyticEntityStorage, \
    IObjectFuelIntervalSettingsStorage

__all__ = (
    "ObjectFuelSettingsQueryHandler",
    "ObjectFuelIntervalSettingsQueryHandler",
    "ObjectFuelAnalyticEntityQueryHandler"
)


class ObjectFuelSettingsQueryHandler(QueryHandler[ObjectFuelSettingsQuery]):
    """Запрос настроек определения заправок/сливов"""

    @inject
    async def handle(self, query: ObjectFuelSettingsQuery, storage: IObjectFuelSettingsStorage)\
            -> List[ObjectFuelSettings]:
        return await storage.query(
            id=query.id,
            organization_id=query.organization_id,
            deletion=query.deletion
        )


class ObjectFuelIntervalSettingsQueryHandler(QueryHandler[ObjectFuelIntervalSettingsQuery]):
    """Запрос настроек определения заправок/сливов на интервал времени"""

    @inject
    async def handle(self, query: ObjectFuelIntervalSettingsQuery, storage: IObjectFuelIntervalSettingsStorage) \
            -> List[ObjectFuelIntervalSettings]:
        return await storage.query(
            id=query.id,
            organization_id=query.organization_id,
            deletion=query.deletion
        )


class ObjectFuelAnalyticEntityQueryHandler(QueryHandler[ObjectFuelAnalyticEntityQuery]):
    """Запрос доступных баков/цистерн у единиц техники"""

    @inject
    async def handle(self, query: ObjectFuelAnalyticEntityQuery, storage: IObjectFuelAnalyticEntityStorage)\
            -> List[ObjectFuelAnalyticEntity]:
        return await storage.query(
            id=query.id,
            organization_id=query.organization_id,
        )
