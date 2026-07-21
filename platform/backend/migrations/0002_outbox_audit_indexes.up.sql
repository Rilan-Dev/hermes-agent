CREATE INDEX idx_conversations_workspace_recent
    ON conversations(workspace_id, updated_at DESC, id DESC);
CREATE INDEX idx_messages_workspace_conversation_sent
    ON messages(workspace_id, conversation_id, sent_at ASC, id ASC);
CREATE INDEX idx_channel_events_idempotency
    ON channel_events(workspace_id, connection_id, platform_event_id);
CREATE INDEX idx_workspace_outbox_cursor
    ON workspace_outbox(workspace_id, cursor ASC);
CREATE INDEX idx_audit_records_workspace_occurred
    ON audit_records(workspace_id, occurred_at DESC, id DESC);
