# redis_logger.py
import os, json, time, redis
from livekit.agents import (
    AgentSession,
    ConversationItemAddedEvent,
    UserInputTranscribedEvent,
)
redis_url = os.getenv(
    "TRANSCRIPT_REDIS_URL",
    "redis://default:Ahoum%40654321@82.29.162.1:5434/0",
)
rdb = redis.from_url(redis_url, decode_responses=True)  # redis-py ≥5.0 

def attach_logging(session: AgentSession):
    room_name = session.room.name            # becomes our convo_id
    user_id   = session.userdata.identity if session.userdata else "unknown"

    @session.on("conversation_item_added")
    def _on_item(ev: ConversationItemAddedEvent):
        doc = {
            "uid": user_id,
            "cid": room_name,
            "role": ev.item.role,
            "text": ev.item.text_content,
            "ts": int(time.time()*1000),
        }
        rdb.xadd(f"convo:{room_name}", doc)  # Stream key per conversation

    # (Optional) capture partial live STT
    @session.on("user_input_transcribed")
    def _on_stt(ev: UserInputTranscribedEvent):
        if not ev.is_final:        # skip interim if you only want finals
            return
        rdb.xadd(
            f"convo:{room_name}",
            {
                "uid": user_id,
                "cid": room_name,
                "role": "user",
                "text": ev.transcript,
                "ts": int(time.time()*1000),
            },
        )

    # Save the full chat at the end for auditing
    async def _flush_history():
        rdb.set(
            f"convo:{room_name}:archive",
            json.dumps(session.history.to_dict(), ensure_ascii=False),
        )
    session.add_shutdown_callback(_flush_history)
