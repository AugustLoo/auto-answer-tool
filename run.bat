@echo off
echo 桌面自动化答题系统
echo.

REM 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] 未找到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

REM 检查依赖
pip list | findstr "keyboard mss pillow pyautogui pyperclip requests" >nul
if errorlevel 1 (
    echo 正在安装依赖...
    pip install keyboard mss pillow pyautogui pyperclip requests -q
    if errorlevel 1 (
        echo [ERROR] 依赖安装失败
        pause
        exit /b 1
    )
    echo 依赖安装完成
)

REM 运行程序
echo 启动程序...
echo 按 Ctrl+Shift+Q 开始答题
echo 按 Ctrl+Shift+W 紧急停止
echo 按 Ctrl+C 退出
echo.
python main.py