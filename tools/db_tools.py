"""
数据库访问工具 - 让 AI 能够查询数据库
默认使用 SQLite（无需安装额外软件）
"""
from typing import Optional, Type
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from config import get_database_url, DB_TYPE


# ============================
# 定义工具的输入参数
# ============================

class SQLQueryInput(BaseModel):
    """执行 SQL 查询的参数"""
    sql: str = Field(description="要执行的 SQL 查询语句（仅支持 SELECT 查询）")


# ============================
# 工具1：列出数据库中的表
# ============================

class ListTablesTool(BaseTool):
    """列出数据库中的所有表"""
    name: str = "list_database_tables"
    description: str = "列出数据库中所有的表名和表结构。当用户想知道数据库里有什么表时使用。"

    def _run(self) -> str:
        try:
            from sqlalchemy import create_engine, inspect

            db_url = get_database_url()
            engine = create_engine(db_url)
            inspector = inspect(engine)
            tables = inspector.get_table_names()

            if not tables:
                return "数据库中没有表。"

            result = f"📊 数据库类型: {DB_TYPE}\n共有 {len(tables)} 张表:\n\n"

            for table_name in tables:
                columns = inspector.get_columns(table_name)
                result += f"📋 表: {table_name}\n"
                for col in columns:
                    col_type = str(col['type'])
                    nullable = "" if col.get('nullable', True) else " (必填)"
                    result += f"   • {col['name']}  [{col_type}]{nullable}\n"
                result += "\n"

            return result

        except Exception as e:
            return f"❌ 连接数据库出错: {str(e)}\n请检查 .env 文件中的数据库配置。"


# ============================
# 工具2：执行 SQL 查询
# ============================

class RunSQLTool(BaseTool):
    """执行 SQL 查询"""
    name: str = "run_sql_query"
    description: str = "在数据库中执行 SQL 查询语句（仅支持 SELECT 查询，不会修改数据）。"
    args_schema: Type[BaseModel] = SQLQueryInput

    def _run(self, sql: str) -> str:
        # 安全检查：只允许 SELECT 查询
        sql_upper = sql.strip().upper()
        if not sql_upper.startswith("SELECT"):
            return "❌ 安全限制：只允许执行 SELECT 查询语句。"

        # 阻止危险关键词
        dangerous = ["DROP", "DELETE", "TRUNCATE", "UPDATE", "INSERT", "ALTER", "CREATE"]
        for keyword in dangerous:
            if keyword in sql_upper:
                return f"❌ 安全限制：不允许执行包含 {keyword} 的语句。"

        try:
            from sqlalchemy import create_engine, text
            import pandas as pd

            db_url = get_database_url()
            engine = create_engine(db_url)

            with engine.connect() as conn:
                df = pd.read_sql(text(sql), conn)

            if df.empty:
                return "查询结果为空（没有匹配的数据）。"

            result = f"✅ 查询成功，返回 {len(df)} 行数据:\n"
            result += f"列名: {', '.join(df.columns.tolist())}\n\n"

            # 显示前50行
            display_rows = min(50, len(df))
            result += df.head(display_rows).to_string(index=False)

            if len(df) > display_rows:
                result += f"\n\n... 还有 {len(df) - display_rows} 行"

            return result

        except Exception as e:
            return f"❌ SQL 执行出错: {str(e)}\n\n请检查 SQL 语法是否正确。"


# ============================
# 工具3：查看表中的示例数据
# ============================

class PreviewTableInput(BaseModel):
    """预览表数据的参数"""
    table_name: str = Field(description="要预览的表名")
    limit: Optional[int] = Field(default=10, description="显示的行数，默认10行")


class PreviewTableTool(BaseTool):
    """预览表中的数据"""
    name: str = "preview_table"
    description: str = "快速预览数据库中某个表的前几行数据，帮助了解表的内容。"
    args_schema: Type[BaseModel] = PreviewTableInput

    def _run(self, table_name: str, limit: int = 10) -> str:
        # 安全检查：表名只能包含字母、数字、下划线
        if not all(c.isalnum() or c == '_' for c in table_name):
            return f"❌ 表名不合法: {table_name}"

        sql = f"SELECT * FROM {table_name} LIMIT {min(limit, 100)}"

        try:
            from sqlalchemy import create_engine, text
            import pandas as pd

            db_url = get_database_url()
            engine = create_engine(db_url)

            with engine.connect() as conn:
                df = pd.read_sql(text(sql), conn)

            result = f"📋 表 {table_name} 的前 {len(df)} 行数据:\n"
            result += f"列名: {', '.join(df.columns.tolist())}\n\n"
            result += df.to_string(index=False)

            return result

        except Exception as e:
            return f"❌ 预览表出错: {str(e)}"


# ============================
# 获取所有数据库工具
# ============================

def get_db_tools():
    """返回所有数据库相关工具的列表"""
    return [ListTablesTool(), RunSQLTool(), PreviewTableTool()]
