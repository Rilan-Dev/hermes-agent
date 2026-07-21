# Phase 1 Task 7 Realtime Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans and superpowers:test-driven-development. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a workspace-scoped, resumable and bounded realtime service plus a browser-safe FastAPI WebSocket endpoint.

**Architecture:** Read ordered events from the existing transactional outbox. The service re-resolves and authorizes the principal before every batch, treats PostgreSQL/outbox storage as the future source of truth, and never creates an unbounded client queue. The WebSocket route serializes stable workspace-event envelopes and closes slow or unauthorized clients with explicit codes and resumable metadata.

**Tech Stack:** Python 3.11+, FastAPI/Starlette WebSockets, pytest, existing `agentic_platform` ports and memory adapter.

## Global Constraints

- Work on `worktree/agentic-platform-phase-1-closure` based on reconciliation head `468ec4bf81f22370ddae6cde331c203c34976b2e` until PR #3 reaches `main`.
- No direct imports from `gateway.*`, `plugins.*`, `hermes_cli.*`, `agent.*`, or `tools.*`.
- Every workspace event read requires `workspace_id`.
- Resume semantics are exclusive: `after=7` starts with cursor `8`.
- Per-client pending inspection is capped at `max_buffered_events + 1`.
- Slow-client close code is `4413`; authorization close code is `4403`; invalid request close code is `4400`.
- Authorization is rechecked before every batch through an injected asynchronous principal resolver.
- No production code is written before a failing test demonstrates the missing behavior.

---

### Task 7.1: Realtime Service Contracts

**Files:**
- Create: `platform/backend/src/agentic_platform/services/realtime.py`
- Test: `platform/backend/tests/services/test_realtime.py`

**Interfaces:**
- Consumes: `Callable[[], UnitOfWork]`, `AuthorizationService`, `Permission.INBOX_READ`, `EventCursor`, `WorkspaceEvent`, `Principal`.
- Produces:
  - `PrincipalResolver = Callable[[Principal], Awaitable[Principal]]`
  - `RealtimeConfig(batch_limit: int = 100, poll_interval_seconds: float = 0.25, max_buffered_events: int = 500)`
  - `SlowConsumerError(last_delivered_cursor: EventCursor)`
  - `RealtimeService.read_batch(...) -> Sequence[WorkspaceEvent]`
  - `RealtimeService.subscribe(...) -> AsyncIterator[WorkspaceEvent]`

- [ ] **Step 1: Write the resume test**

```python
@pytest.mark.asyncio
async def test_subscribe_resumes_after_last_cursor() -> None:
    database = MemoryDatabase()
    workspace_id = WorkspaceId.new()
    await seed_events(database, workspace_id, cursors=(1, 2, 3))
    service = RealtimeService(
        unit_of_work_factory=lambda: MemoryUnitOfWork(database),
        authorization=AuthorizationService(),
        principal_resolver=identity_principal,
        config=RealtimeConfig(batch_limit=2, poll_interval_seconds=0.001),
    )

    stream = service.subscribe(
        principal=principal_for(workspace_id),
        workspace_id=workspace_id,
        after=EventCursor(1),
    )
    assert [(await anext(stream)).cursor.value, (await anext(stream)).cursor.value] == [2, 3]
    await stream.aclose()
```

- [ ] **Step 2: Run the focused test and verify RED**

Run:
```bash
python -m pytest platform/backend/tests/services/test_realtime.py::test_subscribe_resumes_after_last_cursor -q
```
Expected: collection/import failure because `agentic_platform.services.realtime` does not exist.

- [ ] **Step 3: Implement `RealtimeConfig`, `read_batch`, and `subscribe` minimally**

Implementation requirements:
- Reject non-positive limits and configuration values with `DomainValidationError`.
- Resolve the principal and call `AuthorizationService.require(..., Permission.INBOX_READ, resource_workspace_id=workspace_id)` before every batch.
- Read at most `max_buffered_events + 1` events from `uow.outbox`.
- Raise `SlowConsumerError` when the pending count exceeds `max_buffered_events`.
- Yield events in cursor order and update the exclusive resume cursor after each yield.
- Sleep only when no event is available.

- [ ] **Step 4: Verify GREEN**

Run:
```bash
python -m pytest platform/backend/tests/services/test_realtime.py::test_subscribe_resumes_after_last_cursor -q
```
Expected: `1 passed`.

- [ ] **Step 5: Add bounded-buffer and authorization-recheck tests**

```python
@pytest.mark.asyncio
async def test_read_batch_rejects_backlog_larger_than_buffer() -> None:
    # Seed cursors 1 and 2, configure max_buffered_events=1.
    # Assert SlowConsumerError.last_delivered_cursor == EventCursor(0).
```

```python
@pytest.mark.asyncio
async def test_subscribe_rechecks_principal_before_each_batch() -> None:
    # Configure batch_limit=1 and seed two events.
    # Resolver returns a valid principal once, then raises ResourceNotFound.
    # Assert the first event is delivered and the next anext() raises ResourceNotFound.
```

- [ ] **Step 6: Run the service suite**

