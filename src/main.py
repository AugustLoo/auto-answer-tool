"""
桌面自动化答题系统 - 主入口
快捷键 Ctrl+Shift+Q 触发答题
快捷键 Ctrl+Shift+W 停止

用法：
    python main.py              # 启动后台监听
    python main.py --config     # 交互式设置API密钥
    python main.py --test       # 运行自检
"""
import os
import sys
import time
import traceback

# 确保当前目录在 path 中
CUR_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CUR_DIR)

from config import load_config, set_api_key, get_api_key
from capture import (
    capture_active_window, capture_text_from_window,
    get_clipboard_text, try_ocr
)
from parser import extract_questions, format_questions_for_ai, count_questions_by_type
from reasoning import analyze_questions, test_api_connection
from autofill import AutoFiller

# 全局停止标志
STOP_FLAG = False


def on_stop():
    """紧急停止回调"""
    global STOP_FLAG
    STOP_FLAG = True
    print("\n[STOP] 已触发紧急停止！")
    sys.exit(0)


def run_auto_answer():
    """执行一次自动答题流程"""
    global STOP_FLAG
    STOP_FLAG = False

    print("\n" + "=" * 50)
    print("[START] 自动答题已触发")
    print("=" * 50)

    # 第1步：捕获内容
    print("[STEP 1/4] 捕获当前窗口内容...")
    text = capture_text_from_window()
    if not text or len(text.strip()) < 10:
        print("[WARN] 剪贴板捕获失败，尝试OCR...")
        img = capture_active_window()
        text = try_ocr(img)
        if not text:
            print("[ERROR] OCR也未能识别到内容，请确保活动窗口有文字内容")
            return
    print(f"[OK] 捕获到 {len(text)} 个字符")

    if STOP_FLAG:
        return

    # 第2步：解析题目
    print("[STEP 2/4] 解析题目...")
    questions = extract_questions(text)
    if not questions:
        print("[WARN] 未识别到题目，将全文作为一道简答题处理")
        # 如果识别不到题号格式，把整段当一道题
        questions = [{
            "number": "1",
            "type": "essay",
            "content": text[:500],
            "options": [],
            "full_text": text[:500]
        }]
    counts = count_questions_by_type(questions)
    print(f"[OK] 识别到 {len(questions)} 道题: {counts}")

    if STOP_FLAG:
        return

    # 第3步：AI推理
    print("[STEP 3/4] AI推理中...")
    result = analyze_questions(questions)
    if result is None:
        print("[ERROR] AI推理失败，请检查API密钥和网络")
        return

    # 显示推理结果
    for q in result:
        ans = q.get("answer", "?")
        exp = q.get("explanation", "")
        print(f"  第{q['number']}题: {ans} | {exp}")

    if STOP_FLAG:
        return

    # 第4步：自动填写
    print("[STEP 4/4] 自动填写中，请勿移动鼠标...")
    cfg = load_config()
    filler = AutoFiller(fill_delay=cfg.get("fill_delay", 0.3))
    filler.fill_answers(result)

    print("[DONE] 答题完成！")


def start_hotkey_listener():
    """启动全局快捷键监听"""
    try:
        import keyboard
    except ImportError:
        print("[ERROR] 请安装 keyboard 模块: pip install keyboard")
        return

    cfg = load_config()
    hotkey_start = cfg.get("hotkey_start", "ctrl+shift+q")
    hotkey_stop = cfg.get("hotkey_stop", "ctrl+shift+w")

    print(f"[INFO] 快捷键监听已启动")
    print(f"  开始答题: {hotkey_start}")
    print(f"  紧急停止: {hotkey_stop}")
    print(f"  按 Ctrl+C 退出程序")

    keyboard.add_hotkey(hotkey_stop, on_stop)
    keyboard.add_hotkey(hotkey_start, run_auto_answer)

    try:
        keyboard.wait()  # 阻塞等待
    except KeyboardInterrupt:
        print("\n[INFO] 退出程序")
    finally:
        keyboard.unhook_all()


def interactive_config():
    """交互式设置API密钥"""
    print("\n配置 API 密钥")
    print("-" * 30)
    current_key = get_api_key()
    if current_key:
        masked = current_key[:8] + "****" + current_key[-4:] if len(current_key) > 12 else "****"
        print(f"当前密钥: {masked}")

    print("\n请输入 DeepSeek API Key（可直接回车保持现状）:")
    new_key = input("> ").strip()
    if new_key:
        set_api_key(new_key)
        print(f"[OK] API密钥已保存")
        ok, msg = test_api_connection()
        if ok:
            print(f"[OK] {msg}")
        else:
            print(f"[WARN] {msg}")
    else:
        print("[INFO] 未修改")


def run_self_test():
    """运行自检"""
    print("\n自检程序")
    print("=" * 50)

    checks = []

    # 1. 模块导入
    try:
        from capture import capture_screenshot, capture_active_window, capture_text_from_window
        checks.append(("模块导入", True, "所有模块正常"))
    except Exception as e:
        checks.append(("模块导入", False, str(e)))

    # 2. 配置文件
    try:
        cfg = load_config()
        checks.append(("配置文件", True, f"config.json 正常"))
    except Exception as e:
        checks.append(("配置文件", False, str(e)))

    # 3. API密钥
    key = get_api_key()
    if key:
        checks.append(("API密钥", True, "已设置"))
    else:
        checks.append(("API密钥", False, "未设置，请运行 python main.py --config"))

    # 4. API连接
    if key:
        ok, msg = test_api_connection()
        checks.append(("API连接", ok, msg))
    else:
        checks.append(("API连接", False, "跳过（无密钥）"))

    # 5. 键盘监听
    try:
        import keyboard
        checks.append(("键盘监听", True, "keyboard模块正常"))
    except ImportError:
        checks.append(("键盘监听", False, "未安装keyboard"))

    # 6. 截屏
    try:
        img = capture_active_window()
        checks.append(("屏幕截图", True, f"尺寸 {img.size}"))
    except Exception as e:
        checks.append(("屏幕截图", False, str(e)))

    # 打印结果
    print()
    for name, ok, msg in checks:
        status = "✓" if ok else "✗"
        print(f"  [{status}] {name}: {msg}")

    all_ok = all(c[1] for c in checks)
    print(f"\n{'全部通过' if all_ok else '存在失败项，请检查'}")
    return all_ok


if __name__ == "__main__":
    print("桌面自动化答题系统 v1.0")
    print("=" * 50)

    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == "--config":
            interactive_config()
        elif arg == "--test":
            run_self_test()
        else:
            print(f"未知参数: {arg}")
            print("用法: python main.py [--config | --test]")
    else:
        # 先检查配置
        key = get_api_key()
        if not key:
            print("[WARN] 未设置API密钥")
            answer = input("是否现在设置？(y/n): ").strip().lower()
            if answer in ("y", "yes"):
                interactive_config()
            else:
                print("[INFO] 可稍后运行 python main.py --config 设置")
            key = get_api_key()

        if key:
            start_hotkey_listener()
        else:
            print("[ERROR] 需要API密钥才能启动，请运行 python main.py --config")
            sys.exit(1)