"""
配置管理模块 - 读取 .env 文件中的设置
你一般不需要修改这个文件，只需要修改 .env 文件即可
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env 配置文件
load_dotenv()

# ===== 路径设置 =====
BASE_DIR = Path(__file__).parent
KNOWLEDGE_BASE_DIR = BASE_DIR / "data" / "knowledge_base"
DB_DIR = BASE_DIR / "data" / "databases"

# 自动创建文件夹（如果不存在）
KNOWLEDGE_BASE_DIR.mkdir(parents=True, exist_ok=True)
DB_DIR.mkdir(parents=True, exist_ok=True)

# ===== 服务器设置 =====
SERVER_HOST = os.getenv("SERVER_HOST", "localhost")
SERVER_PORT = int(os.getenv("SERVER_PORT", "8501"))

# ===== 大模型设置 =====
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "deepseek")  # deepseek 或 openai
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")   # 模型名称
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))  # 创造性 0-1
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "4096"))     # 最大回复长度

# API 密钥
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# ===== 数据库设置 =====
DB_TYPE = os.getenv("DB_TYPE", "sqlite")  # sqlite, mysql, postgresql
DB_FILE = os.getenv("DB_FILE", str(DB_DIR / "default.db"))

# ===== 文件支持类型 =====
SUPPORTED_FILE_TYPES = {
    ".txt": "文本文件",
    ".csv": "CSV表格",
    ".xlsx": "Excel表格",
    ".xls": "Excel表格(旧版)",
    ".docx": "Word文档",
}


def get_llm():
    """根据配置创建大模型实例"""
    if LLM_PROVIDER == "deepseek":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=LLM_MODEL,
            temperature=LLM_TEMPERATURE,
            max_tokens=LLM_MAX_TOKENS,
            openai_api_key=DEEPSEEK_API_KEY,
            openai_api_base="https://api.deepseek.com",
        )
    elif LLM_PROVIDER == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=LLM_MODEL,
            temperature=LLM_TEMPERATURE,
            max_tokens=LLM_MAX_TOKENS,
            openai_api_key=OPENAI_API_KEY,
        )
    else:
        raise ValueError(f"不支持的大模型: {LLM_PROVIDER}，请选择 deepseek 或 openai")


def get_database_url() -> str:
    """获取数据库连接地址"""
    if DB_TYPE == "sqlite":
        return f"sqlite:///{DB_FILE}"
    elif DB_TYPE == "mysql":
        db_user = os.getenv("DB_USER", "")
        db_pass = os.getenv("DB_PASSWORD", "")
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = os.getenv("DB_PORT", "3306")
        db_name = os.getenv("DB_NAME", "")
        return f"mysql+pymysql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    elif DB_TYPE == "postgresql":
        db_user = os.getenv("DB_USER", "")
        db_pass = os.getenv("DB_PASSWORD", "")
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = os.getenv("DB_PORT", "5432")
        db_name = os.getenv("DB_NAME", "")
        return f"postgresql+psycopg2://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    else:
        raise ValueError(f"不支持的数据库类型: {DB_TYPE}")


def print_config():
    """打印当前配置（隐藏敏感信息）"""
    print("=" * 50)
    print("  🤖 AI Agent 配置信息")
    print("=" * 50)
    print(f"  大模型: {LLM_PROVIDER} ({LLM_MODEL})")
    print(f"  知识库: {KNOWLEDGE_BASE_DIR}")
    print(f"  数据库: {DB_TYPE}")
    if DB_TYPE == "sqlite":
        print(f"  数据库文件: {DB_FILE}")
    print(f"  网页地址: http://{SERVER_HOST}:{SERVER_PORT}")
    print("=" * 50)
