# my_simple_agent.py
from typing import Optional, Iterator, List, Dict, Any
from core.agentBase import Agent
from core.llmClient import HelloAgentsLLM
from core.message import Message
from core.config import Config
import re
from tools.registry import ToolRegistry, Tool
from tools.websearch import WebSearch
from tools.memory import Memory
from tools.weather import Weather


class MySimpleAgent(Agent):
    """
    重写的简单对话Agent
    展示如何基于框架基类构建自定义Agent
    """

    def __init__(
        self,
        name: str,
        llm: HelloAgentsLLM,
        system_prompt: Optional[str] = None,
        config: Optional[Config] = None,
        tool_registry: Optional["ToolRegistry"] = None,
        enable_tool_calling: bool = True,
    ):
        super().__init__(name, llm, system_prompt, config)
        self.tool_registry = tool_registry
        self.enable_tool_calling = enable_tool_calling and tool_registry is not None
        print(
            f"✅ {name} 初始化完成，工具调用: {'启用' if self.enable_tool_calling else '禁用'}"
        )

    def run(self, input_text: str, max_tool_iterations: int = 3, **kwargs) -> str:
        """
        重写的运行方法 - 实现简单对话逻辑，支持可选工具调用
        """
        print(f"🤖 {self.name} 正在处理: {input_text}")

        # 构建消息列表
        messages = []

        # 添加系统消息（可能包含工具信息）
        enhanced_system_prompt = self._get_enhanced_system_prompt()
        messages.append({"role": "system", "content": enhanced_system_prompt})
        print(f" the system prompt is {enhanced_system_prompt} \n")

        # 添加历史消息
        for msg in self._history:
            messages.append({"role": msg.role, "content": msg.content})

        # 添加当前用户消息
        messages.append({"role": "user", "content": input_text})

        # 如果没有启用工具调用，使用简单对话逻辑
        if not self.enable_tool_calling:
            response = self.llm.invoke(messages, **kwargs)
            self.add_message(Message(input_text, "user"))
            self.add_message(Message(response, "assistant"))
            print(f"✅ {self.name} 响应完成")
            return response

        # 支持多轮工具调用的逻辑
        return self._run_with_tools(messages, input_text, max_tool_iterations, **kwargs)

    def _get_enhanced_system_prompt(self) -> str:
        """构建增强的系统提示词，包含工具信息"""
        base_prompt = self.system_prompt or "你是一个有用的AI助手。"

        if not self.enable_tool_calling or not self.tool_registry:
            return base_prompt

        # 获取工具描述
        tools_description = self.tool_registry.get_tools_description()
        if not tools_description or tools_description == "暂无可用工具":
            return base_prompt

        tools_section = "\n\n## 可用工具\n"
        tools_section += "你可以使用以下工具来帮助回答问题:\n"
        tools_section += tools_description + "\n"

        # 添加 JSON Schema 格式的工具定义（供支持结构化工具调用的LLM使用）
        tools_schema = self.tool_registry.get_all_tools_schema()
        if tools_schema:
            import json

            tools_section += "\n## 工具Schema定义\n"
            tools_section += "```json\n"
            tools_section += json.dumps(tools_schema, ensure_ascii=False, indent=2)
            tools_section += "\n```\n"

        tools_section += "\n## 工具调用规则\n"
        tools_section += "1. 当需要使用工具时，请一定使用以下格式:\n"
        tools_section += "   `[TOOL_CALL:{tool_name}:{parameters}]`\n"
        tools_section += "   例如: `[TOOL_CALL:WebSearch:nvidia最新的GPU]` 或 `[TOOL_CALL:memory:recall=用户信息]`\n"
        tools_section += "2. 每个工具调用必须是独立的，不要在一个调用中嵌套另一个。\n"
        tools_section += "3. 工具调用结果会自动插入到对话中，然后你可以基于结果继续回答。\n"
        tools_section += "4. 如果不需要使用工具，直接给出回答即可。\n"

        return base_prompt + tools_section

    def _run_with_tools(
        self, messages: list, input_text: str, max_tool_iterations: int, **kwargs
    ) -> str:
        """支持工具调用的运行逻辑"""
        current_iteration = 0
        final_response = ""

        while current_iteration < max_tool_iterations:
            # 调用LLM
            response = self.llm.invoke(messages, **kwargs)
            print(f"🧠 the LLM output is {response} \n")
            # 检查是否有工具调用
            tool_calls = self._parse_tool_calls(response)
            print(f"tool_calls is {tool_calls} \n")
            if tool_calls:
                print(f"🔧 检测到 {len(tool_calls)} 个工具调用")
                # 执行所有工具调用并收集结果
                tool_results = []
                clean_response = response

                for call in tool_calls:
                    result = self._execute_tool_call(
                        call["tool_name"], call["parameters"]
                    )
                    print(f"🔧 the tool {call['tool_name']} output {result}")
                    tool_results.append(result)
                    # 从响应中移除工具调用标记
                    clean_response = clean_response.replace(call["original"], "")

                # 构建包含工具结果的消息
                messages.append({"role": "assistant", "content": clean_response})

                # 添加工具结果
                tool_results_text = "\n\n".join(tool_results)
                messages.append(
                    {
                        "role": "user",
                        "content": f"工具执行结果:\n{tool_results_text}\n\n请基于这些结果给出完整的回答。",
                    }
                )
                current_iteration += 1
                continue
            # 没有工具调用，这是最终回答
            final_response = response
            break

        # 如果超过最大迭代次数，获取最后一次回答
        if current_iteration >= max_tool_iterations and not final_response:
            final_response = self.llm.invoke(messages, **kwargs)

        # 保存到历史记录
        self.add_message(Message(input_text, "user"))
        self.add_message(Message(final_response, "assistant"))
        print(f"✅ {self.name} 响应完成")

        return final_response

    def _parse_tool_calls(self, text: str) -> List[Dict[str, Any]]:
        """解析文本中的工具调用"""
        pattern = r"\[TOOL_CALL:([^:]+):([^\]]+)\]"
        matches = re.findall(pattern, text)

        tool_calls = []
        for tool_name, parameters in matches:
            tool_calls.append(
                {
                    "tool_name": tool_name.strip(),
                    "parameters": parameters.strip(),
                    "original": f"[TOOL_CALL:{tool_name}:{parameters}]",
                }
            )

        return tool_calls

    def _execute_tool_call(self, tool_name: str, parameters: str) -> str:
        """执行工具调用"""
        if not self.tool_registry:
            return f"❌ 错误:未配置工具注册表"

        try:
            # 直接传入字符串参数，由 ToolRegistry 处理
            result = self.tool_registry.execute_tool(tool_name, parameters)
            return f"🔧 工具 {tool_name} 执行结果:\n{result}"

        except ValueError as e:
            return f"❌ 错误:{str(e)}"
        except Exception as e:
            return f"❌ 工具调用失败:{str(e)}"

    def stream_run(self, input_text: str, **kwargs) -> Iterator[str]:
        """
        自定义的流式运行方法
        """
        print(f"🌊 {self.name} 开始流式处理: {input_text}")

        messages = []

        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})

        for msg in self._history:
            messages.append({"role": msg.role, "content": msg.content})

        messages.append({"role": "user", "content": input_text})

        # 流式调用LLM
        full_response = ""
        print("📝 实时响应: ", end="")
        for chunk in self.llm.stream_invoke(messages, **kwargs):
            full_response += chunk
            print(chunk, end="", flush=True)
            yield chunk

        print()  # 换行

        # 保存完整对话到历史记录
        self.add_message(Message(input_text, "user"))
        self.add_message(Message(full_response, "assistant"))
        print(f"✅ {self.name} 流式响应完成")

