from serpapi import Client
from dotenv import load_dotenv
import os
from tavily import TavilyClient
from .registry import Tool

# 加载 .env 文件中的环境变量
load_dotenv()

class WebSearch(Tool):
    """工具搜索类"""
    def __init__(self):
        super().__init__(
            name = "WebSearch", 
            description = "一个网页搜索引擎。当你需要回答关于时事、事实以及在你的知识库中找不到的信息时，应使用此工具。"
            )
    def run(self, input_text: str) -> str:
        search_query = input_text
        """使用Tavily API进行真实搜索"""
        try:
            api_key=os.getenv("TAVILY_API_KEY")
            if not api_key:
                return "错误:SERPAPI_API_KEY 未在 .env 文件中配置。"
            
            tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
            print(f"🔍 正在搜索: {search_query}")
            
            # 调用Tavily搜索API
            response = tavily_client.search(
                query=search_query,
                search_depth="basic",
                include_answer=True,
                include_raw_content=False,
                max_results=5
            )
            # 处理搜索结果
            search_results = ""
            # 优先使用Tavily的综合答案
            if response.get("answer"):
                search_results = f"综合答案：\n{response['answer']}\n\n"
            # 添加具体的搜索结果
            if response.get("results"):
                search_results += "相关信息：\n"
                for i, result in enumerate(response["results"][:3], 1):
                    title = result.get("title", "")
                    content = result.get("content", "")
                    url = result.get("url", "")
                    search_results += f"{i}. {title}\n{content}\n来源：{url}\n\n"
            if not search_results:
                search_results = "抱歉，没有找到相关信息。"
            # print(f"the rearch result is {search_results}")
            return search_results
        except Exception as e:
            error_msg = f"搜索时发生错误: {str(e)}"
            print(f"❌ {error_msg}")

def serpapi_search(query: str) -> str:
    """
    一个基于SerpApi的实战网页搜索引擎工具。
    它会智能地解析搜索结果，优先返回直接答案或知识图谱信息。
    """
    print(f"🔍 正在执行 [SerpApi] 网页搜索: {query}")
    try:
        api_key = os.getenv("SERPAPI_API_KEY")
        if not api_key:
            return "错误:SERPAPI_API_KEY 未在 .env 文件中配置。"

        params = {
            "engine": "google",
            "q": query,
            "gl": "cn",  # 国家代码
            "hl": "zh-cn", # 语言代码
        }
        client = Client(api_key=api_key)
        results = client.search(params)
        
        # 智能解析:优先寻找最直接的答案
        if "answer_box_list" in results:
            return "\n".join(results["answer_box_list"])
        if "answer_box" in results and "answer" in results["answer_box"]:
            return results["answer_box"]["answer"]
        if "knowledge_graph" in results and "description" in results["knowledge_graph"]:
            return results["knowledge_graph"]["description"]
        if "organic_results" in results and results["organic_results"]:
            # 如果没有直接答案，则返回前三个有机结果的摘要
            snippets = [
                f"[{i+1}] {res.get('title', '')}\n{res.get('snippet', '')}"
                for i, res in enumerate(results["organic_results"][:3])
            ]
            return "\n\n".join(snippets)
        
        return f"对不起，没有找到关于 '{query}' 的信息。"

    except Exception as e:
        return f"搜索时发生错误: {e}"
    
def tavily_search(search_query: str) -> str:
    """：使用Tavily API进行真实搜索"""
    
    try:
        
        api_key=os.getenv("TAVILY_API_KEY")
        if not api_key:
            return "错误:SERPAPI_API_KEY 未在 .env 文件中配置。"
        
        tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
        print(f"🔍 正在搜索: {search_query}")
        
        # 调用Tavily搜索API
        response = tavily_client.search(
            query=search_query,
            search_depth="basic",
            include_answer=True,
            include_raw_content=False,
            max_results=5
        )
        
        # 处理搜索结果
        search_results = ""
        
        # 优先使用Tavily的综合答案
        if response.get("answer"):
            search_results = f"综合答案：\n{response['answer']}\n\n"
        
        # 添加具体的搜索结果
        if response.get("results"):
            search_results += "相关信息：\n"
            for i, result in enumerate(response["results"][:3], 1):
                title = result.get("title", "")
                content = result.get("content", "")
                url = result.get("url", "")
                search_results += f"{i}. {title}\n{content}\n来源：{url}\n\n"
        
        if not search_results:
            search_results = "抱歉，没有找到相关信息。"

        print(f"the rearch result is {search_results}")

        return search_results

        
    except Exception as e:
        error_msg = f"搜索时发生错误: {str(e)}"
        print(f"❌ {error_msg}")



if __name__ == '__main__':

    observation = tavily_search("英伟达最新的GPU型号是什么")
    print("--- 观察 (Observation) ---")
    print(observation)