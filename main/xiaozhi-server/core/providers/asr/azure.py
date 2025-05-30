import time
import os
import uuid
from typing import Optional, Tuple, List
import wave

import requests
from core.providers.asr.base import ASRProviderBase
from config.logger import setup_logging

TAG = __name__
logger = setup_logging()


class ASRProvider(ASRProviderBase):
    def __init__(self, config: dict, delete_audio_file: bool = True):
        super().__init__()
        self.subscription = config.get("subscription")
        self.region = config.get("region", "eastasia")
        self.language = config.get("language", "zh-CN")

        self.output_dir = config.get("output_dir")
        self.delete_audio_file = delete_audio_file

        self.API_URL = (f"https://{self.region}.stt.speech.microsoft.com/speech/"
                        f"recognition/conversation/cognitiveservices/v1?language={self.language}")

        # 确保输出目录存在
        os.makedirs(self.output_dir, exist_ok=True)

    def save_audio_to_file(self, pcm_data: List[bytes], session_id: str) -> str:
        """PCM数据保存为WAV文件"""
        module_name = __name__.split(".")[-1]
        file_name = f"asr_{module_name}_{session_id}_{uuid.uuid4()}.wav"
        file_path = os.path.join(self.output_dir, file_name)

        with wave.open(file_path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # 2 bytes = 16-bit
            wf.setframerate(16000)
            wf.writeframes(b"".join(pcm_data))

        return file_path

    def _send_request(self, request_body: bytes) -> Optional[str]:
        """发送请求到云API"""
        headers = {
            "Content-Type": "audio/wav; codecs=audio/pcm; samplerate=16000",
            "Ocp-Apim-Subscription-Key": self.subscription,
        }

        try:
            response = requests.post(self.API_URL, headers=headers, data=request_body)

            if not response.ok:
                raise IOError(f"请求失败: {response.status_code} {response.reason}")

            response_json = response.json()

            # 检查是否有错误
            if response_json["RecognitionStatus"] == "Success":
                # 提取识别结果
                if "DisplayText" in response_json:
                    return response_json["DisplayText"]
                else:
                    logger.bind(tag=TAG).warning(f"响应中没有识别结果: {response_json}")
                    return ""
            else:
                error = response_json["Response"]["Error"]
                error_code = error["Code"]
                error_message = error["Message"]
                raise IOError(f"API返回错误: {error_code}: {error_message}")

        except Exception as e:
            logger.bind(tag=TAG).error(f"发送请求失败: {e}", exc_info=True)
            return None

    async def speech_to_text(
        self, opus_data: List[bytes], session_id: str
    ) -> Tuple[Optional[str], Optional[str]]:
        """将语音数据转换为文本"""
        if not opus_data:
            logger.bind(tag=TAG).warning("音频数据为空！")
            return None, None

        file_path = None
        try:
            # 将Opus音频数据解码为PCM
            if self.audio_format == "pcm":
                pcm_data = opus_data
            else:
                pcm_data = self.decode_opus(opus_data)
            combined_pcm_data = b"".join(pcm_data)

            # 判断是否保存为WAV文件
            if self.delete_audio_file:
                pass
            else:
                self.save_audio_to_file(pcm_data, session_id)

            # 发送请求
            start_time = time.time()
            result = self._send_request(combined_pcm_data)

            if result:
                logger.bind(tag=TAG).debug(
                    f"{__name__}语音识别耗时: {time.time() - start_time:.3f}s | 结果: {result}"
                )

            return result, file_path
        except Exception as e:
            logger.bind(tag=TAG).error(f"处理音频时发生错误！{e}", exc_info=True)
            return None, file_path
