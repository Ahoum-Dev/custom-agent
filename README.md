# Onboarding Call Agent - Automated Facilitator Outreach

This system transforms facilitators through automated outbound calls using LiveKit telephony with Twilio integration. The AI agent conducts professional onboarding conversations, takes notes, and schedules callbacks.

## Architecture Overview

- **Agent Service**: LiveKit-based AI agent for natural conversations
- **Telephony Service**: Twilio PSTN calling with LiveKit room bridging
- **Database**: PostgreSQL for persistent transcript storage
- **Redis**: Real-time conversation streaming
- **Webhook Service**: Twilio call status and TwiML handling
- **Call Manager**: Orchestration script for automated calling sessions

## Prerequisites

1. **LiveKit Cloud Account**
   - Sign up at [LiveKit Cloud](https://cloud.livekit.io)
   - Create a new project
   - Note your API key and secret

2. **Twilio Account**
   - Sign up at [Twilio](https://www.twilio.com)
   - Purchase a phone number with voice capabilities
   - Note your Account SID and Auth Token

3. **Groq API Access**
   - Sign up at [Groq](https://console.groq.com)
   - Generate an API key

4. **Docker & Docker Compose**
   ## Quick Start

### 1. Clone and Setup Environment

```bash
git clone <repository-url>
cd custom-agent
cp .env.example .env
```

### 2. Configure Environment Variables

Edit `.env` with your credentials:

```bash
# LiveKit Configuration
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_api_secret
NEXT_PUBLIC_LIVEKIT_URL=wss://your-project.livekit.cloud

# Groq API
GROQ_API_KEY=your_groq_api_key

# Database
POSTGRES_PASSWORD=your_secure_password

# Twilio
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890

# Webhook URL (see deployment section)
WEBHOOK_BASE_URL=https://your-domain.com
```

### 3. Prepare Facilitator Data

Edit `agent/facilitators.csv` with your facilitator contacts:

```csv
name,phone_number,status,priority,last_contacted,attempts,notes,contact_preference,timezone
John Smith,+1234567890,pending,high,,0,,phone,America/New_York
Jane Doe,+1987654321,pending,medium,,0,,phone,America/Los_Angeles
```

### 4. Start Services

```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f agent
```

### 5. Run Database Migrations

```bash
# Run inside agent container
docker-compose exec agent alembic upgrade head
```

### 6. Start Calling Session

```bash
# Interactive calling session
docker-compose exec agent python call_manager.py

# Or run in background
docker-compose exec -d agent python call_manager.py --batch-size 5 --delay 30
```

## Legacy Frontend (Optional)

The system includes an optional Next.js frontend for monitoring.

### Frontend Setup

Copy `.env.example` to `.env.local` and set the environment variables. Then run:

```bash
cd frontend
npm install
npm run dev
```

## Deployment

### Production Webhook Setup

1. **Deploy to Cloud Platform**
   - Use platforms like Railway, Render, or DigitalOcean
   - Ensure webhook service is publicly accessible

2. **Configure Twilio Webhook**
   ```bash
   # Set webhook URL in Twilio Console
   # Voice webhook: https://your-domain.com/webhook/voice
   # Status webhook: https://your-domain.com/webhook/status
   ```

3. **SSL Certificate**
   - Twilio requires HTTPS for webhooks
   - Use Let's Encrypt or platform-provided SSL

## Call Flow

1. **Call Initiation**
   - Call Manager reads facilitators from CSV
   - Prioritizes by status and last contact time
   - Initiates Twilio outbound call

2. **Call Bridging**
   - Twilio receives call, requests TwiML from webhook
   - Webhook creates LiveKit room and returns TwiML
   - Call is bridged to LiveKit room

3. **AI Conversation**
   - Agent joins room and starts conversation
   - Real-time transcription and responses
   - Function tools for note-taking and callbacks

4. **Call Completion**
   - Conversation ends, transcripts saved
   - CSV updated with call results
   - Database stores permanent records

## Monitoring and Maintenance

### Check System Health

```bash
# Service status
docker-compose ps

# Database connection
docker-compose exec agent python -c "from database import DatabaseManager; import asyncio; asyncio.run(DatabaseManager().health_check())"

# View recent calls
docker-compose exec db psql -U postgres -d onboarding_calls -c "SELECT facilitator_name, call_status, created_at FROM call_transcripts ORDER BY created_at DESC LIMIT 10;"
```

### View Logs

```bash
# Agent logs
docker-compose logs -f agent

# Webhook logs
docker-compose logs -f webhook

# Database logs
docker-compose logs -f db
```

## Troubleshooting

### Common Issues

1. **Twilio Webhook Failures**
   - Check webhook URL is publicly accessible
   - Verify SSL certificate is valid
   - Check Twilio webhook logs in console

2. **Database Connection Issues**
   - Ensure PostgreSQL service is running
   - Check DATABASE_URL format
   - Run health check command

3. **LiveKit Connection Problems**
   - Verify API credentials
   - Check LiveKit service status
   - Test with LiveKit playground

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run agent with verbose output
docker-compose exec agent python main.py --debug
```

## API Reference

### Call Manager Commands

```bash
# Start interactive session
python call_manager.py

# Batch calling
python call_manager.py --batch-size 10 --delay 60

# Call specific facilitator
python call_manager.py --phone "+1234567890"

# Dry run (no actual calls)
python call_manager.py --dry-run
```

## Support

For issues and questions:
1. Check logs for error messages
2. Review Twilio webhook logs
3. Test individual components
4. Create GitHub issue with logs

## License

This project is licensed under the MIT License.
