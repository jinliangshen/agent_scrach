from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod


class Tool(ABC):
    """工具基类，定义工具的接口"""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    def run(self, input_text: str, **kwargs) -> Any:
        """执行工具，返回结果"""
        pass

    def get_schema(self) -> Dict[str, Any]:
        """获取工具的JSON Schema，用于LLM工具调用"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "input_text": {"type": "string", "description": "输入文本或查询"}
                },
                "required": ["input_text"],
            },
        }


class ToolRegistry:
    """
    工具注册表，负责管理和执行工具。
    支持工具注册、查询、批量执行等操作。
    """

    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    def get_all_tools_schema(self) -> List[Dict[str, Any]]:
        """获取所有工具的Schema列表，用于LLM批量工具调用"""
        return [tool.get_schema() for tool in self._tools.values()]

    def get_tools_description(self) -> str:
        if not self._tools:
            return "暂无可用工具"

        descriptions = []
        for tool in self._tools.values():
            descriptions.append(f"- {tool.name}: {tool.description}")

        return "\n".join(descriptions)

    def registerTool(self, tool: Tool) -> bool:
        """
        向工具箱中注册一个新工具。
        返回True表示注册成功，False表示工具已存在且未覆盖。
        """
        # 检查名称是否已存在
        if tool.name in self._tools:
            existing = self._tools[tool.name]
            if existing is tool:
                print(f"提示:工具 '{tool.name}' 已是最新，无需重复注册。")
                return False
            print(f"警告:工具 '{tool.name}' 已存在，将被覆盖。")

        self._tools[tool.name] = tool
        print(f"工具 '{tool.name}' 已注册成功。")
        return True

    def unregister(self, name: str) -> bool:
        """注销工具"""
        if name in self._tools:
            del self._tools[name]
            print(f"工具 '{name}' 已注销。")
            return True
        print(f"警告:工具 '{name}' 不存在，无法注销。")
        return False

    def get_tool(self, name: str) -> Optional[Tool]:
        """根据名称获取工具对象"""
        return self._tools.get(name)

    def list_tools(self) -> List[str]:
        """列出所有已注册的工具名称"""
        return list(self._tools.keys())

    def has_tool(self, name: str) -> bool:
        """检查工具是否存在"""
        return name in self._tools

    def execute_tool(self, name: str, params: Any = None) -> Any:
        """执行工具调用"""
        tool = self.get_tool(name)
        if not tool:
            raise ValueError(f"工具 '{name}' 不存在")

        # 支持多种参数格式
        if params is None:
            return tool.run("")
        elif isinstance(params, str):
            return tool.run(params)
        elif isinstance(params, dict):
            # 处理dict参数，提取input_text或使用整个dict
            input_text = params.get("input_text", params.get("query", ""))
            return tool.run(input_text, **params)
        else:
            return tool.run(str(params))

    def execute_tools(self, calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        批量执行工具调用
        calls: [{"name": "xxx", "params": "yyy"}, ...]
        """
        results = []
        for call in calls:
            name = call.get("name", "")
            params = call.get("params")
            if not name:
                results.append(
                    {"name": name, "success": False, "error": "工具名称不能为空"}
                )
                continue
            try:
                result = self.execute_tool(name, params)
                results.append({"name": name, "success": True, "result": result})
            except Exception as e:
                results.append({"name": name, "success": False, "error": str(e)})
        return results
