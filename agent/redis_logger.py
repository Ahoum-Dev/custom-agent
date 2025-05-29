"""
Push every chat turn (user + agent) into a Redis Stream.

Key pattern:
    convo:<room_name>      – ordered stream of turns
    convo:<room_name>:archive – full JSON chat history at shutdown
"""
import os, json, time, redis
from livekit.agents import (
    AgentSession,
    ConversationItemAddedEvent,
    UserInputTranscribedEvent,
    ParticipantJoinedEvent,
)

# --------------------------------------------------------------------------- #
REDIS_URL = os.getenv(
    "TRANSCRIPT_REDIS_URL",
    "redis://default:Ahoum%40654321@82.29.162.1:5434/0",
)
rdb = redis.from_url(REDIS_URL, decode_responses=True)     # redis-py ≥5.0

# --------------------------------------------------------------------------- #
def attach_logging(session: AgentSession, room_name: str):
    """
    Register session hooks that stream text to Redis Streams.
    Must be called *before* session.start().
    """
    user_id = "unknown"                                    # filled on join

    # Identify the first non-agent participant as the user
    @session.on("participant_joined")
    def _got_user(ev: ParticipantJoinedEvent):
        nonlocal user_id
        if not ev.participant.identity.startswith("agent"):
            user_id = ev.participant.identity

    # Push every committed turn (user or agent)
    @session.on("conversation_item_added")
    def _on_item(ev: ConversationItemAddedEvent):
        _xadd(ev.item.role, ev.item.text_content)

    # Optional: push final STT segments as soon as they arrive
    @session.on("user_input_transcribed")
    def _on_stt(ev: UserInputTranscribedEvent):
        if ev.is_final:
            _xadd("user", ev.transcript)

    # Helper to write one record
    def _xadd(role: str, text: str):
        rdb.xadd(
            f"convo:{room_name}",
            {
                "uid": user_id,
                "cid": room_name,
                "role": role,
                "text": text,
                "ts": int(time.time() * 1000),
            },
            maxlen=1000,           # trim to 1 000 entries (tune as needed)
            approximate=True,
        )

    # Archive the full history at the end
    async def _flush_history():
        rdb.set(
            f"convo:{room_name}:archive",
            json.dumps(session.history.to_dict(), ensure_ascii=False),
        )

    session.add_shutdown_callback(_flush_history)
