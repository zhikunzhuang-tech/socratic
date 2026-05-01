"""颜色、通用工具函数"""
import re
from pathlib import Path

class Color:
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"

DATA_DIR = Path.home() / "socratic" / "data"


def latex_to_plain(text: str) -> str:
    """将 LaTeX 格式转为终端可读的纯文本"""
    if not text:
        return text

    # 1) \frac{a}{b} → a/b (先用简单的正则，复杂嵌套可能不完美但够用)
    text = re.sub(r'\\frac\{([^}]+)\}\{([^}]+)\}', r'\1/\2', text)
    # 处理 \dfrac（和 \frac 一样）
    text = re.sub(r'\\dfrac\{([^}]+)\}\{([^}]+)\}', r'\1/\2', text)

    # 2) \sqrt[n]{a} → n√(a)
    text = re.sub(r'\\sqrt\[([^}]+)\]\{([^}]+)\}', r'\1√(\2)', text)
    # 3) \sqrt{a} → √(a)
    text = re.sub(r'\\sqrt\{([^}]+)\}', r'√(\1)', text)

    # 4) 上标: x^{2} → x², x^{3} → x³ 等
    superscripts = {'2': '²', '3': '³', '4': '⁴', '5': '⁵',
                    '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹',
                    '+': '⁺', '-': '⁻', '(': '⁽', ')': '⁾',
                    'n': 'ⁿ', 'i': 'ⁱ'}
    def _replace_sup(m):
        inner = m.group(1)
        # 如果全是数字，逐字符转上标
        if inner.isdigit():
            return ''.join(superscripts.get(c, c) for c in inner)
        # 如果是简单的表达式，用 ^() 表示
        if len(inner) <= 4:
            result = ''
            for c in inner:
                result += superscripts.get(c, c)
            return result
        return f'^({inner})'
    text = re.sub(r'\^\{([^}]+)\}', _replace_sup, text)
    # x^2 → x²（不带花括号的简单上标）
    text = re.sub(r'\^(\d+)', lambda m: ''.join(superscripts.get(c, c) for c in m.group(1)), text)

    # 5) 下标: x_{2} → x₂  (简化处理)
    text = re.sub(r'\_\{([^}]+)\}', r'_\1', text)

    # 6) 常用希腊字母
    greek = {
        r'\alpha': 'α', r'\beta': 'β', r'\gamma': 'γ',
        r'\delta': 'δ', r'\theta': 'θ', r'\lambda': 'λ',
        r'\pi': 'π', r'\sigma': 'σ', r'\omega': 'ω',
        r'\Delta': 'Δ', r'\Theta': 'Θ', r'\Pi': 'Π',
        r'\Sigma': 'Σ', r'\Omega': 'Ω',
    }
    for latex, plain in greek.items():
        text = text.replace(latex, plain)

    # 7) 数学符号
    symbols = {
        r'\cdot': '·', r'\times': '×', r'\div': '÷',
        r'\rightarrow': '→', r'\Rightarrow': '⇒',
        r'\leftarrow': '←', r'\Leftarrow': '⇐',
        r'\infty': '∞', r'\partial': '∂',
        r'\leq': '≤', r'\geq': '≥', r'\neq': '≠',
        r'\approx': '≈', r'\equiv': '≡',
        r'\subset': '⊂', r'\supset': '⊃',
        r'\subseteq': '⊆', r'\supseteq': '⊇',
        r'\in': '∈', r'\notin': '∉',
        r'\cup': '∪', r'\cap': '∩',
        r'\sin': 'sin', r'\cos': 'cos', r'\tan': 'tan',
        r'\log': 'log', r'\ln': 'ln', r'\lim': 'lim',
        r'\sum': '∑', r'\prod': '∏', r'\int': '∫',
        r'\angle': '∠', r'\perp': '⊥',
        r'\triangle': '△', r'\cong': '≅', r'\sim': '∼',
        r'\pm': '±', r'\circ': '°',
    }
    for latex, plain in symbols.items():
        text = text.replace(latex, plain)

    # 8) 清理可能残留的花括号（如单纯的分组 {x}）
    text = re.sub(r'\{([^}]+)\}', r'\1', text)

    # 9) 清理多余空格
    text = re.sub(r' +', ' ', text)
    return text.strip()


def normalize_answer(text: str) -> str:
    """归一化用户输入"""
    text = text.strip()
    text = text.replace("＝", "=")
    text = text.replace("（", "(").replace("）", ")")
    text = text.replace("。", "").replace("，", ",")
    text = text.replace(" ", "")
    return text.lower()


def answer_matches(user_ans: str, problem: dict) -> bool:
    """模糊匹配答案"""
    user = normalize_answer(user_ans)
    if not user:
        return False
    candidates = [problem["answer"]] + problem.get("alternatives", [])
    for cand in candidates:
        if user == normalize_answer(cand):
            return True
    # 模糊匹配：用户答案包含核心关键词，或核心答案包含用户输入
    for cand in candidates:
        norm = normalize_answer(cand)
        if len(norm) > 2 and (norm in user or user in norm):
            return True
    for cand in candidates:
        norm = normalize_answer(cand)
        if re.match(r"^-?\d+\.?\d*$", norm) and re.match(r"^-?\d+\.?\d*$", user):
            if abs(float(norm) - float(user)) < 0.01:
                return True
    return False


def get_socratic_hint(problem: dict, wrong_answer: str, attempt: int) -> str | None:
    """获取苏格拉底式引导提示"""
    normalized_wrong = normalize_answer(wrong_answer)
    for wrong_pattern, hint in problem.get("common_errors", {}).items():
        if normalize_answer(wrong_pattern) == normalized_wrong:
            if hint:
                return f"🤔 {hint}"
    hints = problem.get("socratic_hints", [])
    hint_idx = min(attempt - 1, len(hints) - 1)
    if hint_idx >= 0 and hint_idx < len(hints):
        return f"💡 {hints[hint_idx]}"
    return None
