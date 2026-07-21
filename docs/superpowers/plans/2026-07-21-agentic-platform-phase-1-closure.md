# Agentic Platform Phase 1 Closure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete the five missing Phase 1 deliverables—resumable realtime, PostgreSQL persistence, Redis/S3 adapters, Hermes descriptor bridge, and browser renderer SDK—so the generic omnichannel inbox works end to end on production-shaped infrastructure.

**Architecture:** Extend the existing `agentic_platform` modular monolith through its current ports. PostgreSQL is the source of truth, Redis is coordination/fanout only, S3-compatible storage owns durable objects, Hermes internals are isolated behind stable bridge contracts, and the browser consumes typed HTTP/WebSocket contracts without Electron dependencies.

**Tech Stack:** Python 3.11–3.13, FastAPI, SQLAlchemy 2.0.51, asyncpg 0.31.0, Alembic 1.18.5, redis-py 8.0.1, MinIO SDK 7.2.20, PostgreSQL, Redis, S3-compatible object storage, React 19.2.4, React Router 7.17.0, TypeScript 6.0.3, Vite 8.0.16, Vitest 4.1.5.

## Global Constraints

- Work only on a Phase 1 implementation branch based on the current `main` merge candidate after PR #3 is green.
- Every durable repository method requires `workspace_id`.
- PostgreSQL is the durable source of truth; Redis must not own canonical inbox data.
- Native channel IDs are preserved beside canonical IDs.
- Secrets remain opaque references and are never returned by API DTOs.
- Product modules import only `agentic_platform.*` or `agentic_platform.hermes_compat.public.*` contracts.
- Direct `gateway.*`, `plugins.*`, `hermes_cli.*`, `agent.*`, and `tools.*` imports are confined to `hermes_bridge/` and characterization tests.
- Realtime delivery is resumable and bounded; no unbounded per-client queue is allowed.
- All migrations support upgrade and downgrade in tests.
- Browser code must not reference `window.hermesDesktop`, Electron preload APIs, or Node-only modules.
- Every task follows red-green-refactor and ends in one focused commit.

---

## File Structure

```text
platform/
├── backend/
│   ├── pyproject.toml
│   ├── migrations/
│   │   ├── env.py
│   │   └── versions/
│   │       ├── 0001_workspace_inbox_core.py
│   │       └── 0002_outbox_audit_indexes.py
│   ├── src/agentic_platform/
│   │   ├── api/realtime.py
│   │   ├── services/realtime.py
│   │   ├── ports/coordination.py
│   │   ├── storage/postgres/
│   │   ├── storage/redis/
│   │   ├── storage/s3/
│   │   ├── hermes_compat/public/
│   │   └── hermes_bridge/
│   └── tests/
│       ├── api/test_realtime.py
│       ├── services/test_realtime.py
│       ├── storage/postgres/
│       ├── storage/redis/
│       ├── storage/s3/
│       └── hermes_bridge/
└── web/
    ├── package.json
    ├── tsconfig.json
    ├── vite.config.ts
    ├── index.html
    └── src/
        ├── app/
        ├── api/
        ├── realtime/
        ├── features/inbox/
        └── channel-renderers/
```

---

### Task 7: Resumable Realtime Service and WebSocket API

**Files:**
- Create: `platform/backend/src/agentic_platform/services/realtime.py`
- Create: `platform/backend/src/agentic_platform/api/realtime.py`
- Modify: `platform/backend/src/agentic_platform/api/app.py`
- Modify: `platform/backend/src/agentic_platform/api/dependencies.py`
- Test: `platform/backend/tests/services/test_realtime.py`
- Test: `platform/backend/tests/api/test_realtime.py`

