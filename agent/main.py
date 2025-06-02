from dotenv import load_dotenv
import os
import asyncio
import logging
from datetime import datetime

from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions, function_tool, RunContext
from livekit.plugins import (
    groq,
    silero,
    noise_cancellation,
)
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from livekit_plugins.plugins.kokoro_tts import TTS as KokoroTTS

from dataclasses import dataclass
from redis_logger import attach_logging
from csv_manager import CSVManager
from telephony_service import TelephonyService

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize services
csv_manager = CSVManager()
telephony_service = TelephonyService()

class OnboardingAgent(Agent):
    def __init__(self) -> None:
        super().__init__(instructions="""
        Role Definition:
        You are Alex, a professional onboarding specialist at our platform. Your purpose is to:
        - Welcome facilitators to our platform
        - Guide them through the onboarding process
        - Explain platform features and benefits
        - Answer questions about getting started
        - Collect necessary information for account setup
        - Schedule training sessions if needed
        
        You are calling facilitators who have expressed interest in joining our platform as educators/trainers.
                         
        Conversation Flow Guidelines:
        1. Introduction: "Hi [Name], this is Alex calling from [Platform Name]. I understand you're interested in joining our platform as a facilitator. Is this a good time to talk for about 5-10 minutes?"
        
        2. If they say yes, proceed with: "Great! I'd love to help you get started and answer any questions you might have about our platform."
        
        3. Key topics to cover:
        - Confirm their interest and background
        - Explain platform benefits (reach, earnings, support)
        - Outline the simple onboarding process
        - Ask about their expertise area/subject matter
        - Discuss next steps (account creation, documentation, training)
        - Schedule follow-up if needed
        
        4. Gather information:
        - Confirm contact details
        - Ask about their teaching/training background
        - Understand their availability preferences
        - Note any specific requirements or questions
        
        5. Closing: Provide clear next steps and ensure they know how to reach us
        
        Tone and Personality:
        - Professional yet friendly and approachable
        - Enthusiastic about the platform without being pushy
        - Patient and willing to answer all questions thoroughly
        - Clear and concise in explanations
        - Respectful of their time
        
        Important Guidelines:
        - Keep the call focused and within 5-10 minutes unless they want to continue
        - If they're not interested, politely thank them and ask if they'd like us to follow up in the future
        - If they're busy, offer to schedule a callback
        - Always confirm their contact information before ending
        - Take notes on their responses for follow-up
        
        You should NOT:
        - Make any promises about earnings or success
        - Pressure them to make immediate decisions
        - Share confidential platform information
        - Discuss other facilitators or competitive information
        
        Remember: This is a professional business call focused on helping interested facilitators join our platform.
        """)
        
        self.current_facilitator = None
        self.call_start_time = None
        self.call_notes = []

    async def on_enter(self) -> None:
        # Get facilitator info from room metadata or context
        facilitator_info = getattr(self.session, 'facilitator_info', None)
        if facilitator_info:
            self.current_facilitator = facilitator_info
            name = facilitator_info.get('name', 'there')
            await self.session.generate_reply(
                instructions=f"""Start the call professionally. Say: "Hi {name}, this is Alex calling from our learning platform. I understand you're interested in joining us as a facilitator. Is this a good time to talk for about 5-10 minutes about the onboarding process?"""
            )
        else:
            await self.session.generate_reply(
                instructions="Hello, this is Alex calling about facilitator onboarding. May I ask who I'm speaking with?"
            )
        
        self.call_start_time = datetime.now()

    async def on_exit(self):
        # Wrap up the call professionally
        await self.session.generate_reply(
            instructions="""Thank the facilitator for their time. Provide clear next steps. Say something like: "Thank you for your time today. I'll send you the onboarding information we discussed, and someone from our team will follow up with you within 24 hours. Do you have any final questions? Have a great day!" Keep it brief and professional."""
        )
        
        # Update call status in CSV
        if self.current_facilitator:
            facilitator_index = self.current_facilitator.get('index')
            notes = " | ".join(self.call_notes) if self.call_notes else "Call completed"
            csv_manager.update_call_status(
                index=facilitator_index,
                status="completed", 
                notes=notes,
                completed=True  # Mark onboarding as discussed
            )
            logger.info(f"Updated facilitator {facilitator_index} status to completed")

    @function_tool()
    async def take_note(self, note: str) -> str:
        """Take a note about the facilitator's response or requirements during the call."""
        self.call_notes.append(f"{datetime.now().strftime('%H:%M')}: {note}")
        logger.info(f"Note taken: {note}")
        return f"Note recorded: {note}"

    @function_tool()
    async def schedule_callback(self, preferred_time: str, reason: str) -> str:
        """Schedule a callback if the facilitator requests it."""
        note = f"Callback requested for {preferred_time} - Reason: {reason}"
        self.call_notes.append(note)
        
        if self.current_facilitator:
            facilitator_index = self.current_facilitator.get('index')
            csv_manager.update_call_status(
                index=facilitator_index,
                status="callback_scheduled",
                notes=note
            )
        
        logger.info(f"Callback scheduled: {note}")
        return f"I've scheduled a callback for {preferred_time}. We'll follow up with you then."

    @function_tool()
    async def mark_not_interested(self, reason: str = "") -> str:
        """Mark facilitator as not interested if they decline."""
        note = f"Not interested - Reason: {reason}" if reason else "Not interested"
        self.call_notes.append(note)
        
        if self.current_facilitator:
            facilitator_index = self.current_facilitator.get('index')
            csv_manager.update_call_status(
                index=facilitator_index,
                status="not_interested",
                notes=note
            )
        
        logger.info(f"Marked as not interested: {note}")
        return "I understand. Thank you for your time. Would you like us to follow up with you in the future?"


