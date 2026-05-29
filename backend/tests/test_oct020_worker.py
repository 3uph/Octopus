"""OCT-020: Dramatiq worker setup — queue config and test job."""
import dramatiq
import pytest


class TestBrokerConfig:
    def test_stub_broker_initializes(self):
        from app.workers.queues.config import get_broker
        broker = get_broker(testing=True)
        assert broker is not None

    def test_queues_defined(self):
        from app.workers.queues.config import QUEUES
        expected = {"passive", "medium", "active", "intelligence", "ai"}
        assert set(QUEUES.keys()) == expected
        assert set(QUEUES.values()) == expected

    def test_get_broker_returns_same_instance(self):
        from app.workers.queues.config import get_broker
        b1 = get_broker(testing=True)
        b2 = get_broker(testing=True)
        assert b1 is b2


class TestPingJob:
    def setup_method(self):
        from app.workers.queues.config import _broker, get_broker
        import app.workers.queues.config as qc
        # Reset broker for test isolation
        qc._broker = None
        self.broker = get_broker(testing=True)

    def test_ping_is_dramatiq_actor(self):
        from app.workers.jobs.ping import ping
        assert hasattr(ping, "send")  # Dramatiq actors have .send()

    def test_ping_queue_is_passive(self):
        from app.workers.jobs.ping import ping
        assert ping.queue_name == "passive"

    def test_ping_enqueues_without_redis(self):
        from app.workers.jobs.ping import ping
        from dramatiq.brokers.stub import StubBroker
        assert isinstance(self.broker, StubBroker)
        # Declare queues on stub broker so join() works
        for q in ["passive", "medium", "active", "intelligence", "ai"]:
            self.broker.declare_queue(q)
        ping.send("test_message")
        self.broker.join("passive", timeout=1000)

    def test_worker_dockerfile_exists(self):
        from pathlib import Path
        root = Path(__file__).parent.parent.parent
        assert (root / "infra" / "docker" / "worker.Dockerfile").exists()
