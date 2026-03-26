from typing import Optional
from .registry import Tool
import os

# 可选的 dotenv 导入
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


class WebSearch(Tool):
    """
    网页搜索工具，支持 Tavily 和 SerpApi 两种后端。
    用于获取实时信息和时事新闻。
    """

    def __init__(self, provider: str = "tavily"):
        """
        初始化搜索工具

        Args:
            provider: 搜索服务提供商，支持 "tavily" 和 "serpapi"
        """
        self.provider = provider
        super().__init__(
            name="WebSearch",
            description="一个网页搜索引擎。当你需要回答关于时事、事实以及在你的知识库中找不到的信息时，应使用此工具。",
        )

    def run(self, input_text: str, **kwargs) -> str:
        """执行搜索"""
        if self.provider == "tavily":
            return self._tavily_search(input_text)
        elif self.provider == "serpapi":
            return self._serpapi_search(input_text)
        else:
            return f"错误:不支持的搜索提供商 '{self.provider}'"

    def _tavily_search(self, query: str, **kwargs) -> str:
        """使用 Tavily API 进行搜索"""
        try:
            api_key = os.getenv("TAVILY_API_KEY")
            if not api_key:
                return "错误:TAVILY_API_KEY 未在 .env 文件中配置。"

            # 延迟导入，避免未安装时无法加载模块
            from tavily import TavilyClient

            client = TavilyClient(api_key=api_key)

            print(f"🔍 [Tavily] 正在搜索: {query}")

            search_depth = kwargs.get("search_depth", "basic")
            max_results = kwargs.get("max_results", 5)

            response = client.search(
                query=query,
                search_depth=search_depth,
                include_answer=True,
                include_raw_content=False,
                max_results=max_results,
            )

            # 解析结果
            return self._parse_tavily_response(response)

        except ImportError:
            return "错误:请安装 tavily 包 (pip install tavily)"
        except Exception as e:
            return f"搜索时发生错误: {str(e)}"

    def _serpapi_search(self, query: str) -> str:
        """使用 SerpApi 进行搜索"""
        try:
            api_key = os.getenv("SERPAPI_API_KEY")
            if not api_key:
                return "错误:SERPAPI_API_KEY 未在 .env 文件中配置。"

            from serpapi import Client

            print(f"🔍 [SerpApi] 正在搜索: {query}")

            client = Client(api_key=api_key)
            params = {
                "engine": "google",
                "q": query,
                "gl": "cn",
                "hl": "zh-cn",
            }
            results = client.search(params)

            # 智能解析:优先寻找最直接的答案
            if "answer_box_list" in results:
                return "\n".join(results["answer_box_list"])
            if "answer_box" in results and "answer" in results["answer_box"]:
                return results["answer_box"]["answer"]
            if (
                "knowledge_graph" in results
                and "description" in results["knowledge_graph"]
            ):
                return results["knowledge_graph"]["description"]
            if "organic_results" in results and results["organic_results"]:
                snippets = [
                    f"[{i + 1}] {res.get('title', '')}\n{res.get('snippet', '')}"
                    for i, res in enumerate(results["organic_results"][:3])
                ]
                return "\n\n".join(snippets)

            return f"对不起，没有找到关于 '{query}' 的信息。"

        except ImportError:
            return "错误:请安装 serpapi 包 (pip install serpapi)"
        except Exception as e:
            return f"搜索时发生错误: {str(e)}"

    def _parse_tavily_response(self, response: dict) -> str:
        """解析 Tavily 搜索结果"""
        if not response:
            return "抱歉，没有找到相关信息。"

        # 优先使用综合答案
        results = ""
        if response.get("answer"):
            results = f"综合答案：\n{response['answer']}\n\n"

        # 添加具体的搜索结果
        if response.get("results"):
            results += "相关信息：\n"
            for i, result in enumerate(response["results"][:3], 1):
                title = result.get("title", "")
                content = result.get("content", "")
                url = result.get("url", "")
                results += f"{i}. {title}\n{content}\n来源：{url}\n\n"

        if not results.strip():
            results = "抱歉，没有找到相关信息。"

        return results

    def get_schema(self) -> dict:
        """获取工具的JSON Schema"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "input_text": {"type": "string", "description": "搜索查询内容"},
                    "search_depth": {
                        "type": "string",
                        "enum": ["basic", "advanced"],
                        "description": "搜索深度",
                    },
                    "max_results": {"type": "integer", "description": "最大结果数量"},
                },
                "required": ["input_text"],
            },
        }


def quick_search(query: str, provider: str = "tavily") -> str:
    """
    快速搜索函数，直接导入使用

    Args:
        query: 搜索查询
        provider: 搜索提供商

    Returns:
        搜索结果字符串
    """
    tool = WebSearch(provider=provider)
    return tool.run(query)


if __name__ == "__main__":
    # 测试
    result = quick_search("英伟达最新的GPU型号是什么")
    print("--- 搜索结果 ---")
    print(result)
