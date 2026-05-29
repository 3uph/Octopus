"""Ping job — inocuous test actor, no network/recon calls."""
import dramatiq

from app.core.logging import get_logger

logger = get_logger(__name__)


@dramatiq.actor(queue_name="passive", max_retries=0)
def ping(message: str = "pong") -> None:
    """Test job: logs a message. No side effects, no network, no tools."""
    logger.info("ping job executed: %s", message)
