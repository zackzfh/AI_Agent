"""
ARC-1 MCP 客户端 — 连接 SAP ABAP 系统
通过 stdio JSON-RPC 与 ARC-1 MCP Server 通信
"""
import subprocess
import json
import threading
import time
import os
from typing import Any, Dict, Optional


class ArcMCPClient:
    """ARC-1 MCP Server 的 Python 客户端"""

    def __init__(
        self,
        sap_url: str,
        sap_user: str,
        sap_password: str,
        sap_client: str = "100",
        sap_language: str = "EN",
        allow_writes: bool = False,
        allow_data_preview: bool = False,
        allow_free_sql: bool = False,
        arc1_path: Optional[str] = None,
    ):
        self.sap_url = sap_url
        self.sap_user = sap_user
        self.sap_password = sap_password
        self.sap_client = sap_client
        self.sap_language = sap_language
        self.allow_writes = allow_writes
        self.allow_data_preview = allow_data_preview
        self.allow_free_sql = allow_free_sql

        # Find arc-1 binary
        if arc1_path:
            self.arc1_cmd = arc1_path
        else:
            # Try npx first, then local node_modules
            local_bin = os.path.join(os.path.dirname(__file__), "..", "node_modules", ".bin", "arc1")
            if os.path.exists(local_bin):
                self.arc1_cmd = local_bin
            else:
                self.arc1_cmd = "npx"

        self._process: Optional[subprocess.Popen] = None
        self._request_id = 0
        self._lock = threading.Lock()
        self._responses: Dict[int, Any] = {}
        self._response_events: Dict[int, threading.Event] = {}
        self._reader_thread: Optional[threading.Thread] = None
        self._tools: list = []

    def start(self):
        """启动 ARC-1 MCP Server (stdio 模式)"""
        cmd = [
            self.arc1_cmd,
        ]
        if self.arc1_cmd == "npx":
            cmd.append("arc-1")

        cmd.extend([
            "--url", self.sap_url,
            "--user", self.sap_user,
            "--password", self.sap_password,
            "--client", self.sap_client,
            "--language", self.sap_language,
            "--transport", "stdio",
            "--allow-writes", str(self.allow_writes).lower(),
            "--allow-data-preview", str(self.allow_data_preview).lower(),
            "--allow-free-sql", str(self.allow_free_sql).lower(),
        ])

        self._process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=False,  # binary mode for proper JSON handling
        )

        # Start reader thread
        self._reader_thread = threading.Thread(target=self._read_loop, daemon=True)
        self._reader_thread.start()

        # Initialize
        self._send_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "arc-python-client", "version": "1.0.0"}
        })

        # Send initialized notification
        self._send_notification("notifications/initialized", {})

        # Fetch tools list
        self._discover_tools()

    def _send_request(self, method: str, params: dict) -> Any:
        """发送 JSON-RPC 请求并等待响应"""
        with self._lock:
            self._request_id += 1
            req_id = self._request_id

        msg = {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": method,
            "params": params,
        }

        event = threading.Event()
        self._response_events[req_id] = event
        self._responses[req_id] = None

        raw = json.dumps(msg).encode("utf-8")
        content = f"Content-Length: {len(raw)}\r\n\r\n".encode("utf-8") + raw
        self._process.stdin.write(content)
        self._process.stdin.flush()

        # Wait for response (30s timeout)
        event.wait(timeout=30)
        return self._responses.pop(req_id, None)

    def _send_notification(self, method: str, params: dict):
        """发送 JSON-RPC 通知（无响应）"""
        msg = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
        }
        raw = json.dumps(msg).encode("utf-8")
        content = f"Content-Length: {len(raw)}\r\n\r\n".encode("utf-8") + raw
        self._process.stdin.write(content)
        self._process.stdin.flush()

    def _read_loop(self):
        """后台读取 MCP Server 的响应"""
        while self._process and self._process.poll() is None:
            try:
                # Read Content-Length header
                header = b""
                while True:
                    byte = self._process.stdout.read(1)
                    if not byte:
                        return
                    header += byte
                    if header.endswith(b"\r\n\r\n"):
                        break

                length_str = header.decode("utf-8").replace("Content-Length: ", "").strip()
                content_length = int(length_str)

                # Read body
                body = self._process.stdout.read(content_length)
                msg = json.loads(body.decode("utf-8"))

                # Route response
                if "id" in msg and msg["id"] in self._response_events:
                    self._responses[msg["id"]] = msg.get("result") or msg.get("error")
                    self._response_events[msg["id"]].set()

            except Exception as e:
                break

    def _discover_tools(self):
        """获取工具列表"""
        result = self._send_request("tools/list", {})
        if result and "tools" in result:
            self._tools = result["tools"]

    def get_tools_info(self) -> list:
        """返回所有可用工具的名称和描述"""
        return [
            {"name": t["name"], "description": t.get("description", "")}
            for t in self._tools
        ]

    def call_tool(self, tool_name: str, arguments: dict) -> Any:
        """调用 MCP 工具"""
        return self._send_request("tools/call", {
            "name": tool_name,
            "arguments": arguments,
        })

    def stop(self):
        """停止 MCP Server"""
        if self._process:
            self._process.terminate()
            self._process.wait(timeout=5)
            self._process = None


# ============================================================
# 便捷函数 — 从 .env 创建客户端
# ============================================================

def create_arc_client_from_env() -> Optional[ArcMCPClient]:
    """从环境变量创建 ARC-1 客户端"""
    from dotenv import load_dotenv
    load_dotenv()

    url = os.getenv("SAP_URL")
    user = os.getenv("SAP_USER")
    password = os.getenv("SAP_PASSWORD")

    if not all([url, user, password]):
        return None

    return ArcMCPClient(
        sap_url=url,
        sap_user=user,
        sap_password=password,
        sap_client=os.getenv("SAP_CLIENT", "100"),
        sap_language=os.getenv("SAP_LANGUAGE", "EN"),
        allow_writes=os.getenv("SAP_ALLOW_WRITES", "false").lower() == "true",
        allow_data_preview=os.getenv("SAP_ALLOW_DATA_PREVIEW", "false").lower() == "true",
        allow_free_sql=os.getenv("SAP_ALLOW_FREE_SQL", "false").lower() == "true",
    )
