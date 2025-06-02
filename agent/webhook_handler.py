"""
Webhook handler for Twilio telephony integration
"""
from flask import Flask, request, Response
from twilio.twiml import VoiceResponse
import os
import logging
from telephony_service import TelephonyService

app = Flask(__name__)
logger = logging.getLogger(__name__)

# Initialize telephony service
telephony_service = TelephonyService()

@app.route('/webhook/twilio-call', methods=['POST'])
def handle_twilio_call():
    """Handle incoming Twilio call webhook"""
    try:
        # Get parameters from query string
        room_name = request.args.get('room_name')
        
        if not room_name:
            logger.error("No room_name provided in webhook")
            return Response("Missing room_name parameter", status=400)
        
        # Create TwiML response to bridge call to LiveKit
        response = VoiceResponse()
        
        # Play a greeting message
        response.say("Hello! You are being connected to our onboarding specialist. Please hold while we establish the connection.", voice='alice')
        response.pause(length=2)
        
        # For a full integration, you would:
        # 1. Generate a LiveKit token for this participant
        # 2. Use Twilio's Stream feature to connect to LiveKit
        # 3. Handle the audio bridging
        
        # For now, we'll record the call and play a message
        response.say("Thank you for your interest in joining our platform as a facilitator. Due to technical setup, we'll be calling you back shortly to complete the onboarding process.", voice='alice')
        
        # Record the response for follow-up
        response.record(
            action='/webhook/recording-complete',
            method='POST',
            max_length=120,  # 2 minutes max
            timeout=10
        )
        
        return Response(str(response), mimetype='text/xml')
        
    except Exception as e:
        logger.error(f"Error handling Twilio webhook: {e}")
        response = VoiceResponse()
        response.say("We're experiencing technical difficulties. We'll call you back shortly.")
        return Response(str(response), mimetype='text/xml')

@app.route('/webhook/twilio-call/status', methods=['POST'])
def handle_call_status():
    """Handle Twilio call status updates"""
    try:
        call_sid = request.form.get('CallSid')
        call_status = request.form.get('CallStatus')
        from_number = request.form.get('From')
        to_number = request.form.get('To')
        
        logger.info(f"Call status update: {call_sid} - {call_status}")
        
        # Update call status in your system
        # You would implement this based on your needs
        
        return Response("OK", status=200)
        
    except Exception as e:
        logger.error(f"Error handling call status: {e}")
        return Response("Error", status=500)

@app.route('/webhook/recording-complete', methods=['POST'])
def handle_recording_complete():
    """Handle completed call recording"""
    try:
        recording_url = request.form.get('RecordingUrl')
        call_sid = request.form.get('CallSid')
        recording_duration = request.form.get('RecordingDuration')
        
        logger.info(f"Recording completed for call {call_sid}: {recording_url}")
        
        # Save recording information to database
        # You would implement this based on your needs
        
        return Response("OK", status=200)
        
    except Exception as e:
        logger.error(f"Error handling recording: {e}")
        return Response("Error", status=500)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "twilio-webhook-handler"}

if __name__ == '__main__':
    port = int(os.getenv('WEBHOOK_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
