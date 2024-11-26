from typing import List, Optional
import pymongo
from dpt.domain.fuel import FuelCharge, FuelDischarge, ObjectFuelIntervalSettings, ObjectFuelIntervalSettingsId
from dpt.domain.fuel.entity import ObjectFuelSettings, ObjectFuelAnalyticEntity, ObjectFuelSettingsId
from dpt.domain.identity import OrganizationId, DeletionStatus, ObjectId, FuelChargeId, ObjectModelId
from dpt.domain.telemetry import AnalyticEntityId
from dpt.fuel.storage.interface import IObjectFuelSettingsStorage, IObjectFuelAnalyticEntityStorage, IFuelChargeStorage, \
    IFuelDischargeStorage, IObjectFuelIntervalSettingsStorage
from dpt.monro import BaseCRUDRepository, FilterBuilder
from dpt.utils import DateTimeOpenInterval


class ObjectFuelSettingsStorage(IObjectFuelSettingsStorage, BaseCRUDRepository):
    """Хранилище настроек заправок для объектов"""
    entity_class = ObjectFuelSettings
    collection_name = 'object_fuel_settings'

    async def query(
            self,
            id: Optional[ObjectFuelSettingsId | List[ObjectFuelSettingsId]] = None,
            organization_id: Optional[OrganizationId | List[OrganizationId]] = None,
            deletion: DeletionStatus = DeletionStatus.PRESENT
    ) -> List[ObjectFuelSettings]:
        return await self.find(
            FilterBuilder(
                instance_id=id,
                organization_id=organization_id
            ).by_deletion(deletion=deletion)
        )


class ObjectFuelIntervalSettingsStorage(IObjectFuelIntervalSettingsStorage, BaseCRUDRepository):
    """Хранилище настроек заправок для объектов на интервал времени"""
    entity_class = ObjectFuelIntervalSettings
    collection_name = 'object_fuel_interval_settings'

    async def query(
            self,
            id: Optional[ObjectFuelIntervalSettingsId | List[ObjectFuelIntervalSettingsId]] = None,
            organization_id: Optional[OrganizationId | List[OrganizationId]] = None,
            deletion: DeletionStatus = DeletionStatus.PRESENT
    ) -> List[ObjectFuelIntervalSettings]:
        return await self.find(
            FilterBuilder(
                instance_id=id,
                organization_id=organization_id
            ).by_deletion(deletion=deletion)
        )


class ObjectFuelAnalyticEntityStorage(IObjectFuelAnalyticEntityStorage, BaseCRUDRepository):
    """Хранилище возможных топливных анал. параметров для объектов """
    entity_class = ObjectFuelAnalyticEntity
    collection_name = 'object_fuel_analytic_entity'

    async def query(
            self,
            id: Optional[ObjectId | List[ObjectId]] = None,
            organization_id: Optional[OrganizationId | List[OrganizationId]] = None,
    ) -> List[ObjectFuelAnalyticEntity]:
        return await self.find(
            FilterBuilder(
                instance_id=id,
                organization_id=organization_id
            )
        )


class FuelChargeStorage(IFuelChargeStorage, BaseCRUDRepository):
    """Хранилище заправок"""
    entity_class = FuelCharge
    collection_name = 'charge'

    async def query(
            self,
            id: Optional[FuelChargeId | List[FuelChargeId]] = None,
            object_id: Optional[ObjectId | List[ObjectId]] = None,
            organization_id: Optional[OrganizationId | List[OrganizationId]] = None,
            interval: Optional[DateTimeOpenInterval] = None,
    ) -> List[ObjectFuelAnalyticEntity]:
        return await self.find(
            FilterBuilder(
                instance_id=id,
                organization_id=organization_id,
            ).by_equal(
                object_id=object_id,
            ).by_interval(
                is_interval=False,
                begin=interval,
                end=interval,
            )
        )

    async def get_last(
            self,
            object_id: ObjectId,
            analytic_entity_id: AnalyticEntityId,
            is_charge: Optional[bool] = None,
            organization_id: Optional[OrganizationId | List[OrganizationId]] = None,
    ) -> Optional[FuelCharge]:
        """Получить последнюю заправку"""
        filters = FilterBuilder(organization_id=organization_id).by_equal(
            object_id=object_id,
            analytic_entity_id=analytic_entity_id
        ).build()
        last_charge = await self.collection.find_one(filters, sort=[('begin', pymongo.DESCENDING)])
        if last_charge:
            return self._serde.deserialize(last_charge, self.entity_class)


class FuelDischargeStorage(IFuelDischargeStorage, BaseCRUDRepository):
    """Хранилище сливов топлива"""
    entity_class = FuelDischarge
    collection_name = 'discharge'

    async def query(
            self,
            id: Optional[FuelChargeId | List[FuelChargeId]] = None,
            object_id: Optional[ObjectId | List[ObjectId]] = None,
            organization_id: Optional[OrganizationId | List[OrganizationId]] = None,
            interval: Optional[DateTimeOpenInterval] = None,
    ) -> List[ObjectFuelAnalyticEntity]:
        return await self.find(
            FilterBuilder(
                instance_id=id,
                organization_id=organization_id
            ).by_equal(
                object_id=object_id,
            ).by_interval(
                is_interval=False,
                begin=interval,
                end=interval,
            )
        )

    async def get_last(
            self,
            object_id: ObjectId,
            analytic_entity_id: AnalyticEntityId,
            is_charge: Optional[bool] = None,
            organization_id: Optional[OrganizationId | List[OrganizationId]] = None,
    ) -> Optional[FuelDischarge]:
        """Получить последний слив"""
        filters = FilterBuilder(organization_id=organization_id).by_equal(
            object_id=object_id,
            analytic_entity_id=analytic_entity_id
        ).build()
        last_charge = await self.collection.find_one(filters, sort=[('begin', pymongo.DESCENDING)])
        if last_charge:
            return self._serde.deserialize(last_charge, self.entity_class)
