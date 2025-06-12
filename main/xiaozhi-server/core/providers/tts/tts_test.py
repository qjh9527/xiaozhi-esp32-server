from core.providers.tts.base import TTSProviderBase
from config.logger import setup_logging

TAG = __name__
logger = setup_logging()


class TTSProvider(TTSProviderBase):
    def __init__(self, config, delete_audio_file):
        super().__init__(config, delete_audio_file)

    async def text_to_speak(self, text, output_file):
        try:
            pass
            with open(r".\config\assets\bind_code\0.wav", "rb") as f:
                return f.read()
        except Exception as e:
            raise Exception(f"{__name__} error: {e}")
