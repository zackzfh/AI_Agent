# 🤖 智能文件助手 (AI Agent)

一个能读取本地文件（Excel、Word、TXT、CSV）并连接数据库的 AI 助手。

---

## 🚀 快速开始（3步搞定）

### 第1步：安装依赖

在 VS Code 终端中输入：

```bash
pip install -r requirements.txt
```

### 第2步：配置 API Key

1. 复制 `.env.example` 并重命名为 `.env`（去掉 `.example` 后缀）
2. 用记事本打开 `.env`，把 `你的DeepSeek密钥` 替换成你的真实密钥

> 💡 去 https://platform.deepseek.com 注册并获取免费 API Key

### 第3步：启动程序

**方式A - 网页界面（推荐）：**
```bash
streamlit run app.py
```

**方式B - 命令行：**
```bash
python app.py
```

---

## 📁 使用方法

1. 把你的文件（Excel、Word、TXT、CSV）放到 `data/knowledge_base` 文件夹
2. 启动程序后，在聊天框里问问题
3. AI 会自动找到相关文件并回答

### 示例问题
- "知识库里有哪些文件？"
- "帮我看看销售数据.xlsx 的内容"
- "搜索包含'利润'的文件"
- "数据库里有哪些表？"
- "查询最近一个月的销售记录"

---

## 🗄️ 数据库配置

默认使用 **SQLite**（不需要安装额外软件，开箱即用）。

如果需要连接 MySQL 或 PostgreSQL：
1. 在 `.env` 文件中修改 `DB_TYPE` 为 `mysql` 或 `postgresql`
2. 填写对应的连接信息（主机、端口、用户名、密码等）
3. 运行 `pip install pymysql` (MySQL) 或 `pip install psycopg2-binary` (PostgreSQL)

---

## 📂 项目结构

```
AI_Agent/
├── app.py              # 启动入口（网页/命令行）
├── config.py           # 配置读取
├── agent.py            # AI Agent 核心逻辑
├── requirements.txt    # Python 依赖
├── .env.example        # 配置模板
│
├── data/
│   ├── knowledge_base/ # ← 在这里放你的文件！
│   └── databases/      # 数据库存储位置
│
└── tools/
    ├── file_tools.py   # 文件读取工具
    └── db_tools.py     # 数据库查询工具
```

---

## ❓ 常见问题

**Q: 提示 'pip' 不是内部命令？**
A: 试试 `python -m pip install -r requirements.txt`

**Q: Excel 文件读取失败？**
A: 确保文件是 .xlsx 格式，旧版 .xls 可能需要 `pip install xlrd`

**Q: 怎么获取 DeepSeek API Key？**
A: 访问 https://platform.deepseek.com 注册账号，在"API Keys"页面创建

**Q: 连接数据库报错？**
A: 检查 `.env` 文件中的数据库配置是否正确，确保数据库服务已启动
