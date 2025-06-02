"""
Realtime transcript streaming → Redis Streams + PostgreSQL storage.

•  convo:<room_name>             — ordered timeline (trimmed to 1 000 items)
•  convo:<room_name>:archive     — full JSON history at shutdown
•  PostgreSQL database          — permanent storage for call transcripts
"""
import os
import json
import time
import asyncio
import logging
from datetime import datetime
from livekit.agents import AgentSession

logger = logging.getLogger("redis_logger")

REDIS_URL = os.getenv(
    "TRANSCRIPT_REDIS_URL",
    "redis://default:Ahoum%40654321@82.29.162.1:5434/0",
)


def attach_logging(session: AgentSession, room_name: str, ctx, call_id: str = None, facilitator_info: dict = None):
    """
    Register session hooks **and** a shutdown hook on the JobContext.
    Now includes PostgreSQL storage for call transcripts.

    Parameters
    ----------
    session : AgentSession
        The current agent session.
    room_name : str
        LiveKit room → conversation ID.
    ctx : JobContext
        Needed to register `ctx.add_shutdown_callback`.
    call_id : str, optional
        Unique identifier for this call
    facilitator_info : dict, optional
        Information about the facilitator being called
    """
    # Lazy import so build-time commands (`python main.py download-files`) work
    import redis  # noqa:  E402
    
    # Import database manager
    try:
        from database import db_manager
    except ImportError:
        logger.warning("Database module not available, skipping PostgreSQL logging")
        db_manager = None

    rdb = redis.from_url(REDIS_URL, decode_responses=True)

    user_id = "unknown"  # will be set on the first participant join
    call_start_time = datetime.utcnow()
    
    # Initialize database record for this call
    db_call_id = call_id or f"call_{room_name}_{int(time.time())}"
    
    if facilitator_info and db_manager:
        call_data = {
            "call_id": db_call_id,
            "facilitator_name": facilitator_info.get("name", "Unknown"),
            "facilitator_phone": facilitator_info.get("phone_number", "Unknown"),
            "call_start_time": call_start_time,
            "call_status": "connected"
        }
        
        # Save initial call record to database
        try:
            asyncio.create_task(db_manager.save_call_transcript(call_data))
            logger.info(f"Created database record for call {db_call_id}")
        except Exception as e:
            logger.error(f"Error creating database record: {e}")

    # —— identify the human participant ——————————————————
    @session.on("participant_joined")
    def _remember_user(ev):
        nonlocal user_id
        if not ev.participant.identity.startswith("agent"):
            user_id = ev.participant.identity
            logger.info(f"Facilitator joined call: {user_id}")

    # —— helper to push a single record ——————————————————
    def _xadd(role: str, text: str):
        timestamp = datetime.utcnow()
        
        # Add to Redis stream
        rdb.xadd(
            f"convo:{room_name}",
            {
                "uid": user_id,
                "cid": room_name,
                "role": role,
                "text": text,
                "ts": int(time.time() * 1000),
                "call_id": db_call_id
            },
            maxlen=1000,
            approximate=True,
        )
        
        # Save to PostgreSQL if available
        if db_manager:
            try:
                asyncio.create_task(
                    db_manager.save_conversation_turn(
                        call_id=db_call_id,
                        speaker_role=role,
                        text_content=text,
                        timestamp=timestamp
                    )
                )
            except Exception as e:
                logger.error(f"Error saving conversation turn to database: {e}")

    # —— full turns ——————————————————————————————————————
    @session.on("conversation_item_added")
    def _on_turn(ev):
        _xadd(ev.item.role, ev.item.text_content)

    # —— final STT segments ——————————————————————————————
    @session.on("user_input_transcribed")
    def _on_stt(ev):
        if ev.is_final:
            _xadd("user", ev.transcript)

    # —— archive the whole history after disconnect ——————
    async def _flush_history():
        try:
            # Save to Redis archive
            rdb.set(
                f"convo:{room_name}:archive",
                json.dumps(session.history.to_dict(), ensure_ascii=False),
            )
            
            # Update call status and save final transcript to database
            if db_manager:
                call_end_time = datetime.utcnow()
                call_duration = int((call_end_time - call_start_time).total_seconds())
                
                full_transcript = ""
                for item in session.history:
                    if hasattr(item, 'text_content') and item.text_content:
                        role = "Agent" if item.role == "assistant" else "Facilitator"
                        full_transcript += f"{role}: {item.text_content}\n"
                
                # Update database record
                await db_manager.update_call_status(
                    call_id=db_call_id,
                    status="completed",
                    call_end_time=call_end_time,
                    call_duration_seconds=call_duration,
                    full_transcript=full_transcript
                )
                
                logger.info(f"Call {db_call_id} completed and archived")
            
        except Exception as e:
            logger.error(f"Error during call archival: {e}")
            # Try to mark call as failed in database
            if db_manager:
                try:
                    await db_manager.update_call_status(
                        call_id=db_call_id,
                        status="failed",
                        notes=f"Error during archival: {str(e)}"
                    )
                except:
                    pass

    ctx.add_shutdown_callback(_flush_history)
