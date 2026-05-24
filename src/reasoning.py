"""AI推理模块 - 调用DeepSeek API分析题目并生成答案"""
import json
import time
import requests
from typing import List, Dict, Optional
from config import get_api_key


def call_deepseek_api(questions_text: str) -> Optional[List[Dict]]:
    """
    调用DeepSeek API分析题目。
    返回格式: [{"题号": 1, "答案": "B", "解释": "..."}, ...]
    """
    api_key = get_api_key()
    if not api_key:
        print("[ERROR] 未设置API密钥，请在config.json中配置api_key")
        return None

    # 构造Prompt
    prompt = f"""You are an expert quiz solver. Your task is to answer each question with 100% accuracy. Follow these rules strictly:

---RULES---
1. Output a JSON array. Each object MUST have: "题号", "答案", "解释". "题号" must be ONLY the number (e.g. "1", "2"), NOT "Q1".
2. READ EVERY OPTION CAREFULLY. Do NOT guess. Eliminate wrong options first, then select the best one.
3. For single choice: output exactly ONE letter (e.g. "B").
4. For multiple choice: output combined letters with NO spaces (e.g. "ACD").
5. For True/False or 判断题: "True"/"False" for English, "正确"/"错误" for Chinese.
6. For fill-in-the-blank: output ONLY the missing word/phrase, nothing extra.
7. For essay/short answer: 2-4 precise sentences.
8. For math: think step-by-step, then output the final answer using ^ for exponents, sqrt() for roots.
9. "解释" must be ONE sentence explaining WHY the answer is correct. Do NOT restate the question.

---QUESTIONS---
{questions_text}

Output ONLY the JSON array. No markdown, no extra text:"""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "You are an expert quiz solver. Read every option carefully. Eliminate wrong answers before selecting. Never guess. Output ONLY valid JSON. Every answer must be factually correct."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0,
        "max_tokens": 2000
    }

    try:
        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        response.raise_for_status()
        result = response.json()
        content = result["choices"][0]["message"]["content"].strip()

        # 提取JSON部分（可能包含markdown代码块）
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        answers = json.loads(content)
        if not isinstance(answers, list):
            answers = [answers]
        return answers

    except json.JSONDecodeError as e:
        print(f"[ERROR] JSON解析失败: {e}")
        print(f"原始内容: {content[:200]}")
        return None
    except requests.exceptions.Timeout:
        print("[ERROR] API请求超时")
        return None
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] API请求失败: {e}")
        return None
    except Exception as e:
        print(f"[ERROR] 未知错误: {e}")
        return None


def analyze_questions(questions: List[Dict]) -> Optional[List[Dict]]:
    """
    分析题目列表，返回带答案的题目列表。
    每个题目对象添加"answer"和"explanation"字段。
    """
    if not questions:
        return []

    questions_text = "\n".join([
        f"Q{q['number']} [{q['type']}]: {q['content']}"
        + (f"\nOptions: {chr(10).join([opt['label'] + '. ' + opt['text'] for opt in q['options']])}" if q['options'] else "")
        for q in questions
    ])

    answers = call_deepseek_api(questions_text)
    if not answers:
        return None

    # 将答案映射到题目（兼容 "1" 和 "Q1" 两种题号格式）
    import re
    def _normalize_num(s):
        return re.sub(r'^[Qq]', '', str(s))
    answer_map = {}
    for i, a in enumerate(answers):
        key = _normalize_num(a.get("题号", i+1))
        answer_map[key] = a
    result = []
    for i, q in enumerate(questions):
        q_num = _normalize_num(q["number"])
        ans = answer_map.get(q_num) or answer_map.get(str(i+1))
        if ans:
            q_copy = q.copy()
            q_copy["answer"] = ans.get("答案", "")
            q_copy["explanation"] = ans.get("解释", "")
            result.append(q_copy)
        else:
            # 没有对应答案，保留原题
            result.append(q)

    return result


def test_api_connection():
    """测试API连接是否正常"""
    api_key = get_api_key()
    if not api_key:
        return False, "未设置API密钥"

    # 简单测试题
    test_questions = [{
        "number": "1",
        "type": "single",
        "content": "中国的首都是哪个城市？",
        "options": [{"label": "A", "text": "上海"}, {"label": "B", "text": "北京"}, {"label": "C", "text": "广州"}],
        "full_text": "1. 中国的首都是哪个城市？\nA. 上海\nB. 北京\nC. 广州"
    }]

    result = analyze_questions(test_questions)
    if result and result[0].get("answer"):
        return True, f"连接成功，测试答案: {result[0]['answer']}"
    else:
        return False, "API调用失败，请检查密钥和网络"