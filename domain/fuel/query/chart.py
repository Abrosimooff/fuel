from dataclasses import dataclass

from dpt.domain.telemetry import ChartIntervalQuery

__all__ = (
    "ChargeChartIntervalQuery",
    "DischargeChartIntervalQuery",
)


@dataclass
class ChargeChartIntervalQuery(ChartIntervalQuery):
    ...


@dataclass
class DischargeChartIntervalQuery(ChartIntervalQuery):
    ...
