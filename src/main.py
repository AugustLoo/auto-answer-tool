"""
桌面自动化答题系统 - 主入口
快捷键 Ctrl+CapsLock 触发：截图 → AI分析 → 屏幕显示答案
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
import pyautogui
import pyperclip

# 全局停止标志
STOP_FLAG = False


def on_stop():
    """紧急停止回调"""
    global STOP_FLAG
    STOP_FLAG = True
    print("\n[STOP] 已触发紧急停止！")
    sys.exit(0)


def show_answers_overlay(questions_with_answers):
    """在屏幕上显示答案窗口（悬浮置顶，不抢焦点）"""
    import tkinter as tk
    import tkinter.font as tkfont

    root = tk.Tk()
    root.title("Answer")
    root.attributes("-topmost", True)
    root.attributes("-alpha", 0.92)
    root.overrideredirect(True)
    # 放在屏幕右下角
    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()
    win_w, win_h = 480, min(600, 80 + len(questions_with_answers) * 52)
    root.geometry(f"{win_w}x{win_h}+{screen_w - win_w - 20}+{screen_h - win_h - 80}")

    # 黑色半透明背景，白色文字
    frame = tk.Frame(root, bg="#1e1e2e", bd=2, relief="ridge")
    frame.pack(fill="both", expand=True)

    # 标题栏
    title_font = tkfont.Font(family="Microsoft YaHei", size=11, weight="bold")
    title = tk.Label(frame, text="Answer", bg="#2d2d44", fg="#cdd6f4", font=title_font, pady=4)
    title.pack(fill="x")

    # 可滚动的答案区域
    canvas = tk.Canvas(frame, bg="#1e1e2e", highlightthickness=0)
    scrollbar = tk.Scrollbar(frame, orient="vertical", command=canvas.yview)
    scrollable = tk.Frame(canvas, bg="#1e1e2e")
    scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=scrollable, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    answer_font = tkfont.Font(family="Consolas", size=10)
    explain_font = tkfont.Font(family="Microsoft YaHei", size=9)

    for q in questions_with_answers:
        num = q.get("number", "?")
        ans = q.get("answer", "?")
        exp = q.get("explanation", "")
        q_type = q.get("type", "")

        row = tk.Frame(scrollable, bg="#1e1e2e", pady=2)
        row.pack(fill="x", padx=8)

        # 题号 + 答案（高亮）
        type_tag = ""
        if q_type == "essay":
            type_tag = "[Essay]"
        elif q_type == "math" or q_type == "essay":
            type_tag = "[Math]"

        q_text = f"Q{num} {type_tag}"
        tk.Label(row, text=q_text, bg="#1e1e2e", fg="#89b4fa", font=answer_font, width=14, anchor="w").pack(side="left")

        # 答案
        ans_color = "#a6e3a1"  # 绿色
        ans_display = ans if len(ans) <= 60 else ans[:57] + "..."
        tk.Label(row, text=ans_display, bg="#1e1e2e", fg=ans_color, font=answer_font, wraplength=280).pack(side="left", padx=(4, 0))

        # 解释（灰色小字）
        if exp:
            exp_row = tk.Frame(scrollable, bg="#1e1e2e")
            exp_row.pack(fill="x", padx=22)
            tk.Label(exp_row, text=exp, bg="#1e1e2e", fg="#6c7086", font=explain_font,
                     wraplength=440, justify="left", anchor="w").pack(anchor="w")

    # 关闭按钮
    close_btn = tk.Button(frame, text="Close (Esc)", bg="#45475a", fg="#cdd6f4", relief="flat",
                          command=root.destroy, font=tkfont.Font(size=9))
    close_btn.pack(pady=4)
    root.bind("<Escape>", lambda e: root.destroy())

    # 3秒后自动关闭
    root.after(15000, root.destroy)
    root.mainloop()


def run_auto_answer():
    """截图 → AI分析 → 屏幕显示答案"""
    global STOP_FLAG
    STOP_FLAG = False

    print("\n" + "=" * 50)
    print("[START] Screenshot & Analyze")
    print("=" * 50)

    # Step 1: Capture
    print("[1/3] Capturing screen content...")
    text = capture_text_from_window()
    if not text or len(text.strip()) < 10:
        print("[WARN] Clipboard empty, trying OCR...")
        img = capture_active_window()
        text = try_ocr(img)
        if not text:
            print("[ERROR] No text detected. Make sure the quiz window is active.")
            return
    print(f"[OK] {len(text)} chars captured")

    if STOP_FLAG:
        return

    # Step 2: Parse & AI
    print("[2/3] AI analyzing...")
    questions = extract_questions(text)
    if not questions:
        questions = [{
            "number": "1", "type": "essay",
            "content": text[:500], "options": [], "full_text": text[:500]
        }]
    counts = count_questions_by_type(questions)
    print(f"[OK] {len(questions)} questions: {counts}")

    if STOP_FLAG:
        return

    result = analyze_questions(questions)
    if result is None:
        print("[ERROR] AI analysis failed")
        return

    # Print to console
    for q in result:
        print(f"  Q{q['number']}: {q.get('answer', '?')}  |  {q.get('explanation', '')}")

    # Step 3: Show overlay
    print("[3/3] Displaying answers on screen...")
    show_answers_overlay(result)

    print("[DONE] Answers displayed. Press Esc to close.")


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
    print("Desktop Quiz Assistant v2.0 (Screenshot → AI → Display)")
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