async def make_outbound_calls():
    """
    Main function to process facilitators and make outbound calls
    """
    logger.info("Starting outbound calling process...")
    
    # Initialize database if available
    try:
        from database import db_manager
        await db_manager.create_tables()
        logger.info("Database initialized successfully")
    except ImportError:
        logger.warning("Database module not available")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
    
    call_count = 0
    max_calls_per_session = int(os.getenv("MAX_CALLS_PER_SESSION", "5"))
    
    while call_count < max_calls_per_session:
        # Get next facilitator to call
        facilitator = csv_manager.get_next_facilitator()
        
        if not facilitator:
            logger.info("No more facilitators to call")
            break
        
        logger.info(f"Preparing to call {facilitator['name']} at {facilitator['phone_number']}")
        
        # Update status to in_progress
        csv_manager.update_call_status(
            index=facilitator['index'],
            status="in_progress",
            notes="Call initiated"
        )
        
        # Generate unique room name for this call
        room_name = f"onboarding-call-{facilitator['index']}-{int(datetime.now().timestamp())}"
        
        try:
            # Initiate outbound call
            call_result = await telephony_service.initiate_outbound_call(
                phone_number=facilitator['phone_number'],
                room_name=room_name,
                facilitator_name=facilitator['name']
            )
            
            if call_result.get('success'):
                logger.info(f"Call initiated successfully: {call_result}")
                
                # Start the agent session for this call
                await start_agent_session(room_name, facilitator)
                call_count += 1
                
                # Wait between calls
                await asyncio.sleep(int(os.getenv("CALL_INTERVAL_SECONDS", "60")))
                
            else:
                logger.error(f"Failed to initiate call: {call_result}")
                csv_manager.update_call_status(
                    index=facilitator['index'],
                    status="failed",
                    notes=f"Call initiation failed: {call_result.get('error', 'Unknown error')}"
                )
                
        except Exception as e:
            logger.error(f"Error during call to {facilitator['name']}: {e}")
            csv_manager.update_call_status(
                index=facilitator['index'],
                status="failed",
                notes=f"Exception during call: {str(e)}"
            )
        
        # Short break between calls
        await asyncio.sleep(5)
    
    logger.info(f"Completed calling session. Made {call_count} calls.")


async def start_agent_session(room_name: str, facilitator_info: dict):
    """
    Start an agent session for handling the call
    """
    # This would typically be called when a participant joins the room
    # For now, we'll simulate the session start
    logger.info(f"Starting agent session for room: {room_name}")
    
    # The actual session would be created when the LiveKit room gets a participant
    # This is just a placeholder for the session management logic


async def entrypoint(ctx: agents.JobContext):
    await ctx.connect()
    
    # Get facilitator info from room metadata
    facilitator_info = None
    if ctx.room.metadata:
        try:
            import json
            metadata = json.loads(ctx.room.metadata)
            facilitator_info = metadata.get('facilitator_info')
        except:
            pass

    session = AgentSession(
        stt=groq.STT(
            model="whisper-large-v3-turbo",
            language="en",
        ),
        llm=groq.LLM(model="gemma2-9b-it"),
        tts=groq.TTS(
            model="playai-tts",
            voice="Arista-PlayAI",
        ),
        vad=silero.VAD.load(),
        turn_detection=MultilingualModel(),
    )
    
    # Attach logging with facilitator info
    call_id = f"call_{ctx.room.name}_{int(datetime.now().timestamp())}"
    attach_logging(session, ctx.room.name, ctx, call_id, facilitator_info)

    # Set facilitator info on session for the agent to access
    session.facilitator_info = facilitator_info

    await session.start(
        room=ctx.room,
        agent=OnboardingAgent(),
        room_input_options=RoomInputOptions(),
    )


# CLI command for making outbound calls
@agents.cli.command()
async def start_calling():
    """Start the outbound calling process"""
    await make_outbound_calls()


if __name__ == "__main__":
    # Add custom command to CLI
    agents.cli.run_app(
        agents.WorkerOptions(entrypoint_fnc=entrypoint),
        start_calling_command=start_calling
    )
