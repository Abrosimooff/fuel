import datetime
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Optional, List, Dict, Tuple

from dpt.component import interface
from dpt.domain.fuel import FuelCharge, FuelDischarge, ObjectFuelIntervalSettings
from dpt.domain.fuel.entity import ObjectFuelSettings, ObjectFuelAnalyticEntity, ObjectFuelSettingsId
from dpt.domain.identity import OrganizationId, DeletionStatus, ObjectId, FuelChargeId, ObjectModelId
from dpt.domain.telemetry import AnalyticEntityId
from dpt.cqrs.repository import ICRUDRepository
from dpt.utils import DateTimeOpenInterval


@interface
class IObjectFuelSettingsStorage(ICRUDRepository[ObjectFuelSettings], ABC):
    """Хранилище настроек заправок для объектов"""

    _data_by_model_id: Dict[Tuple[OrganizationId, ObjectModelId, AnalyticEntityId], ObjectFuelSettings]
    _data_by_object_id: Dict[Tuple[OrganizationId, ObjectId, AnalyticEntityId], ObjectFuelSettings]

    def __init__(self):
        super().__init__()
        self._data_by_model_id = {}
        self._data_by_object_id = {}

    @abstractmethod
    async def query(
        self,
        id: Optional[ObjectFuelSettingsId | List[ObjectFuelSettingsId]] = None,
        organization_id: Optional[OrganizationId | List[OrganizationId]] = None,
        deletion: DeletionStatus = DeletionStatus.PRESENT,
    ) -> List[ObjectFuelSettings]: ...

    async def load(self) -> None:
        """Загрузить все данные в локальный кэш"""
        items = await self.query()
        for item in items:
            if item.object_id:
                self._data_by_object_id[(item.organization_id, item.object_id, item.analytic_entity_id)] = item
            else:
                self._data_by_model_id[(item.organization_id, item.model_id, item.analytic_entity_id)] = item

    async def get_settings(
        self,
        organization_id: OrganizationId,
        analytic_entity_id: AnalyticEntityId,
        object_id: Optional[ObjectId] = None,
        model_id: Optional[ObjectModelId] = None,
    ) -> Optional[ObjectFuelSettings]:
        """Получить настройки для объекта или для модели"""
        settings = None
        if object_id:
            settings = self._data_by_object_id.get((organization_id, object_id, analytic_entity_id))
        if settings is None and model_id:
            settings = self._data_by_model_id.get((organization_id, model_id, analytic_entity_id))
        return settings


@interface
class IObjectFuelIntervalSettingsStorage(ICRUDRepository[ObjectFuelIntervalSettings], ABC):
    """Хранилище настроек заправок/сливов на интервал времени"""

    _data_by_model_id: Dict[Tuple[OrganizationId, ObjectModelId, AnalyticEntityId], List[ObjectFuelIntervalSettings]]
    _data_by_object_id: Dict[Tuple[OrganizationId, ObjectId, AnalyticEntityId], List[ObjectFuelIntervalSettings]]

    def __init__(self):
        super().__init__()
        self._data_by_model_id = defaultdict(list)
        self._data_by_object_id = defaultdict(list)

    @abstractmethod
    async def query(
        self,
        id: Optional[ObjectFuelSettingsId | List[ObjectFuelSettingsId]] = None,
        organization_id: Optional[OrganizationId | List[OrganizationId]] = None,
        deletion: DeletionStatus = DeletionStatus.PRESENT,
    ) -> List[ObjectFuelIntervalSettings]: ...

    async def load(self) -> None:
        """Загрузить все данные в локальный кэш"""
        items = await self.query()
        for item in items:
            if item.object_id:
                self._data_by_object_id[(item.organization_id, item.object_id, item.analytic_entity_id)].append(item)
            else:
                self._data_by_model_id[(item.organization_id, item.model_id, item.analytic_entity_id)].append(item)

    async def get_settings(
        self,
        time: datetime.datetime,
        organization_id: OrganizationId,
        analytic_entity_id: AnalyticEntityId,
        object_id: Optional[ObjectId] = None,
        model_id: Optional[ObjectModelId] = None,
    ) -> Optional[ObjectFuelIntervalSettings]:
        """Получить настройки для объекта или для модели на конкретное время"""
        settings = None
        if object_id:
            settings_list = self._data_by_object_id[(organization_id, object_id, analytic_entity_id)]
            for setting_item in settings_list:
                if setting_item.interval.begin < time <= setting_item.interval.end:
                    settings = setting_item
                    break

        if settings is None and model_id:
            settings_list = self._data_by_model_id[(organization_id, model_id, analytic_entity_id)]
            for setting_item in settings_list:
                if setting_item.interval.begin < time <= setting_item.interval.end:
                    settings = setting_item
                    break
        return settings


@interface
class IObjectFuelAnalyticEntityStorage(ICRUDRepository[ObjectFuelAnalyticEntity], ABC):
    """Хранилище возможных топливных анал. параметров для объектов"""

    @abstractmethod
    async def query(
        self,
        id: Optional[ObjectId | List[ObjectId]] = None,
        organization_id: Optional[OrganizationId | List[OrganizationId]] = None,
    ) -> List[ObjectFuelAnalyticEntity]: ...


@interface
class IFuelChargeStorage(ICRUDRepository[FuelCharge], ABC):
    """Хранилище заправок"""

    @abstractmethod
    async def query(
        self,
        id: Optional[FuelChargeId | List[FuelChargeId]] = None,
        object_id: Optional[ObjectId | List[ObjectId]] = None,
        organization_id: Optional[OrganizationId | List[OrganizationId]] = None,
        interval: Optional[DateTimeOpenInterval] = None,
    ) -> List[FuelCharge]: ...

    async def get_last(
        self,
        object_id: ObjectId,
        analytic_entity_id: AnalyticEntityId,
        organization_id: Optional[OrganizationId | List[OrganizationId]] = None,
    ) -> Optional[FuelCharge]: ...


@interface
class IFuelDischargeStorage(ICRUDRepository[FuelDischarge], ABC):
    """Хранилище сливов"""

    @abstractmethod
    async def query(
        self,
        id: Optional[FuelChargeId | List[FuelChargeId]] = None,
        object_id: Optional[ObjectId | List[ObjectId]] = None,
        organization_id: Optional[OrganizationId | List[OrganizationId]] = None,
        interval: Optional[DateTimeOpenInterval] = None,
    ) -> List[FuelDischarge]: ...

    async def get_last(
        self,
        object_id: ObjectId,
        analytic_entity_id: AnalyticEntityId,
        organization_id: Optional[OrganizationId | List[OrganizationId]] = None,
    ) -> Optional[FuelDischarge]: ...
