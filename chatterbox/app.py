from fastapi import FastAPI, UploadFile, File, Response
from pydantic import BaseModel
from transformers import pipeline
import uuid
import os
import soundfile as sf
import io

app = FastAPI()
# Directory to store uploaded voice prompts
os.makedirs("voices", exist_ok=True)
# Initialize the Chatterbox TTS pipeline
tts_model = pipeline("text-to-speech", model="ResembleAI/Chatterbox", trust_remote_code=True)

class UploadResponse(BaseModel):
    voice_id: str

class SynthesizeRequest(BaseModel):
    text: str
    voice_id: str

@app.post("/upload", response_model=UploadResponse)
async def upload_voice(file: UploadFile = File(...)):
    # Save uploaded voice prompt and return an ID
    ext = os.path.splitext(file.filename)[1]
    voice_id = str(uuid.uuid4())
    path = f"voices/{voice_id}{ext}"
    content = await file.read()
    with open(path, "wb") as f:
        f.write(content)
    return {"voice_id": voice_id}

@app.post("/synthesize")
async def synthesize(req: SynthesizeRequest):
    # Lookup the prompt file by ID
    files = os.listdir("voices")
    matched = [f for f in files if f.startswith(req.voice_id)]
    if not matched:
        return {"error": "voice not found"}
    voice_file = f"voices/{matched[0]}"
    # Generate speech
    result = tts_model(req.text, voice_prompt=voice_file)
    audio_array = result["wav"]
    sr = result.get("sample_rate", 24000)
    # Encode to WAV
    buf = io.BytesIO()
    sf.write(buf, audio_array, sr, format="WAV")
    buf.seek(0)
    return Response(content=buf.read(), media_type="audio/wav") 