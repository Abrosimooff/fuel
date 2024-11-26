from typing import Optional, List

from dpt.component import get_utility
from dpt.cqrs import CommandHandler
from dpt.cqrs.exception import ValidationError
from dpt.domain.fuel import SetObjectFuelSettingsCommand, DeleteObjectFuelSettingsCommand, \
    RestoreObjectFuelSettingsCommand, SetObjectFuelIntervalSettingsCommand, ObjectFuelIntervalSettings, \
    ObjectFuelIntervalSettingsModifiedEvent, DeleteObjectFuelIntervalSettingsCommand, \
    ObjectFuelIntervalSettingsDeletedEvent, RestoreObjectFuelIntervalSettingsCommand
from dpt.domain.fuel.entity import ObjectFuelSettings
from dpt.domain.fuel.event import ObjectFuelSettingsModifiedEvent, ObjectFuelSettingsDeletedEvent
from dpt.fuel.analytic_entity import FuelAnalyticEntitiesStorage
from dpt.fuel.storage.interface import IObjectFuelSettingsStorage, IObjectFuelAnalyticEntityStorage, \
    IObjectFuelIntervalSettingsStorage
from dpt.monro import FilterBuilder
from dpt.monro.command.implements import MongoSetObjectMixin, MongoDeleteObjectMixin, MongoRestoreObjectMixin


__all__ = (
    "SetObjectFuelSettingsCommandHandler",
    "DeleteObjectFuelSettingsCommandHandler",
    "RestoreObjectFuelSettingsCommandHandler",

    "SetObjectFuelIntervalSettingsCommandHandler",
    "DeleteObjectFuelIntervalSettingsCommandHandler",
    "RestoreObjectFuelIntervalSettingsCommandHandler"
)


class ValidateSettingsMixin:

    async def get_existed_settings_by_model_id(self, instance: ObjectFuelSettings | ObjectFuelIntervalSettings)\
            -> List[ObjectFuelSettings | ObjectFuelIntervalSettings]:
        """Запросить существующие настройки для этой модели и этого анал. параметра"""
        return await self.storage.find(
            FilterBuilder(
                organization_id=instance.organization_id).by_equal(
                analytic_entity_id=instance.analytic_entity_id,
                model_id=instance.model_id,
            ).is_null(object_id=True)
        )

    async def get_existed_settings_by_object_id(self, instance: ObjectFuelSettings | ObjectFuelIntervalSettings)\
            -> List[ObjectFuelSettings | ObjectFuelIntervalSettings]:
        """Запросить существующие настройки для этого объекта и этого анал. параметра"""
        return await self.storage.find(
            FilterBuilder(
                organization_id=instance.organization_id).by_equal(
                analytic_entity_id=instance.analytic_entity_id,
                object_id=instance.object_id
            )
        )

    async def validate_analytic_entity_by_model_id(self, instance: ObjectFuelSettings | ObjectFuelIntervalSettings)\
            -> bool:
        """Проверка, что выбранный аналитический параметр доступен дял модели """
        return instance.analytic_entity_id in FuelAnalyticEntitiesStorage().ids

    async def validate_existed_settings_by_model_id(self, instance: ObjectFuelSettings | ObjectFuelIntervalSettings)\
            -> bool:
        """Проверка, что таких же настроек для модели не существует """
        existed_settings = await self.get_existed_settings_by_model_id(instance=instance)
        return (not existed_settings) or (existed_settings[0].id == instance.id)

    async def validate_object_id(self, instance: ObjectFuelSettings | ObjectFuelIntervalSettings) -> bool:
        """Проверка, что объект диспетчеризации доступен для топливных настроек """
        object_storage = get_utility(IObjectFuelAnalyticEntityStorage)
        object_analytic_entity = await object_storage.query(id=instance.object_id)
        return bool(object_analytic_entity)

    async def validate_analytic_entity_by_object_id(self, instance: ObjectFuelSettings | ObjectFuelIntervalSettings)\
            -> bool:
        """Проверка, что выбранный аналитический параметр доступен для объекта диспетчеризации """
        object_storage = get_utility(IObjectFuelAnalyticEntityStorage)
        object_analytic_entity = await object_storage.query(id=instance.object_id)
        if not object_analytic_entity:
            return False
        available_analytic_entity_ids = object_analytic_entity[0].analytic_entity_ids
        return instance.analytic_entity_id in available_analytic_entity_ids

    async def validate_existed_settings_by_object_id(self, instance: ObjectFuelSettings | ObjectFuelIntervalSettings)\
            -> bool:
        """Проверка, что таких же настроек для объекта диспетчеризации не существует """
        existed_settings = await self.get_existed_settings_by_object_id(instance=instance)
        return (not existed_settings) or (existed_settings[0].id == instance.id)


