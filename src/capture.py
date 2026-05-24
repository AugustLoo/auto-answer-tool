"""内容捕获模块 - 截屏OCR 和 剪贴板文本获取"""
import time
import pyautogui
import pyperclip
import mss
import mss.tools
from PIL import Image


def capture_screenshot():
    """截取当前主显示器全屏，返回 PIL Image"""
    with mss.mss() as sct:
        monitor = sct.monitors[1]  # 主显示器
        sct_img = sct.grab(monitor)
        return Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")


def capture_active_window():
    """截取当前活动窗口，返回 PIL Image"""
    try:
        win = pyautogui.getActiveWindow()
        if win is None:
            return capture_screenshot()
        left, top, width, height = win.left, win.top, win.width, win.height
        # 边界保护
        left = max(0, left)
        top = max(0, top)
        img = pyautogui.screenshot(region=(left, top, width, height))
        return img
    except Exception:
        return capture_screenshot()


def get_clipboard_text():
    """获取剪贴板文本内容"""
    try:
        text = pyperclip.paste()
        return text if isinstance(text, str) else str(text)
    except Exception:
        return ""


def capture_text_from_window():
    """
    通过全选+复制获取当前窗口文本。
    适用于浏览器、Word、记事本等支持 Ctrl+A / Ctrl+C 的窗口。
    返回文本内容。
    """
    # 先清空剪贴板
    pyperclip.copy("")
    time.sleep(0.1)

    # 全选
    pyautogui.hotkey("ctrl", "a")
    time.sleep(0.15)

    # 复制
    pyautogui.hotkey("ctrl", "c")
    time.sleep(0.2)

    # 读取剪贴板
    text = get_clipboard_text()
    return text


def try_ocr(image, ocr_engine=None):
    """
    使用 OCR 识别图片中的文本。
    如果 OCR 引擎未加载，尝试加载 PaddleOCR。
    返回识别的文本。
    """
    if ocr_engine is not None:
        result = ocr_engine.ocr(image)
        if result is None or len(result) == 0 or result[0] is None:
            return ""
        texts = [line[1][0] for line in result[0] if line is not None]
        return "\n".join(texts)

    # 尝试加载 PaddleOCR
    try:
        from paddleocr import PaddleOCR
        engine = PaddleOCR(use_angle_cls=True, lang="ch", show_log=False)
        result = engine.ocr(image)
        if result is None or len(result) == 0 or result[0] is None:
            return ""
        texts = [line[1][0] for line in result[0] if line is not None]
        return "\n".join(texts)
    except ImportError:
        return "[OCR] PaddleOCR 未安装，请运行: pip install paddlepaddle paddleocr"
    except Exception as e:
        return f"[OCR] 识别失败: {e}"