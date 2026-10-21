from mcp.server.fastmcp import FastMCP
import os
import requests

mcp = FastMCP("LocalOfficeAssistant")

@mcp.tool()
def get_weather(city: str) -> str:
    """获取指定城市的天气。参数 city 为城市中文名，如 '北京'、'广州'。"""
    try:
        url = f"https://wttr.in/{city}?format=%C+%t+湿度:%h+风速:%w&lang=zh"
        resp = requests.get(url, timeout=5)
        return f"{city} 实时天气：{resp.text.strip()}"
    except Exception as e:
        return f"查询天气失败: {str(e)}"

@mcp.tool()
def save_file(filename: str, content: str) -> str:
    """在当前工作目录的 workspace 文件夹中保存或创建文件。
    filename: 文件名（如 plan.md 或 report.txt）
    content: 文件具体内容
    """
    try:
        work_dir = "./workspace"
        os.makedirs(work_dir, exist_ok=True)
        path = os.path.join(work_dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"成功保存文件至 {path}，内容共 {len(content)} 字符。"
    except Exception as e:
        return f"写入文件失败: {str(e)}"


@mcp.tool()
def list_files() -> str:
    """查看 workspace 目录下的所有文件列表。"""
    work_dir = "./workspace"
    os.makedirs(work_dir, exist_ok=True)
    files = os.listdir(work_dir)
    return f"当前已有文件: {', '.join(files)}" if files else "当前目录为空。"

if __name__ == "__main__":
    mcp.run(transport="stdio")