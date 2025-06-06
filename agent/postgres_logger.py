import os
from datetime import datetime
import asyncpg
import httpx
import json

from livekit.agents import AgentSession


# Postgres connection URL, e.g. postgres://user:password@host:port/dbname
DATABASE_URL = os.getenv("DATABASE_URL", "postgres://postgres:Ahoum%40654321@82.29.162.1:5435/postgres")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is required for Postgres logging")

def attach_logging(session: AgentSession, room_name: str, ctx):
    """
    Attach handlers to log conversation metadata and messages to Postgres.
    """
    user_id = "unknown"
    # Mark the conversation start time
    started_at = datetime.utcnow()
    # Buffer messages until shutdown
    message_buffer = []

    @session.on("participant_joined")
    def _remember_user(ev):
        nonlocal user_id
        # Identify the first non-agent participant as the user
        if not ev.participant.identity.startswith("agent"):
            user_id = ev.participant.identity

    @session.on("conversation_item_added")
    def _on_turn(ev):
        message_buffer.append({
            "role": ev.item.role,
            "content": ev.item.text_content,
            "timestamp": datetime.utcnow(),
        })

    @session.on("user_input_transcribed")
    def _on_stt(ev):
        if ev.is_final:
            message_buffer.append({
                "role": "user",
                "content": ev.transcript,
                "timestamp": datetime.utcnow(),
            })

    async def _flush_history():
        """
        On job shutdown, persist the buffered conversation to Postgres and notify external service.
        """
        ended_at = datetime.utcnow()
        # Connect to Postgres
        conn = await asyncpg.connect(DATABASE_URL)
        # Ensure pgcrypto extension and necessary tables exist
        await conn.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
        await conn.execute("""
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    started_at TIMESTAMPTZ NOT NULL,
    ended_at TIMESTAMPTZ NOT NULL
)
""")
        await conn.execute("""
CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    conversation_id UUID NOT NULL REFERENCES conversations(id),
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
)
""")
        try:
            # Insert conversation metadata
            conv_sql = """
                INSERT INTO conversations(session_id, user_id, started_at, ended_at)
                VALUES($1, $2, $3, $4)
                RETURNING id
            """
            conv_id = await conn.fetchval(
                conv_sql, room_name, user_id, started_at, ended_at
            )
            # Insert all messages in order
            msg_sql = """
                INSERT INTO messages(conversation_id, role, content, created_at)
                VALUES($1, $2, $3, $4)
            """
            for msg in message_buffer:
                await conn.execute(
                    msg_sql,
                    conv_id,
                    msg["role"],
                    msg["content"],
                    msg["timestamp"],
                )
        finally:
            await conn.close()

        # Persist conversation as JSON file
        try:
            os.makedirs("conversation_logs", exist_ok=True)
            convo_log = {
                "uid": user_id,
                "conversation_id": str(conv_id),
                "created_at": started_at.isoformat() + "Z",
                "updated_at": ended_at.isoformat() + "Z",
                "conversation": [
                    {"speaker": msg["role"], "text": msg["content"]}
                    for msg in message_buffer
                ],
            }
            with open(os.path.join("conversation_logs", f"{conv_id}.json"), "w") as f:
                json.dump(convo_log, f, indent=2)
        except Exception as e:
            print(f"Error writing conversation JSON: {e}", flush=True)

        # Optionally notify another endpoint with session and user IDs
        notify_url = os.getenv("NOTIFY_URL")
        if notify_url:
            try:
                await httpx.post(
                    notify_url,
                    json={"session_id": room_name, "user_id": user_id},
                )
            except Exception:
                # Log or ignore notification failures
                pass

    # Register shutdown callback
    ctx.add_shutdown_callback(_flush_history)

    # Also flush when the audio stream closes
    @session.on("stream_closed")
    async def _on_stream_closed(ev):
        await _flush_history() 