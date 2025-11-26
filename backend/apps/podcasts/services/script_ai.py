"""
AI 脚本生成服务 - 基于 OpenAI-compatible API (Moonshot/Kimi)
"""
from typing import Dict, List, Optional
import json

from django.conf import settings
from openai import OpenAI
from .tools import AITools


class ScriptAIService:
    """封装与 OpenAI-compatible API 的交互逻辑"""

    def __init__(self):
        api_key = getattr(settings, 'OPENAI_API_KEY', None)
        if not api_key:
            raise ValueError('OPENAI_API_KEY 未配置，请在环境变量或 .env 中设置')

        self.client = OpenAI(
            api_key=api_key,
            base_url=getattr(settings, 'OPENAI_API_BASE', 'https://api.moonshot.cn/v1')
        )
        self.model = getattr(settings, 'OPENAI_MODEL', 'moonshot-v1-8k')

    def chat(
        self,
        messages: List[Dict[str, str]],
        reference_texts: Optional[List[str]] = None,
        current_script: Optional[str] = None,
        enable_tools: bool = True
    ) -> Dict[str, Optional[str]]:
        """
        与 Kimi 对话，生成或修改脚本。
        支持 function calling 以调用外部工具。

        返回 {
            success: bool,
            response: str,
            script: str | None,
            error: str | None,
            tool_calls: List[Dict] | None  # 工具调用历史
        }
        """
        try:
            system_prompt = self._build_system_prompt(reference_texts, current_script)
            full_messages = [{'role': 'system', 'content': system_prompt}] + messages

            # 工具调用历史
            tool_calls_history = []

            # 最多允许3轮工具调用，防止死循环
            max_iterations = 3
            iteration = 0

            while iteration < max_iterations:
                iteration += 1

                # 准备API调用参数
                api_params = {
                    'model': self.model,
                    'messages': full_messages,
                    'temperature': 0.7,
                    'max_tokens': 2800,
                }

                # 如果启用工具，添加工具定义
                if enable_tools:
                    api_params['tools'] = AITools.get_tool_definitions()
                    api_params['tool_choice'] = 'auto'

                completion = self.client.chat.completions.create(**api_params)

                assistant_message = completion.choices[0].message

                # 检查是否有工具调用
                if assistant_message.tool_calls:
                    # 将助手消息添加到对话历史
                    full_messages.append({
                        'role': 'assistant',
                        'content': assistant_message.content or '',
                        'tool_calls': [
                            {
                                'id': tc.id,
                                'type': tc.type,
                                'function': {
                                    'name': tc.function.name,
                                    'arguments': tc.function.arguments
                                }
                            }
                            for tc in assistant_message.tool_calls
                        ]
                    })

                    # 执行每个工具调用
                    for tool_call in assistant_message.tool_calls:
                        function_name = tool_call.function.name
                        function_args = json.loads(tool_call.function.arguments)

                        # 记录工具调用
                        tool_calls_history.append({
                            'name': function_name,
                            'arguments': function_args
                        })

                        # 执行工具
                        function_response = AITools.execute_tool(function_name, function_args)

                        # 将工具响应添加到对话历史
                        full_messages.append({
                            'role': 'tool',
                            'tool_call_id': tool_call.id,
                            'name': function_name,
                            'content': function_response
                        })

                    # 继续循环，让AI处理工具响应
                    continue

                # 没有工具调用，获取最终响应
                response_text = assistant_message.content
                extracted_script = self._extract_script(response_text)

                return {
                    'success': True,
                    'response': response_text,
                    'script': extracted_script if extracted_script else current_script,
                    'error': None,
                    'tool_calls': tool_calls_history if tool_calls_history else None
                }

            # 达到最大迭代次数
            return {
                'success': False,
                'response': None,
                'script': current_script,
                'error': '工具调用次数超过限制',
                'tool_calls': tool_calls_history
            }

        except Exception as exc:  # pylint: disable=broad-except
            return {
                'success': False,
                'response': None,
                'script': current_script,
                'error': f'AI调用失败: {exc}',
                'tool_calls': None
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
        from datetime import datetime
        current_date = datetime.now().strftime('%Y年%m月%d日')

        base_prompt = (
            f"你是一个专业的播客脚本编剧助手，需要帮助用户创作高质量的播客脚本。\n\n"
            f"## 当前时间\n"
            f"今天是：{current_date}\n\n"
            "## 交互模式判断\n"
            "**你需要根据用户意图智能切换回复模式：**\n\n"
            "**模式 1: 正常对话**（满足以下任一条件时使用）\n"
            "- 用户在提问、咨询信息（如\"今天沪指怎么样\"、\"macOS最新版本是什么\"）\n"
            "- 用户在讨论想法、寻求建议（如\"我想聊聊AI话题\"、\"有什么好的选题\"）\n"
            "- 用户没有明确要求生成或修改脚本\n"
            "- 当前没有脚本，或用户在探索阶段\n"
            "→ **用自然、简洁的语言直接回答，不要输出脚本格式**\n\n"
            "**模式 2: 脚本创作**（满足以下任一条件时使用）\n"
            "- 用户明确要求\"生成脚本\"、\"写一个播客\"、\"帮我改下脚本\"等\n"
            "- 用户提供了完整的脚本创作需求（主题、风格、时长等）\n"
            "- 已有现成脚本，用户要求修改特定部分\n"
            "→ **输出完整的播客脚本，使用【大牛】【一帆】格式**\n\n"
            "## 重要：使用搜索结果\n"
            "**如果参考资料中包含【搜索结果】，这是系统自动为你提供的最新实时信息：**\n"
            "1. **必须优先使用**搜索结果中的真实数据\n"
            "2. **绝对不要编造**任何数据、新闻、事件\n"
            "3. 如果搜索结果不足以回答问题，明确告诉用户\"搜索结果中未找到相关信息\"\n"
            "4. 引用数据时要准确，不要篡改数字或事实\n\n"
            "## 脚本格式要求（仅在模式2时使用）\n"
            "1. 使用【大牛】和【一帆】作为固定的两个角色名（主持人用【大牛】，嘉宾用【一帆】）\n"
            "2. 每个角色说话一段，用空行分隔\n"
            "3. 可以在开头使用 # 标题\n"
            "4. **重要：直接输出纯净的 Markdown 文本，不要用 ```markdown 代码块包裹**\n\n"
            "## 脚本内容要求\n"
            "1. 对话自然流畅，符合播客节目的口语化风格\n"
            "2. 【大牛】作为主持人，负责引导话题、提问和总结\n"
            "3. 【一帆】作为嘉宾，负责分享观点、回答问题\n"
            "4. 每段对话长度适中，避免过长的独白\n"
            "5. 如在修改现有脚本，请给出更新后的完整版本\n"
            "6. **如果使用了搜索结果，必须基于真实信息创作，不要编造**\n\n"
            "## 输出示例\n"
            "**示例 1: 正常对话模式**\n"
            "用户: 今天沪指怎么样？\n"
            "助手: 根据搜索结果，今天沪指收于3263.76点，下跌0.1%，成交额5965亿元。\n\n"
            "**示例 2: 脚本创作模式**\n"
            "用户: 帮我写个播客讲今天的沪指行情\n"
            "助手:\n"
            "# 今天沪指：小幅回调，成交清淡\n\n"
            "【大牛】大家好，欢迎来到今天的节目。\n\n"
            "【一帆】大家好，今天聊聊沪指的表现。\n\n"
            "【大牛】今天收盘怎么样？\n\n"
            "【一帆】沪指收于3263.76点，下跌0.1%，成交额5965亿元...\n"
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
