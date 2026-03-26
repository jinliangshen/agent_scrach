import os
from openai import OpenAI
from dotenv import load_dotenv
from typing import List, Dict, Optional

# 加载 .env 文件中的环境变量
load_dotenv()

class HelloAgentsLLM:
    """
    LLM客户端。
    它用于调用任何兼容OpenAI接口的服务，并默认使用流式响应。
    """
    def __init__(
            self, 
            model: Optional[str] = None, 
            apiKey: Optional[str] = None, 
            baseUrl: Optional[str] = None,
            provider: Optional[str] = "auto",
            **kwargs
            ):
        """
        初始化客户端。优先使用传入参数，如果未提供，则从环境变量加载。
        """
        if provider == "ollama":
            self.model = "qwen3.5:4b"
            apiKey = "ollama"
            baseUrl = "http://127.0.0.1:11434/v1"
            timeout = kwargs.get('timeout', 120)
            # 1. 显式清除当前进程的代理环境变量
            os.environ["http_proxy"] = ""
            os.environ["https_proxy"] = ""
            # 2. 明确指定本地地址不走代理（双重保险）
            os.environ["no_proxy"] = "localhost,127.0.0.1,11434"

        else: 
            self.model = model or os.getenv("LLM_MODEL_ID")
            apiKey = apiKey or os.getenv("LLM_API_KEY")
            baseUrl = baseUrl or os.getenv("LLM_BASE_URL")
            timeout = kwargs.get('timeout', 60)
            
            if not all([self.model, apiKey, baseUrl]):
                raise ValueError("模型ID、API密钥和服务地址必须被提供或在.env文件中定义。")

        self.client = OpenAI(api_key=apiKey, base_url=baseUrl, timeout=timeout)

    def invoke(self, messages: List[Dict[str, str]], temperature: float = 0) -> str:
        """
        调用大语言模型进行思考，并返回其响应。
        """
        print(f"🧠 正在调用 {self.model} 模型...")
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                stream=False,
            )
            
            # 处理流式响应
            print("✅ 大语言模型响应成功:\n LLM输出内容为:")
            # collected_content = []
            # for chunk in response:
            #     content = chunk.choices[0].delta.content or ""
            #     print(content, end="", flush=True)
            #     collected_content.append(content)
            # print()  # 在流式输出结束后换行
            return response.choices[0].message.content

        except Exception as e:
            print(f"❌ 调用LLM API时发生错误: {e}")
            return None

    def stream_invoke(self, messages: List[Dict[str, str]], temperature: float = 0) -> str:
        """
        调用大语言模型进行思考，并返回其响应。
        """
        print(f"🧠 正在调用 {self.model} 模型...")
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                stream=True,
            )
            
            # 处理流式响应
            print("✅ 大语言模型响应成功:\n LLM输出内容为:")
            for chunk in response:
                content = chunk.choices[0].delta.content or ""
                if content:
                    yield content

        except Exception as e:
            print(f"❌ 调用LLM API时发生错误: {e}")
            return None


    def think(self, messages: List[Dict[str, str]], temperature: float = 0) -> str:
        """
        调用大语言模型进行思考，并返回其响应。
        """
        print(f"🧠 正在调用 {self.model} 模型...")
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                stream=True,
            )
            
            # 处理流式响应
            print("✅ 大语言模型响应成功:\n LLM输出内容为:")
            collected_content = []
            for chunk in response:
                content = chunk.choices[0].delta.content or ""
                print(content, end="", flush=True)
                collected_content.append(content)
            print()  # 在流式输出结束后换行
            return "".join(collected_content)

        except Exception as e:
            print(f"❌ 调用LLM API时发生错误: {e}")
            return None

# --- 客户端使用示例 ---
if __name__ == '__main__':
    try:
        llmClient = HelloAgentsLLM(provider="ollama")
        exampleMessages = [
            {"role": "system", "content": "You are a helpful assistant that writes Python code."},
            {"role": "user", "content": "who are you"}
        ]
        print("--- 调用LLM ---")
        # responseText = llmClient.invoke(exampleMessages)
        # if responseText:
        #     print("\n\n--- 完整模型响应 ---")
        #     print(responseText)

        full_response = ""
        for chunk in llmClient.stream_invoke(exampleMessages):
            full_response += chunk
            print(chunk, end="", flush=True)

        print()  # 换行            

    except ValueError as e:
        print(e)