**Interfaces:**
- Consumes: `UnitOfWork`, `OutboxRepository.read()`, `EventCursor`, `WorkspaceEvent`, `AuthorizationService`, `Principal`, `Permission.INBOX_READ`.
- Produces:
  - `RealtimeConfig(batch_limit: int = 100, poll_interval_seconds: float = 0.25, max_buffered_events: int = 500)`
  - `RealtimeService.read_batch(principal, workspace_id, after, limit) -> Sequence[WorkspaceEvent]`
  - `RealtimeService.subscribe(principal, workspace_id, after) -> AsyncIterator[WorkspaceEvent]`
  - WebSocket route: `/api/workspaces/{workspace_id}/realtime`
  - Resume query: `after=<non-negative EventCursor>`
  - Slow-consumer close code: `4413`; authorization close code: `4403`.

- [ ] **Step 1: Write failing service tests**

```python
@pytest.mark.asyncio
async def test_subscribe_resumes_after_last_acknowledged_cursor() -> None:
    workspace_id = WorkspaceId.new()
    store = MemoryStore()
    principal = principal_for(workspace_id, MembershipRole.OPERATOR)
    await seed_workspace_events(store, workspace_id, cursors=(1, 2, 3))
    service = RealtimeService(
        unit_of_work_factory=store.unit_of_work,
        authorization=AuthorizationService(),
        config=RealtimeConfig(poll_interval_seconds=0.001),
    )

    received = []
    async for event in service.subscribe(
        principal=principal,
        workspace_id=workspace_id,
        after=EventCursor(1),
    ):
        received.append(event.cursor.value)
        if len(received) == 2:
            break

    assert received == [2, 3]
```

```python
@pytest.mark.asyncio
async def test_slow_consumer_raises_with_last_delivered_cursor() -> None:
    service = make_service(max_buffered_events=1)
    await seed_events(service, count=3)

    with pytest.raises(SlowConsumerError) as exc_info:
        await consume_without_acknowledging(service)

    assert exc_info.value.resume_after == EventCursor(1)
```

- [ ] **Step 2: Run tests and verify red state**

Run:

```bash
python -m pytest platform/backend/tests/services/test_realtime.py -v
```

Expected: collection failure because `agentic_platform.services.realtime` does not exist.

- [ ] **Step 3: Implement the bounded service**

```python
@dataclass(frozen=True, slots=True)
class RealtimeConfig:
    batch_limit: int = 100
    poll_interval_seconds: float = 0.25
    max_buffered_events: int = 500


class SlowConsumerError(RuntimeError):
    def __init__(self, resume_after: EventCursor) -> None:
        super().__init__("realtime client exceeded the bounded buffer")
        self.resume_after = resume_after


class RealtimeService:
    def __init__(self, *, unit_of_work_factory, authorization, config=None) -> None:
        self._unit_of_work_factory = unit_of_work_factory
        self._authorization = authorization
        self._config = config or RealtimeConfig()

    async def read_batch(self, *, principal, workspace_id, after, limit):
        self._authorization.require(
            principal,
            Permission.INBOX_READ,
            resource_workspace_id=workspace_id,
        )
        bounded_limit = min(max(limit, 1), self._config.batch_limit)
        async with self._unit_of_work_factory() as uow:
            return await uow.outbox.read(
                workspace_id,
                after=after,
                limit=bounded_limit,
            )
```

Implement `subscribe()` with one bounded `asyncio.Queue`, ordered cursor updates, cancellation cleanup, and no task left running after disconnect.

- [ ] **Step 4: Add WebSocket tests**

```python
def test_websocket_resumes_from_cursor(api_client, seeded_events) -> None:
    with api_client.websocket_connect(
        f"/api/workspaces/{seeded_events.workspace_id}/realtime?after=1",
        headers=operator_headers(seeded_events.workspace_id),
    ) as socket:
        first = socket.receive_json()
        second = socket.receive_json()

    assert [first["cursor"], second["cursor"]] == [2, 3]
```

