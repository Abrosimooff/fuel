from typing import Optional, Dict, Tuple
from dpt.component.utils import Singleton
from dpt.domain.identity import ObjectId, OrganizationId
from dpt.domain.telemetry import AnalyticEntityId
from .state import ChargeState, FuelDataEvent, DischargeState

from dpt.domain.fuel import LastFuelChargeQuery, LastFuelDischargeQuery

__all__ = (
    "FuelChargeStateStorage",
    "FuelDischargeStateStorage"
)


class FuelChargeStateStorage(metaclass=Singleton):
    """Хранилище состояний заправки"""

    def __init__(self):
        self._state: Dict[Tuple[ObjectId, AnalyticEntityId], ChargeState] = {}

    async def get(self, event: FuelDataEvent) -> ChargeState:
        object_id = event.object_id
        analytic_entity_id = event.fuel_entity.id
        organization_id = event.organization_id
        key = (object_id, analytic_entity_id)
        if key not in self._state:
            state = await self.load_state(object_id, analytic_entity_id, organization_id)
            if state is None:
                state = ChargeState.from_event(event)
            self._state[key] = state
        return self._state[key]

    async def set(self, object_id: ObjectId, analytic_entity_id: AnalyticEntityId, state: ChargeState) -> None:
        self._state[(object_id, analytic_entity_id)] = state

    async def load_state(
            self,
            object_id:
            ObjectId,
            analytic_entity_id: AnalyticEntityId,
            organization_id: OrganizationId
    ) -> Optional[ChargeState]:
        charge = await LastFuelChargeQuery(
            object_id=object_id,
            analytic_entity_id=analytic_entity_id,
            organization_id=organization_id,
        ).fetch()
        if charge:
            return ChargeState.from_charge(charge)


class FuelDischargeStateStorage(metaclass=Singleton):
    """Хранилище состояний сливов"""

    def __init__(self):
        self._state: Dict[Tuple[ObjectId, AnalyticEntityId], DischargeState] = {}

    async def get(self, event: FuelDataEvent) -> DischargeState:
        object_id = event.object_id
        analytic_entity_id = event.fuel_entity.id
        organization_id = event.organization_id
        key = (object_id, analytic_entity_id)
        if key not in self._state:
            state = await self.load_state(object_id, analytic_entity_id, organization_id)
            if state is None:
                state = DischargeState.from_event(event)
            self._state[key] = state
        return self._state[key]

    async def set(self, object_id: ObjectId, analytic_entity_id: AnalyticEntityId, state: DischargeState) -> None:
        self._state[(object_id, analytic_entity_id)] = state

    async def load_state(
            self,
            object_id: ObjectId,
            analytic_entity_id: AnalyticEntityId,
            organization_id: OrganizationId
    ) -> Optional[DischargeState]:
        charge = await LastFuelDischargeQuery(
            object_id=object_id,
            analytic_entity_id=analytic_entity_id,
            organization_id=organization_id,
        ).fetch()
        if charge:
            return DischargeState.from_discharge(charge)
