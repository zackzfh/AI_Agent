"""
ARC-1 SAP 工具集 — LangChain 工具封装
将 ARC-1 MCP 工具暴露为 LangChain Tool，供 Agent 调用
"""
from typing import Optional
from langchain_core.tools import tool
from .arc_client import ArcMCPClient, create_arc_client_from_env

# 全局客户端实例
_arc_client: Optional[ArcMCPClient] = None


def get_arc_client() -> Optional[ArcMCPClient]:
    """获取或创建 ARC-1 客户端"""
    global _arc_client
    if _arc_client is None:
        _arc_client = create_arc_client_from_env()
        if _arc_client:
            try:
                _arc_client.start()
            except Exception as e:
                print(f"[ARC-1] 启动失败: {e}")
                _arc_client = None
    return _arc_client


@tool
def sap_read(
    read_type: str,
    object_name: str,
    method_name: str = "",
    version: str = "active",
    grep: str = "",
    context_lines: int = 0,
) -> str:
    """
    读取 SAP ABAP 对象的源代码或元数据。

    参数:
    - read_type: 读取类型，如 PROG(程序), CLAS(类), INTF(接口), TABL(表), VIEW, DDLS(CDS视图), DCLS(访问控制), SRVB(服务绑定), SKTD(知识转移文档), MSAG(消息类), VERSIONS(版本历史)
    - object_name: 对象名称
    - method_name: (可选) 类的方法名，只读取该方法
    - version: active(激活版本), inactive(未激活版本), auto(自动)
    - grep: (可选) 正则表达式，只返回匹配的源代码行
    - context_lines: (可选) grep 上下文行数
    """
    client = get_arc_client()
    if not client:
        return "错误: SAP 系统未配置。请在 .env 中设置 SAP_URL, SAP_USER, SAP_PASSWORD"

    args = {"type": read_type, "name": object_name, "version": version}
    if method_name:
        args["method"] = method_name
    if grep:
        args["grep"] = grep
        if context_lines:
            args["contextLines"] = context_lines

    result = client.call_tool("SAPRead", args)
    return _format_result(result)


@tool
def sap_search(
    query: str,
    search_type: str = "object",
    object_types: str = "",
    max_results: int = 20,
) -> str:
    """
    在 SAP 系统中搜索 ABAP 对象或全文搜索源代码。

    参数:
    - query: 搜索关键词
    - search_type: object(对象搜索) 或 fulltext(全文搜索)
    - object_types: (可选) 限制对象类型，如 CLAS,PROG,TABL
    - max_results: 最大返回数量
    """
    client = get_arc_client()
    if not client:
        return "错误: SAP 系统未配置"

    args = {"query": query, "searchType": search_type, "maxResults": max_results}
    if object_types:
        args["objectTypes"] = object_types

    result = client.call_tool("SAPSearch", args)
    return _format_result(result)


@tool
def sap_write(
    object_type: str,
    object_name: str,
    source: str,
    transport: str = "",
    package: str = "$TMP",
) -> str:
    """
    创建或更新 SAP ABAP 对象（需要 SAP_ALLOW_WRITES=true）。

    参数:
    - object_type: 对象类型 (PROG, CLAS, INTF, TABL, DDLS 等)
    - object_name: 对象名称
    - source: ABAP 源代码
    - transport: (可选) 传输请求号
    - package: 目标包 (默认 $TMP)
    """
    client = get_arc_client()
    if not client:
        return "错误: SAP 系统未配置"

    args = {
        "type": object_type,
        "name": object_name,
        "source": source,
        "package": package,
    }
    if transport:
        args["transport"] = transport

    result = client.call_tool("SAPWrite", args)
    return _format_result(result)


@tool
def sap_activate(
    object_type: str,
    object_name: str,
) -> str:
    """
    激活 SAP ABAP 对象。

    参数:
    - object_type: 对象类型 (PROG, CLAS, INTF 等)
    - object_name: 对象名称
    """
    client = get_arc_client()
    if not client:
        return "错误: SAP 系统未配置"

    result = client.call_tool("SAPActivate", {
        "type": object_type,
        "name": object_name,
    })
    return _format_result(result)


@tool
def sap_query(
    sql: str,
    max_rows: int = 100,
) -> str:
    """
    执行 ABAP SQL 查询（需要 SAP_ALLOW_FREE_SQL=true）。

    参数:
    - sql: ABAP SQL 语句 (SELECT ... FROM ...)
    - max_rows: 最大返回行数
    """
    client = get_arc_client()
    if not client:
        return "错误: SAP 系统未配置"

    result = client.call_tool("SAPQuery", {
        "sql": sql,
        "maxRows": max_rows,
    })
    return _format_result(result)


@tool
def sap_context(
    context_type: str,
    object_type: str,
    object_name: str,
) -> str:
    """
    获取 SAP 对象的上下文信息（依赖关系、引用等）。

    参数:
    - context_type: deps(依赖), usages(引用), impact(CDS影响), structure(表结构)
    - object_type: 对象类型
    - object_name: 对象名称
    """
    client = get_arc_client()
    if not client:
        return "错误: SAP 系统未配置"

    result = client.call_tool("SAPContext", {
        "action": context_type,
        "type": object_type,
        "name": object_name,
    })
    return _format_result(result)


@tool
def sap_navigate(
    action: str,
    object_type: str,
    object_name: str,
    line: int = 1,
) -> str:
    """
    SAP 代码导航（跳转定义、查找引用、代码补全）。

    参数:
    - action: definition(跳转定义), references(查找引用), completion(代码补全)
    - object_type: 对象类型
    - object_name: 对象名称
    - line: (可选) 行号，用于定位
    """
    client = get_arc_client()
    if not client:
        return "错误: SAP 系统未配置"

    result = client.call_tool("SAPNavigate", {
        "action": action,
        "type": object_type,
        "name": object_name,
        "line": line,
    })
    return _format_result(result)


def _format_result(result) -> str:
    """格式化 MCP 工具的返回结果"""
    if result is None:
        return "无结果"
    if isinstance(result, dict):
        if "error" in result:
            return f"错误: {result['error']}"
        # MCP content format
        if "content" in result:
            texts = []
            for item in result["content"]:
                if item.get("type") == "text":
                    texts.append(item["text"])
            return "\n".join(texts) if texts else str(result)
        return str(result)
    return str(result)


def get_arc_tools() -> list:
    """返回所有 ARC-1 工具（如果 SAP 已配置）"""
    from dotenv import load_dotenv
    import os
    load_dotenv()

    if not os.getenv("SAP_URL"):
        return []

    return [
        sap_read,
        sap_search,
        sap_write,
        sap_activate,
        sap_query,
        sap_context,
        sap_navigate,
    ]
