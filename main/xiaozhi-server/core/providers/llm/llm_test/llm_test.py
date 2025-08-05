from config.logger import setup_logging
from core.providers.llm.base import LLMProviderBase

TAG = __name__
logger = setup_logging()


class LLMProvider(LLMProviderBase):
    def __init__(self, config):
        pass

    def response(self, session_id, dialogue, **kwargs):
        try:
            for chunk in ["llm1", "-llm2"]:
                yield chunk

        except Exception as e:
            logger.bind(tag=TAG).error(f"Error in response generation: {e}")

    def response_with_functions(self, session_id, dialogue, functions=None):
        try:
            for chunk in ["llm1", "-llm2"]:
                yield {"content": chunk}, None
        except Exception as e:
            logger.bind(tag=TAG).error(f"Error in function call streaming: {e}")
            yield f"【{TAG}服务响应异常: {e}】", None
