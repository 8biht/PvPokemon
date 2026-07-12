"""Optional Kafka adapter for publishing domain events.

This module tries to use kafka-python (KafkaProducer) if available and a
bootstrap server is configured. If either condition is missing it falls back
to a no-op publisher so the app continues to work without Kafka.

To enable Kafka, set environment variable KAFKA_BOOTSTRAP_SERVERS to a
comma-separated list (e.g. 'localhost:9092') and install `kafka-python`.
"""
import os
import json
from typing import Any, Dict, Optional

KAFKA_TOPIC = os.environ.get('KAFKA_TOPIC', 'pvpokemon.box_events')
BOOTSTRAP = os.environ.get('KAFKA_BOOTSTRAP_SERVERS')


class _NoOpProducer:
    def send(self, topic, value):
        return None


_producer = None
_enabled = False

if BOOTSTRAP:
    try:
        from kafka import KafkaProducer
        _producer = KafkaProducer(bootstrap_servers=BOOTSTRAP.split(','), value_serializer=lambda v: json.dumps(v).encode('utf-8'))
        _enabled = True
    except Exception as e:
        # kafka not installed or broker unreachable — fall back to no-op
        try:
            print(f"[kafka_adapter] kafka init failed: {e}")
        except Exception:
            pass
        _producer = _NoOpProducer()
        _enabled = False
else:
    _producer = _NoOpProducer()


def publish(event_type: str, payload: Dict[str, Any]) -> Optional[bool]:
    """Publish event to Kafka topic if enabled. Returns True on success or None.

    This call is best-effort; failures are logged but not raised so the
    command path remains robust.
    """
    msg = { 'event_type': event_type, 'payload': payload }
    try:
        if _enabled and _producer:
            _producer.send(KAFKA_TOPIC, msg)
            return True
    except Exception as e:
        try:
            print(f"[kafka_adapter] publish failed: {e}")
        except Exception:
            pass
    return None
