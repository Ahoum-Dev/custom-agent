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
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("chatterbox")

# Default voice prompt path (if provided, this will be used for all syntheses)
DEFAULT_VOICE_PROMPT = os.getenv("DEFAULT_VOICE_PROMPT_PATH")
USE_CUSTOM_VOICE_PROMPT = os.getenv("USE_CUSTOM_VOICE_PROMPT", "true").lower() in ("1", "true", "yes")

app = FastAPI()
# Directory to store uploaded voice prompts
os.makedirs("voices", exist_ok=True)
# Determine device: allow override via DEVICE env var, else auto-select CUDA, MPS, or CPU
device_env = os.getenv("DEVICE")
if device_env:
    device = device_env
else:
    if torch.cuda.is_available():
        device = "cuda"
    elif torch.backends.mps.is_available():
        device = "mps"
    else:
        device = "cpu"
# Patch torch.load to map to the selected device
map_location = torch.device(device)
_orig_torch_load = torch.load
def _patched_torch_load(*args, **kwargs):
    if 'map_location' not in kwargs:
        kwargs['map_location'] = map_location
    return _orig_torch_load(*args, **kwargs)
torch.load = _patched_torch_load

@app.on_event("startup")
async def startup_event():
    logger.info("Chatterbox TTS service starting up")
    logger.info(f"Using device: {device}")
    logger.info(f"Default voice prompt: {DEFAULT_VOICE_PROMPT}")
    logger.info(f"Use custom voice prompt: {USE_CUSTOM_VOICE_PROMPT}")

# Initialize the Chatterbox TTS model on the selected device
tts_model = ChatterboxTTS.from_pretrained(device=device)
logger.info(f"Loaded ChatterboxTTS model on device: {device}")

class UploadResponse(BaseModel):
    voice_id: str

class SynthesizeRequest(BaseModel):
    text: str
    voice_id: Optional[str] = None
    # Optional path to a specific audio prompt file
    audio_prompt_path: Optional[str] = None
    # Speech exaggeration factor
    exaggeration: Optional[float] = 1.0
    # CFG scaling weight
    cfg_weight: Optional[float] = 1.0

@app.post("/upload", response_model=UploadResponse)
async def upload_voice(file: UploadFile = File(...)):
    # Save uploaded voice prompt and return an ID
    ext = os.path.splitext(file.filename)[1]
    voice_id = str(uuid.uuid4())
    path = f"voices/{voice_id}{ext}"
    content = await file.read()
    with open(path, "wb") as f:
        f.write(content)
    logger.info(f"Uploaded voice prompt with ID {voice_id}, saved to {path}")
    return {"voice_id": voice_id}

@app.post("/synthesize")
async def synthesize(req: SynthesizeRequest):
    # Comment out file input logic - use no voice prompt for now
    # if not USE_CUSTOM_VOICE_PROMPT:
    #     # Use default voice prompt only
    #     if not DEFAULT_VOICE_PROMPT:
    #         return {"error": "Default voice prompt not configured"}
    #     voice_file = DEFAULT_VOICE_PROMPT
    # else:
    #     # Use custom voice prompt if provided, else fallback to default
    #     if req.audio_prompt_path:
    #         voice_file = req.audio_prompt_path
    #     elif DEFAULT_VOICE_PROMPT:
    #         voice_file = DEFAULT_VOICE_PROMPT
    #     else:
    #         if not req.voice_id:
    #             return {"error": "voice_id required"}
    #         files = os.listdir("voices")
    #         matched = [f for f in files if f.startswith(req.voice_id)]
    #         if not matched:
    #             return {"error": "voice not found"}
    #         voice_file = f"voices/{matched[0]}"
    logger.info(
        f"Received synthesize request: text='{req.text[:30]}...', "
        f"exaggeration={req.exaggeration}, cfg_weight={req.cfg_weight}"
    )
    # Generate speech using ChatterboxTTS without voice prompt
    wav = tts_model.generate(
        req.text,
        exaggeration=req.exaggeration,
        cfg_weight=req.cfg_weight,
    )
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