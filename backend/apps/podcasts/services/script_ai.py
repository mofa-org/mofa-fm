"""
AI 脚本生成服务 - 基于 Moonshot (Kimi) API
"""
from typing import Dict, List, Optional

from django.conf import settings
from openai import OpenAI


class ScriptAIService:
    """封装与 Kimi Chat Completion 的交互逻辑"""

    def __init__(self):
        api_key = getattr(settings, 'KIMI_API_KEY', None)
        if not api_key:
            raise ValueError('KIMI_API_KEY 未配置，请在环境变量或 .env 中设置')

        self.client = OpenAI(
            api_key=api_key,
            base_url=getattr(settings, 'KIMI_BASE_URL', 'https://api.moonshot.cn/v1')
        )
        self.model = getattr(settings, 'KIMI_MODEL', 'moonshot-v1-8k')

    def chat(
        self,
        messages: List[Dict[str, str]],
        reference_texts: Optional[List[str]] = None,
        current_script: Optional[str] = None
    ) -> Dict[str, Optional[str]]:
        """
        与 Kimi 对话，生成或修改脚本。
        返回 {
            success: bool,
            response: str,
            script: str | None,
            error: str | None
        }
        """
        try:
            system_prompt = self._build_system_prompt(reference_texts, current_script)
            full_messages = [{'role': 'system', 'content': system_prompt}] + messages

            completion = self.client.chat.completions.create(
                model=self.model,
                messages=full_messages,
                temperature=0.7,
                max_tokens=2800,
            )

            response_text = completion.choices[0].message.content
            extracted_script = self._extract_script(response_text)

            return {
                'success': True,
                'response': response_text,
                'script': extracted_script if extracted_script else current_script,
                'error': None
            }
        except Exception as exc:  # pylint: disable=broad-except
            return {
                'success': False,
                'response': None,
                'script': current_script,
                'error': f'AI调用失败: {exc}'
            }

    def generate_initial_script(
        self,
        topic: str,
        duration_minutes: int = 5,
        num_characters: int = 2,
        style: str = '轻松对话'
    ) -> Dict[str, Optional[str]]:
        """用于快速生成初稿脚本"""
        prompt = (
            f"请根据以下要求撰写一份播客脚本：\n"
            f"- 主题：{topic}\n"
            f"- 预计时长：{duration_minutes} 分钟\n"
            f"- 角色数量：{num_characters}\n"
            f"- 风格：{style}\n"
            "输出完整脚本，并使用 ```markdown 包裹。"
        )
        return self.chat(
            messages=[{'role': 'user', 'content': prompt}],
            reference_texts=None,
            current_script=None
        )

    # --------------------------------------------------------------------- #
    # 内部工具
    # --------------------------------------------------------------------- #
    def _build_system_prompt(
        self,
        reference_texts: Optional[List[str]],
        current_script: Optional[str]
    ) -> str:
        base_prompt = (
            "你是一个专业的播客脚本编剧助手，需要帮助用户创作高质量的播客脚本。\n\n"
            "## 脚本格式要求\n"
            "1. 使用【大牛】和【一帆】作为固定的两个角色名（主持人用【大牛】，嘉宾用【一帆】）\n"
            "2. 每个角色说话一段，用空行分隔\n"
            "3. 可以在开头使用 # 标题\n"
            "4. **重要：直接输出纯净的 Markdown 文本，不要用 ```markdown 代码块包裹**\n\n"
            "## 内容要求\n"
            "1. 对话自然流畅，符合播客节目的口语化风格\n"
            "2. 【大牛】作为主持人，负责引导话题、提问和总结\n"
            "3. 【一帆】作为嘉宾，负责分享观点、回答问题\n"
            "4. 每段对话长度适中，避免过长的独白\n"
            "5. 如在修改现有脚本，请给出更新后的完整版本\n\n"
            "## 输出示例\n"
            "# 播客标题\n\n"
            "【大牛】大家好，欢迎来到今天的节目。\n\n"
            "【一帆】大家好，很高兴来到这里。\n\n"
            "【大牛】今天我们聊聊...\n"
        )

        if reference_texts:
            base_prompt += "\n## 参考资料（节选）\n"
            for idx, text in enumerate(reference_texts, start=1):
                snippet = text[:1000] + ('...' if len(text) > 1000 else '')
                base_prompt += f"\n### 资料 {idx}\n{snippet}\n"

        if current_script:
            base_prompt += f"\n## 当前脚本\n```markdown\n{current_script}\n```\n"

        return base_prompt

    @staticmethod
    def _extract_script(response_text: str) -> Optional[str]:
        """从回复中提取 Markdown 脚本内容"""
        import re

        # 1. 尝试提取 markdown 代码块
        markdown_pattern = r'```markdown\s*(.*?)\s*```'
        matches = re.findall(markdown_pattern, response_text, re.DOTALL)
        if matches:
            return matches[-1].strip()

        # 2. 尝试提取普通代码块
        generic_pattern = r'```\s*(.*?)\s*```'
        matches = re.findall(generic_pattern, response_text, re.DOTALL)
        for segment in matches:
            if '【' in segment and '】' in segment:
                return segment.strip()

        # 3. 如果没有代码块，检查是否包含【大牛】或【一帆】
        # 如果包含，说明 AI 直接输出了脚本，直接返回整个文本
        if ('【大牛】' in response_text or '【一帆】' in response_text):
            return response_text.strip()

        return None
