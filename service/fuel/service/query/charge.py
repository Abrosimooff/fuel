from typing import Optional

from dpt.component import inject
from dpt.cqrs import QueryHandler
from dpt.domain.fuel import LastFuelChargeQuery, FuelCharge
from dpt.fuel.storage.interface import IFuelChargeStorage


__all__ = (
    "LastFuelChargeQueryHandler",
)


class LastFuelChargeQueryHandler(QueryHandler[LastFuelChargeQuery]):
    """Запрос последней заправки по объекту и баку"""

    @inject
    async def handle(self, query: LastFuelChargeQuery, storage: IFuelChargeStorage) -> Optional[FuelCharge]:
        return await storage.get_last(
            object_id=query.object_id,
            analytic_entity_id=query.analytic_entity_id,
            organization_id=query.organization_id,
        )