class SetObjectFuelSettingsCommandHandler(MongoSetObjectMixin, ValidateSettingsMixin, CommandHandler[SetObjectFuelSettingsCommand]):
    """Сохранение настроек заправок/сливов"""
    model_class = ObjectFuelSettings
    storage_class = IObjectFuelSettingsStorage
    event_class = ObjectFuelSettingsModifiedEvent

    async def validate(self, instance: ObjectFuelSettings, is_created: Optional[bool] = None):
        if instance.object_id:
            if not await self.validate_object_id(instance):
                raise ValidationError(
                    "Настройки нельзя сохранить. Выбранный объект недоступен для определения заправок.")

            if not await self.validate_analytic_entity_by_object_id(instance):
                raise ValidationError(
                    "Настройки нельзя сохранить. Выбранный топливный параметр недоступен для объекта.")

            if not await self.validate_existed_settings_by_object_id(instance):
                raise ValidationError(
                    "Настройки нельзя сохранить. Настройки для выбранного объекта и параметра уже существуют."
                )
        else:
            if not await self.validate_analytic_entity_by_model_id(instance):
                raise ValidationError("Настройки нельзя сохранить. Выбранный топливный параметр недоступен.")

            if not await self.validate_existed_settings_by_model_id(instance):
                raise ValidationError(
                    "Настройки нельзя сохранить. Настройки для выбранной модели и параметра уже существуют."
                )


class DeleteObjectFuelSettingsCommandHandler(MongoDeleteObjectMixin, CommandHandler[DeleteObjectFuelSettingsCommand]):
    """Сохранение настроек заправок/сливов"""
    model_class = ObjectFuelSettings
    storage_class = IObjectFuelSettingsStorage
    event_class = ObjectFuelSettingsDeletedEvent


class RestoreObjectFuelSettingsCommandHandler(MongoRestoreObjectMixin, CommandHandler[RestoreObjectFuelSettingsCommand]):
    """Сохранение настроек заправок/сливов"""
    model_class = ObjectFuelSettings
    storage_class = IObjectFuelSettingsStorage
    event_class = ObjectFuelSettingsModifiedEvent


class SetObjectFuelIntervalSettingsCommandHandler(MongoSetObjectMixin, ValidateSettingsMixin, CommandHandler[SetObjectFuelIntervalSettingsCommand]):
    """Сохранение настроек заправок/сливов на интервал времени"""
    model_class = ObjectFuelIntervalSettings
    storage_class = IObjectFuelIntervalSettingsStorage
    event_class = ObjectFuelIntervalSettingsModifiedEvent

    async def validate(self, instance: ObjectFuelSettings, is_created: Optional[bool] = None):
        if instance.object_id:
            if not await self.validate_object_id(instance):
                raise ValidationError(
                    "Настройки нельзя сохранить. Выбранный объект недоступен для определения заправок.")

            if not await self.validate_analytic_entity_by_object_id(instance):
                raise ValidationError(
                    "Настройки нельзя сохранить. Выбранный топливный параметр недоступен для объекта.")

            if not await self.validate_existed_settings_by_object_id(instance):
                raise ValidationError(
                    "Настройки нельзя сохранить. Настройки для выбранного объекта и параметра уже существуют "
                    "и пересекаются с выбранным интервалом."
                )
        else:
            if not await self.validate_analytic_entity_by_model_id(instance):
                raise ValidationError("Настройки нельзя сохранить. Выбранный топливный параметр недоступен")

            if not await self.validate_existed_settings_by_model_id(instance):
                raise ValidationError(
                    "Настройки нельзя сохранить. Настройки для выбранной модели и параметра уже существуют "
                    "и пересекаются с выбранным интервалом."
                )

    async def get_existed_settings_by_object_id(self, instance: ObjectFuelSettings | ObjectFuelIntervalSettings)\
            -> List[ObjectFuelSettings | ObjectFuelIntervalSettings]:
        """Запросить существующие настройки для этого объекта и этого анал. параметра (КОТОРЫЕ ПЕРЕСЕКАЮТСЯ)"""
        return await self.storage.find(
            FilterBuilder(
                organization_id=instance.organization_id).by_equal(
                analytic_entity_id=instance.analytic_entity_id,
                object_id=instance.object_id
            ).by_interval(is_interval=True, interval=instance.interval)
        )

    async def get_existed_settings_by_model_id(self, instance: ObjectFuelSettings | ObjectFuelIntervalSettings)\
            -> List[ObjectFuelSettings | ObjectFuelIntervalSettings]:
        """Запросить существующие настройки для этой модели и этого анал. параметра (КОТОРЫЕ ПЕРЕСЕКАЮТСЯ)"""
        return await self.storage.find(
            FilterBuilder(
                organization_id=instance.organization_id).by_equal(
                analytic_entity_id=instance.analytic_entity_id,
                model_id=instance.model_id,
            ).is_null(object_id=True).by_interval(is_interval=True, interval=instance.interval)
        )


class DeleteObjectFuelIntervalSettingsCommandHandler(MongoDeleteObjectMixin, CommandHandler[DeleteObjectFuelIntervalSettingsCommand]):
    """Сохранение настроек заправок/сливов на интервал времени"""
    model_class = ObjectFuelIntervalSettings
    storage_class = IObjectFuelIntervalSettingsStorage
    event_class = ObjectFuelIntervalSettingsDeletedEvent


class RestoreObjectFuelIntervalSettingsCommandHandler(MongoRestoreObjectMixin, CommandHandler[RestoreObjectFuelIntervalSettingsCommand]):
    """Сохранение настроек заправок/сливов на интервал времени"""
    model_class = ObjectFuelIntervalSettings
    storage_class = IObjectFuelIntervalSettingsStorage
    event_class = ObjectFuelIntervalSettingsModifiedEvent
