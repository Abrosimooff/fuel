import datetime
import logging
from typing import Optional

from dpt.domain.alerta import CreateAlertCommand, Alert, AlertTypeId
from dpt.domain.fuel import FuelChargeSettings, FuelCharge, BeginFuelChargeCommand, EndFuelChargeCommand, \
    SetFuelChargeCommand, FuelDischargeSettings, FuelDischarge, BeginFuelDischargeCommand, SetFuelDischargeCommand, \
    EndFuelDischargeCommand, DeleteFuelDischargeCommand
from dpt.domain.identity import OrganizationId, ObjectId
from dpt.domain.telemetry import AnalyticEntity
from dpt.fuel.logic.state import ChargeState, FuelDataEvent, State, FuelStateData, DischargeState, DischargeStateEnum

logger = logging.getLogger(__name__)


class ChargeFSM:
    """State машина для определения Заправок"""
    SPEED = 0

    def __init__(
            self,
            organization_id: OrganizationId,
            object_id: ObjectId,
            analytic_entity: AnalyticEntity,
            settings: FuelChargeSettings,
            object_state: ChargeState,
    ):
        self.organization_id = organization_id
        self.object_id = object_id
        self.analytic_entity = analytic_entity
        self.settings = settings
        self.object_state = object_state

    def __repr__(self):
        return "<ChargeFSM {!r}>".format(self.object_state)

    async def process(self, event: FuelDataEvent) -> Optional[FuelCharge]:
        """Обработать событие с данными о топливе"""

        if event.state_data.time < self.object_state.current_data.time:
            logger.warning(
                f"Time from past {event.object_id=} {event.state_data.time=} < {self.object_state.current_data.time}")
            return

        handler = self._map.get(self.object_state.state)
        if handler is None:
            raise TypeError(f"Unknown state {self.object_state.state}")

        await self.begin_move_handler(event)
        state = await handler(self, event)
        self.object_state.set_event(event, state)
        return self.object_state.current_charge

    async def begin_move_handler(self, event: FuelDataEvent) -> None:
        """Обработчик начала движения."""
        if self.settings.ignore_duration_begin_move:
            if self.object_state.current_data.speed == 0 and event.state_data.speed > 0:
                self.object_state.set_begin_move_threshold(
                    event.state_data.time + self.settings.ignore_duration_begin_move)

    async def fsm_charging(self, event: FuelDataEvent) -> State:
        """Обработка сообщения в состоянии "ЗАПРАВКА" """

        # Если уровень топлива стал меньше, чем в предыдущем состоянии - входим в MAYBE_FREE
        if event.state_data.fuel_volume < self.object_state.current_data.fuel_volume:
            self.object_state.set_time_threshold(self.settings.min_duration_out)
            return State.MAYBE_FREE
        else:
            await self.continue_charging(event)
            return State.CHARGING

    async def fsm_free(self, event: FuelDataEvent) -> State:
        """Обработка сообщения в состоянии "СВОБОДЕН ОТ ЗАПРАВКИ" """

        # Если уровень топлива стал больше, чем в предыдущем сообщении - входим в MAYBE_CHARGING
        if event.state_data.fuel_volume > self.object_state.current_data.fuel_volume:

            # Если игнорируем нечаянное определение заправок на скорости и есть скорость - FREE
            if self.settings.ignore_on_speed and event.state_data.speed > self.SPEED:
                return State.FREE

            # Если в этом сообщении произошла внезапная заправка - фиксируем
            if self.settings.min_duration_sudden:
                if self.object_state.is_sudden_charge(
                        event,
                        min_fuel_volume=self.settings.min_volume,
                        time_threshold=self.settings.min_duration_sudden
                ):
                    # Начинаем заправку с момента предыдущего сообщения
                    await self.start_charging(begin_state=self.object_state.current_data, event=event)
                    return State.CHARGING

            self.object_state.set_time_threshold(self.settings.min_duration_in)
            self.object_state.set_fuel_volume_threshold(self.settings.min_volume)
            return State.MAYBE_CHARGING
        else:
            return State.FREE

    async def fsm_maybe_charging(self, event: FuelDataEvent) -> State:
        """Обработка сообщения в состоянии "ВОЗМОЖНО ЗАПРАВКА" """

        # Если игнорируем нечаянное определение заправок на скорости и есть скорость - FREE
        if self.settings.ignore_on_speed and event.state_data.speed > self.SPEED:
            return State.FREE

        # Если игнорируем сообщения после начала движения, и ещё не дождались порога - FREE
        if self.settings.ignore_duration_begin_move and \
                not self.object_state.begin_move_threshold_is_completed(event.state_data.time):
            return State.FREE

        # Если уровень топлива стал меньше, чем в предыдущем состоянии - выходим
        if event.state_data.fuel_volume < self.object_state.current_data.fuel_volume:
            return State.FREE
        else:

            if self.object_state.time_threshold_is_completed(event.state_data.time) and \
                    self.object_state.fuel_volume_threshold_is_completed(event.state_data.fuel_volume):
                # Начинаем заправку с момента попадания в MAYBE_CHARGING
                await self.start_charging(begin_state=self.object_state.state_data, event=event)
                return State.CHARGING
            return State.MAYBE_CHARGING

    async def fsm_maybe_free(self, event: FuelDataEvent) -> State:
        """Обработка сообщения в состоянии "ВОЗМОЖНО СВОБОДЕН ОТ ЗАПРАВКИ" """

        # Если уровень топлива меньше или равен, чем в предыдущем сообщении (+ порог времени) - входим в FREE
        if event.state_data.fuel_volume <= self.object_state.current_data.fuel_volume:
            if self.object_state.time_threshold_is_completed(event.state_data.time):
                await self.stop_charging(event)
                return State.FREE
            else:
                return State.MAYBE_FREE
        else:
            # Если топливо увеличилось на скорости, возможно выход их заправки
            if event.state_data.speed > 0:
                return State.MAYBE_FREE
            else:
                return State.CHARGING

    _map = {
        State.CHARGING: fsm_charging,
        State.FREE: fsm_free,
        State.MAYBE_CHARGING: fsm_maybe_charging,
        State.MAYBE_FREE: fsm_maybe_free,
    }

    async def start_charging(self, begin_state: FuelStateData, event: FuelDataEvent):
        fuel_charge = await self.object_state.start_charging(begin_state, event)
        await BeginFuelChargeCommand(object=fuel_charge).execute()
        await CreateAlertCommand(
            organization_id=self.organization_id,
            object_id=self.object_id,
            alert=Alert(
                resource=self.object_id.hex,
                event=AlertTypeId("fuel_charge_begin"),
                service=["fuel"],
                createTime=begin_state.time,
                attributes={
                    "tank_name": self.analytic_entity.name,
                    "volume_begin": fuel_charge.volume_begin,
                    "volume_end": fuel_charge.volume_end,
                    "volume": fuel_charge.volume,
                    "begin_time": fuel_charge.begin.isoformat(),
                    "end_time": fuel_charge.end.isoformat(),
                },
                text=f"Началась заправка ({self.analytic_entity.name})"
            ),
        ).execute()
        logger.info('Start charging %s', fuel_charge)

    async def continue_charging(self, event: FuelDataEvent):
        fuel_charge = await self.object_state.continue_charging(event)
        await SetFuelChargeCommand(object=fuel_charge).execute()

    async def stop_charging(self, event: FuelDataEvent):
        fuel_charge = await self.object_state.stop_charging(event)
        await EndFuelChargeCommand(object=fuel_charge).execute()
        await CreateAlertCommand(
            organization_id=self.organization_id,
            object_id=self.object_id,
            alert=Alert(
                resource=self.object_id.hex,
                event=AlertTypeId("fuel_charge_end"),
                service=["fuel"],
                createTime=event.state_data.time,
                attributes={
                    "tank_name": self.analytic_entity.name,
                    "volume_begin": fuel_charge.volume_begin,
                    "volume_end": fuel_charge.volume_end,
                    "volume": fuel_charge.volume,
                    "begin_time": fuel_charge.begin.isoformat(),
                    "end_time": fuel_charge.end.isoformat(),
                },
                text=f"Окончилась заправка ({self.analytic_entity.name})"
            ),
        ).execute()
        logger.info('Stop charging %s', fuel_charge)


