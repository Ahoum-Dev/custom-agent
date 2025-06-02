"""
Telephony service for making outbound calls using LiveKit and Twilio
"""
import os
import logging
from typing import Optional, Dict
from livekit import api
from livekit.api import CreateEgressRequest, EgressInfo
from livekit.plugins import telephony
from twilio.rest import Client
import asyncio

logger = logging.getLogger("telephony_service")

class TelephonyService:
    def __init__(self):
        # Twilio credentials
        self.twilio_account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.twilio_phone_number = os.getenv("TWILIO_PHONE_NUMBER")
        
        # LiveKit credentials
        self.livekit_url = os.getenv("LIVEKIT_URL")
        self.livekit_api_key = os.getenv("LIVEKIT_API_KEY")
        self.livekit_api_secret = os.getenv("LIVEKIT_API_SECRET")
        
        # Initialize Twilio client
        if self.twilio_account_sid and self.twilio_auth_token:
            self.twilio_client = Client(self.twilio_account_sid, self.twilio_auth_token)
        else:
            logger.warning("Twilio credentials not found")
            self.twilio_client = None
        
        # Initialize LiveKit client
        if self.livekit_url and self.livekit_api_key and self.livekit_api_secret:
            self.livekit_client = api.LiveKitAPI(
                url=self.livekit_url,
                api_key=self.livekit_api_key,
                api_secret=self.livekit_api_secret
            )
        else:
            logger.warning("LiveKit credentials not found")
            self.livekit_client = None
    
    async def initiate_outbound_call(self, phone_number: str, room_name: str, facilitator_name: str = "Facilitator") -> Dict:
        """
        Initiate an outbound call using LiveKit telephony
        """
        try:
            if not self.livekit_client:
                raise Exception("LiveKit client not initialized")
            
            # Create a room for the call
            room_options = api.CreateRoomRequest(
                name=room_name,
                empty_timeout=60 * 5,  # 5 minutes
                max_participants=2,
                metadata=f"Outbound call to {facilitator_name}"
            )
            
            room = await self.livekit_client.room.create_room(room_options)
            logger.info(f"Created room {room_name} for call to {phone_number}")
            
            # Create SIP outbound call using LiveKit telephony
            # Note: This requires LiveKit Cloud with telephony features enabled
            outbound_request = {
                "sip_trunk_id": os.getenv("LIVEKIT_SIP_TRUNK_ID"),  # You'll need to configure this
                "number": phone_number,
                "room_name": room_name,
                "participant_identity": f"facilitator-{phone_number.replace('+', '')}",
                "participant_name": facilitator_name
            }
            
            # Start the outbound call (this depends on your LiveKit setup)
            # For now, we'll simulate with Twilio call initiation
            call_sid = await self._initiate_twilio_call(phone_number, room_name)
            
            return {
                "success": True,
                "room_name": room_name,
                "call_sid": call_sid,
                "phone_number": phone_number,
                "facilitator_name": facilitator_name
            }
            
        except Exception as e:
            logger.error(f"Error initiating outbound call: {e}")
            return {
                "success": False,
                "error": str(e),
                "phone_number": phone_number
            }
    
    async def _initiate_twilio_call(self, phone_number: str, room_name: str) -> Optional[str]:
        """
        Initiate a call using Twilio and bridge to LiveKit room
        """
        try:
            if not self.twilio_client:
                raise Exception("Twilio client not initialized")
            
            # Webhook URL that will handle the call and bridge to LiveKit
            webhook_url = f"{os.getenv('BASE_URL', 'https://your-domain.com')}/webhook/twilio-call"
            
            # Create TwiML for the call
            twiml_url = f"{webhook_url}?room_name={room_name}"
            
            call = self.twilio_client.calls.create(
                to=phone_number,
                from_=self.twilio_phone_number,
                url=twiml_url,
                method='POST',
                status_callback=f"{webhook_url}/status",
                status_callback_event=['initiated', 'ringing', 'answered', 'completed']
            )
            
            logger.info(f"Twilio call initiated: {call.sid} to {phone_number}")
            return call.sid
            
        except Exception as e:
            logger.error(f"Error initiating Twilio call: {e}")
            return None
    
    async def check_call_status(self, call_sid: str) -> Dict:
        """
        Check the status of a Twilio call
        """
        try:
            if not self.twilio_client:
                raise Exception("Twilio client not initialized")
            
            call = self.twilio_client.calls(call_sid).fetch()
            
            return {
                "status": call.status,
                "duration": call.duration,
                "start_time": call.start_time,
                "end_time": call.end_time,
                "price": call.price,
                "price_unit": call.price_unit
            }
            
        except Exception as e:
            logger.error(f"Error checking call status: {e}")
            return {"error": str(e)}
    
    async def end_call(self, call_sid: str) -> bool:
        """
        End a Twilio call
        """
        try:
            if not self.twilio_client:
                raise Exception("Twilio client not initialized")
            
            call = self.twilio_client.calls(call_sid).update(status='completed')
            logger.info(f"Call {call_sid} ended")
            return True
            
        except Exception as e:
            logger.error(f"Error ending call: {e}")
            return False
    
    def generate_twiml_response(self, room_name: str) -> str:
        """
        Generate TwiML response to bridge Twilio call to LiveKit room
        """
        # This would typically be handled by a webhook endpoint
        # For now, we'll return basic TwiML that plays a message
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">Hello! You are being connected to our onboarding agent. Please hold while we establish the connection.</Say>
    <Pause length="2"/>
    <Say voice="alice">Thank you for your patience. Our agent will be with you shortly to discuss the onboarding process.</Say>
    <Record action="/webhook/recording-complete" method="POST" maxLength="300" timeout="10" />
</Response>"""
        return twiml
