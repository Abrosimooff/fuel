from abc import ABC, abstractmethod
from typing import List

from dpt.component import get_utility
from dpt.cqrs import QueryHandler
from dpt.domain.fuel import ChargeChartIntervalQuery, DischargeChartIntervalQuery
from dpt.domain.telemetry import ChartIntervalQuery, ChartInterval
from dpt.utils import DateTimeInterval

from ...storage.interface import IFuelChargeStorage, IFuelDischargeStorage

__all__ = (
    "ChargeChartIntervalQueryHandler",
    "DischargeChartIntervalQueryHandler",
)


class BaseChartIntervalQueryHandler(ABC):

    @property
    @abstractmethod
    def storage_class(self) -> IFuelChargeStorage | IFuelDischargeStorage:
        ...

    async def handle(self, query: ChartIntervalQuery) -> List[ChartInterval]:
        return [
            ChartInterval(
                object_id=charge.object_id,
                interval=DateTimeInterval(
                    begin=charge.begin,
                    end=charge.end,
                ),
                attributes={
                    "volume_begin": charge.volume_begin,
                    "volume_end": charge.volume_end,
                },
            )
            for charge in await get_utility(self.storage_class).query(
                object_id=query.object_id,
                organization_id=query.organization_id,
                interval=query.interval,
            )
        ]


class ChargeChartIntervalQueryHandler(BaseChartIntervalQueryHandler, QueryHandler[ChargeChartIntervalQuery]):
    storage_class = IFuelChargeStorage


class DischargeChartIntervalQueryHandler(BaseChartIntervalQueryHandler, QueryHandler[DischargeChartIntervalQuery]):
    storage_class = IFuelDischargeStorage
