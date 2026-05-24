"""自动填写模块 - 根据答案模拟键盘鼠标输入"""
import time
import pyautogui
import pyperclip
from typing import List, Dict


class AutoFiller:
    def __init__(self, fill_delay: float = 0.3):
        self.fill_delay = fill_delay
        pyautogui.PAUSE = fill_delay
        # 安全保护
        pyautogui.FAILSAFE = True

    def fill_answers(self, questions: List[Dict]):
        """
        按顺序填写所有题目的答案。
        假设当前活动窗口就是答题界面。
        """
        if not questions:
            print("[INFO] 没有题目需要填写")
            return

        print(f"[INFO] 开始填写 {len(questions)} 道题...")
        time.sleep(0.5)

        # 点击窗口中心确保焦点在答题窗口
        screen_width, screen_height = pyautogui.size()
        pyautogui.click(screen_width // 2, screen_height // 2)
        time.sleep(0.3)

        for i, q in enumerate(questions):
            print(f"[INFO] 填写第{i+1}题: {q.get('answer', '无答案')}")
            self._fill_one_question(q)
            # 题间间隔
            time.sleep(0.5)

        print("[INFO] 所有题目填写完成")

    def _fill_one_question(self, question: Dict):
        """填写一道题"""
        q_type = question.get("type", "single")
        answer = question.get("answer", "")

        if not answer:
            print(f"[WARN] 第{question.get('number', '?')}题无答案，跳过")
            # 按Tab跳到下一题
            pyautogui.press("tab")
            return

        if q_type == "single":
            self._fill_single_choice(answer)
        elif q_type == "multi":
            self._fill_multi_choice(answer)
        elif q_type == "judge":
            self._fill_judgment(answer)
        elif q_type == "fill":
            self._fill_blank(answer)
        elif q_type == "essay":
            self._fill_essay(answer)
        else:
            print(f"[WARN] 未知题型 {q_type}，按Tab跳过")
            pyautogui.press("tab")

        time.sleep(self.fill_delay)

    def _fill_single_choice(self, answer: str):
        """单选题：先按数字键(1-4)，再按字母键(A-D)，确保覆盖不同网站的答题方式"""
        if not answer:
            return
        key = answer.strip()[0].upper()
        if key in "ABCDEFGH":
            # 先尝试数字键（如 A→1, B→2）
            num_key = str(ord(key) - ord("A") + 1)
            pyautogui.press(num_key)
            time.sleep(0.1)
            # 再尝试字母键
            pyautogui.press(key.lower())
        else:
            # 答案本身就是数字或文字
            pyautogui.press(str(answer))

    def _fill_multi_choice(self, answer: str):
        """多选题：依次按多个字母键"""
        if not answer:
            return
        for ch in answer.strip().upper():
            if ch in "ABCDEFGH":
                pyautogui.press(ch.lower())
                time.sleep(0.1)
            else:
                print(f"[WARN] 无效选项字母: {ch}")

    def _fill_judgment(self, answer: str):
        """判断题：根据答案选择正确/错误 (True/False, 正确/错误, Yes/No)"""
        ans_lower = answer.strip().lower()
        # True / 正确 / Yes
        if any(kw in ans_lower for kw in ["正确", "对", "true", "yes", "√", "t"]):
            pyautogui.press("a")  # Usually A=True
            pyautogui.press("1")  # Backup: press 1
        # False / 错误 / No
        elif any(kw in ans_lower for kw in ["错误", "错", "false", "no", "×", "f"]):
            pyautogui.press("b")  # Usually B=False
            pyautogui.press("2")  # Backup: press 2
        else:
            # Unknown judgment answer, paste it as text
            print(f"[WARN] 无法识别的判断题答案: {answer}，尝试粘贴")
            pyperclip.copy(answer)
            time.sleep(0.1)
            pyautogui.hotkey("ctrl", "v")

    def _fill_blank(self, answer: str):
        """填空题：粘贴答案文本"""
        if not answer:
            return
        # 先清空剪贴板
        pyperclip.copy("")
        time.sleep(0.1)
        # 复制答案到剪贴板
        pyperclip.copy(answer)
        time.sleep(0.1)
        # 粘贴
        pyautogui.hotkey("ctrl", "v")
        time.sleep(0.1)

    def _fill_essay(self, answer: str):
        """简答题：粘贴大段文本"""
        if not answer:
            return
        # 简答题可能有多行，用剪贴板粘贴
        pyperclip.copy("")
        time.sleep(0.1)
        pyperclip.copy(answer)
        time.sleep(0.1)
        pyautogui.hotkey("ctrl", "v")
        time.sleep(0.2)

    def test_fill(self):
        """测试填写功能（在安全位置）"""
        print("[TEST] 测试自动填写功能...")
        # 在屏幕右下角安全区域测试
        screen_width, screen_height = pyautogui.size()
        test_x = screen_width - 100
        test_y = screen_height - 100

        # 测试1：鼠标移动
        pyautogui.moveTo(test_x, test_y, duration=0.5)
        print("  鼠标移动 ✓")

        # 测试2：键盘输入
        pyautogui.click(test_x, test_y)
        pyautogui.write("test", interval=0.1)
        print("  键盘输入 ✓")

        # 测试3：剪贴板
        pyperclip.copy("剪贴板测试")
        text = pyperclip.paste()
        assert "剪贴板测试" in text
        print("  剪贴板 ✓")

        print("[TEST] 所有测试通过")
        return True


def simulate_typing(text: str, interval: float = 0.05):
    """模拟人工打字（逐字符输入）"""
    for char in text:
        pyautogui.write(char)
        time.sleep(interval)


def press_tab(times: int = 1):
    """按Tab键切换焦点"""
    for _ in range(times):
        pyautogui.press("tab")
        time.sleep(0.1)


def press_enter():
    """按回车键确认"""
    pyautogui.press("enter")
    time.sleep(0.2)