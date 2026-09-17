@echo off
echo ========================================
echo   智能文件助手 - 安装向导
echo ========================================
echo.

echo [1/3] 检查 Python...
python --version
if errorlevel 1 (
    echo 错误: 未找到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)

echo.
echo [2/3] 安装依赖包...
pip install -r requirements.txt
if errorlevel 1 (
    echo 警告: 部分包安装失败，尝试继续...
)

echo.
echo [3/3] 创建配置文件...
if not exist .env (
    copy .env.example .env
    echo 已创建 .env 配置文件
    echo 请用记事本打开 .env 文件，填入你的 API Key
) else (
    echo .env 文件已存在，跳过创建
)

echo.
echo ========================================
echo   安装完成！
echo ========================================
echo.
echo 下一步：
echo   1. 编辑 .env 文件，填入你的 API Key
echo   2. 把文件放到 data\knowledge_base 文件夹
echo   3. 运行: streamlit run app.py
echo.
pause