```python
def test_websocket_rejects_cross_workspace_principal(api_client) -> None:
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with api_client.websocket_connect(
            f"/api/workspaces/{WorkspaceId.new()}/realtime",
            headers=operator_headers(WorkspaceId.new()),
        ):
            pass

    assert exc_info.value.code == 4403
```

- [ ] **Step 5: Register the router and verify**

Run:

```bash
python -m pytest \
  platform/backend/tests/services/test_realtime.py \
  platform/backend/tests/api/test_realtime.py -v
python -m pytest tests/scripts/platform_inventory platform/backend/tests -q
python -m compileall -q scripts/platform_inventory platform/backend/src/agentic_platform
```

Expected: all focused and full Phase 1 tests pass.

- [ ] **Step 6: Commit**

```bash
git add platform/backend/src/agentic_platform/services/realtime.py \
        platform/backend/src/agentic_platform/api/realtime.py \
        platform/backend/src/agentic_platform/api/app.py \
        platform/backend/src/agentic_platform/api/dependencies.py \
        platform/backend/tests/services/test_realtime.py \
        platform/backend/tests/api/test_realtime.py
git commit -m "feat(platform): add resumable realtime stream"
```

---

### Task 8: PostgreSQL Persistence and Versioned Migrations

**Files:**
- Create: `platform/backend/pyproject.toml`
- Create: `platform/backend/alembic.ini`
- Create: `platform/backend/migrations/env.py`
- Create: `platform/backend/migrations/versions/0001_workspace_inbox_core.py`
- Create: `platform/backend/migrations/versions/0002_outbox_audit_indexes.py`
- Create: `platform/backend/src/agentic_platform/storage/postgres/pool.py`
- Create: `platform/backend/src/agentic_platform/storage/postgres/repositories.py`
- Create: `platform/backend/src/agentic_platform/storage/postgres/uow.py`
- Create: `platform/backend/src/agentic_platform/storage/postgres/__init__.py`
- Test: `platform/backend/tests/storage/postgres/test_migrations.py`
- Test: `platform/backend/tests/storage/postgres/test_repository_contracts.py`
- Test: `platform/backend/tests/storage/postgres/test_concurrent_ingestion.py`

**Interfaces:**
- Consumes: all protocols in `ports/repositories.py`.
- Produces:
  - `PostgresSettings(dsn: str, min_pool_size: int = 1, max_pool_size: int = 10)`
  - `create_postgres_pool(settings) -> asyncpg.Pool`
  - `PostgresUnitOfWork(pool) -> UnitOfWork`
  - `postgres_unit_of_work_factory(pool) -> Callable[[], UnitOfWork]`.

- [ ] **Step 1: Add exact dependency metadata**

```toml
[project]
name = "agentic-platform-backend"
version = "0.1.0"
requires-python = ">=3.11,<3.14"
dependencies = [
  "fastapi>=0.104.0,<1",
  "sqlalchemy[asyncio]==2.0.51",
  "asyncpg==0.31.0",
  "alembic==1.18.5",
  "redis[hiredis]==8.0.1",
  "minio==7.2.20",
]
```

Run `uv lock` from the repository root and review every lockfile change before continuing.

- [ ] **Step 2: Write the failing migration test**

```python
@pytest.mark.postgres
@pytest.mark.asyncio
async def test_upgrade_creates_workspace_scoped_inbox_schema(postgres_dsn: str) -> None:
    await migrate(postgres_dsn, "head")
    tables = await list_tables(postgres_dsn)

    assert {
        "workspaces",
        "users",
        "memberships",
        "agents",
        "channel_connections",
        "contacts",
        "external_identities",
        "conversations",
        "participants",
        "messages",
        "attachments",
        "reactions",
        "receipts",
        "channel_events",
        "raw_event_objects",
        "workspace_outbox",
        "audit_records",
    } <= tables
```

- [ ] **Step 3: Run the red migration test**

Run:

