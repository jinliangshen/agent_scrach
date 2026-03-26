from typing import Optional, Dict, Any
from .registry import Tool
import os
import json
import urllib.request
import urllib.error
from urllib.parse import quote


class Weather(Tool):
    """
    天气查询工具，支持查询指定城市的天气情况。
    使用 wttr.in 的免费天气服务，无需 API Key。
    """

    def __init__(self):
        super().__init__(
            name="Weather",
            description="天气查询工具。可以查询指定城市或地区的当前天气、温度、湿度等信息。",
        )

    def run(self, input_text: str, **kwargs) -> str:
        """执行天气查询"""
        if not input_text or not input_text.strip():
            return "❌ 错误:请指定要查询的城市，如: Weather:北京"

        city = input_text.strip()
        return self._get_weather(city)

    def _get_weather(self, city: str) -> str:
        """获取天气信息"""
        try:
            # 对城市名进行URL编码
            encoded_city = quote(city)
            # 使用 wttr.in 的免费天气 API
            # 也可以使用其他免费服务
            url = f"https://wttr.in/{encoded_city}?format=j1"

            # 设置请求头模拟浏览器
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }

            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))

            # 解析天气数据
            return self._parse_weather_data(data, city)

        except urllib.error.HTTPError as e:
            return f"❌ HTTP错误: 无法获取天气数据，请检查城市名称是否正确"
        except urllib.error.URLError as e:
            return f"❌ 网络错误: {str(e)}"
        except json.JSONDecodeError:
            return "❌ 错误: 天气数据解析失败"
        except Exception as e:
            return f"❌ 错误: {str(e)}"

    def _parse_weather_data(self, data: dict, city: str) -> str:
        """解析天气数据"""
        try:
            current = data.get("current_condition", [{}])[0]

            if not current:
                return f"❌ 无法获取 {city} 的天气数据"

            # 提取天气信息
            temp = current.get("temp_C", "未知")
            weather = current.get("weatherDesc", "未知")
            humidity = current.get("humidity", "未知")
            wind = current.get("windspeedKmph", "未知")
            feels_like = current.get("FeelsLikeC", "未知")
            visibility = current.get("visibility", "未知")

            # 格式化输出
            result = f"🌤️ {city} 当前天气\n"
            result += f"━━━━━━━━━━━━━━━━━━━━\n"
            result += f"🌡️  温度: {temp}°C (体感 {feels_like}°C)\n"
            result += f"☁️  天气: {weather}\n"
            result += f"💧  湿度: {humidity}%\n"
            result += f"💨  风速: {wind} km/h\n"
            result += f"👁️  能见度: {visibility} km"

            return result

        except (KeyError, IndexError) as e:
            return f"❌ 天气数据解析失败: {str(e)}"

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
                        "description": "要查询的城市名称，如: 北京、上海、Shanghai",
                    }
                },
                "required": ["input_text"],
            },
        }


def quick_weather(city: str) -> str:
    """
    快速天气查询函数

    Args:
        city: 城市名称

    Returns:
        天气信息字符串
    """
    tool = Weather()
    return tool.run(city)


if __name__ == "__main__":
    # 测试
    print("=== 测试天气查询 ===")
    print(quick_weather("北京"))
    print()
    print(quick_weather("上海"))
