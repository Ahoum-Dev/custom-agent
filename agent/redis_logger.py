"""
Realtime transcript streaming → Redis Streams.

•  convo:<room_name>             — ordered timeline (trimmed to 1 000 items)
•  convo:<room_name>:archive     — full JSON history at shutdown
"""
import os, json, time
from livekit.agents import AgentSession

REDIS_URL = os.getenv(
    "TRANSCRIPT_REDIS_URL",
    "redis://default:Ahoum%40654321@82.29.162.1:5434/0",
)


def attach_logging(session: AgentSession, room_name: str, ctx):
    """
    Register session hooks **and** a shutdown hook on the JobContext.

    Parameters
    ----------
    session : AgentSession
        The current agent session.
    room_name : str
        LiveKit room → conversation ID.
    ctx : JobContext
        Needed to register `ctx.add_shutdown_callback`.
    """
    # Lazy import so build-time commands (`python main.py download-files`) work
    import redis  # noqa:  E402

    rdb = redis.from_url(REDIS_URL, decode_responses=True)

    user_id = "unknown"  # will be set on the first participant join

    # —── identify the human participant —───────────────────────
    @session.on("participant_joined")
    def _remember_user(ev):
        nonlocal user_id
        if not ev.participant.identity.startswith("agent"):
            user_id = ev.participant.identity

    # —── helper to push a single record —────────────────────────
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

    # —── full turns —───────────────────────────────────────────
    @session.on("conversation_item_added")
    def _on_turn(ev):
        _xadd(ev.item.role, ev.item.text_content)

    # —── final STT segments —───────────────────────────────────
    @session.on("user_input_transcribed")
    def _on_stt(ev):
        if ev.is_final:
            _xadd("user", ev.transcript)

    # —── archive the whole history after disconnect —───────────
    async def _flush_history():
        rdb.set(
            f"convo:{room_name}:archive",
            json.dumps(session.history.to_dict(), ensure_ascii=False),
        )

    ctx.add_shutdown_callback(_flush_history)
