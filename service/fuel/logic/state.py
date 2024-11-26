import datetime
from dataclasses import dataclass, replace, field
from enum import StrEnum
from typing import Optional, Self, List

from dpt.domain.fuel import FuelCharge, FuelDischarge
from dpt.domain.identity import OrganizationId, ObjectId, ObjectModelId, FuelChargeId, FuelDischargeId
from dpt.domain.telemetry import AnalyticEntity
from dpt.geojson import Point
from dpt.utils import gen_uuid


@dataclass
class FuelStateData:
    """Данные о состоянии бака на момент времени"""
    time: datetime.datetime
    """Время сообщения"""
    speed: float
    """Скорость"""
    fuel_volume: float
    """Объём топлива, л"""
    location: Optional[Point] = None
    """Положение"""
    fuel_speed: float = 0.0
    """Скорость изменения уровня топлива л/с"""

    def set_fuel_speed(self, prev_state: Self) -> None:
        """Посчитать и задать скорость изменения топлива от предыдущего состояния"""
        duration = (self.time - prev_state.time).total_seconds()
        volume_delta = self.fuel_volume - prev_state.fuel_volume
        if duration > 0 and volume_delta:
            self.fuel_speed = volume_delta / duration


@dataclass
class FuelDataEvent:
    """Данные о топливе из события"""
    organization_id: OrganizationId
    """Идентификатор организации"""
    object_id: ObjectId
    """Идентификатор объекта диспетчеризации"""
    model_id: ObjectModelId
    """Идентификатор модели объекта"""
    fuel_entity: AnalyticEntity
    """Аналит. параметр (Бак/Цистерна)"""
    state_data: FuelStateData
    """Состояние бака"""


class State(StrEnum):
    MAYBE_CHARGING = 'MAYBE_CHARGING'
    """Возможно заправка"""
    MAYBE_FREE = 'MAYBE_FREE'
    """Возможно свободен"""
    CHARGING = 'CHARGING'
    """Заправка"""
    FREE = 'FREE'
    """Свободен"""


@dataclass
class ChargeState:
    """Состояние объекта для определения заправки"""
    state: State
    """Состояние"""
    current_data: FuelStateData
    """Данные о состоянии бака (текущие)"""
    state_data: FuelStateData
    """Данные о состоянии бака (на начало состояния)"""

    time_threshold: Optional[datetime.datetime] = None
    """Пороговое время. Время, когда можно перейти в следующее состояние"""
    fuel_volume_threshold: Optional[float] = None
    """Пороговый объем. Объём, когда можно перейти в следующее состояние"""
    current_charge: Optional[FuelCharge] = None
    """Текущая заправка"""
    begin_move_threshold: Optional[datetime.datetime] = None
    """Пороговое время. Время, когда можно обрабатывать сообщения (после начала движения)"""

    def set_event(self, event: FuelDataEvent, state: State):
        if self.state != state:
            self.state = state
            self.state_data = replace(self.current_data)  # Запоминаем с каких данных начался state

        self.current_data = replace(event.state_data)     # Меняем текущие данные state

    def set_begin_move_threshold(self, begin_move_threshold: datetime.datetime):
        """Время, когда можно обрабатывать сообщения (после начала движения)"""
        self.begin_move_threshold = begin_move_threshold

    def begin_move_threshold_is_completed(self, time: datetime.datetime):
        """Наступило ли пороговое время после начала движения ?"""
        return self.begin_move_threshold < time if self.begin_move_threshold else True

    def set_time_threshold(self, time_threshold: datetime.timedelta):
        """Установить время, когда можно перейти в следующее состояние"""
        self.time_threshold = self.current_data.time + time_threshold

    def time_threshold_is_completed(self, time: datetime.datetime) -> bool:
        """Наступило ли пороговое время ?"""
        return time >= self.time_threshold

    def set_fuel_volume_threshold(self, fuel_volume_threshold: float):
        """Установить объём, когда можно перейти в следующее состояние"""
        self.fuel_volume_threshold = self.current_data.fuel_volume + fuel_volume_threshold

    def fuel_volume_threshold_is_completed(self, fuel_volume: float) -> bool:
        """Наступило ли пороговое время ?"""
        return fuel_volume >= self.fuel_volume_threshold

    def set_current_charge(self, current_charge: Optional[FuelCharge]):
        """Задать текущую заправку"""
        self.current_charge = current_charge

    def is_sudden_charge(self, event: FuelDataEvent, min_fuel_volume: float, time_threshold: datetime.timedelta) -> bool:
        """
        Произошла ли внезапная заправка в этом сообщении ?
        Т.е с момента последнего сообщения прошло time_threshold и было заправлено более min_fuel_volume
        """
        volume = event.state_data.fuel_volume - self.current_data.fuel_volume
        delta = event.state_data.time - self.current_data.time
        return volume > min_fuel_volume and delta > time_threshold

    async def start_charging(self, begin_state: FuelStateData, event: FuelDataEvent) -> FuelCharge:
        """Начинаем заправку, когда мы в состоянии MAYBE_CHARGING (перед переходом в CHARGING) """
        volume = event.state_data.fuel_volume - begin_state.fuel_volume
        fuel_charge = FuelCharge(
            id=FuelChargeId(gen_uuid()),
            organization_id=event.organization_id,
            object_id=event.object_id,
            analytic_entity_id=event.fuel_entity.id,

            location=begin_state.location,
            begin=begin_state.time,
            volume_begin=begin_state.fuel_volume,
            is_complete=False,

            end=event.state_data.time,
            volume_end=event.state_data.fuel_volume,
            volume=volume,
        )
        self.set_current_charge(fuel_charge)
        return fuel_charge

    async def continue_charging(self, event: FuelDataEvent) -> FuelCharge:
        """Продолжаем заправку, когда мы в состоянии CHARGING """
        self.current_charge.end = event.state_data.time
        self.current_charge.volume_end = event.state_data.fuel_volume
        self.current_charge.volume = self.current_charge.volume_end - self.current_charge.volume_begin
        return self.current_charge

    async def stop_charging(self, event: FuelDataEvent) -> FuelCharge:
        """Оканчиваем заправку, когда мы в состоянии MAYBE_FREE (перед переходом в FREE) """
        self.current_charge.is_complete = True
        return self.current_charge

    @classmethod
    def from_event(cls, event: FuelDataEvent) -> Self:
        """Создаем FREE STATE """
        return cls(
            state=State.FREE,
            current_data=replace(event.state_data),
            state_data=replace(event.state_data),
        )

    @classmethod
    def from_charge(cls, charge: FuelCharge) -> Optional[Self]:
        """Если есть неоконченная заправка - то создаем CHARGING STATE """
        if charge.is_complete:
            return None

        state_data = FuelStateData(
            time=charge.begin,
            fuel_volume=charge.volume_begin,
            location=charge.location,
            speed=0,
        )
        current_data = FuelStateData(
            time=charge.end,
            fuel_volume=charge.volume_end,
            location=charge.location,
            speed=0,
        )
        state = cls(
            state=State.CHARGING,
            current_data=current_data,
            state_data=state_data
        )
        state.set_current_charge(charge)
        return state


