"""
ElevenLabs TTS Provider for Sisters-AWS-Coach
"""

import os
import requests
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class ElevenLabsTTS:
    """ElevenLabs Text-to-Speech provider"""

    def __init__(self):
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        self.model = os.getenv("ELEVENLABS_MODEL", "eleven_multilingual_v2")

        # Voice IDs for each character
        self.voice_ids = {
            "Botan": os.getenv("ELEVENLABS_VOICE_ID_BOTAN", "emSmWzY0c0xtx5IFMCVv"),
            "Kasho": os.getenv("ELEVENLABS_VOICE_ID_KASHO", "XrExE9yKIg1WjnnlVkGX"),
            "Yuri": os.getenv("ELEVENLABS_VOICE_ID_YURI", "Pt5YrLNyu6d2s3s4CVMg"),
            "Ojisan": os.getenv("ELEVENLABS_VOICE_ID_USER", "scOwDtmlUjD3prqpp97I"),
        }

        # Voice settings
        self.stability = float(os.getenv("ELEVENLABS_STABILITY", "0.5"))
        self.similarity = float(os.getenv("ELEVENLABS_SIMILARITY", "0.75"))
        self.style = float(os.getenv("ELEVENLABS_STYLE", "0.75"))

    def generate_speech(
        self,
        text: str,
        voice_id: Optional[str] = None,
        character: str = "Yuri",
        output_path: Optional[str] = None
    ) -> Optional[bytes]:
        """
        Generate speech from text using ElevenLabs API

        Args:
            text: Text to convert to speech
            voice_id: Direct voice ID (takes priority)
            character: Character name for voice selection (fallback)
            output_path: Optional path to save audio file

        Returns:
            Audio bytes or None if failed
        """
        if not self.api_key:
            print("ElevenLabs API key not configured")
            return None

        # Use voice_id if provided, otherwise look up by character
        if not voice_id:
            voice_id = self.voice_ids.get(character, self.voice_ids["Yuri"])

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.api_key
        }

        data = {
            "text": text,
            "model_id": self.model,
            "voice_settings": {
                "stability": self.stability,
                "similarity_boost": self.similarity,
                "style": self.style,
                "use_speaker_boost": True
            }
        }

        try:
            response = requests.post(url, json=data, headers=headers, timeout=30)

            if response.status_code == 200:
                audio_bytes = response.content

                if output_path:
                    with open(output_path, 'wb') as f:
                        f.write(audio_bytes)

                return audio_bytes
            else:
                print(f"ElevenLabs API error: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            print(f"TTS error: {e}")
            return None

    def get_available_voices(self) -> dict:
        """Get available voice IDs for each character"""
        return self.voice_ids.copy()
