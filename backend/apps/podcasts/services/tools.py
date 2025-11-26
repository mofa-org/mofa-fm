"""
AI Tools for function calling
"""
from typing import List, Dict, Any
from django.conf import settings
from tavily import TavilyClient


class AITools:
    """AI工具集合，用于function calling"""

    @staticmethod
    def get_tool_definitions() -> List[Dict[str, Any]]:
        """
        返回所有可用工具的定义（OpenAI function calling 格式）
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "tavily_search",
                    "description": "搜索最新的实时信息、新闻、数据。当用户询问涉及时效性的内容时（今天、最近、最新、当前、现在等），或需要具体的实时数据（股价、新闻、天气等），必须使用此工具。返回相关搜索结果摘要。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "搜索查询内容"
                            },
                            "max_results": {
                                "type": "integer",
                                "description": "返回结果数量（默认5）",
                                "default": 5
                            }
                        },
                        "required": ["query"]
                    }
                }
            }
        ]

    @staticmethod
    def execute_tool(tool_name: str, tool_args: Dict[str, Any]) -> str:
        """
        执行指定的工具调用

        Args:
            tool_name: 工具名称
            tool_args: 工具参数

        Returns:
            工具执行结果（字符串格式）
        """
        if tool_name == "tavily_search":
            return AITools._execute_tavily_search(**tool_args)
        else:
            return f"错误：未知工具 {tool_name}"

    @staticmethod
    def _execute_tavily_search(query: str, max_results: int = 5) -> str:
        """
        执行 Tavily 搜索

        Args:
            query: 搜索查询
            max_results: 最大结果数

        Returns:
            搜索结果摘要
        """
        try:
            api_key = settings.TAVILY_API_KEY
            if not api_key:
                return "错误：Tavily API密钥未配置"

            client = TavilyClient(api_key=api_key)

            # 执行搜索
            response = client.search(
                query=query,
                max_results=max_results,
                search_depth="basic"  # 可选: "basic" 或 "advanced"
            )

            # 格式化结果
            results = []
            for idx, result in enumerate(response.get('results', []), 1):
                results.append(
                    f"{idx}. {result.get('title', 'N/A')}\n"
                    f"   来源: {result.get('url', 'N/A')}\n"
                    f"   摘要: {result.get('content', 'N/A')}"
                )

            if not results:
                return f"未找到关于 '{query}' 的相关结果"

            return f"搜索 '{query}' 的结果：\n\n" + "\n\n".join(results)

        except Exception as e:
            return f"搜索失败：{str(e)}"
