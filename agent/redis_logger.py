"""
Stream every chat turn to Redis Streams.

Key pattern
-----------
convo:<room_name>           → XADD-based timeline
convo:<room_name>:archive   → JSON dump at shutdown
"""
import os, json, time
from livekit.agents import (
    AgentSession,
    ConversationItemAddedEvent,
    UserInputTranscribedEvent,
    ParticipantJoinedEvent,
)

REDIS_URL = os.getenv(
    "TRANSCRIPT_REDIS_URL",
    "redis://default:Ahoum%40654321@82.29.162.1:5434/0",
)

# ─────────────────────────────────────────────────────────────────────────────
def attach_logging(session: AgentSession, room_name: str):
    """
    Register session hooks.  Called from main.py *after* you create the session
    but *before* session.start().
    """
    # ↓↓  local import so `python main.py download-files` works even if redis
    # is not yet installed — it’s only needed at runtime.
    import redis                                    # noqa:  E402
    rdb = redis.from_url(REDIS_URL, decode_responses=True)   # 

    user_id = "unknown"                             # filled once someone joins

    @session.on("participant_joined")
    def _on_join(ev: ParticipantJoinedEvent):
        nonlocal user_id
        if not ev.participant.identity.startswith("agent"):
            user_id = ev.participant.identity

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
            maxlen=1000,
            approximate=True,
        )

    @session.on("conversation_item_added")
    def _on_item(ev: ConversationItemAddedEvent):
        _xadd(ev.item.role, ev.item.text_content)

    @session.on("user_input_transcribed")
    def _on_stt(ev: UserInputTranscribedEvent):
        if ev.is_final:
            _xadd("user", ev.transcript)

    async def _flush_history():
        rdb.set(
            f"convo:{room_name}:archive",
            json.dumps(session.history.to_dict(), ensure_ascii=False),
        )

    session.add_shutdown_callback(_flush_history)