if __name__ == "__main__":
    llmClient = HelloAgentsLLM()
    # 测试1:基础对话Agent（无工具）
    # print("=== 测试1:基础对话 ===")
    # basic_agent = MySimpleAgent(
    #     name="基础助手",
    #     llm=llmClient,
    #     system_prompt="你是一个友好的AI助手，请用简洁明了的方式回答问题。",
    #     enable_tool_calling = False
    # )
    # response1 = basic_agent.run("你好，请介绍一下自己")
    # print(f"基础对话响应: {response1}\n")

    # 测试2:带多个工具的Agent
    print("=== 测试2:多工具增强对话 ===")
    tool_registry = ToolRegistry()
    tool_registry.registerTool(WebSearch())
    tool_registry.registerTool(Memory())
    tool_registry.registerTool(Weather())

    print(f"已注册工具: {tool_registry.list_tools()}")

    enhanced_agent = MySimpleAgent(
        name="增强助手",
        llm=llmClient,
        system_prompt="你是一个智能助手，可以使用工具来帮助用户。",
        tool_registry=tool_registry,
        enable_tool_calling=True,
    )
    response2 = enhanced_agent.run("北京天气如何")
    print(f"工具增强响应: {response2}\n")
    # 测试3:流式响应
    # print("=== 测试3:流式响应 ===")
    # print("流式响应: ", end="")
    # for chunk in basic_agent.stream_run("请解释什么是人工智能"):
    #     pass  # 内容已在stream_run中实时打印

    # 查看对话历史
    print(f"\n对话历史: {len(enhanced_agent.get_history())} 条消息")