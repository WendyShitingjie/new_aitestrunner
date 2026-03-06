import uuid
from datetime import datetime, timedelta
from ..function_registry import function_registry

@function_registry.register("uuid")
def get_uuid():
    return str(uuid.uuid4()).replace('-', '')

@function_registry.register("timestamp")
def get_timestamp():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

@function_registry.register("timestamp_minus_minutes")
def timestamp_minus_minutes(minutes: int):
    return (datetime.now() - timedelta(minutes=int(minutes))).strftime('%Y-%m-%d %H:%M:%S')

