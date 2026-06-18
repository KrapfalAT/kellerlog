"""
SSE (Server-Sent Events) tests.

Strategy for notification tests: inject an asyncio.Queue into
_sse_subscribers directly, trigger a mutation endpoint, then assert
the queue received a "wines" event.  This avoids spinning up a real
HTTP streaming client while still exercising the full
notify_clients() → _sse_notify() path.
"""
import asyncio
import time

import pytest
import main


# ── helpers ──────────────────────────────────────────────────────────────────

def _drain(q: asyncio.Queue, wait: float = 0.2) -> list[str]:
    """Wait briefly for the event loop to deliver events, then drain the queue."""
    time.sleep(wait)
    items = []
    while not q.empty():
        try:
            items.append(q.get_nowait())
        except asyncio.QueueEmpty:
            break
    return items


def _subscribe() -> asyncio.Queue:
    q: asyncio.Queue = asyncio.Queue()
    main._sse_subscribers.append(q)
    return q


def _unsubscribe(q: asyncio.Queue) -> None:
    if q in main._sse_subscribers:
        main._sse_subscribers.remove(q)


@pytest.fixture()
def subscriber():
    """Yield a queue pre-registered in _sse_subscribers; clean up after."""
    q = _subscribe()
    yield q
    _unsubscribe(q)


# ── HTTP-level tests ──────────────────────────────────────────────────────────

def test_sse_endpoint_no_auth_required(client):
    """GET /events must be accessible without a token."""
    with client.stream("GET", "/events") as r:
        assert r.status_code == 200


def test_sse_content_type(client):
    with client.stream("GET", "/events") as r:
        assert "text/event-stream" in r.headers["content-type"]


def test_sse_initial_retry_directive(client):
    """First data sent must be the retry directive."""
    with client.stream("GET", "/events") as r:
        for line in r.iter_lines():
            if line:
                assert line == "retry: 3000"
                break


def test_sse_subscriber_registered_and_removed(client):
    """Opening a connection adds a subscriber; closing removes it."""
    before = len(main._sse_subscribers)
    with client.stream("GET", "/events"):
        assert len(main._sse_subscribers) == before + 1
    time.sleep(0.05)
    assert len(main._sse_subscribers) == before


# ── notification tests ────────────────────────────────────────────────────────

def test_sse_create_wine_notifies(client, admin_headers, subscriber):
    client.post("/wines", json={"name": "SSE Wine", "type": "red", "quantity": 1},
                headers=admin_headers)
    assert _drain(subscriber) == ["wines"]


def test_sse_update_wine_notifies(client, admin_headers, subscriber):
    wine_id = client.post(
        "/wines", json={"name": "SSE Update", "type": "white", "quantity": 2},
        headers=admin_headers,
    ).json()["id"]
    _unsubscribe(subscriber)  # discard create-event
    q = _subscribe()

    client.put(f"/wines/{wine_id}", json={"quantity": 5}, headers=admin_headers)
    assert _drain(q) == ["wines"]
    _unsubscribe(q)


def test_sse_delete_wine_notifies(client, admin_headers, subscriber):
    wine_id = client.post(
        "/wines", json={"name": "SSE Delete", "type": "red", "quantity": 1},
        headers=admin_headers,
    ).json()["id"]
    _unsubscribe(subscriber)
    q = _subscribe()

    client.delete(f"/wines/{wine_id}", headers=admin_headers)
    assert _drain(q) == ["wines"]
    _unsubscribe(q)


def test_sse_batch_update_notifies(client, admin_headers, subscriber):
    id1 = client.post("/wines", json={"name": "Batch A", "type": "red", "quantity": 1},
                      headers=admin_headers).json()["id"]
    id2 = client.post("/wines", json={"name": "Batch B", "type": "red", "quantity": 1},
                      headers=admin_headers).json()["id"]
    _unsubscribe(subscriber)
    q = _subscribe()

    client.put("/wines/batch",
               json={"ids": [id1, id2], "updates": {"quantity": 10}},
               headers=admin_headers)
    events = _drain(q)
    assert events == ["wines"]
    _unsubscribe(q)


def test_sse_library_update_notifies(client, admin_headers, subscriber):
    entry_id = client.post(
        "/wines", json={"name": "Lib Update", "type": "rosé", "quantity": 1},
        headers=admin_headers,
    ).json()["id"]
    _unsubscribe(subscriber)
    q = _subscribe()

    client.put(f"/library/{entry_id}", json={"price": 12.5}, headers=admin_headers)
    assert _drain(q) == ["wines"]
    _unsubscribe(q)


def test_sse_library_delete_notifies(client, admin_headers, subscriber):
    entry_id = client.post(
        "/wines", json={"name": "Lib Delete", "type": "sparkling", "quantity": 1},
        headers=admin_headers,
    ).json()["id"]
    _unsubscribe(subscriber)
    q = _subscribe()

    client.delete(f"/library/{entry_id}", headers=admin_headers)
    assert _drain(q) == ["wines"]
    _unsubscribe(q)


def test_sse_multiple_subscribers_all_notified(client, admin_headers):
    """All connected subscribers receive the event."""
    queues = [_subscribe() for _ in range(3)]
    try:
        client.post("/wines", json={"name": "Multi SSE", "type": "other", "quantity": 1},
                    headers=admin_headers)
        for q in queues:
            assert _drain(q) == ["wines"], "not all subscribers received the event"
    finally:
        for q in queues:
            _unsubscribe(q)


def test_sse_no_spurious_events_without_mutation(subscriber):
    """No event must be in the queue if no mutation happened."""
    time.sleep(0.1)
    assert _drain(subscriber) == []
