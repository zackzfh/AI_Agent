import os
import sys
import json
import asyncio
from pathlib import Path
from typing import Optional, List

from langchain_classic.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage

from config import get_llm, KNOWLEDGE_BASE_DIR, DB_TYPE
from tools.file_tools import get_file_tools
from tools.db_tools import get_db_tools
from tools.arc_tools import get_arc_tools

SYSTEM_PROMPT = f"""你是一个智能助手，能够帮助用户完成以下任务：

1. **读取本地文件**：你可以读取知识库中的 Excel、Word、TXT、CSV 文件。
2. **搜索文件**：你可以按关键词搜索文件名或文件内容。
3. **查询数据库**：你可以查看数据库表结构、执行 SQL 查询。
4. **SAP ABAP 开发**：你可以读取/搜索/创建/激活 SAP ABAP 对象，执行 SQL 查询，查看依赖关系。

## 使用规则
- 当用户问到文件相关的问题时，先用 list_knowledge_files 看有哪些文件，再读取相关文件。
- 当用户问到数据相关的问题时，先用 list_database_tables 看有哪些表，再执行查询。
- 当用户问到 SAP/ABAP 相关问题时，使用 SAP 工具（sap_read, sap_search 等）。
- 回答要简洁、清晰，使用中文。
- 如果用户的问题不明确，主动询问澄清。

## 知识库位置
{KNOWLEDGE_BASE_DIR}

## 数据库类型
{DB_TYPE}
"""

def create_agent():
    """创建并返回配置好的 AI Agent"""
    llm = get_llm()
    tools = get_file_tools() + get_db_tools() + get_arc_tools()

    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="chat_history", optional=True),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_tool_calling_agent(llm, tools, prompt)

    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=10,
    )

    return agent_executor

def chat(agent_executor, user_input: str) -> str:
    """发送消息给 Agent 并获取回复"""
    try:
        result = agent_executor.invoke({"input": user_input})
        return result.get("output", "抱歉，我无法处理这个请求。")
    except Exception as e:
        return f"处理出错: {str(e)}"

if __name__ == "__main__":
    print("正在初始化 AI Agent...")
    agent = create_agent()
    print("AI Agent 准备就绪！")
    print("输入 'quit' 退出\n")

    while True:
        user_input = input("你: ").strip()
        if user_input.lower() in ['quit', 'exit', 'q', '退出']:
            print("再见！")
            break
        if not user_input:
            continue

        response = chat(agent, user_input)
        print(f"\n助手: {response}\n")
