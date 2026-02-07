# ================================
# SensorPulse API - WebSocket Manager Unit Tests
# ================================

import asyncio
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone

import pytest
import pytest_asyncio
from websocket import WebSocketManager, ConnectionInfo


@pytest_asyncio.fixture
async def manager():
    return WebSocketManager()


def _mock_ws(accept=True):
    ws = AsyncMock()
    ws.accept = AsyncMock()
    ws.send_json = AsyncMock()
    ws.close = AsyncMock()
    return ws


@pytest.mark.asyncio
class TestWebSocketManager:

    async def test_connect_adds_client(self, manager):
        ws = _mock_ws()
        await manager.connect(ws, "c1")
        assert manager.get_connection_count() == 1

    async def test_disconnect_removes_client(self, manager):
        ws = _mock_ws()
        await manager.connect(ws, "c1")
        await manager.disconnect("c1")
        assert manager.get_connection_count() == 0

    async def test_disconnect_nonexistent_is_safe(self, manager):
        await manager.disconnect("nonexistent")  # should not raise

    async def test_subscribe(self, manager):
        ws = _mock_ws()
        await manager.connect(ws, "c1")
        await manager.subscribe("c1", {"office", "bedroom"})
        stats = manager.get_stats()
        subs = stats["clients"][0]["subscriptions"]
        assert "office" in subs
        assert "bedroom" in subs

    async def test_unsubscribe(self, manager):
        ws = _mock_ws()
        await manager.connect(ws, "c1")
        await manager.subscribe("c1", {"office", "bedroom"})
        await manager.unsubscribe("c1", {"office"})
        stats = manager.get_stats()
        subs = stats["clients"][0]["subscriptions"]
        assert "office" not in subs
        assert "bedroom" in subs

    async def test_broadcast_reading_to_all(self, manager):
        ws1, ws2 = _mock_ws(), _mock_ws()
        await manager.connect(ws1, "c1")
        await manager.connect(ws2, "c2")
        await manager.broadcast_reading({"device_name": "office", "temperature": 22.0})
        ws1.send_json.assert_called_once()
        ws2.send_json.assert_called_once()

    async def test_broadcast_reading_respects_subscription(self, manager):
        ws1, ws2 = _mock_ws(), _mock_ws()
        await manager.connect(ws1, "c1")
        await manager.connect(ws2, "c2")
        await manager.subscribe("c2", {"bedroom"})
        await manager.broadcast_reading({"device_name": "office", "temperature": 22.0})
        # c1 has no subs → gets everything; c2 subscribed to bedroom → skips office
        ws1.send_json.assert_called_once()
        ws2.send_json.assert_not_called()

    async def test_broadcast_cleans_up_failed_connections(self, manager):
        ws = _mock_ws()
        ws.send_json.side_effect = Exception("broken pipe")
        await manager.connect(ws, "c1")
        await manager.broadcast_all({"type": "test"})
        assert manager.get_connection_count() == 0

    async def test_disconnect_all(self, manager):
        for i in range(3):
            await manager.connect(_mock_ws(), f"c{i}")
        assert manager.get_connection_count() == 3
        await manager.disconnect_all()
        assert manager.get_connection_count() == 0

    async def test_get_stats(self, manager):
        ws = _mock_ws()
        await manager.connect(ws, "c1", user_id="u1")
        stats = manager.get_stats()
        assert stats["active_connections"] == 1
        assert stats["clients"][0]["client_id"] == "c1"
        assert stats["clients"][0]["user_id"] == "u1"
