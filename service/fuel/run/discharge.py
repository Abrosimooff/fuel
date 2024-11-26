import logging
import os
from typing import Any, Optional

from dpt.common import IPort, EntrypointLauncher
from dpt.component import implements, get_utility
from dpt.config import Configuration
from dpt.cqrs import IEventBus
from dpt.domain.fuel import ObjectFuelSettingsModifiedEvent, ObjectFuelSettingsDeletedEvent, FuelDischarge, \
    FuelDischargeSettings, ObjectFuelIntervalSettingsModifiedEvent, ObjectFuelIntervalSettingsDeletedEvent
from dpt.domain.telemetry import FullTelemetryEvent
from dpt.fuel.analytic_entity import FuelAnalyticEntitiesStorage
from dpt.fuel.logic.fsm import DischargeFSM
from dpt.fuel.logic.state import FuelDataEvent, FuelStateData
from dpt.fuel.logic.storage import FuelDischargeStateStorage
from dpt.fuel.storage.interface import IObjectFuelSettingsStorage, IObjectFuelIntervalSettingsStorage
from dpt.geojson import Point


@implements
class FuelDischargeService(IPort):
    """Сервис определения сливов"""

    def __init__(self, **kwargs: Any):
        self._bus = get_utility(IEventBus)
        self._state_storage = FuelDischargeStateStorage()
        self._fuel_entities = FuelAnalyticEntitiesStorage()
        self._settings_storage = get_utility(IObjectFuelSettingsStorage)
        self._interval_settings_storage = get_utility(IObjectFuelIntervalSettingsStorage)
        self._logger = logging.getLogger(self.__class__.__name__)
        super().__init__(**kwargs)

    async def _on_start(self):
        await self.load_settings()

    async def load_settings(self):
        await self._settings_storage.load()
        await self._interval_settings_storage.load()
        self._logger.info('FuelSettingsStorage loaded.')

    async def _stop(self, err: Exception = None) -> None:
        pass

    async def _start(self):
        await self._on_start()

        async with self._bus as bus:
            async for event in bus.consume(
                    FullTelemetryEvent,
                    ObjectFuelSettingsModifiedEvent,
                    ObjectFuelSettingsDeletedEvent,
                    ObjectFuelIntervalSettingsModifiedEvent,
                    ObjectFuelIntervalSettingsDeletedEvent
            ):
                match event:
                    case FullTelemetryEvent():
                        await self.on_telemetry_event(event)
                    case ObjectFuelSettingsModifiedEvent():
                        await self.load_settings()
                    case ObjectFuelSettingsDeletedEvent():
                        await self.load_settings()
                    case ObjectFuelIntervalSettingsModifiedEvent():
                        await self.load_settings()
                    case ObjectFuelIntervalSettingsDeletedEvent():
                        await self.load_settings()

    async def on_telemetry_event(self, event: FullTelemetryEvent):
        """Обработать событие телеметрии"""
        for fuel_entity in self._fuel_entities.list:
            fuel_value = event.get_parameter_value(fuel_entity.msg_attr, None)
            if fuel_value is not None:
                fuel_event = FuelDataEvent(
                    organization_id=event.enterprise_id,
                    model_id=event.model_id,
                    object_id=event.object_id,
                    fuel_entity=fuel_entity,
                    state_data=FuelStateData(
                        time=event.time,
                        speed=event.get_parameter_value("speed", 0.0),
                        location=Point(event.location) if event.location else None,
                        fuel_volume=fuel_value,
                    )
                )
                discharge = await self.process_fuel_event(fuel_event)

    async def process_fuel_event(self, fuel_event: FuelDataEvent) -> Optional[FuelDischarge]:
        """Обработать топливное событие"""
        fsm = await self.create_fsm(fuel_event)
        discharge = await fsm.process(fuel_event)
        await self.save_fsm(fsm)
        return discharge

    async def get_settings(self, fuel_event: FuelDataEvent) -> FuelDischargeSettings:
        # Поиск интервальных настроек на текущее время
        settings = await self._interval_settings_storage.get_settings(
            time=fuel_event.state_data.time,
            organization_id=fuel_event.organization_id,
            analytic_entity_id=fuel_event.fuel_entity.id,
            object_id=fuel_event.object_id,
            model_id=fuel_event.model_id,
        )
        if not settings:
            # Поиск постоянных настроек
            settings = await self._settings_storage.get_settings(
                organization_id=fuel_event.organization_id,
                analytic_entity_id=fuel_event.fuel_entity.id,
                object_id=fuel_event.object_id,
                model_id=fuel_event.model_id
            )
        return settings.discharge if settings else FuelDischargeSettings()


    async def create_fsm(self, fuel_event: FuelDataEvent) -> DischargeFSM:
        """Создать State машину для определения сливов"""
        charge_settings = await self.get_settings(fuel_event)
        object_state = await self._state_storage.get(fuel_event)
        return DischargeFSM(
            organization_id=fuel_event.organization_id,
            object_id=fuel_event.object_id,
            analytic_entity=fuel_event.fuel_entity,
            settings=charge_settings,
            object_state=object_state,
        )

    async def save_fsm(self, fsm: DischargeFSM):
        await self._state_storage.set(fsm.object_id, fsm.analytic_entity.id, fsm.object_state)


if __name__ == "__main__":
    from dpt.fuel.analytic_entity import AnalyticEntityConfigProvider  # Чтобы подключился провайдер
    config = Configuration.from_file(os.getenv("CONFIGURATION_FILE", "config.toml"))
    launcher = EntrypointLauncher()
    launcher.launch()