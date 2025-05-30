from fastapi import FastAPI, UploadFile, File, Response
from pydantic import BaseModel
from chatterbox.tts import ChatterboxTTS
from typing import Optional
import uuid
import os
import soundfile as sf
import io
import numpy as np
import torch

app = FastAPI()
# Directory to store uploaded voice prompts
os.makedirs("voices", exist_ok=True)
# Determine device: allow override via DEVICE env var, else auto-select GPU if available
device_env = os.getenv("DEVICE")
if device_env:
    device = device_env
else:
    device = "cuda" if torch.cuda.is_available() else "cpu"
# If loading on CPU, ensure checkpoints map to CPU
if device == "cpu":
    _orig_torch_load = torch.load
    def _load_cpu(location, *args, **kwargs):
        return _orig_torch_load(location, *args, map_location=torch.device('cpu'), **kwargs)
    torch.load = _load_cpu
# Initialize the Chatterbox TTS model on the selected device
tts_model = ChatterboxTTS.from_pretrained(device=device)
# Default voice prompt path (if provided, this will be used for all syntheses)
DEFAULT_VOICE_PROMPT = os.getenv("DEFAULT_VOICE_PROMPT_PATH")

class UploadResponse(BaseModel):
    voice_id: str

class SynthesizeRequest(BaseModel):
    text: str
    voice_id: Optional[str] = None

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
    # Determine which voice prompt to use
    if DEFAULT_VOICE_PROMPT:
        voice_file = DEFAULT_VOICE_PROMPT
    else:
        if not req.voice_id:
            return {"error": "voice_id required"}
        files = os.listdir("voices")
        matched = [f for f in files if f.startswith(req.voice_id)]
        if not matched:
            return {"error": "voice not found"}
        voice_file = f"voices/{matched[0]}"
    # Generate speech using ChatterboxTTS
    wav = tts_model.generate(req.text, audio_prompt_path=voice_file)
    audio_np = wav.cpu().numpy()
    # Ensure shape is (frames, channels)
    if audio_np.ndim > 1:
        audio_array = audio_np.T
    else:
        audio_array = audio_np
    sr = tts_model.sr
    # Encode to WAV
    buf = io.BytesIO()
    sf.write(buf, audio_array, sr, format="WAV")
    buf.seek(0)
    return Response(content=buf.read(), media_type="audio/wav") 