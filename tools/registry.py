from typing import Dict, Any, Optional
from abc import ABC, abstractmethod


class Tool(ABC):    
    def __init__(self, name: str, description: str):        
        self.name = name        
        self.description = description
    @abstractmethod  
    def run(self, input_text: str, **kwargs) -> Any:        
        pass
    
class ToolRegistry:
    """
    一个工具执行器，负责管理和执行工具。
    """
    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    def get_tools_description(self) ->str:
        if not self._tools:            
            return "暂无可用工具"        
        desc = ""        
        for tool in self._tools.values():            
            desc += f"- {tool.name}: {tool.description}\n"        
            return desc        

    def registerTool(self, tool:Tool)->None:
        """
        向工具箱中注册一个新工具。
        """
        if tool in self._tools.values():
            print(f"警告:工具 '{tool.name}' 已存在，将被覆盖。")
        self._tools[tool.name] = tool
        print(f"工具 '{tool.name}' 已注册成功。")

    def get_tool(self, name: str) -> callable:
        """
        根据名称获取一个工具的执行函数。
        """
        return self._tools.get(name)

    def execute_tool(self, name: str, params: Any) -> Any:        
        """执行工具调用"""        
        tool = self.get_tool(name)        
        if not tool:            
            raise ValueError(f"工具 '{name}' 不存在")        
        if isinstance(params, str):            
            return tool.run(params)        
        else:
            return tool.run(params)
