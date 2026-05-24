"""内容捕获模块 - 截屏OCR 和 剪贴板文本获取"""
import time
import pyautogui
import pyperclip
import mss
import mss.tools
from PIL import Image

# 安全设置
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1


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
    # 先释放所有修饰键（热键触发时可能残留Ctrl/Shift按下状态）
    for key in ["ctrl", "shift", "alt", "win"]:
        pyautogui.keyUp(key)
    time.sleep(0.3)

    # 点击屏幕中心，确保焦点在答题窗口
    screen_width, screen_height = pyautogui.size()
    pyautogui.click(screen_width // 2, screen_height // 2)
    time.sleep(0.2)

    # 清空剪贴板
    pyperclip.copy("")
    time.sleep(0.1)

    # 全选
    pyautogui.keyDown("ctrl")
    pyautogui.press("a")
    pyautogui.keyUp("ctrl")
    time.sleep(0.2)

    # 复制
    pyautogui.keyDown("ctrl")
    pyautogui.press("c")
    pyautogui.keyUp("ctrl")
    time.sleep(0.3)

    # 读取剪贴板
    text = get_clipboard_text()

    # 如果剪贴板为空，重试一次
    if not text or len(text.strip()) < 5:
        pyperclip.copy("")
        time.sleep(0.1)
        pyautogui.keyDown("ctrl")
        pyautogui.press("a")
        pyautogui.keyUp("ctrl")
        time.sleep(0.2)
        pyautogui.keyDown("ctrl")
        pyautogui.press("c")
        pyautogui.keyUp("ctrl")
        time.sleep(0.3)
        text = get_clipboard_text()

    return text


def try_ocr(image, ocr_engine=None):
    """
    使用 OCR 识别图片中的文本。
    优先使用 EasyOCR，兼容旧版 PaddleOCR。
    返回识别的文本。
    """
    # 尝试 EasyOCR
    try:
        import easyocr
        import numpy as np
        reader = easyocr.Reader(["ch_sim", "en"], gpu=False, verbose=False)
        img_array = np.array(image)
        result = reader.readtext(img_array, detail=0)
        return "\n".join(result) if result else ""
    except ImportError:
        # 回退到 PaddleOCR
        try:
            from paddleocr import PaddleOCR
            engine = PaddleOCR(use_angle_cls=True, lang="ch", show_log=False)
            result = engine.ocr(image)
            if result is None or len(result) == 0 or result[0] is None:
                return ""
            texts = [line[1][0] for line in result[0] if line is not None]
            return "\n".join(texts)
        except ImportError:
            return "[OCR] 未安装 OCR 引擎，请运行: pip install easyocr"
        except Exception as e:
            return f"[OCR] 识别失败: {e}"
    except Exception as e:
        return f"[OCR] 识别失败: {e}"