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
        prompt = conn.config.get("atis").get("end_prompt", None)
        if not prompt:
            prompt = "请你以“时间过得真快”为开头，用富有感情、依依不舍的话来结束这场对话吧。！"

        conn.dialogue.update_system_message(prompt)

        conn.executor.submit(conn.chat)
