from typing import Optional, List

from dpt.domain.fuel import FuelCharge, ObjectFuelSettings, ObjectFuelSettingsId, FuelDischarge, \
    ObjectFuelIntervalSettingsId, ObjectFuelIntervalSettings
from dpt.domain.identity import FuelChargeId, ObjectId, OrganizationId, DeletionStatus, FuelDischargeId
from dpt.domain.telemetry import AnalyticEntityId
from dpt.fuel.storage.interface import IFuelChargeStorage, IObjectFuelSettingsStorage, IFuelDischargeStorage, \
    IObjectFuelIntervalSettingsStorage
from dpt.monro import LocalDictCRUDRepository


class LocalFuelChargeStorage(IFuelChargeStorage, LocalDictCRUDRepository):
    """Локальное хранилище заправок"""
    entity_class = FuelCharge

    async def query(
            self,
            id: Optional[FuelChargeId | List[FuelChargeId]] = None,
            object_id: Optional[ObjectId | List[ObjectId]] = None,
            organization_id: Optional[OrganizationId | List[OrganizationId]] = None,
    ) -> List[FuelCharge]:
        filters = {}
        if id is not None:
            filters["id"] = id
        if object_id is not None:
            filters["object_id"] = object_id
        if organization_id is not None:
            filters["organization_id"] = organization_id
        return await self.find(filters)

    async def get_last(
            self,
            object_id: ObjectId,
            analytic_entity_id: AnalyticEntityId,
            organization_id: Optional[OrganizationId | List[OrganizationId]] = None,
    ) -> Optional[FuelCharge]:
        filters = {}
        if object_id is not None:
            filters["object_id"] = object_id
        if analytic_entity_id is not None:
            filters["analytic_entity_id"] = analytic_entity_id
        if organization_id is not None:
            filters["organization_id"] = organization_id
        items = await self.find(filters)
        if items:
            items.sort(key=lambda x: x.begin, reverse=True)
            return items[0]


class LocalFuelDischargeStorage(IFuelDischargeStorage, LocalDictCRUDRepository):
    """Локальное хранилище сливов"""
    entity_class = FuelDischarge

    async def query(
            self,
            id: Optional[FuelDischargeId | List[FuelDischargeId]] = None,
            object_id: Optional[ObjectId | List[ObjectId]] = None,
            organization_id: Optional[OrganizationId | List[OrganizationId]] = None,
    ) -> List[FuelDischarge]:
        filters = {}
        if id is not None:
            filters["id"] = id
        if object_id is not None:
            filters["object_id"] = object_id
        if organization_id is not None:
            filters["organization_id"] = organization_id
        return await self.find(filters)

    async def get_last(
            self,
            object_id: ObjectId,
            analytic_entity_id: AnalyticEntityId,
            organization_id: Optional[OrganizationId | List[OrganizationId]] = None,
    ) -> Optional[FuelDischarge]:
        filters = {}
        if object_id is not None:
            filters["object_id"] = object_id
        if analytic_entity_id is not None:
            filters["analytic_entity_id"] = analytic_entity_id
        if organization_id is not None:
            filters["organization_id"] = organization_id
        items = await self.find(filters)
        if items:
            items.sort(key=lambda x: x.begin, reverse=True)
            return items[0]


class LocalObjectFuelSettingsStorage(IObjectFuelSettingsStorage, LocalDictCRUDRepository):
    """Локальное хранилище настроек заправок для объектов"""

    async def query(
            self,
            id: Optional[ObjectFuelSettingsId | List[ObjectFuelSettingsId]] = None,
            organization_id: Optional[OrganizationId | List[OrganizationId]] = None,
            deletion: DeletionStatus = DeletionStatus.PRESENT
    ) -> List[ObjectFuelSettings]:
        filters = {}
        if id is not None:
            filters["id"] = id
        if organization_id is not None:
            filters["organization_id"] = organization_id
        return await self.find(filters)


class LocalObjectFuelIntervalSettingsStorage(IObjectFuelIntervalSettingsStorage, LocalDictCRUDRepository):
    """Локальное хранилище настроек заправок для объектов на период"""

    async def query(
            self,
            id: Optional[ObjectFuelIntervalSettingsId | List[ObjectFuelIntervalSettingsId]] = None,
            organization_id: Optional[OrganizationId | List[OrganizationId]] = None,
            deletion: DeletionStatus = DeletionStatus.PRESENT
    ) -> List[ObjectFuelIntervalSettings]:
        filters = {}
        if id is not None:
            filters["id"] = id
        if organization_id is not None:
            filters["organization_id"] = organization_id
        return await self.find(filters)