class DischargeStateEnum(StrEnum):
    NORM = 'NORM'
    """Состояние нормы"""
    MAYBE_DISCHARGING = 'MAYBE_DISCHARGING'
    """Возможно слив"""
    DISCHARGING = 'DISCHARGING'
    """Слив"""
    EXIT_DISCHARGING = 'EXIT_DISCHARGING'
    """Выход из слива (определение подлинности)"""


@dataclass
class DischargeState:
    """Состояние объекта для определения слива"""
    state: DischargeStateEnum
    """Состояние"""
    current_data: FuelStateData
    """Данные о состоянии бака (текущие)"""
    state_data: FuelStateData
    """Данные о состоянии бака (на начало состояния)"""

    stop_time_threshold: Optional[datetime.datetime] = None
    """Пороговое время в остановке, когда можно перейти в следующее состояние"""
    fuel_volume_threshold: Optional[float] = None
    """Пороговый объем. Объём, когда можно перейти в следующее состояние"""
    current_discharge: Optional[FuelDischarge] = None
    """Текущий слив"""
    begin_move_threshold: Optional[datetime.datetime] = None
    """Пороговое время. Время, когда можно обрабатывать сообщения (после начала движения)"""

    check_time_threshold: Optional[datetime.datetime] = None
    """Пороговое время. Время окончания состояния "Выход из слива" """
    check_values: List[float] = field(default_factory=list)
    """ Значения уровня топлива в состоянии "Выход из слива" """

    def set_event(self, event: FuelDataEvent, state: DischargeStateEnum):
        if self.state != state:
            self.state = state
            self.state_data = replace(self.current_data)  # Запоминаем с каких данных начался state

        self.current_data = replace(event.state_data)     # Меняем текущие данные state

    def set_begin_move_threshold(self, begin_move_threshold: datetime.datetime):
        """Время, когда можно обрабатывать сообщения (после начала движения)"""
        self.begin_move_threshold = begin_move_threshold

    def begin_move_threshold_is_completed(self, time: datetime.datetime):
        """Наступило ли пороговое время после начала движения ?"""
        return self.begin_move_threshold < time if self.begin_move_threshold else True

    def set_stop_time_threshold(self, time_threshold: datetime.datetime):
        """Установить время, когда можно перейти в следующее состояние"""
        self.stop_time_threshold = time_threshold

    def stop_time_threshold_is_completed(self, time: datetime.datetime) -> bool:
        """Наступило ли пороговое время ?"""
        return not self.stop_time_threshold or time >= self.stop_time_threshold

    def set_fuel_volume_threshold(self, fuel_volume_threshold: float):
        """Установить объём, когда можно перейти в следующее состояние"""
        self.fuel_volume_threshold = self.current_data.fuel_volume - fuel_volume_threshold

    def fuel_volume_threshold_is_completed(self, fuel_volume: float) -> bool:
        """Опустился ли объём ниже порогового объёма ?"""
        return fuel_volume <= self.fuel_volume_threshold

    def set_current_discharge(self, current_discharge: Optional[FuelDischarge]):
        """Задать текущий слив"""
        self.current_discharge = current_discharge

    def set_check_time_threshold(self, time_threshold: datetime.datetime):
        """Задать пороговое время окончания периода проверки ложности слива"""
        self.check_time_threshold = time_threshold

    def add_check_value(self, value: float):
        """Добавить значение топлива в период проверки ложности слива"""
        if value is not None:
            self.check_values.append(value)

    def clear_check_values(self):
        """Очистить значения проверки ложности слива"""
        self.check_values = []

    def check_time_threshold_is_complete(self, time: datetime.datetime):
        """Наступило ли пороговое время проверки ложности слива ?"""
        return time >= self.check_time_threshold

    def check_discharge_is_confirmed(self, min_volume: float) -> bool:
        """Проверка подтвердилась ли заправка или ложная"""
        avg_fuel_volume = self.get_check_avg_fuel_volume()
        if avg_fuel_volume is not None:
            # Если разница уровня топлива на начало слива и средним значение на выходе из слива больше MIN
            # И общий объём слива больше MIN - считаем слив подтвержденным.
            delta = self.current_discharge.volume_begin - avg_fuel_volume
            return delta > min_volume and self.current_discharge.volume > min_volume

    def get_check_avg_fuel_volume(self) -> Optional[float]:
        """Получить средний уровень топлива за время проверки ложности слива"""
        if self.check_values:
            return sum(self.check_values) / len(self.check_values)

    async def start_discharging(self, begin_state: FuelStateData, event: FuelDataEvent) -> FuelDischarge:
        """Начинаем слив"""
        volume = begin_state.fuel_volume - event.state_data.fuel_volume
        fuel_discharge = FuelDischarge(
            id=FuelDischargeId(gen_uuid()),
            organization_id=event.organization_id,
            object_id=event.object_id,
            analytic_entity_id=event.fuel_entity.id,

            location=begin_state.location,
            begin=begin_state.time,
            volume_begin=begin_state.fuel_volume,
            is_complete=False,

            end=event.state_data.time,
            volume_end=event.state_data.fuel_volume,
            volume=volume,
        )
        self.set_current_discharge(fuel_discharge)
        return fuel_discharge

    async def continue_discharging(self, event: FuelDataEvent) -> Optional[FuelDischarge]:
        """Продолжаем слив"""
        self.current_discharge.end = event.state_data.time
        self.current_discharge.volume_end = event.state_data.fuel_volume
        self.current_discharge.volume = self.current_discharge.volume_begin - self.current_discharge.volume_end
        return self.current_discharge

    async def cancel_discharging(self) -> None:
        self.current_discharge = None

    async def stop_discharging(self, event: FuelDataEvent) -> Optional[FuelDischarge]:
        """Оканчиваем слив """
        self.current_discharge.is_complete = True
        return self.current_discharge

    @classmethod
    def from_event(cls, event: FuelDataEvent) -> Self:
        """Создаем NORM STATE """
        return cls(
            state=DischargeStateEnum.NORM,
            current_data=replace(event.state_data),
            state_data=replace(event.state_data),
        )

    @classmethod
    def from_discharge(cls, discharge: FuelDischarge) -> Optional[Self]:
        """Если есть неоконченная заправка - то создаем DISCHARGING STATE """
        if discharge.is_complete:
            return None

        state_data = FuelStateData(
            time=discharge.begin,
            fuel_volume=discharge.volume_begin,
            location=discharge.location,
            speed=0,
        )
        current_data = FuelStateData(
            time=discharge.end,
            fuel_volume=discharge.volume_end,
            location=discharge.location,
            speed=0,
        )
        return cls(
            state=DischargeStateEnum.DISCHARGING,
            current_data=current_data,
            state_data=state_data,
            current_discharge=discharge
        )