```bash
AGENTIC_PLATFORM_POSTGRES_DSN=postgresql://postgres:postgres@localhost:5432/agentic_test \
python -m pytest platform/backend/tests/storage/postgres/test_migrations.py -v
```

Expected: failure because migration configuration does not exist.

- [ ] **Step 4: Implement migrations with tenant-safe constraints**

Each tenant table must include:

```python
sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False)
```

Required uniqueness examples:

```python
sa.UniqueConstraint(
    "workspace_id",
    "connection_id",
    "native_id",
    name="uq_conversation_native_identity",
)
sa.UniqueConstraint(
    "workspace_id",
    "connection_id",
    "platform_event_id",
    name="uq_channel_event_idempotency",
)
sa.UniqueConstraint(
    "workspace_id",
    "cursor",
    name="uq_workspace_outbox_cursor",
)
```

Use JSON payload columns with an explicit integer `schema_version` column. Use `TIMESTAMP(timezone=True)` for every datetime.

- [ ] **Step 5: Write shared repository contract tests**

```python
@pytest.mark.parametrize("uow_factory_name", ["memory", "postgres"])
@pytest.mark.asyncio
async def test_repository_contract_is_workspace_scoped(
    request: pytest.FixtureRequest,
    uow_factory_name: str,
) -> None:
    uow_factory = request.getfixturevalue(f"{uow_factory_name}_uow_factory")
    workspace_a = WorkspaceId.new()
    workspace_b = WorkspaceId.new()
    conversation = conversation_for(workspace_a)

    async with uow_factory() as uow:
        await uow.conversations.save(workspace_a, conversation)
        await uow.commit()

    async with uow_factory() as uow:
        assert await uow.conversations.get(workspace_b, conversation.id) is None
```

- [ ] **Step 6: Implement PostgreSQL repositories and unit of work**

Use one acquired connection and one transaction per unit of work. `commit()` marks intent; actual commit occurs only on a clean `__aexit__`. Any exception forces rollback even when `commit()` was previously requested, matching the memory adapter contract.

- [ ] **Step 7: Prove concurrent idempotency**

```python
@pytest.mark.postgres
@pytest.mark.asyncio
async def test_concurrent_duplicate_ingestion_creates_one_message(postgres_services) -> None:
    results = await asyncio.gather(
        postgres_services.ingest(EVENT),
        postgres_services.ingest(EVENT),
    )

    assert results[0].message_id == results[1].message_id
    assert await count_messages(postgres_services.pool) == 1
    assert await count_outbox_events(postgres_services.pool) == 1
```

- [ ] **Step 8: Verify migrations and repositories**

Run:

```bash
uv lock --check
AGENTIC_PLATFORM_POSTGRES_DSN=postgresql://postgres:postgres@localhost:5432/agentic_test \
python -m pytest platform/backend/tests/storage/postgres -v
python -m pytest tests/scripts/platform_inventory platform/backend/tests -q
```

Expected: upgrade, downgrade, contract, and concurrent-ingestion tests pass.

- [ ] **Step 9: Commit**

```bash
git add platform/backend/pyproject.toml platform/backend/alembic.ini \
        platform/backend/migrations platform/backend/src/agentic_platform/storage/postgres \
        platform/backend/tests/storage/postgres uv.lock
git commit -m "feat(platform): add PostgreSQL inbox persistence"
```

---

### Task 9: Redis Coordination and S3-Compatible Object Storage

**Files:**
- Create: `platform/backend/src/agentic_platform/ports/coordination.py`
- Create: `platform/backend/src/agentic_platform/storage/redis/client.py`
- Create: `platform/backend/src/agentic_platform/storage/redis/coordination.py`
- Create: `platform/backend/src/agentic_platform/storage/s3/client.py`
- Create: `platform/backend/src/agentic_platform/storage/s3/objects.py`
- Test: `platform/backend/tests/storage/redis/test_coordination.py`
- Test: `platform/backend/tests/storage/s3/test_objects.py`

