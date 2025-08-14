import uuid
import re
from typing import List, Dict
from datetime import datetime


class Message:
    def __init__(
        self,
        role: str,
        content: str = None,
        uniq_id: str = None,
        tool_calls=None,
        tool_call_id=None,
    ):
        self.uniq_id = uniq_id if uniq_id is not None else str(uuid.uuid4())
        self.role = role
        self.content = content
        self.tool_calls = tool_calls
        self.tool_call_id = tool_call_id

class Dialogue:
    def __init__(self):
        self.dialogue: List[Message] = []
        # 获取当前时间
        self.current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def put(self, message: Message):
        self.dialogue.append(message)

    def getMessages(self, m, dialogue):
        if m.tool_calls is not None:
            dialogue.append({"role": m.role, "tool_calls": m.tool_calls})
        elif m.role == "tool":
            dialogue.append(
                {
                    "role": m.role,
                    "tool_call_id": (
                        str(uuid.uuid4()) if m.tool_call_id is None else m.tool_call_id
                    ),
                    "content": m.content,
                }
            )
        else:
            dialogue.append({"role": m.role, "content": m.content})

    def get_llm_dialogue(self) -> List[Dict[str, str]]:
        # 直接调用get_llm_dialogue_with_memory，传入None作为memory_str
        # 这样确保说话人功能在所有调用路径下都生效
        return self.get_llm_dialogue_with_memory(None, None)

    def update_system_message(self, new_content: str):
        """更新或添加系统消息"""
        # 查找第一个系统消息
        system_msg = next((msg for msg in self.dialogue if msg.role == "system"), None)
        if system_msg:
            system_msg.content = new_content
        else:
            self.put(Message(role="system", content=new_content))

    def add_system_message(self, new_content: str):
        """添加系统消息"""
        self.put(Message(role="system", content=new_content))

    def get_llm_dialogue_with_memory(
            self, memory_str: str = None, voiceprint_config: dict = None
    ) -> List[Dict[str, str]]:
        dialogue: List[Dict[str, str]] = []
        first_system_processed = False  # 标记是否已处理过第一条 system

        for msg in self.dialogue:
            if msg.role == "system":
                content = msg.content
                if not first_system_processed:  # 仅增强第一条
                    first_system_processed = True
                    # 时间占位符
                    content = content.replace(
                        "{{current_time}}", datetime.now().strftime("%H:%M")
                    )

                    # 说话人信息
                    try:
                        speakers = (voiceprint_config or {}).get("speakers", [])
                        if speakers:
                            speaker_lines = ["<speakers_info>"]
                            for s in speakers:
                                try:
                                    parts = s.split(",", 2)
                                    if len(parts) >= 2:
                                        name = parts[1].strip()
                                        desc = parts[2].strip() if len(parts) >= 3 else ""
                                        speaker_lines.append(f"- {name}：{desc}")
                                except Exception:
                                    continue
                            speaker_lines.append("</speakers_info>")
                            content += "\n\n" + "\n".join(speaker_lines)
                    except Exception:
                        pass

                    # memory 替换
                    if memory_str is not None:
                        content = re.sub(
                            r"<memory>.*?</memory>",
                            f"<memory>\n{memory_str}\n</memory>",
                            content,
                            flags=re.DOTALL,
                        )

                dialogue.append({"role": "system", "content": content})
            else:
                # 非 system 消息，原样追加
                self.getMessages(msg, dialogue)

        return dialogue
