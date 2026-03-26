from dotenv import load_dotenv
from tools.websearch import WebSearch
from tools.registry import ToolRegistry

load_dotenv()

if __name__ == "__main__":
    tool_registory = ToolRegistry()
    tool_search = WebSearch()
    tool_registory.registerTool(tool_search)

    print("--- 输出可用工具 ---")
    print(tool_registory.get_tools_description())
    # print("---执行可用工具 ---")
    # query = input("input your question: ")
    # tool_registory.execute_tool(name=tool_search.name, params=query)

    tool_name = 'search'
    if 'search' in tool_name.lower():
        print(True)