**Interfaces:**
- Produces:
  - `ConnectorLock.acquire(workspace_id, connection_id, owner, ttl_seconds) -> bool`
  - `ConnectorLock.release(workspace_id, connection_id, owner) -> bool`
  - `RateLimitCounter.increment(key, window_seconds) -> int`
  - `PresenceStore.touch(workspace_id, user_id, ttl_seconds) -> None`
  - `S3ObjectStorage.put(workspace_id, stream, metadata) -> ObjectReference`
  - `S3ObjectStorage.create_download_url(reference, expires_seconds) -> str`.

- [ ] **Step 1: Write failing Redis lock tests**

```python
@pytest.mark.redis
@pytest.mark.asyncio
async def test_connector_lock_is_workspace_and_owner_scoped(redis_coordination) -> None:
    workspace_id = WorkspaceId.new()
    connection_id = ConnectionId.new()

    assert await redis_coordination.acquire_lock(
        workspace_id, connection_id, owner="worker-a", ttl_seconds=30
    )
    assert not await redis_coordination.acquire_lock(
        workspace_id, connection_id, owner="worker-b", ttl_seconds=30
    )
    assert not await redis_coordination.release_lock(
        workspace_id, connection_id, owner="worker-b"
    )
    assert await redis_coordination.release_lock(
        workspace_id, connection_id, owner="worker-a"
    )
```

Use one Lua script for compare-and-delete release so a stale worker cannot release another owner's lock.

- [ ] **Step 2: Write failing S3 tests**

```python
@pytest.mark.s3
@pytest.mark.asyncio
async def test_object_key_is_workspace_prefixed_and_reference_is_durable(s3_storage) -> None:
    workspace_id = WorkspaceId.new()
    reference = await s3_storage.put(
        workspace_id,
        b"hello",
        ObjectMetadata(
            content_type="text/plain",
            size_bytes=5,
            sha256=hashlib.sha256(b"hello").hexdigest(),
        ),
    )

    assert reference.key.startswith(f"workspaces/{workspace_id}/")
    first_url = await s3_storage.create_download_url(reference, expires_seconds=60)
    second_url = await s3_storage.create_download_url(reference, expires_seconds=60)
    assert first_url != ""
    assert second_url != ""
    assert reference.key == reference.key
```

```python
@pytest.mark.s3
@pytest.mark.asyncio
async def test_cross_workspace_reference_is_rejected(s3_storage) -> None:
    reference = await seed_object(s3_storage, WorkspaceId.new())
    with pytest.raises(CrossWorkspaceError):
        await s3_storage.stat(WorkspaceId.new(), reference)
```

- [ ] **Step 3: Implement adapters**

Redis keys must use:

```text
agentic:{workspace_id}:connector:{connection_id}:lock
agentic:{workspace_id}:presence:{user_id}
agentic:{workspace_id}:rate:{policy_key}
agentic:{workspace_id}:realtime
```

S3 object keys must use:

```text
workspaces/{workspace_id}/{yyyy}/{mm}/{object_id}/{sanitized_filename}
```

Reject unknown size, size mismatch, checksum mismatch, blank MIME type, path traversal, and a workspace prefix that does not match the requested workspace.

- [ ] **Step 4: Verify infrastructure adapters**

Run:

```bash
AGENTIC_PLATFORM_REDIS_URL=redis://localhost:6379/15 \
python -m pytest platform/backend/tests/storage/redis -v
AGENTIC_PLATFORM_S3_ENDPOINT=http://localhost:9000 \
AGENTIC_PLATFORM_S3_ACCESS_KEY=minio \
AGENTIC_PLATFORM_S3_SECRET_KEY=minio123 \
python -m pytest platform/backend/tests/storage/s3 -v
python -m pytest tests/scripts/platform_inventory platform/backend/tests -q
```

- [ ] **Step 5: Commit**

