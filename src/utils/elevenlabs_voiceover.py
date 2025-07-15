"""ElevenLabs voiceover service for manim_voiceover."""
import os
from pathlib import Path
from manim_voiceover.services.base import SpeechService
from elevenlabs.client import ElevenLabs


class ElevenLabsService(SpeechService):
    """Speech service using the ElevenLabs API."""

    def __init__(self,
                 api_key: str = None,
                 voice_id: str = None,
                 model_id: str = None,
                 **kwargs):
        self.api_key = api_key or os.getenv("ELEVEN_API_KEY")
        self.voice_id = voice_id or os.getenv("ELEVEN_VOICE_ID", "")
        self.model_id = model_id or os.getenv("ELEVEN_MODEL_ID", "eleven_monolingual_v1")
        self.client = ElevenLabs(api_key=self.api_key)
        super().__init__(**kwargs)

    def generate_from_text(self, text: str, cache_dir: str = None, path: str = None) -> dict:
        if cache_dir is None:
            cache_dir = self.cache_dir
        input_data = {
            "input_text": text,
            "service": "elevenlabs",
            "voice": self.voice_id,
            "model": self.model_id,
        }
        cached_result = self.get_cached_result(input_data, cache_dir)
        if cached_result is not None:
            return cached_result
        if path is None:
            filename = self.get_audio_basename(input_data) + ".mp3"
        else:
            filename = path
        out_path = Path(cache_dir) / filename
        os.makedirs(Path(cache_dir), exist_ok=True)
        audio_iter = self.client.text_to_speech.convert(
            voice_id=self.voice_id,
            text=text,
            model_id=self.model_id,
            output_format="mp3_44100_128",
        )
        with open(out_path, "wb") as f:
            for chunk in audio_iter:
                f.write(chunk)
        json_dict = {
            "input_text": text,
            "input_data": input_data,
            "original_audio": filename,
        }
        return json_dict
