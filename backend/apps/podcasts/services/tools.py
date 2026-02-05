"""
AI Tools for function calling
"""
from typing import List, Dict, Any
from django.conf import settings
from tavily import TavilyClient
import threading


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

            # 使用线程实现超时（signal不能在多线程中使用）
            result = {}
            error = {}

            def do_search():
                try:
                    response = client.search(
                        query=query,
                        max_results=max_results,
                        search_depth="basic"  # 可选: "basic" 或 "advanced"
                    )
                    result['response'] = response
                except Exception as e:
                    error['exception'] = e

            # 启动搜索线程
            search_thread = threading.Thread(target=do_search)
            search_thread.start()
            search_thread.join(timeout=20)  # 20秒超时

            # 检查是否超时
            if search_thread.is_alive():
                return f"搜索 '{query}' 超时，请稍后重试"

            # 检查是否有错误
            if 'exception' in error:
                raise error['exception']

            # 获取结果
            response = result.get('response', {})

            # 格式化结果
            results = []
            for idx, item in enumerate(response.get('results', []), 1):
                results.append(
                    f"{idx}. {item.get('title', 'N/A')}\n"
                    f"   来源: {item.get('url', 'N/A')}\n"
                    f"   摘要: {item.get('content', 'N/A')}"
                )

            if not results:
                return f"未找到关于 '{query}' 的相关结果"

            return f"搜索 '{query}' 的结果：\n\n" + "\n\n".join(results)

        except Exception as e:
            return f"搜索失败：{str(e)}"