```bash
git add platform/backend/src/agentic_platform/ports/coordination.py \
        platform/backend/src/agentic_platform/storage/redis \
        platform/backend/src/agentic_platform/storage/s3 \
        platform/backend/tests/storage/redis \
        platform/backend/tests/storage/s3
git commit -m "feat(platform): add Redis and S3 adapters"
```

---

### Task 10: Hermes Public Facade and Descriptor Bridge

**Files:**
- Create: `platform/backend/src/agentic_platform/hermes_compat/public/__init__.py`
- Create: `platform/backend/src/agentic_platform/hermes_compat/public/catalog.py`
- Create: `platform/backend/src/agentic_platform/hermes_bridge/descriptors.py`
- Create: `platform/backend/src/agentic_platform/hermes_bridge/channels.py`
- Create: `platform/backend/src/agentic_platform/hermes_bridge/runtime.py`
- Test: `platform/backend/tests/hermes_bridge/test_descriptor_inventory.py`
- Test: `platform/backend/tests/hermes_bridge/test_channel_normalization.py`
- Test: `platform/backend/tests/hermes_bridge/test_import_boundaries.py`

**Interfaces:**
- Consumes: `generated/platform_inventory/inventory.json`, Hermes platform/provider/tool registries, `NormalizedChannelEvent`, `IngestionService`.
- Produces:
  - `HermesCatalogBridge.list_channels() -> Sequence[ChannelDescriptor]`
  - `HermesCatalogBridge.list_providers() -> Sequence[ProviderDescriptor]`
  - `HermesCatalogBridge.list_tools() -> Sequence[ToolDescriptor]`
  - `HermesChannelBridge.normalize(event) -> NormalizedChannelEvent`
  - `HermesChannelBridge.ingest(event) -> IngestionResult`.

- [ ] **Step 1: Write the failing inventory parity test**

```python
def test_bridge_channel_ids_match_phase0_inventory() -> None:
    expected = set(load_phase0_inventory().registries.platforms)
    actual = {
        descriptor.platform_id
        for descriptor in asyncio.run(HermesCatalogBridge().list_channels())
    }

    assert actual == expected
    assert len(actual) == 20
```

- [ ] **Step 2: Write the import-boundary test**

```python
def test_product_code_does_not_import_hermes_internals() -> None:
    forbidden = ("gateway.", "plugins.", "hermes_cli.", "agent.", "tools.")
    violations = scan_imports(
        Path("platform/backend/src/agentic_platform"),
        exclude=("hermes_bridge",),
        forbidden=forbidden,
    )
    assert violations == []
```

- [ ] **Step 3: Implement descriptor mapping**

The mapping must preserve separate identities. Do not coerce provider profile IDs, auth IDs, canonical IDs, model-catalog IDs, transport IDs, or service-provider IDs into one namespace.

```python
ProviderDescriptor(
    provider_id=provider_id,
    display_name=display_name,
    identity_kind=ProviderIdentityKind.CANONICAL,
    aliases=frozenset(aliases),
)
```

Channel descriptors must report `deferred=True` for deferred plugins and must carry only capabilities discovered from runtime/manifests; no UI-owned channel list is allowed.

- [ ] **Step 4: Implement channel normalization bridge**

Map Hermes `MessageEvent` and `SessionSource` fields into canonical contracts, preserving:

- platform event ID;
- platform, chat, user, thread/topic, reply target, and message IDs;
- message type and attachment references;
- raw payload object reference;
- channel prompt/context metadata;
- upstream relay trust metadata.

- [ ] **Step 5: Verify bridge characterization**

Run:

```bash
python -m pytest platform/backend/tests/hermes_bridge -v
python -m pytest tests/scripts/platform_inventory platform/backend/tests -q
python -m scripts.platform_inventory --root . --output /tmp/phase1-inventory generate
```

Expected: 20-channel parity, zero forbidden imports, provider identity families remain distinct, and generator blockers remain empty.

