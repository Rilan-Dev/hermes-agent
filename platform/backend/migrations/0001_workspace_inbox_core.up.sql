CREATE TABLE workspaces (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL CHECK (btrim(name) <> ''),
    created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE users (
    id UUID PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE memberships (
    workspace_id UUID NOT NULL,
    user_id UUID NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('owner', 'admin', 'operator', 'developer', 'viewer')),
    created_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (workspace_id, user_id),
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE agents (
    workspace_id UUID NOT NULL,
    id UUID NOT NULL,
    name TEXT NOT NULL CHECK (btrim(name) <> ''),
    status TEXT NOT NULL DEFAULT 'draft',
    config JSONB NOT NULL DEFAULT '{}'::jsonb,
    payload_version INTEGER NOT NULL DEFAULT 1 CHECK (payload_version > 0),
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (workspace_id, id),
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
);

CREATE TABLE channel_connections (
    workspace_id UUID NOT NULL,
    id UUID NOT NULL,
    platform_id TEXT NOT NULL CHECK (btrim(platform_id) <> ''),
    display_name TEXT NOT NULL CHECK (btrim(display_name) <> ''),
    secret_ref TEXT,
    created_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (workspace_id, id),
    UNIQUE (workspace_id, id, platform_id),
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
);

CREATE TABLE contacts (
    workspace_id UUID NOT NULL,
    id UUID NOT NULL,
    display_name TEXT NOT NULL CHECK (btrim(display_name) <> ''),
    created_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (workspace_id, id),
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
);

CREATE TABLE external_identities (
    workspace_id UUID NOT NULL,
    id UUID NOT NULL,
    connection_id UUID NOT NULL,
    contact_id UUID NOT NULL,
    platform_id TEXT NOT NULL CHECK (btrim(platform_id) <> ''),
    native_id TEXT NOT NULL CHECK (btrim(native_id) <> ''),
    display_name TEXT,
    created_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (workspace_id, id),
    UNIQUE (workspace_id, connection_id, native_id),
    FOREIGN KEY (workspace_id, connection_id, platform_id)
        REFERENCES channel_connections(workspace_id, id, platform_id)
        ON DELETE CASCADE,
    FOREIGN KEY (workspace_id, contact_id)
        REFERENCES contacts(workspace_id, id)
        ON DELETE CASCADE
);

CREATE TABLE conversations (
    workspace_id UUID NOT NULL,
    id UUID NOT NULL,
    connection_id UUID NOT NULL,
    platform_id TEXT NOT NULL CHECK (btrim(platform_id) <> ''),
    native_id TEXT NOT NULL CHECK (btrim(native_id) <> ''),
    conversation_type TEXT NOT NULL CHECK (
        conversation_type IN ('direct', 'group', 'channel', 'thread', 'topic', 'mailbox', 'notification')
    ),
    status TEXT NOT NULL CHECK (status IN ('open', 'pending', 'snoozed', 'resolved', 'closed')),
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    unread_count INTEGER NOT NULL DEFAULT 0 CHECK (unread_count >= 0),
    last_message_text TEXT,
    last_message_at TIMESTAMPTZ,
    PRIMARY KEY (workspace_id, id),
    UNIQUE (workspace_id, id, platform_id),
    UNIQUE (workspace_id, connection_id, native_id),
    FOREIGN KEY (workspace_id, connection_id, platform_id)
        REFERENCES channel_connections(workspace_id, id, platform_id)
        ON DELETE CASCADE
);

CREATE TABLE participants (
    workspace_id UUID NOT NULL,
    conversation_id UUID NOT NULL,
    external_identity_id UUID NOT NULL,
    role TEXT NOT NULL DEFAULT 'member',
    joined_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (workspace_id, conversation_id, external_identity_id),
    FOREIGN KEY (workspace_id, conversation_id)
        REFERENCES conversations(workspace_id, id)
        ON DELETE CASCADE,
    FOREIGN KEY (workspace_id, external_identity_id)
        REFERENCES external_identities(workspace_id, id)
        ON DELETE CASCADE
);

CREATE TABLE messages (
    workspace_id UUID NOT NULL,
    id UUID NOT NULL,
    conversation_id UUID NOT NULL,
    platform_id TEXT NOT NULL CHECK (btrim(platform_id) <> ''),
    native_id TEXT NOT NULL CHECK (btrim(native_id) <> ''),
    direction TEXT NOT NULL CHECK (direction IN ('inbound', 'outbound', 'internal')),
    text TEXT,
    sent_at TIMESTAMPTZ NOT NULL,
    delivery_state TEXT NOT NULL CHECK (delivery_state IN ('queued', 'sent', 'delivered', 'read', 'failed')),
    reply_to_native_id TEXT,
    thread_native_id TEXT,
    PRIMARY KEY (workspace_id, id),
    UNIQUE (workspace_id, conversation_id, native_id),
    FOREIGN KEY (workspace_id, conversation_id, platform_id)
        REFERENCES conversations(workspace_id, id, platform_id)
        ON DELETE CASCADE
);

CREATE TABLE attachments (
    workspace_id UUID NOT NULL,
    id UUID NOT NULL,
    message_id UUID NOT NULL,
    object_ref TEXT NOT NULL CHECK (btrim(object_ref) <> ''),
    mime_type TEXT NOT NULL CHECK (btrim(mime_type) <> ''),
    size_bytes BIGINT NOT NULL CHECK (size_bytes >= 0),
    checksum_sha256 CHAR(64) NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    payload_version INTEGER NOT NULL DEFAULT 1 CHECK (payload_version > 0),
    created_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (workspace_id, id),
    FOREIGN KEY (workspace_id, message_id)
        REFERENCES messages(workspace_id, id)
        ON DELETE CASCADE
);

CREATE TABLE reactions (
    workspace_id UUID NOT NULL,
    id UUID NOT NULL,
    message_id UUID NOT NULL,
    external_identity_id UUID,
    native_id TEXT,
    emoji TEXT NOT NULL CHECK (btrim(emoji) <> ''),
    created_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (workspace_id, id),
    UNIQUE (workspace_id, message_id, native_id),
    FOREIGN KEY (workspace_id, message_id)
        REFERENCES messages(workspace_id, id)
        ON DELETE CASCADE,
    FOREIGN KEY (workspace_id, external_identity_id)
        REFERENCES external_identities(workspace_id, id)
        ON DELETE RESTRICT
);

CREATE TABLE receipts (
    workspace_id UUID NOT NULL,
    id UUID NOT NULL,
    message_id UUID NOT NULL,
    external_identity_id UUID,
    state TEXT NOT NULL CHECK (state IN ('sent', 'delivered', 'read', 'failed')),
    occurred_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (workspace_id, id),
    UNIQUE (workspace_id, message_id, external_identity_id, state),
    FOREIGN KEY (workspace_id, message_id)
        REFERENCES messages(workspace_id, id)
        ON DELETE CASCADE,
    FOREIGN KEY (workspace_id, external_identity_id)
        REFERENCES external_identities(workspace_id, id)
        ON DELETE RESTRICT
);

CREATE TABLE channel_events (
    workspace_id UUID NOT NULL,
    id UUID NOT NULL,
    connection_id UUID NOT NULL,
    platform_event_id TEXT NOT NULL CHECK (btrim(platform_event_id) <> ''),
    kind TEXT NOT NULL CHECK (
        kind IN ('message', 'message_edit', 'message_delete', 'reaction', 'receipt', 'typing', 'membership', 'connection_state')
    ),
    occurred_at TIMESTAMPTZ NOT NULL,
    native_target_platform_id TEXT,
    native_target_id TEXT,
    raw_payload_ref TEXT,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    payload_version INTEGER NOT NULL DEFAULT 1 CHECK (payload_version > 0),
    PRIMARY KEY (workspace_id, id),
    UNIQUE (workspace_id, connection_id, platform_event_id),
    FOREIGN KEY (workspace_id, connection_id)
        REFERENCES channel_connections(workspace_id, id)
        ON DELETE CASCADE,
    CHECK (
        (native_target_platform_id IS NULL AND native_target_id IS NULL)
        OR (native_target_platform_id IS NOT NULL AND native_target_id IS NOT NULL)
    )
);

CREATE TABLE raw_event_objects (
    workspace_id UUID NOT NULL,
    id UUID NOT NULL,
    event_id UUID NOT NULL,
    object_ref TEXT NOT NULL CHECK (btrim(object_ref) <> ''),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    payload_version INTEGER NOT NULL DEFAULT 1 CHECK (payload_version > 0),
    created_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (workspace_id, id),
    FOREIGN KEY (workspace_id, event_id)
        REFERENCES channel_events(workspace_id, id)
        ON DELETE CASCADE
);

CREATE TABLE workspace_outbox (
    workspace_id UUID NOT NULL,
    cursor BIGINT NOT NULL CHECK (cursor > 0),
    event_id UUID NOT NULL,
    aggregate_type TEXT NOT NULL CHECK (btrim(aggregate_type) <> ''),
    aggregate_id TEXT NOT NULL CHECK (btrim(aggregate_id) <> ''),
    event_type TEXT NOT NULL CHECK (btrim(event_type) <> ''),
    payload JSONB NOT NULL,
    payload_version INTEGER NOT NULL DEFAULT 1 CHECK (payload_version > 0),
    occurred_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (workspace_id, cursor),
    UNIQUE (workspace_id, event_id),
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
);

CREATE TABLE audit_records (
    workspace_id UUID NOT NULL,
    id UUID NOT NULL,
    actor_user_id UUID,
    action TEXT NOT NULL CHECK (btrim(action) <> ''),
    target_type TEXT NOT NULL CHECK (btrim(target_type) <> ''),
    target_id TEXT NOT NULL CHECK (btrim(target_id) <> ''),
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    payload_version INTEGER NOT NULL DEFAULT 1 CHECK (payload_version > 0),
    occurred_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (workspace_id, id),
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE,
    FOREIGN KEY (actor_user_id) REFERENCES users(id) ON DELETE SET NULL
);
