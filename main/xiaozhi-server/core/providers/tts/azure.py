import os
import uuid
from datetime import datetime
from core.utils.util import check_model_key
from core.providers.tts.base import TTSProviderBase
from config.logger import setup_logging
import azure.cognitiveservices.speech as speechsdk

TAG = __name__
logger = setup_logging()


class TTSProvider(TTSProviderBase):
    def __init__(self, config, delete_audio_file):
        super().__init__(config, delete_audio_file)

        self.subscription = config.get("subscription")
        self.region = config.get("region", "eastasia")
        self.language = config.get("language", "zh-CN")
        self.voiceName = config.get("voiceName", "zh-CN-XiaoshuangNeural")
        self.style = config.get("style", "chat")
        self.role = config.get("role", "Girl")
        self.styleDegree = config.get("styleDegree", 2)

        # 处理空字符串的情况
        rate = config.get("rate", "1.0")

        self.rate = float(rate) if rate else 1.0

        check_model_key("TTS", self.subscription)

    async def text_to_speak(self, text, output_file):
        try:
            speech_config = speechsdk.SpeechConfig(subscription=self.subscription,
                                                   region=self.region,
                                                   speech_recognition_language=self.language)

            speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)

            ssml = f"""<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis'
            xmlns:mstts='https://www.w3.org/2001/mstts' xml:lang='{self.language}'>
            <voice name='{self.voiceName}'>
                <mstts:express-as style='{self.style}' styledegree='{self.styleDegree}' role='{self.role}'>
                    <prosody rate='{self.rate}'>
                        {text}
                    </prosody>
                </mstts:express-as>
            </voice>
        </speak>"""

            speech_synthesis_result = speech_synthesizer.speak_ssml_async(ssml).get()

            if speech_synthesis_result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                stream = speechsdk.AudioDataStream(speech_synthesis_result)
                stream.save_to_wav_file(output_file)
            elif speech_synthesis_result.reason == speechsdk.ResultReason.Canceled:
                resp = speech_synthesis_result.cancellation_details
                print("Speech synthesis canceled: {}".format(resp.reason))
                if resp.reason == speechsdk.CancellationReason.Error:
                    if resp.error_details:
                        raise Exception(
                            f"{__name__} status_code: {resp.status_code} response: {resp.content}"
                        )
        except Exception as e:
            raise Exception(f"{__name__} error: {e}")