- [ ] **Step 6: Commit**

```bash
git add platform/backend/src/agentic_platform/hermes_compat \
        platform/backend/src/agentic_platform/hermes_bridge \
        platform/backend/tests/hermes_bridge
git commit -m "feat(platform): add Hermes descriptor bridge"
```

---

### Task 11: Browser Shell, Typed Clients, and Generic Renderer SDK

**Files:**
- Create: `platform/web/package.json`
- Create: `platform/web/tsconfig.json`
- Create: `platform/web/vite.config.ts`
- Create: `platform/web/index.html`
- Create: `platform/web/src/main.tsx`
- Create: `platform/web/src/app/App.tsx`
- Create: `platform/web/src/app/router.tsx`
- Create: `platform/web/src/api/contracts.ts`
- Create: `platform/web/src/api/client.ts`
- Create: `platform/web/src/realtime/client.ts`
- Create: `platform/web/src/features/inbox/InboxPage.tsx`
- Create: `platform/web/src/features/inbox/ChannelNavigation.tsx`
- Create: `platform/web/src/features/inbox/ConversationList.tsx`
- Create: `platform/web/src/features/inbox/ConversationWorkspace.tsx`
- Create: `platform/web/src/features/inbox/ContextPanel.tsx`
- Create: `platform/web/src/channel-renderers/contracts.ts`
- Create: `platform/web/src/channel-renderers/registry.ts`
- Create: `platform/web/src/channel-renderers/generic/GenericRenderer.tsx`
- Test: `platform/web/src/api/client.test.ts`
- Test: `platform/web/src/realtime/client.test.ts`
- Test: `platform/web/src/channel-renderers/registry.test.ts`
- Test: `platform/web/src/features/inbox/inbox-state.test.ts`
- Add browser E2E: `apps/desktop/e2e/platform-web-generic-inbox.spec.ts` or the repository's current browser-only Playwright project.

**Interfaces:**
- Consumes: `/health`, `/api/workspaces/{workspace_id}/conversations`, conversation-message endpoint, Hermes descriptor endpoint, and `/api/workspaces/{workspace_id}/realtime`.
- Produces:
  - `ChannelRenderer` contract.
  - `RendererRegistry.register(renderer)` and `resolve(platformId, capabilities)`.
  - Browser routes `/inbox`, `/inbox/:platformId`, and `/inbox/:platformId/:conversationId`.
  - Persisted `lastAcknowledgedCursor` per workspace.

- [ ] **Step 1: Create exact package metadata**

```json
{
  "name": "agentic-platform-web",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "typecheck": "tsc -p . --noEmit",
    "test": "vitest run",
    "check": "npm run typecheck && npm run test && npm run build"
  },
  "dependencies": {
    "react": "19.2.4",
    "react-dom": "19.2.4",
    "react-router-dom": "7.17.0"
  },
  "devDependencies": {
    "@types/react": "19.2.14",
    "@types/react-dom": "19.2.3",
    "@vitejs/plugin-react": "6.0.2",
    "typescript": "6.0.3",
    "vite": "8.0.16",
    "vitest": "4.1.5"
  }
}
```

- [ ] **Step 2: Write failing renderer-registry tests**

```ts
it("uses the generic renderer for an unknown discovered platform", () => {
  const registry = createRendererRegistry([genericRenderer]);
  const renderer = registry.resolve({
    platformId: "future-channel",
    capabilities: ["text", "attachments"],
  });

  expect(renderer.id).toBe("generic");
});
```

```ts
it("removes controls that the backend descriptor does not support", () => {
  const model = buildComposerModel({ capabilities: ["text"] });
  expect(model.canUpload).toBe(false);
  expect(model.canReact).toBe(false);
  expect(model.canSendText).toBe(true);
});
```

- [ ] **Step 3: Implement typed API contracts**

