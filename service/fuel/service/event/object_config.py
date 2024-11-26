from dpt.component import inject
from dpt.cqrs import EventHandler
from dpt.cqrs.bus import UnitOfWork
from dpt.domain.fuel.entity import ObjectFuelAnalyticEntity
from dpt.domain.telemetry import ObjectConfigurationModifiedEvent, AnalyticEntityId
from dpt.fuel.analytic_entity import FuelAnalyticEntitiesStorage
from dpt.fuel.storage.interface import IObjectFuelAnalyticEntityStorage

__all__ = (
    "ObjectConfigurationModifiedEventHandler",
)


class ObjectConfigurationModifiedEventHandler(EventHandler[ObjectConfigurationModifiedEvent]):
    """Обработчик события изменения конфигурации оборудования объекта"""

    @inject
    async def handle(self, event: ObjectConfigurationModifiedEvent, storage: IObjectFuelAnalyticEntityStorage):
        analytic_entity_ids = set()
        for controller_config in event.object.controllers:
            for analytic_settings in controller_config.analytic_settings:
                if analytic_settings.analytic_entity_id in FuelAnalyticEntitiesStorage().ids:
                    if analytic_settings.analytic_entity_id not in analytic_entity_ids:
                        analytic_entity_ids.add(AnalyticEntityId(analytic_settings.analytic_entity_id))

        if analytic_entity_ids:
            saved_object = ObjectFuelAnalyticEntity(
                id=event.object.id,
                organization_id=event.object.enterprise_id,
                analytic_entity_ids=sorted(analytic_entity_ids)
            )
            # Сохраняем список доступных топливных аналит. параметров для объекта диспетчеризации
            async with UnitOfWork() as unit_of_work:
                await storage.set(saved_object, unit_of_work)
        else:
            # Удаляем список доступных топливных аналит. параметров для объекта диспетчеризации
            async with UnitOfWork() as unit_of_work:
                await storage.delete(event.object.id, unit_of_work)
