import uuid
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


ASD_prompt = """## 角色设定
您是一名经验丰富的自闭症儿童干预医生（{0}身份），遵循应用行为分析（ABA）原则为儿童提供有效支持。您的目标是帮助他们在主题对话中提高沟通与社交能力。
## 遵循原则
1. 请在交流中应用ABA原则，结合回合制教学原则（DTT）和情景教学原则（NET），在对话中注意以下三个要素：指令、辅助、强化
指令 - 清晰简单地提供指示，引导儿童围绕主题展开对话
辅助 - 在儿童需要帮助时，提供适度的言语支持，以促进正确的回应
强化 - 及时给予积极的反馈和表扬，以鼓励正确和积极的行为
2. 当儿童正确反应时，应该给予强化；当儿童无响应时，应当给予其恰当的辅助，促进其正确回应；当儿童错误反应时，不强化其错误反应，重发指令或给予其适当的辅助，促进其正确回应
3. 请保持温暖亲切的语气，充分表现出共情，对儿童的回应给予肯定和表扬。确保对话自然简洁，以便儿童能轻松理解。
4. 需耐心主动维持话题，除非另有要求，不要主动结束对话。
## 开始对话
现在，您将与一名自闭症儿童进行主题对话，{1} 请围绕此主题开始对话"""

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
        dialogue = []
        for m in self.dialogue:
            self.getMessages(m, dialogue)
        return dialogue

    def update_system_message(self, new_content: str):
        """更新或添加系统消息"""
        # 查找第一个系统消息
        system_msg = next((msg for msg in self.dialogue if msg.role == "system"), None)
        if system_msg:
            system_msg.content = new_content
        else:
            self.put(Message(role="system", content=new_content))

    def get_llm_dialogue_with_memory(
        self, memory_str: str = None
    ) -> List[Dict[str, str]]:
        if memory_str is None or len(memory_str) == 0:
            return self.get_llm_dialogue()

        # 构建带记忆的对话
        dialogue = []

        # 添加系统提示和记忆
        system_message = next(
            (msg for msg in self.dialogue if msg.role == "system"), None
        )

        if system_message:
            enhanced_system_prompt = (
                f"{system_message.content}\n\n"
                f"以下是用户的历史记忆：\n```\n{memory_str}\n```"
            )
            dialogue.append({"role": "system", "content": enhanced_system_prompt})

        # 添加用户和助手的对话
        for m in self.dialogue:
            if m.role != "system":  # 跳过原始的系统消息
                self.getMessages(m, dialogue)

        return dialogue