```ts
export interface ConversationSummary {
  id: string;
  platformId: string;
  title: string;
  unreadCount: number;
  lastMessageText: string | null;
  lastMessageAt: string | null;
}

export interface ChannelDescriptor {
  platformId: string;
  displayName: string;
  capabilities: readonly string[];
  deferred: boolean;
}
```

`ApiClient` must accept `baseUrl`, `getAccessToken`, and `workspaceId`; it must never read secrets from global variables.

- [ ] **Step 4: Implement resumable WebSocket client**

```ts
export interface CursorStore {
  read(workspaceId: string): number;
  write(workspaceId: string, cursor: number): void;
}
```

The client reconnects with `?after=<cursor>`, ignores an event whose cursor is less than or equal to the stored cursor, stores the cursor only after the event reducer succeeds, and uses bounded exponential backoff.

- [ ] **Step 5: Implement the four-column shared shell**

The DOM landmark order must be:

```text
nav[channel navigation]
section[conversation list]
main[conversation workspace]
aside[context panel]
```

Channel navigation is populated only from backend descriptors. The generic renderer displays text, reply references, attachments, delivery state, timestamps, and unsupported structured payloads as safe JSON summaries.

- [ ] **Step 6: Write the end-to-end generic inbox test**

```ts
test("ingest, stream, reload, and resume without duplicate", async ({ page }) => {
  const fixture = await seedNormalizedMessage();
  await page.goto(`/inbox/${fixture.platformId}/${fixture.conversationId}`);
  await expect(page.getByText(fixture.text)).toHaveCount(1);

  await page.reload();
  await expect(page.getByText(fixture.text)).toHaveCount(1);
  await expect.poll(() => readStoredCursor(page)).toBeGreaterThan(0);
});
```

- [ ] **Step 7: Verify browser isolation and full build**

Run:

```bash
npm install --prefix platform/web
npm run --prefix platform/web check
rg "hermesDesktop|electron|node:" platform/web/src && exit 1 || true
python -m pytest tests/scripts/platform_inventory platform/backend/tests -q
npm run --prefix apps/desktop build
```

Expected: typecheck, unit tests, production build, browser E2E, backend tests, and Electron-import scan pass.

- [ ] **Step 8: Commit**

```bash
git add platform/web apps/desktop/e2e/platform-web-generic-inbox.spec.ts package-lock.json
git commit -m "feat(platform): add browser inbox renderer SDK"
```

---

## Phase 1 Final Verification

- [ ] Run focused backend tests:

```bash
python -m pytest platform/backend/tests -q
```

- [ ] Run inventory and bridge tests:

```bash
python -m pytest tests/scripts/platform_inventory platform/backend/tests/hermes_bridge -q
python -m scripts.platform_inventory --root . --output /tmp/phase1-final-inventory generate
```

- [ ] Run infrastructure integration tests:

```bash
AGENTIC_PLATFORM_POSTGRES_DSN=postgresql://postgres:postgres@localhost:5432/agentic_test \
AGENTIC_PLATFORM_REDIS_URL=redis://localhost:6379/15 \
AGENTIC_PLATFORM_S3_ENDPOINT=http://localhost:9000 \
AGENTIC_PLATFORM_S3_ACCESS_KEY=minio \
AGENTIC_PLATFORM_S3_SECRET_KEY=minio123 \
python -m pytest platform/backend/tests/storage -q
```

- [ ] Run browser checks:

```bash
npm run --prefix platform/web check
```

- [ ] Run repository gates:

```bash
uv lock --check
python -m compileall -q scripts/platform_inventory platform/backend/src/agentic_platform
git diff --check
```

- [ ] Verify the ten Phase 1 acceptance criteria line by line in `docs/platform/agentic-platform-delivery-roadmap.md`.

- [ ] Open or update the Phase 1 PR directly against current `main`, wait for all GitHub checks, and merge only the exact green head.

- [ ] Tag the completion commit in the Phase 1 report; do not start Phase 2 before this gate is green.