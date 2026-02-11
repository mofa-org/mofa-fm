"""
发言策略 - 基于 mofa-studio 的 UnifiedRatioPolicy
用于决定下一个发言人
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
import random


@dataclass
class Participant:
    """参与者"""
    id: str
    role: str
    system_prompt: str
    voice_id: str = ""
    word_count: int = 0


@dataclass
class PolicyStats:
    """策略统计"""
    total_words: int = 0
    participant_stats: Dict[str, Dict] = field(default_factory=dict)
    current_round: int = 0


class UnifiedRatioPolicy:
    """
    统一比例策略 - 根据字数比例决定下一发言人

    逻辑：
    - 计算每个参与者的字数比例
    - 选择比例最低的参与者作为下一发言人
    - 支持优先级（如 tutor 在 conference 模式优先）
    """

    def __init__(self, participants: List[Participant] = None):
        self.participants = participants or []
        self.last_speaker: Optional[str] = None
        self.current_round = 0
        self._participant_map: Dict[str, Participant] = {}
        self._priority_participant: Optional[str] = None

        if participants:
            self._build_map()

    def _build_map(self):
        """构建参与者映射"""
        self._participant_map = {p.id: p for p in self.participants}
        # 检测优先级参与者（tutor/judge）
        for p in self.participants:
            if "tutor" in p.id.lower() or "judge" in p.id.lower():
                self._priority_participant = p.id
                break

    def configure(self, mode: str = "debate") -> "UnifiedRatioPolicy":
        """
        根据模式配置策略

        Args:
            mode: 'debate' 或 'conference'
        """
        if mode == "conference":
            # Conference 模式：tutor 优先
            self._priority_participant = next(
                (p.id for p in self.participants if "tutor" in p.id.lower()),
                None
            )
        else:
            # Debate 模式：无优先，纯比例
            self._priority_participant = None
        return self

    def update_word_count(self, participant_id: str, word_count: int):
        """更新参与者字数统计"""
        if participant_id in self._participant_map:
            self._participant_map[participant_id].word_count += word_count

    def determine_next_speaker(self) -> Optional[str]:
        """
        决定下一发言人

        Returns:
            下一发言人的 ID
        """
        if not self.participants:
            return None

        # 如果是第一轮且设置了优先级参与者，让优先级参与者先发言
        if self.current_round == 0 and self._priority_participant:
            return self._priority_participant

        # 计算总字数
        total_words = sum(p.word_count for p in self.participants)
        if total_words == 0:
            # 冷启动：选择第一个非优先级参与者（让其他人先发言）
            for p in self.participants:
                if p.id != self._priority_participant:
                    return p.id
            return self.participants[0].id

        # 计算每个参与者的字数比例
        ratios = []
        for p in self.participants:
            ratio = p.word_count / total_words if total_words > 0 else 0
            ratios.append((p.id, ratio, p.word_count))

        # 选择比例最低的参与者
        ratios.sort(key=lambda x: (x[1], x[2]))
        next_speaker = ratios[0][0]

        self.last_speaker = next_speaker
        return next_speaker

    def increment_round(self):
        """增加轮次计数"""
        self.current_round += 1

    def get_stats(self) -> PolicyStats:
        """获取策略统计"""
        total = sum(p.word_count for p in self.participants)
        stats = {
            p.id: {
                "role": p.role,
                "word_count": p.word_count,
                "ratio": p.word_count / total if total > 0 else 0
            }
            for p in self.participants
        }
        return PolicyStats(
            total_words=total,
            participant_stats=stats,
            current_round=self.current_round
        )

    def reset_counts(self):
        """重置字数统计"""
        for p in self.participants:
            p.word_count = 0
        self.current_round = 0
        self.last_speaker = None

    def set_last_speaker(self, speaker_id: Optional[str]):
        """设置最后发言人（用于 human 打断后重置）"""
        self.last_speaker = speaker_id
