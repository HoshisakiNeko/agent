import asyncio
import json
import os
from openai import OpenAI
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# 1. 配置 DeepSeek API
DEEPSEEK_API_KEY = "sk-3e3aa219c7124363a4b3961a2686cf29"  # 填入你的 key
llm_client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)


async def main():
    # 2. 启动并连接本地的 MCP Server 子进程
    server_params = StdioServerParameters(
        command="python",
        args=["agent_server.py"],
        env=os.environ.copy()
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # 3. 从 MCP Server 动态获取所有可用工具
            mcp_tools = await session.list_tools()
            print(f"已就绪！成功挂载 {len(mcp_tools.tools)} 个工具。")

            # 4. 转换 MCP 工具协议为 DeepSeek / OpenAI 兼容格式
            openai_tools = [
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.inputSchema
                    }
                }
                for tool in mcp_tools.tools
            ]

            messages = [
                {"role": "system", "content": "你是一个高效的个人办公智能体。你可以根据用户需求自主调用工具完成操作。"}
            ]

            print("\n=== AI Agent 已启动 (输入 'exit' 退出) ===")

            while True:
                user_input = input("\n用户: ").strip()
                if not user_input or user_input.lower() == "exit":
                    break

                messages.append({"role": "user", "content": user_input})

                # 5. Agent 思考循环 (ReAct: Think -> Act -> Observe)
                while True:
                    response = llm_client.chat.completions.create(
                        model="deepseek-chat",
                        messages=messages,
                        tools=openai_tools,
                        tool_choice="auto"
                    )
                    msg = response.choices[0].message
                    messages.append(msg)

                    # 判断大模型是否要求调用工具
                    if msg.tool_calls:
                        for tool_call in msg.tool_calls:
                            fn_name = tool_call.function.name
                            fn_args = json.loads(tool_call.function.arguments)

                            print(f"\n[智能体决策] 正在调用工具: {fn_name}({fn_args}) ...")

                            # 执行 MCP 工具调用
                            result = await session.call_tool(fn_name, fn_args)
                            tool_output = result.content[0].text
                            print(f"[执行结果] -> {tool_output}")

                            # 将工具执行结果回传给大模型
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": tool_output
                            })
                        # 继续循环，让 DeepSeek 根据工具返回的结果组织下一轮回复
                    else:
                        # 模型不需要调工具了，直接输出最终人话回答
                        print(f"\nAI: {msg.content}")
                        break


if __name__ == "__main__":
    asyncio.run(main())