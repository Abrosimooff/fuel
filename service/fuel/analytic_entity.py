from typing import Mapping, List, Set
from dpt.component import implements
from dpt.component.utils import Singleton
from dpt.config import IConfigurationProvider, Configuration
from dpt.domain.telemetry import AnalyticEntity, AnalyticEntityId


__all__ = (
    'FuelAnalyticEntitiesStorage',
    'AnalyticEntityConfigProvider',
)


class FuelAnalyticEntitiesStorage(metaclass=Singleton):
    """Все топливные аналитические параметры"""
    list: List[AnalyticEntity]
    dict: Mapping[AnalyticEntityId, AnalyticEntity]
    ids: Set[AnalyticEntityId]

    @classmethod
    def create(cls, entities: List[AnalyticEntity]):
        store = cls()
        store.list = entities
        store.dict = {item.id: item for item in store.list}
        store.ids = set([x.id for x in store.list])


@implements
class AnalyticEntityConfigProvider(IConfigurationProvider):
    section = 'analytic_entity'

    def parse_section(self, config: Configuration, section: Mapping):
        FuelAnalyticEntitiesStorage.create(entities=[AnalyticEntity(**parameters) for parameters in section])
