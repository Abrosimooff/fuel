import datetime
from typing import List, Dict

from dpt.domain.telemetry import FullTelemetryEvent
from dpt.serde.encoder.json import JsonEncoder


def load_telemetry_file(file_name: str) -> List[Dict]:
    """Загрузить сообщения телеметрии из файла"""
    with open(file_name, 'r') as telemetry_file:
        return JsonEncoder().loads(telemetry_file.read())


def make_full_telemetry_event(message: Dict):
    """Сделать из сырого сообщения FullTelemetryEvent"""
    location = message.get('location')
    return FullTelemetryEvent(
        object_id=message['object_id'],
        enterprise_id=message['enterprise_id'],
        time=message['time'],
        receive_time=message.get('receive_time', None) or datetime.datetime.utcnow(),
        location=tuple(location) if location else None,
        params={
            key: value for key, value in message.items()
            if key not in ('_id', 'object_id', 'model_id', 'enterprise_id', 'time', 'receive_time', 'location')
            and value is not None
        }
    )
