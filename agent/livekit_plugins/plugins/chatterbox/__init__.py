import httpx
import io
import soundfile as sf
import av
from livekit.agents.tts.tts import TTS as BaseTTS, TTSCapabilities
from livekit.agents.tts.tts import ChunkedStream, SynthesizedAudio
from livekit.agents.utils.audio import AudioBuffer

class TTS(BaseTTS):
    def __init__(self, service_url: str, voice_id: str, sample_rate: int = 24000, num_channels: int = 1):
        """
        Local Chatterbox TTS plugin that calls the Chatterbox HTTP service.
        """
        super().__init__(
            capabilities=TTSCapabilities(streaming=False),
            sample_rate=sample_rate,
            num_channels=num_channels,
        )
        self.service_url = service_url.rstrip('/')
        self.voice_id = voice_id

    @property
    def label(self) -> str:
        return f"chatterbox.TTS({self.voice_id})"

    def synthesize(self, text: str, *, conn_options=None):
        service_url = self.service_url
        voice_id = self.voice_id
        sample_rate = self.sample_rate
        num_channels = self.num_channels

        class _ChatterboxStream(ChunkedStream):
            async def _run(inner_self):
                # Call the external TTS service
                url = f"{service_url}/synthesize"
                payload = {"text": text, "voice_id": voice_id}
                async with httpx.AsyncClient() as client:
                    resp = await client.post(url, json=payload)
                    resp.raise_for_status()
                    data = resp.content
                # Decode WAV bytes to PCM audio
                wav_buf = io.BytesIO(data)
                audio, sr = sf.read(wav_buf, dtype='int16')
                # Create an AudioFrame for LiveKit
                frame = av.AudioFrame.from_ndarray(audio, format="s16", layout="mono")
                # Send the synthesized audio as a final frame
                inner_self._event_ch.send_nowait(
                    SynthesizedAudio(frame=frame, request_id="", is_final=True)
                )
        return _ChatterboxStream(tts=self, input_text=text, conn_options=conn_options) 