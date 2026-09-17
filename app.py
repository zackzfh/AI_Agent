"""
启动入口 - 运行此文件启动 AI Agent
方式1: python app.py  (命令行模式)
方式2: streamlit run app.py  (网页模式)
"""
import sys
from pathlib import Path

# 确保当前目录正确
sys.path.insert(0, str(Path(__file__).parent))


def run_cli():
    """命令行模式"""
    from agent import create_agent, chat
    from config import print_config

    print_config()
    print("\n正在启动 AI Agent...\n")

    agent = create_agent()

    print("=" * 50)
    print("  🤖 AI Agent 已就绪！")
    print("  输入你的问题开始对话")
    print("  输入 'quit' 或 '退出' 结束")
    print("=" * 50)
    print()

    while True:
        try:
            user_input = input("🧑 你: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见！")
            break

        if user_input.lower() in ['quit', 'exit', 'q', '退出']:
            print("👋 再见！")
            break

        if not user_input:
            continue

        response = chat(agent, user_input)
        print(f"\n🤖 助手: {response}\n")
        print("-" * 50)


def run_streamlit():
    """网页模式 - 使用 Streamlit"""
    import streamlit as st
    from agent import create_agent, chat
    from config import print_config, SERVER_HOST, SERVER_PORT

    st.set_page_config(
        page_title="🤖 智能文件助手",
        page_icon="🤖",
        layout="wide"
    )

    st.title("🤖 智能文件助手")
    st.caption("能读取本地文件（Excel、Word、TXT、CSV）并查询数据库的 AI 助手")

    # 侧边栏
    with st.sidebar:
        st.header("⚙️ 设置")
        st.info("配置请修改 .env 文件")
        st.info(f"当前监听: {SERVER_HOST}:{SERVER_PORT}")

        if st.button("🔄 重新加载 Agent"):
            st.session_state.pop("agent", None)
            st.success("Agent 已重新加载！")

        st.divider()
        st.header("📁 使用说明")
        st.markdown("""
        1. 把文件放到 `data/knowledge_base` 文件夹
        2. 在聊天框输入你的问题
        3. AI 会自动读取文件并回答

        **支持的文件格式：**
        - Excel (.xlsx)
        - Word (.docx)
        - 文本 (.txt)
        - CSV (.csv)
        """)

    # 初始化 Agent
    if "agent" not in st.session_state:
        with st.spinner("正在初始化 AI Agent..."):
            st.session_state.agent = create_agent()
        st.success("Agent 已就绪！")

    # 初始化聊天历史
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # 显示历史消息
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # 用户输入
    if prompt := st.chat_input("输入你的问题..."):
        # 显示用户消息
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # 获取 AI 回复
        with st.chat_message("assistant"):
            with st.spinner("正在思考..."):
                response = chat(st.session_state.agent, prompt)
                st.markdown(response)

        st.session_state.messages.append({"role": "assistant", "content": response})


# ============================
# 主入口
# ============================

if __name__ == "__main__":
    # 检查是否通过 streamlit 运行
    # streamlit 会设置特定的环境变量
    is_streamlit = "streamlit" in sys.modules or any("streamlit" in arg for arg in sys.argv)

    if is_streamlit:
        run_streamlit()
    else:
        run_cli()
