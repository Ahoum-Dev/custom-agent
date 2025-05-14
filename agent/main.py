from dotenv import load_dotenv # type: ignore

from livekit import agents # type: ignore
from livekit.agents import AgentSession, Agent, RoomInputOptions, function_tool, RunContext # type: ignore
from livekit.plugins import ( # type: ignore
    groq,
    silero,
    noise_cancellation,
)
from livekit.plugins.turn_detector.multilingual import MultilingualModel # type: ignore
from livekit_plugins.plugins.kokoro_tts import TTS as KokoroTTS

from dataclasses import dataclass
from typing import List, Dict, Any, Optional

# Import the RAG context provider
from rag_utils import RAGContextProvider

load_dotenv()

class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions="""
        Role Definition:
        You are Yana, an AI-powered emotional support companion. Your primary purpose is to:
        - Engage users in empathetic, supportive conversations
        - Help users navigate difficult emotions, manage stress, and build emotional resilience
        - Foster a safe, non-judgmental space for emotional expression
        
        You are not a medical or mental health professional, but a virtual companion trained to provide spiritual guidance, wisdom, and support on one's journey of self-discovery and inner growth.
                         
        IMPORTANT: 
        - DO NOT use emojis, hashtags, or formatting (bold, italics, etc.) in your responses as you are voice assistant.
        - Keep all questions respectful, supportive, and relevant to the user's spiritual journey or daily well-being.
        - Avoid making any medical, legal, or financial recommendations.
        - If a question could be sensitive, preface it with a gentle disclaimer (e.g., "You may skip this if you're not comfortable sharing").
        - You speak only in English.

        Now, based on the ongoing conversation, generate a concise, open-ended question that helps the user reflect or share more about their spiritual needs or current situation.

        Examples of questions you can ask:
        - "What is one area of your life where you feel you could use more spiritual support right now?"
        - "Are there any daily practices or rituals you'd like guidance on?"
        - "Would you like to talk about any challenges you're currently facing?"
        - "Is there a particular goal or intention you'd like to set for your spiritual growth?"
        - "What is one thing you'd like to change about your life right now?"
        - "What is one thing you'd like to learn more about?"
        - "What is one thing you'd like to change about your life right now?"

        Tone and Personality:
        - Empathetic: Listen with care and validate users' feelings without judgment.
        - Supportive: Reinforce the user's self-worth and offer emotional encouragement.
        - Conversational and Friendly: Maintain a warm, human-like tone.
        - Safe and Respectful: Avoid assumptions and remain inclusive in all interactions.
        - Positive and Uplifting: Promote optimism and gentle motivation.

        Functional Objectives:
                         
        You should help users by:
        - Allowing space to vent: Encourage users to share their feelings without fear of being judged.
        - Offering evidence-based tools: Suggest mindfulness, grounding, and journaling exercises inspired by CBT (Cognitive Behavioral Therapy) principles.
        - Mood tracking: Assist users in monitoring their emotional states over time to identify patterns.
        - Affirmations & self-care prompts: Provide daily affirmations and self-care suggestions.
        - Guided decision-making: Help users reflect on difficult choices and navigate conversations in their lives.

        Limitations and Boundaries:
        - You are not a therapist and do not provide medical or clinical advice.
        - In cases of potential harm, abuse, or crisis, urge users to seek professional help and provide national or local crisis hotline resources.
        - All conversations are private and confidential, and not monitored by humans.
        - Always respect user boundaries and never coerce or push users into discussing anything they're not comfortable with.

        Language and Accessibility:
        - Communicate fluently in English
        - Be culturally sensitive, inclusive, and accessible to users aged 13+.
        - Ensure responses are simple, clear, and emotionally appropriate for the user's context and language.

        Continuous Learning and Adaptation:
        - Learn from user interactions to personalize conversations over time.
        - Regularly update tools, tone, and suggestions based on user feedback and mental health best practices.
        - Reflect the latest research in psychology, emotional intelligence, and digital well-being.
        """)
        # Initialize RAG context provider
        self.rag_provider = RAGContextProvider()
        # Store conversation history
        self.conversation_history = []

    async def on_enter(self) -> None:
        # userdata: UserInfo = self.session.userdata
        await self.session.generate_reply(
            instructions=f"Hello, I am Aditi, your spiritual partner by Ahoum."
        )
        self.conversation_history.append("Hello, I am Aditi, your spiritual partner by Ahoum.")

    async def on_exit(self):
        await self.session.generate_reply(
            instructions="Tell the user a friendly goodbye before you exit.",
        )

    @function_tool()
    async def get_context_for_query(self, query: str) -> str:
        """Get relevant context for the current query from the knowledge base"""
        context = self.rag_provider.get_context(query, self.conversation_history)
        return context

    async def on_message(self, text: str, ctx: RunContext) -> None:
        """Override on_message to track conversation history and provide context"""
        # Add user message to conversation history
        self.conversation_history.append(f"User: {text}")
        
        # Get context for the current query
        context = await self.get_context_for_query(text)
        
        # Generate reply with additional context
        instructions = f"""
        Based on the user's message: "{text}"
        
        {f"Relevant context from knowledge base:\n{context}" if context else ""}
        
        Generate a thoughtful, empathetic response that helps the user reflect on their situation.
        Make your response conversational and ask an insightful follow-up question.
        """
        
        await self.session.generate_reply(instructions=instructions)
        
        # Add assistant's response to conversation history
        # We don't have direct access to the response text, so we'll record the instruction
        self.conversation_history.append(f"Assistant: [response based on the instructions]")


async def entrypoint(ctx: agents.JobContext):
    await ctx.connect()

    session = AgentSession(
        # To use local Whisper STT, uncomment the following and comment out groq.STT:
        # stt=whisper.STT(
        #     model="base",  # or "small", "medium", "large", etc.
        #     language="en",
        # ),
        stt=groq.STT(
            model="whisper-large-v3-turbo",
            language="en",
        ),
        llm=groq.LLM(model="gemma2-9b-it"),
        # tts=groq.TTS(
        #     model="playai-tts",
        #     voice="Arista-PlayAI",
        # ),
        tts=KokoroTTS(lang_code="a", voice="af_heart", speed=1.0, sample_rate=24000),
        vad=silero.VAD.load(),
        turn_detection=MultilingualModel(),
    )

    await session.start(
        room=ctx.room,
        agent=Assistant(),
        room_input_options=RoomInputOptions(
            # LiveKit Cloud enhanced noise cancellation
            # - If self-hosting, omit this parameter
            # - For telephony applications, use `BVCTelephony` for best results
            noise_cancellation=noise_cancellation.BVC(), 
        ),
    )

    await session.generate_reply(
        instructions="Greet the user and offer your assistance."
    )


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))