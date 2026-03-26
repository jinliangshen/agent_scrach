from typing import Optional, Dict, Any
from .registry import Tool


class Memory(Tool):
    """
    记忆工具，用于存储和检索对话上下文中的关键信息。
    支持存储、检索、列出和清除记忆。
    """

    def __init__(self):
        # 类级别的存储，所有实例共享
        if not hasattr(Memory, "_storage"):
            Memory._storage: Dict[str, str] = {}
        super().__init__(
            name="Memory",
            description="一个记忆存储工具。可以存储、检索、列出和清除信息。用于记住用户偏好、关键事实等。",
        )

    def run(self, input_text: str, **kwargs) -> str:
        """执行记忆操作"""
        # 解析操作类型
        action, content = self._parse_input(input_text)

        if action == "store" or action == "save":
            return self._store(content)
        elif action == "recall" or action == "search" or action == "get":
            return self._recall(content)
        elif action == "list":
            return self._list()
        elif action == "clear" or action == "delete":
            return self._clear(content)
        else:
            # 默认尝试检索
            return self._recall(input_text)

    def _parse_input(self, input_text: str) -> tuple:
        """解析输入，提取操作和内容"""
        input_text = input_text.strip()

        # 格式: action=content 或 content
        if "=" in input_text:
            parts = input_text.split("=", 1)
            return parts[0].strip().lower(), parts[1].strip()

        return "", input_text

    def _store(self, content: str) -> str:
        """存储记忆"""
        if not content:
            return "❌ 错误:存储内容不能为空"

        # 格式: key=value 或 直接存储
        if "=" in content:
            key, value = content.split("=", 1)
            Memory._storage[key.strip()] = value.strip()
            return f"✅ 已记住: {key.strip()} = {value.strip()}"
        else:
            # 自动生成键名
            key = f"memory_{len(Memory._storage) + 1}"
            Memory._storage[key] = content
            return f"✅ 已记住: {content}"

    def _recall(self, query: str) -> str:
        """检索记忆"""
        if not query:
            # 返回所有记忆
            return self._list()

        query = query.lower()

        # 精确匹配
        if query in Memory._storage:
            return f"找到: {query} = {Memory._storage[query]}"

        # 模糊匹配
        results = []
        for key, value in Memory._storage.items():
            if query in key.lower() or query in value.lower():
                results.append(f"- {key}: {value}")

        if results:
            return "相关记忆:\n" + "\n".join(results)

        return f"没有找到关于 '{query}' 的记忆"

    def _list(self) -> str:
        """列出所有记忆"""
        if not Memory._storage:
            return "记忆库为空"

        lines = ["当前记忆:"]
        for key, value in Memory._storage.items():
            lines.append(f"- {key}: {value}")

        return "\n".join(lines)

    def _clear(self, key: Optional[str] = None) -> str:
        """清除记忆"""
        if key:
            if key in Memory._storage:
                del Memory._storage[key]
                return f"✅ 已删除记忆: {key}"
            return f"❌ 记忆 '{key}' 不存在"

        Memory._storage.clear()
        return "✅ 已清除所有记忆"

    def get_schema(self) -> Dict[str, Any]:
        """获取工具的JSON Schema"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "input_text": {
                        "type": "string",
                        "description": "操作指令。格式: action=content 或直接内容。操作: store/recall/list/clear",
                    }
                },
                "required": ["input_text"],
            },
        }


def quick_memory(action: str, content: str = "") -> str:
    """
    快速记忆函数

    Args:
        action: 操作类型 (store/recall/list/clear)
        content: 内容

    Returns:
        操作结果
    """
    tool = Memory()
    if action == "list":
        return tool.run("list")
    elif action == "clear":
        return tool.run("clear")
    elif action in ("store", "save"):
        return tool.run(f"store={content}")
    elif action in ("recall", "search", "get"):
        return tool.run(f"recall={content}")
    else:
        return tool.run(content)


if __name__ == "__main__":
    # 测试
    m = Memory()

    print("=== 测试存储 ===")
    print(m.run("store=用户名字=张三"))
    print(m.run("store=用户喜欢=Python"))

    print("\n=== 测试检索 ===")
    print(m.run("recall=用户"))
    print(m.run("Python"))

    print("\n=== 测试列表 ===")
    print(m.run("list"))

    print("\n=== 测试清除 ===")
    print(m.run("clear=用户名字"))
    print(m.run("list"))
