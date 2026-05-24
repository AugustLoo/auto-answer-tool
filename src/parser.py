"""题目解析模块 - 从文本中提取题目、识别题型、解析选项"""
import re


def extract_questions(text):
    """
    从文本中切分出每道题。
    识别模式：
    - "1. xxx" / "1、xxx" / "1) xxx" 开头的题目
    - "第1题" 开头的题目
    - "一、" 开头的中文题号
    返回 list of dict: [{"number": "1", "type": "single", "content": "...", "options": [...], "full_text": "..."}]
    """
    if not text or not text.strip():
        return []

    # 按常见题号模式切分
    # 匹配: 1.  1)  1、  (1)  第1题  一、
    pattern = r'(?:^|\n)\s*((?:\(?\d+[\.\)、]\s*)|(?:第\d+题)|(?:[一二三四五六七八九十]+、))'
    parts = re.split(pattern, text)

    questions = []
    i = 1
    while i < len(parts):
        number_raw = parts[i].strip()
        body = parts[i + 1].strip() if i + 1 < len(parts) else ""
        i += 2

        if not body:
            continue

        number = _clean_number(number_raw)
        q_type, content, options = _parse_question_body(body)
        full_text = f"{number_raw} {body}"

        questions.append({
            "number": number,
            "type": q_type,
            "content": content,
            "options": options,
            "full_text": full_text,
        })

    return questions


def _clean_number(raw):
    """清理题号，返回字符串数字"""
    m = re.search(r'(\d+)', raw)
    if m:
        return m.group(1)
    # 中文数字映射
    cn_map = {"一": "1", "二": "2", "三": "3", "四": "4", "五": "5",
              "六": "6", "七": "7", "八": "8", "九": "9", "十": "10"}
    for cn, num in cn_map.items():
        if cn in raw:
            return num
    return raw.strip()


def _parse_question_body(body):
    """
    解析题目正文：识别题型和选项。
    返回 (type, content, options)
    type: "single" / "multi" / "judge" / "fill" / "essay"
    """
    q_type = _detect_question_type(body)
    content, options = _extract_options(body, q_type)
    return q_type, content, options


def _detect_question_type(body):
    """根据关键词和选项格式判断题型"""
    # 判断题
    if re.search(r'(正确|错误|对|错|√|×|T|F|true|false|YES|NO|是|否)', body, re.IGNORECASE):
        # 有选项形式的可能是选择题而非判断题，进一步判断
        pass

    # 多选题：有 "多选" 关键词，或选项标记允许选多个
    if re.search(r'(多选|多选题|不定项|多项选择)', body):
        return "multi"

    # 填空题：有下划线或括号空位
    if re.search(r'[_]{2,}|（\s+）|（\s*）|\b___\b', body):
        return "fill"

    # 简答题：有"简述""请回答""论述""分析""解释"等关键词
    if re.search(r'(简述|简答|请回答|论述|分析|解释|说明|谈谈|讨论|总结|概述)', body):
        return "essay"

    # 判断题：有"正确/错误"或"对/错"选项
    if re.search(r'[Aa]\s*[\.\、]?\s*正确|[Bb]\s*[\.\、]?\s*错误', body):
        return "judge"
    if re.search(r'[Aa]\s*[\.\、]?\s*对|[Bb]\s*[\.\、]?\s*错', body):
        return "judge"

    # 默认选择题
    return "single"


def _extract_options(body, q_type):
    """
    提取选项。返回 (content, options)
    content: 去掉选项后的题目正文
    options: [{"label": "A", "text": "..."}, ...]
    """
    # 选项模式: A. xxx  /  A) xxx  /  A、xxx
    opt_pattern = r'\n?\s*([A-Ha-h])\s*[\.\)、]\s*(.+?)(?=\n?\s*[A-Ha-h]\s*[\.\)、]|\n?\s*$|$)'
    matches = list(re.finditer(opt_pattern, body, re.DOTALL))

    if not matches:
        return body.strip(), []

    # 找到第一个选项的位置，之前为题目内容
    first_match_start = matches[0].start()
    content = body[:first_match_start].strip()

    options = []
    for m in matches:
        label = m.group(1).upper()
        text = m.group(2).strip()
        options.append({"label": label, "text": text})

    return content, options


def format_questions_for_ai(questions):
    """将题目列表格式化为发送给AI的文本"""
    lines = []
    for q in questions:
        lines.append(f"题号{q['number']}（{_type_name(q['type'])}）：{q['content']}")
        for opt in q.get("options", []):
            lines.append(f"  {opt['label']}. {opt['text']}")
        lines.append("")
    return "\n".join(lines)


def _type_name(q_type):
    """题型中文名"""
    names = {
        "single": "单选题",
        "multi": "多选题",
        "judge": "判断题",
        "fill": "填空题",
        "essay": "简答题",
    }
    return names.get(q_type, "未知题型")


def count_questions_by_type(questions):
    """统计各题型数量"""
    counts = {}
    for q in questions:
        t = q["type"]
        counts[t] = counts.get(t, 0) + 1
    return counts