"""Dramatiq broker configuration and queue definitions.

Queues are isolated by recon mode to prevent active jobs from blocking passive ones.
"""
from __future__ import annotations

import dramatiq
from dramatiq.brokers.redis import RedisBroker
from dramatiq.brokers.stub import StubBroker

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Queue names — one per mode (D-22)
QUEUES = {
    "passive": "passive",
    "medium": "medium",
    "active": "active",
    "intelligence": "intelligence",
    "ai": "ai",
}

_broker: dramatiq.Broker | None = None


def get_broker(*, testing: bool = False) -> dramatiq.Broker:
    """Return the configured broker (lazy init, cached)."""
    global _broker
    if _broker is not None:
        return _broker

    if testing:
        _broker = StubBroker()
        _broker.emit_after("process_boot")
    else:
        _broker = RedisBroker(url=settings.redis_url)
        logger.info("Dramatiq broker connected: %s", settings.redis_url)

    dramatiq.set_broker(_broker)
    return _broker


def configure_broker() -> None:
    """Call at app/worker startup to initialize the broker."""
    get_broker()
