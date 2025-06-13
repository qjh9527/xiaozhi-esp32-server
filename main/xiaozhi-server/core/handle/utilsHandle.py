import json

TAG = __name__

async def update_config(conn, msg_type, *args, **kwargs):
    try:
        # 更新WebSocketServer的配置
        if not conn.server:
            await conn.websocket.send(
                json.dumps(
                    {
                        "type": msg_type,
                        "status": "error",
                        "message": "无法获取服务器实例",
                        "content": {"action": "update_config"},
                    }
                )
            )
            return

        if msg_type == "server":
            success = await conn.server.update_config()
        elif msg_type == "atis_update_config":
            success = await conn.server.update_config_from_client(conn, *args, **kwargs)
        else:
            success = False

        if not success:
            await conn.websocket.send(
                json.dumps(
                    {
                        "type": msg_type,
                        "status": "error",
                        "message": "更新服务器配置失败",
                        "content": {"action": "update_config"},
                    }
                )
            )
            return

        # 发送成功响应
        await conn.websocket.send(
            json.dumps(
                {
                    "type": msg_type,
                    "status": "success",
                    "message": "配置更新成功",
                    "content": {"action": "update_config"},
                }
            )
        )
    except Exception as e:
        conn.logger.bind(tag=TAG).error(f"更新配置失败: {str(e)}")
        await conn.websocket.send(
            json.dumps(
                {
                    "type": msg_type,
                    "status": "error",
                    "message": f"更新配置失败: {str(e)}",
                    "content": {"action": "update_config"},
                }
            )
        )

async def send_error_message(conn, module, msg_type, message):
    """发送错误消息"""
    try:
        error_message = {
            "type": "error",
            "error_module": module,
            "error_type": msg_type,
            "error_message": message,
        }
        await conn.websocket.send(json.dumps(error_message))
    except Exception as e:
        conn.logger.bind(tag=TAG).error(f"发送错误消息失败: {str(e)}")