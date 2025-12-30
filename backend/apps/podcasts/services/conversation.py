"""
多参与者对话管理器 - 用于Debate和Conference模式
"""
from typing import Dict, List, Optional, Callable, Iterator
from dataclasses import dataclass
from datetime import datetime
from openai import OpenAI
from django.conf import settings


@dataclass
class ParticipantConfig:
    """参与者配置"""
    id: str  # llm1, llm2, judge 或 student1, student2, tutor
    role: str  # 角色名称（如：正方辩手、主持人）
    system_prompt: str  # system prompt
    voice_id: Optional[str] = None  # TTS音色ID（预留）


class ConversationManager:
    """
    多参与者对话管理器

    功能：
    1. 管理3个参与者的独立对话历史
    2. 控制轮次策略（sequential: A→B→C）
    3. 流式生成对话内容
    """

    def __init__(
        self,
        participants: List[ParticipantConfig],
        policy: str = "sequential",
        rounds: int = 3
    ):
        """
        初始化对话管理器

        Args:
            participants: 参与者配置列表（必须3个）
            policy: 轮次策略，目前只支持 "sequential"
            rounds: 对话轮数
        """
        if len(participants) != 3:
            raise ValueError("目前只支持3个参与者")

        self.participants = {p.id: p for p in participants}
        self.policy = policy
        self.rounds = rounds

        # 每个参与者的对话历史
        self.histories: Dict[str, List[Dict[str, str]]] = {
            p.id: [] for p in participants
        }

        # 完整对话记录（用于前端显示和存储）
        self.dialogue_log: List[Dict] = []

        # OpenAI客户端
        api_key = getattr(settings, 'OPENAI_API_KEY', None)
        if not api_key:
            raise ValueError('OPENAI_API_KEY 未配置')

        self.client = OpenAI(
            api_key=api_key,
            base_url=getattr(settings, 'OPENAI_API_BASE', 'https://api.moonshot.cn/v1')
        )
        self.model = getattr(settings, 'OPENAI_MODEL', 'moonshot-v1-8k')

    def generate_dialogue(
        self,
        topic: str,
        on_chunk: Optional[Callable[[str, str], None]] = None
    ) -> Iterator[Dict]:
        """
        生成完整对话

        Args:
            topic: 对话主题（辩题或学习主题）
            on_chunk: 回调函数 on_chunk(participant_id, content_chunk)

        Yields:
            {"participant": "llm1", "content": "...", "timestamp": "..."}
        """
        # 获取参与者顺序（根据participants的顺序）
        participant_order = list(self.participants.keys())

        # 第一轮：judge/tutor开场
        moderator_id = participant_order[2]  # 假设第3个是主持人/导师
        opening = self._generate_opening(moderator_id, topic)

        # 记录并yield开场白
        entry = self._log_message(moderator_id, opening)
        if on_chunk:
            on_chunk(moderator_id, opening)
        yield entry

        # 多轮对话
        for round_num in range(1, self.rounds + 1):
            # 参与者1发言
            response_1 = self._generate_response(
                participant_order[0],
                topic,
                round_num
            )
            entry_1 = self._log_message(participant_order[0], response_1)
            if on_chunk:
                on_chunk(participant_order[0], response_1)
            yield entry_1

            # 参与者2发言
            response_2 = self._generate_response(
                participant_order[1],
                topic,
                round_num
            )
            entry_2 = self._log_message(participant_order[1], response_2)
            if on_chunk:
                on_chunk(participant_order[1], response_2)
            yield entry_2

            # 主持人/导师点评
            if round_num < self.rounds:  # 不是最后一轮
                comment = self._generate_comment(moderator_id, round_num)
            else:  # 最后一轮，总结
                comment = self._generate_summary(moderator_id)

            entry_mod = self._log_message(moderator_id, comment)
            if on_chunk:
                on_chunk(moderator_id, comment)
            yield entry_mod

    def _generate_opening(self, participant_id: str, topic: str) -> str:
        """生成开场白"""
        participant = self.participants[participant_id]

        prompt = f"请为以下主题生成开场白：{topic}\n\n开场白要求：简洁、引人入胜，30-50字。"

        messages = [
            {"role": "system", "content": participant.system_prompt},
            {"role": "user", "content": prompt}
        ]

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.8,
            max_tokens=200
        )

        content = response.choices[0].message.content.strip()

        # 添加到历史
        self.histories[participant_id].append({"role": "assistant", "content": content})

        return content

    def _generate_response(
        self,
        participant_id: str,
        topic: str,
        round_num: int
    ) -> str:
        """生成参与者回复"""
        participant = self.participants[participant_id]

        # 构建上下文：其他参与者最近的发言
        context = self._build_context(participant_id)

        prompt = (
            f"当前正在讨论：{topic}\n"
            f"这是第{round_num}轮发言。\n\n"
            f"其他人的发言：\n{context}\n\n"
            f"请基于你的角色和立场，给出你的观点。长度100-200字。"
        )

        messages = [
            {"role": "system", "content": participant.system_prompt},
            {"role": "user", "content": prompt}
        ]

        # 添加历史记录
        for msg in self.histories[participant_id]:
            messages.insert(-1, msg)  # 插在最后一条user消息前

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.9,
            max_tokens=500
        )

        content = response.choices[0].message.content.strip()

        # 添加到历史
        self.histories[participant_id].append({"role": "user", "content": prompt})
        self.histories[participant_id].append({"role": "assistant", "content": content})

        return content

    def _generate_comment(self, participant_id: str, round_num: int) -> str:
        """生成主持人点评"""
        participant = self.participants[participant_id]

        # 获取刚刚两位参与者的发言
        context = self._build_context(participant_id, recent_only=True)

        prompt = (
            f"这是第{round_num}轮对话。\n\n"
            f"双方发言：\n{context}\n\n"
            f"请作为主持人进行点评和引导。长度80-150字。"
        )

        messages = [
            {"role": "system", "content": participant.system_prompt},
            {"role": "user", "content": prompt}
        ]

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
            max_tokens=400
        )

        content = response.choices[0].message.content.strip()

        # 添加到历史
        self.histories[participant_id].append({"role": "assistant", "content": content})

        return content

    def _generate_summary(self, participant_id: str) -> str:
        """生成总结"""
        participant = self.participants[participant_id]

        # 获取完整对话摘要
        full_context = "\n\n".join([
            f"{entry['participant']}: {entry['content'][:100]}..."
            for entry in self.dialogue_log[-6:]  # 最近6条
        ])

        prompt = (
            f"对话即将结束，请对整场讨论进行总结。\n\n"
            f"最近的对话：\n{full_context}\n\n"
            f"总结要求：概括双方观点，给出中立的结论。长度150-250字。"
        )

        messages = [
            {"role": "system", "content": participant.system_prompt},
            {"role": "user", "content": prompt}
        ]

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.6,
            max_tokens=600
        )

        content = response.choices[0].message.content.strip()

        # 添加到历史
        self.histories[participant_id].append({"role": "assistant", "content": content})

        return content

    def _build_context(
        self,
        exclude_participant: str,
        recent_only: bool = False
    ) -> str:
        """构建其他参与者的发言上下文"""
        context_parts = []

        # 获取其他参与者
        other_participants = [
            pid for pid in self.participants.keys()
            if pid != exclude_participant
        ]

        if recent_only:
            # 只取最近一轮的发言
            relevant_entries = self.dialogue_log[-2:]
        else:
            # 取所有发言
            relevant_entries = self.dialogue_log

        for entry in relevant_entries:
            if entry['participant'] in other_participants:
                participant_role = self.participants[entry['participant']].role
                context_parts.append(f"{participant_role}: {entry['content']}")

        return "\n\n".join(context_parts)

    def _log_message(self, participant_id: str, content: str) -> Dict:
        """记录消息到对话日志"""
        entry = {
            "participant": participant_id,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        self.dialogue_log.append(entry)
        return entry

    def get_dialogue_log(self) -> List[Dict]:
        """获取完整对话记录"""
        return self.dialogue_log
