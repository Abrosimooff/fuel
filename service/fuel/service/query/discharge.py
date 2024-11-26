from typing import Optional

from dpt.component import inject
from dpt.cqrs import QueryHandler
from dpt.domain.fuel import LastFuelDischargeQuery, FuelDischarge
from dpt.fuel.storage.interface import IFuelDischargeStorage

__all__ = (
    "LastFuelDischargeQueryHandler",
)


class LastFuelDischargeQueryHandler(QueryHandler[LastFuelDischargeQuery]):
    """Запрос последнего слива по объекту и баку"""

    @inject
    async def handle(self, query: LastFuelDischargeQuery, storage: IFuelDischargeStorage) -> Optional[FuelDischarge]:
        return await storage.get_last(
            object_id=query.object_id,
            analytic_entity_id=query.analytic_entity_id,
            organization_id=query.organization_id,
        )

