from core.providers.tts.dto.dto import ContentType
from core.handle.utilsHandle import update_config

TAG = __name__

async def handleAtisMessage(conn, msg_json):
    """处理Atis消息"""
    msg_type = "atis_update_config"
    state = msg_json.get("state")

    if state == "chat":
        await update_config(conn, msg_type, msg_json)
        conn.executor.submit(conn.chat)
    elif state == "tts":
        await update_config(conn, msg_type, msg_json)
        conn.client_abort = False
        conn.tts.tts_one_sentence(conn, ContentType.TEXT, content_detail=msg_json.get("text"))
    elif state == "chat_end":
        # server 发送总结消息. 发送后关闭连接
        conn.close_after_chat = True
        conn.client_abort = False
        end_prompt = conn.config.get("end_prompt", {})
        if end_prompt and end_prompt.get("enable", True) is False:
            conn.logger.bind(tag=TAG).info("结束对话，无需发送结束提示语")
            await conn.close()
            return
        prompt = end_prompt.get("prompt")
        if not prompt:
            prompt = "请你以```时间过得真快```未来头，用富有感情、依依不舍的话来结束这场对话吧。！"

        conn.dialogue.update_system_message(prompt)

        conn.executor.submit(conn.chat)