Run:
```bash
python -m pytest platform/backend/tests/services/test_realtime.py -q
```
Expected: all realtime service tests pass.

- [ ] **Step 7: Commit service slice**

```bash
git add platform/backend/src/agentic_platform/services/realtime.py platform/backend/tests/services/test_realtime.py
git commit -m "feat(platform): add resumable realtime service"
```

Rollback boundary: revert this commit; existing HTTP inbox behavior remains unchanged.

---

### Task 7.2: WebSocket API and Stable Event Envelope

**Files:**
- Create: `platform/backend/src/agentic_platform/api/realtime.py`
- Modify: `platform/backend/src/agentic_platform/api/app.py`
- Modify: `platform/backend/src/agentic_platform/api/dependencies.py`
- Test: `platform/backend/tests/api/test_realtime.py`

**Interfaces:**
- Consumes: Task 7.1 `RealtimeService`, existing header principal fields, and `ApplicationDependencies`.
- Produces:
  - WebSocket route `/api/workspaces/{workspace_id}/realtime?after=<cursor>`.
  - Event JSON fields: `type`, `cursor`, `event_id`, `aggregate_type`, `aggregate_id`, `event_type`, `payload`, `occurred_at`.
  - Close reason JSON for slow clients: `{"error":{"code":"slow_consumer","message":"reconnect with the supplied cursor","resume_after":"<cursor>"}}`.

- [ ] **Step 1: Write the resume-envelope WebSocket test**

```python
def test_websocket_resumes_and_serializes_workspace_event() -> None:
    database = MemoryDatabase()
    workspace_id = WorkspaceId.new()
    seed_events_sync(database, workspace_id, cursors=(1, 2))
    client = make_client(database)

    with client.websocket_connect(
        f"/api/workspaces/{workspace_id}/realtime?after=1",
        headers=headers_for(workspace_id),
    ) as websocket:
        payload = websocket.receive_json()

    assert payload["type"] == "workspace_event"
    assert payload["cursor"] == "2"
    assert payload["event_type"] == "message.created"
```

- [ ] **Step 2: Run the focused API test and verify RED**

Run:
```bash
python -m pytest platform/backend/tests/api/test_realtime.py::test_websocket_resumes_and_serializes_workspace_event -q
```
Expected: WebSocket route is not found.

- [ ] **Step 3: Implement the WebSocket route minimally**

Implementation requirements:
- Reuse one pure header-to-principal parser for HTTP and WebSocket callers.
- Parse workspace ID and `after` before subscription.
- Accept the socket, stream serialized events, and stop cleanly on `WebSocketDisconnect`.
- Close with `4413` and the stable slow-consumer reason JSON.
- Close with `4403` for `AuthorizationDenied` or `ResourceNotFound`.
- Close with `4400` for invalid workspace/cursor/header values.
- Include the router in `create_app`.

- [ ] **Step 4: Verify GREEN**

Run:
```bash
python -m pytest platform/backend/tests/api/test_realtime.py::test_websocket_resumes_and_serializes_workspace_event -q
```
Expected: `1 passed`.

- [ ] **Step 5: Add slow-client and cross-workspace close tests**

```python
def test_websocket_closes_slow_consumer_with_resume_cursor() -> None:
    # max_buffered_events=1 and two pending events.
    # Assert WebSocketDisconnect.code == 4413 and JSON reason resume_after == "0".
```

```python
def test_websocket_cross_workspace_access_closes_not_found_safe() -> None:
    # Requested workspace differs from X-Workspace-ID.
    # Assert WebSocketDisconnect.code == 4403 and reason contains only authorization_failed.
```

- [ ] **Step 6: Run focused API and service suites**

Run:
```bash
python -m pytest platform/backend/tests/services/test_realtime.py platform/backend/tests/api/test_realtime.py -q
```
Expected: all Task 7 tests pass.

- [ ] **Step 7: Run the complete Phase 1 regression gate**

Run:
```bash
python -m pytest platform/backend/tests -q
python -m compileall -q platform/backend/src/agentic_platform
git diff --check
```
Expected: zero failures and zero diff errors.

- [ ] **Step 8: Commit WebSocket slice**

```bash
git add platform/backend/src/agentic_platform/api/realtime.py platform/backend/src/agentic_platform/api/app.py platform/backend/src/agentic_platform/api/dependencies.py platform/backend/tests/api/test_realtime.py
git commit -m "feat(platform): expose resumable realtime websocket"
```

Rollback boundary: revert this commit to remove the public WebSocket route while retaining the tested realtime service.

---

## Task 7 Acceptance Gate

- [ ] Resume cursor is exclusive and preserves event order.
- [ ] Principal resolution and authorization occur before every batch.
- [ ] Per-client pending inspection is bounded by `max_buffered_events + 1`.
- [ ] Slow clients receive close code `4413` and an exact resume cursor.
- [ ] Cross-workspace clients receive close code `4403` without resource disclosure.
- [ ] WebSocket event envelopes contain no secret material.
- [ ] Focused Task 7 tests pass.
- [ ] Full Phase 1 regression tests, compile checks, diff checks, and GitHub CI pass on the exact commit.