class DischargeFSM:
    """State машина для определения сливов"""
    CHECK_DISCHARGE_DURATION = datetime.timedelta(seconds=60)  # Время проверки подлинности слива (после слива)

    def __init__(
            self,
            organization_id: OrganizationId,
            object_id: ObjectId,
            analytic_entity: AnalyticEntity,
            settings: FuelDischargeSettings,
            object_state: DischargeState,
    ):
        self.organization_id = organization_id
        self.object_id = object_id
        self.analytic_entity = analytic_entity
        self.settings = settings
        self.object_state = object_state

    def __repr__(self):
        return "<DischargeFSM {!r}>".format(self.object_state)

    async def process(self, event: FuelDataEvent) -> Optional[FuelDischarge]:
        """Обработать событие с данными о топливе"""

        if event.state_data.time < self.object_state.current_data.time:
            logger.warning(
                f"Time from past {event.object_id=} {event.state_data.time=} < {self.object_state.current_data.time}")
            return

        handler = self._map.get(self.object_state.state)
        if handler is None:
            raise TypeError(f"Unknown state {self.object_state.state}")

        event.state_data.set_fuel_speed(prev_state=self.object_state.current_data)
        await self.move_handler(event)
        state = await handler(self, event)
        self.object_state.set_event(event, state)
        return self.object_state.current_discharge

    async def move_handler(self, event: FuelDataEvent) -> None:
        """Обработчик начала движения|остановки"""

        # Если началось движение
        if self.settings.ignore_duration_begin_move:
            if self.object_state.current_data.speed == 0 and event.state_data.speed > 0:
                self.object_state.set_begin_move_threshold(
                    event.state_data.time + self.settings.ignore_duration_begin_move)

        # Если началась остановка
        if self.settings.min_stoppage_duration:
            if self.object_state.current_data.speed > 0 and event.state_data.speed == 0:
                self.object_state.set_stop_time_threshold(
                    event.state_data.time + self.settings.min_stoppage_duration)
                # todo этот трешходл должен работать только пока машина стоит в остановке

    async def fsm_discharging(self, event: FuelDataEvent) -> DischargeStateEnum:
        """Обработка сообщения в состоянии "СЛИВ" """

        # Если "скорость уменьшения топлива" стоит на месте (уровень не меняется) - ничего не меняем
        if event.state_data.fuel_speed == 0:
            await self.continue_discharging(event)
            return DischargeStateEnum.DISCHARGING

        # Если "скорость уменьшения топлива" ВСЁ ВРЕМЯ превышает максимальную - Всё ещё слив
        if event.state_data.fuel_speed < 0 and \
                abs(event.state_data.fuel_speed) > abs(self.settings.max_fuel_speed):
            await self.continue_discharging(event)
            return DischargeStateEnum.DISCHARGING
        else:
            # Выход в состояние "Проверка ложности слива"
            self.object_state.set_check_time_threshold(event.state_data.time + self.CHECK_DISCHARGE_DURATION)
            self.object_state.clear_check_values()
            return DischargeStateEnum.EXIT_DISCHARGING

    async def fsm_norm(self, event: FuelDataEvent) -> DischargeStateEnum:
        """Обработка сообщения в состоянии "НОРМА" """

        # Если игнорируем нечаянное определение сливов на скорости и есть скорость - NORM
        if self.settings.ignore_on_speed and event.state_data.speed > 0:
            return DischargeStateEnum.NORM

        # Если игнорируем сообщения после начала движения, и ещё не дождались порога - NORM
        if self.settings.ignore_duration_begin_move and \
                not self.object_state.begin_move_threshold_is_completed(event.state_data.time):
            return DischargeStateEnum.NORM

        # Если "скорость уменьшения топлива" превысила максимальную - MAYBE_DISCHARGING
        if event.state_data.fuel_speed < 0 and abs(event.state_data.fuel_speed) > abs(self.settings.max_fuel_speed):
            self.object_state.set_fuel_volume_threshold(self.settings.min_volume)  # Устанавливаем мин. объём слива
            return DischargeStateEnum.MAYBE_DISCHARGING
        else:
            return DischargeStateEnum.NORM

    async def fsm_maybe_discharging(self, event: FuelDataEvent) -> DischargeStateEnum:
        """Обработка сообщения в состоянии "ВОЗМОЖНО СЛИВ" """

        # Если игнорируем сообщения после начала движения, и ещё не дождались порога - NORM
        if self.settings.ignore_duration_begin_move and \
                not self.object_state.begin_move_threshold_is_completed(event.state_data.time):
            return DischargeStateEnum.NORM

        # Если "скорость уменьшения топлива" стоит на месте (уровень не меняется) - ничего не меняем
        if event.state_data.fuel_speed == 0:
            return DischargeStateEnum.MAYBE_DISCHARGING

        # Если "скорость уменьшения топлива" ВСЁ ВРЕМЯ превышает максимальную
        if (event.state_data.fuel_speed <= 0 and
                abs(event.state_data.fuel_speed) > abs(self.settings.max_fuel_speed)):

            # Если превысили проги по времени и объёму - DISCHARGING
            if self.object_state.stop_time_threshold_is_completed(event.state_data.time) and \
                    self.object_state.fuel_volume_threshold_is_completed(event.state_data.fuel_volume):
                # Начинаем заправку с момента попадания в MAYBE_CHARGING
                await self.start_discharging(begin_state=self.object_state.state_data, event=event)
                return DischargeStateEnum.DISCHARGING

            return DischargeStateEnum.MAYBE_DISCHARGING
        else:
            return DischargeStateEnum.NORM

    async def fsm_exit_discharging(self, event: FuelDataEvent) -> DischargeStateEnum:
        """Обработка сообщения в состоянии Выход из слива (Проверка подлинности слива)"""

        # Если порог времени на выход ещё не окончен
        if not self.object_state.check_time_threshold_is_complete(event.state_data.time):

            # Если скорость падения топлива снова превышает максимальную И
            # уровень топлива стал меньше, чем на конец слива - продолжаем слив
            if event.state_data.fuel_speed <= 0 and \
                    abs(event.state_data.fuel_speed) > abs(self.settings.max_fuel_speed) and \
                    event.state_data.fuel_volume < self.object_state.current_discharge.volume_end:
                return DischargeStateEnum.DISCHARGING
            else:
                # добавляем значение топлива для подсчета среднего за период "выход из слива"
                self.object_state.add_check_value(event.state_data.fuel_volume)
                return DischargeStateEnum.EXIT_DISCHARGING
        else:
            if self.object_state.check_discharge_is_confirmed(min_volume=self.settings.min_volume):
                # Если слив подтвердился - заканчиваем, сохраняем
                await self.stop_discharging(event)
            else:
                # Если слив НЕ подтвердился - удаляем
                await self.cancel_discharging()

            return DischargeStateEnum.NORM

    _map = {
        DischargeStateEnum.DISCHARGING: fsm_discharging,
        DischargeStateEnum.NORM: fsm_norm,
        DischargeStateEnum.MAYBE_DISCHARGING: fsm_maybe_discharging,
        DischargeStateEnum.EXIT_DISCHARGING: fsm_exit_discharging,
    }

    async def start_discharging(self, begin_state: FuelStateData, event: FuelDataEvent):
        fuel_discharge = await self.object_state.start_discharging(begin_state, event)
        await BeginFuelDischargeCommand(object=fuel_discharge).execute()
        await CreateAlertCommand(
            organization_id=self.organization_id,
            object_id=self.object_id,
            alert=Alert(
                resource=self.object_id.hex,
                event=AlertTypeId("fuel_discharge_begin"),
                service=["fuel"],
                createTime=begin_state.time,
                attributes={
                    "tank_name": self.analytic_entity.name,
                    "volume_begin": fuel_discharge.volume_begin,
                    "volume_end": fuel_discharge.volume_end,
                    "volume": fuel_discharge.volume,
                    # todo speed
                    "begin_time": fuel_discharge.begin.isoformat(),
                    "end_time": fuel_discharge.end.isoformat(),
                },
                text=f"Возможно, начался слив топлива ({self.analytic_entity.name})"
            ),
        ).execute()
        logger.info('Start Discharging %s', fuel_discharge)

    async def continue_discharging(self, event: FuelDataEvent):
        fuel_discharge = await self.object_state.continue_discharging(event)
        await SetFuelDischargeCommand(object=fuel_discharge).execute()

    async def stop_discharging(self, event: FuelDataEvent):
        """Закончить слив. Оповестить о зафиксированном сливе"""
        fuel_discharge = await self.object_state.stop_discharging(event)
        await EndFuelDischargeCommand(object=fuel_discharge).execute()
        await CreateAlertCommand(
            organization_id=self.organization_id,
            object_id=self.object_id,
            alert=Alert(
                resource=self.object_id.hex,
                event=AlertTypeId("fuel_discharge_end"),
                service=["fuel"],
                createTime=event.state_data.time,
                attributes={
                    "tank_name": self.analytic_entity.name,
                    "volume_begin": fuel_discharge.volume_begin,
                    "volume_end": fuel_discharge.volume_end,
                    "volume": fuel_discharge.volume,
                    "begin_time": fuel_discharge.begin.isoformat(),
                    "end_time": fuel_discharge.end.isoformat(),
                },
                text=f"Зафиксирован слив топлива ({self.analytic_entity.name})"
            ),
        ).execute()
        logger.info('Stop Discharging %s', fuel_discharge)

    async def cancel_discharging(self):
        logger.info('Cancel Discharging id=%s', self.object_state.current_discharge)
        await DeleteFuelDischargeCommand(
            object_id=self.object_state.current_discharge.id,
            organization_id=self.object_state.current_discharge.organization_id
        ).execute()
        await self.object_state.cancel_discharging()

