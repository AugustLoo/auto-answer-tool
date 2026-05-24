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
    prompt = f"""你是一个专业的答题助手。请分析以下题目，给出每道题的答案和简要解释。

要求：
1. 严格按照JSON数组格式输出，每个对象包含"题号"、"答案"、"解释"三个字段
2. 题号使用题目中的数字（如1,2,3）
3. 答案格式：
   - 单选题：选项字母（如"A"）
   - 多选题：选项字母组合（如"ACD"）
   - 判断题："正确"或"错误"
   - 填空题：填写内容
   - 简答题：简要回答要点
4. 解释用一句话说明理由

题目：
{questions_text}

请直接输出JSON数组，不要有其他文字："""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "你是一个专业的答题助手，严格按照要求输出JSON。"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1,
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
        f"题号{q['number']}（题型：{q['type']}）：{q['content']}"
        + (f"\n选项：{chr(10).join([opt['label'] + '. ' + opt['text'] for opt in q['options']])}" if q['options'] else "")
        for q in questions
    ])

    answers = call_deepseek_api(questions_text)
    if not answers:
        return None

    # 将答案映射到题目
    answer_map = {str(a.get("题号", i+1)): a for i, a in enumerate(answers)}
    result = []
    for i, q in enumerate(questions):
        q_num = str(q["number"])
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