"""问题缓存 — 管理 AI 生成题目的缓存 + 种子题"""
import json
import random as rnd
import subprocess as sp
import time
from pathlib import Path
from .utils import DATA_DIR, Color, latex_to_plain

CACHE_DIR = DATA_DIR / "cache"

SUBJECT_NAMES = {"math": "数学", "english": "英语", "physics": "物理", "chinese": "语文", "biology": "生物", "geography": "地理"}
SUBJECT_TAGS = {"math": "math", "english": "eng", "physics": "phy", "chinese": "chn", "biology": "bio", "geography": "geo"}


# ── 种子题（每个科目 5 道，冷启动 + 断网备用）────────────────
SEEDS = {
    "math": [
        {"id": "seed-math-1", "topic": "一元一次方程", "grade": "初一", "difficulty": 1,
         "question": "解方程：2x + 5 = 13", "answer": "x = 4", "alternatives": ["4"],
         "steps": ["移项：2x = 13 - 5", "合并：2x = 8", "x = 4"],
         "socratic_hints": ["等式两边同时减去几？", "2x = 8，两边除以几？", "x = 4"],
         "common_errors": {"9": "13-5=8，不是9", "3": "2×3+5=11≠13"},
         "tags": ["方程"], "concept_note": "等式两边同加减同乘除，保持平衡。"},
        {"id": "seed-math-2", "topic": "勾股定理", "grade": "初二", "difficulty": 2,
         "question": "直角三角形两条直角边分别为 3 和 4，斜边长是多少？", "answer": "5",
         "alternatives": ["5cm"],
         "steps": ["勾股定理：a²+b²=c²", "c² = 9 + 16 = 25", "c = 5"],
         "socratic_hints": ["直角三角形三边满足什么定理？", "a²+b²=c²，代入a=3,b=4", "√25=5"],
         "common_errors": {"7": "3+4=7？勾股定理是平方相加", "25": "25是c²，要开方"},
         "tags": ["几何"], "concept_note": "勾股定理：a²+b²=c²。"},
        {"id": "seed-math-3", "topic": "概率", "grade": "初三", "difficulty": 1,
         "question": "袋中有3个红球2个蓝球，摸到红球的概率？", "answer": "3/5",
         "alternatives": ["0.6", "60%"],
         "steps": ["总球数=5", "红球=3", "P=3/5"],
         "socratic_hints": ["概率 = 符合条件数 / 总数", "红球3个，总共几个？", "3/5"],
         "common_errors": {"2/5": "那是蓝球的概率", "3/2": "分子分母反了"},
         "tags": ["概率"], "concept_note": "P(A)=发生数/总数。"},
        {"id": "seed-math-4", "topic": "二次函数", "grade": "初三", "difficulty": 2,
         "question": "y = x² - 2x - 3 的顶点坐标是？", "answer": "(1, -4)",
         "alternatives": ["(1,-4)"],
         "steps": ["配方法：x²-2x+1-4", "(x-1)²-4", "顶点(1,-4)"],
         "socratic_hints": ["顶点式y=a(x-h)²+k，h和k是什么？", "x=-b/(2a)=1", "代入得y=-4"],
         "common_errors": {"(-1,-4)": "x-1对应x=1", "(1,3)": "-1-3=-4"},
         "tags": ["函数"], "concept_note": "顶点式y=a(x-h)²+k。"},
        {"id": "seed-math-5", "topic": "有理数运算", "grade": "初一", "difficulty": 1,
         "question": "计算：(-2)² - 2² = ?", "answer": "0", "alternatives": ["0"],
         "steps": ["(-2)²=4", "2²=4", "4-4=0"],
         "socratic_hints": ["(-2)²底数是-2还是2？", "(-2)²=(-2)×(-2)=4", "4-4=0"],
         "common_errors": {"-4": "(-2)²=4不是-4", "-8": "4-4=0"},
         "tags": ["运算"], "concept_note": "(-a)²=a²，-a²=-(a²)。"},
    ],
    "english": [
        {"id": "seed-eng-1", "topic": "主谓一致", "grade": "初一", "difficulty": 1,
         "question": "She ___ to school every day. (go/goes/going)", "answer": "goes",
         "alternatives": [],
         "steps": ["She是第三人称单数", "一般现在时加-s/es", "go→goes"],
         "socratic_hints": ["She是第几人称？", "第三人称单数，动词加什么？", "加-s：goes"],
         "common_errors": {"go": "She是第三人称单数", "going": "缺少be动词"},
         "tags": ["语法"], "concept_note": "三单主语+动词-s/es。"},
        {"id": "seed-eng-2", "topic": "过去时", "grade": "初二", "difficulty": 2,
         "question": "Yesterday, I ___ (go) to the park.", "answer": "went",
         "alternatives": [],
         "steps": ["Yesterday表示过去", "go的过去式是不规则变化", "go→went"],
         "socratic_hints": ["Yesterday表示什么时态？", "一般过去时。go的过去式是？", "went"],
         "common_errors": {"go": "yesterday是过去", "goed": "go是不规则动词"},
         "tags": ["语法"], "concept_note": "go→went（不规则变化）。"},
        {"id": "seed-eng-3", "topic": "冠词", "grade": "初一", "difficulty": 1,
         "question": "I have ___ apple. (a/an/the)", "answer": "an", "alternatives": [],
         "steps": ["apple以元音音素开头", "元音前用an", "an apple"],
         "socratic_hints": ["apple发音以什么开头？", "元音音素前用an", "an apple"],
         "common_errors": {"a": "apple发音以元音开头", "the": "第一次泛指用an"},
         "tags": ["词汇"], "concept_note": "元音音素前用an。"},
        {"id": "seed-eng-4", "topic": "介词搭配", "grade": "初一", "difficulty": 2,
         "question": "He is good ___ basketball. (at/in/on/with)", "answer": "at",
         "alternatives": [],
         "steps": ["固定搭配：be good at", "表示擅长某事"],
         "socratic_hints": ["be good ___ doing sth，填什么？", "固定搭配be good at", "at"],
         "common_errors": {"in": "不是be good in", "on": "be good at是固定搭配"},
         "tags": ["词汇"], "concept_note": "be good at = 擅长。"},
        {"id": "seed-eng-5", "topic": "疑问句", "grade": "初一", "difficulty": 1,
         "question": "___ you a student? (be动词填空)", "answer": "Are",
         "alternatives": ["are"],
         "steps": ["主语是you", "you对应are", "句首大写：Are"],
         "socratic_hints": ["主语you对应哪个be动词？", "are，句首大写。", "Are you a student?"],
         "common_errors": {"Is": "you搭配are", "Am": "am搭配I"},
         "tags": ["语法"], "concept_note": "you用are，句首大写。"},
    ],
    "physics": [
        {"id": "seed-phy-1", "topic": "重力", "grade": "初二", "difficulty": 1,
         "question": "质量5kg，g=10N/kg，重力是多少？", "answer": "50",
         "alternatives": ["50N"],
         "steps": ["G=mg", "G=5×10=50N"],
         "socratic_hints": ["重力公式是什么？", "G=mg", "5×10=50N"],
         "common_errors": {"5": "G=mg=5×10", "10": "5×10=50"},
         "tags": ["力学"], "concept_note": "G=mg。"},
        {"id": "seed-phy-2", "topic": "串联电路", "grade": "初三", "difficulty": 1,
         "question": "R₁=2Ω，R₂=3Ω串联，总电阻？", "answer": "5",
         "alternatives": ["5Ω"],
         "steps": ["串联：R=R₁+R₂", "R=2+3=5Ω"],
         "socratic_hints": ["串联怎么算？", "直接相加", "2+3=5Ω"],
         "common_errors": {"1.2": "那是并联的算法", "6": "2+3=5"},
         "tags": ["电路"], "concept_note": "串联：R=R₁+R₂。"},
        {"id": "seed-phy-3", "topic": "光速", "grade": "初二", "difficulty": 1,
         "question": "光在真空中的速度约为多少m/s？", "answer": "3×10⁸",
         "alternatives": ["3e8", "300000000"],
         "steps": ["c≈3×10⁸ m/s"],
         "socratic_hints": ["光速大约是？", "3后面8个零", "3×10⁸ m/s"],
         "common_errors": {"340": "340是声速", "3×10³": "太慢了"},
         "tags": ["光"], "concept_note": "c≈3×10⁸m/s。"},
        {"id": "seed-phy-4", "topic": "密度", "grade": "初二", "difficulty": 2,
         "question": "1g/cm³等于多少kg/m³？", "answer": "1000",
         "alternatives": ["1000kg/m³"],
         "steps": ["1g=10⁻³kg", "1cm³=10⁻⁶m³", "10⁻³/10⁻⁶=1000"],
         "socratic_hints": ["1g等于多少kg？1cm³等于多少m³？", "10⁻³/10⁻⁶", "1000"],
         "common_errors": {"1": "要乘1000", "0.001": "方向反了"},
         "tags": ["密度"], "concept_note": "1g/cm³=1000kg/m³。"},
        {"id": "seed-phy-5", "topic": "并联电路", "grade": "初三", "difficulty": 3,
         "question": "R₁=3Ω，R₂=6Ω并联，总电阻？", "answer": "2",
         "alternatives": ["2Ω"],
         "steps": ["1/R=1/3+1/6=1/2", "R=2Ω"],
         "socratic_hints": ["并联公式是什么？", "1/R=1/R₁+1/R₂", "1/3+1/6=1/2→R=2"],
         "common_errors": {"9": "那是串联的算法", "4.5": "并联总电阻比每个都小"},
         "tags": ["电路"], "concept_note": "并联：1/R=1/R₁+1/R₂。"},
    ],
    "chinese": [
        {"id": "seed-chn-1", "topic": "古诗文默写", "grade": "初一", "difficulty": 1,
         "question": "补全诗句：举头望明月，___。", "answer": "低头思故乡",
         "alternatives": [],
         "steps": ["李白《静夜思》", "床前明月光，疑是地上霜", "举头望明月，低头思故乡"],
         "socratic_hints": ["作者是李白，诗题是？", "《静夜思》，诗人低头想到了什么？", "故乡"],
         "common_errors": {"疑是地上霜": "那是第二句"},
         "tags": ["古诗", "李白"], "concept_note": "《静夜思》李白。"},
        {"id": "seed-chn-2", "topic": "文言文字词", "grade": "初一", "difficulty": 1,
         "question": "「温故而知新」中「故」的意思是？\nA.故事 B.旧的 C.故意 D.所以", "answer": "B",
         "alternatives": ["b", "旧的"],
         "steps": ["出自《论语》", "「温故」温习旧知识", "「故」=旧的知识"],
         "socratic_hints": ["「温」是温习，那「故」可能是什么？", "温习什么才能知新？", "旧的知识"],
         "common_errors": {"A": "不是温习故事", "C": "故意讲不通"},
         "tags": ["文言文", "论语"], "concept_note": "故：旧的知识。"},
        {"id": "seed-chn-3", "topic": "修辞手法", "grade": "初一", "difficulty": 1,
         "question": "「飞流直下三千尺」用了什么修辞？", "answer": "夸张",
         "alternatives": [],
         "steps": ["出自李白《望庐山瀑布》", "「三千尺」明显夸大", "夸张手法"],
         "socratic_hints": ["三千尺是真的吗？", "故意夸大就是夸张", "是夸张"],
         "common_errors": {"比喻": "主要手法是夸张", "拟人": "不是拟人"},
         "tags": ["修辞", "李白"], "concept_note": "夸张：故意言过其实。"},
        {"id": "seed-chn-4", "topic": "文学常识", "grade": "初二", "difficulty": 1,
         "question": "「但愿人长久，千里共婵娟」出自谁的作品？", "answer": "苏轼",
         "alternatives": ["苏东坡", "水调歌头"],
         "steps": ["苏轼《水调歌头》", "写于中秋", "「婵娟」指月亮"],
         "socratic_hints": ["作者是宋代哪位词人？", "苏轼。", "对，是苏轼。"],
         "common_errors": {"李白": "李白是唐代", "辛弃疾": "这首是苏轼的"},
         "tags": ["文学常识", "宋词"], "concept_note": "苏轼《水调歌头》。"},
        {"id": "seed-chn-5", "topic": "成语", "grade": "初一", "difficulty": 2,
         "question": "「画蛇添足」比喻什么？", "answer": "做多余的事",
         "alternatives": ["多此一举"],
         "steps": ["画蛇比赛，先画完的人给蛇添脚", "蛇没有脚", "比喻做了多余的事"],
         "socratic_hints": ["蛇本来有脚吗？", "那给蛇画脚是不是多余？", "对，做多余的事。"],
         "common_errors": {"多管闲事": "强调做了多余的事"},
         "tags": ["成语"], "concept_note": "画蛇添足：做多余的事。"},
    ],
    "biology": [
        {"id": "seed-bio-1", "topic": "生物特征", "grade": "初二", "difficulty": 1,
         "question": "生物最基本的特征是什么？", "answer": "新陈代谢",
         "alternatives": ["代谢"],
         "steps": ["生物需要营养、能呼吸、能排出废物", "这些都是新陈代谢的表现", "新陈代谢是生物最基本的特征"],
         "socratic_hints": ["生物和/or非生物的根本区别是什么？", "生物需要营养和能量来维持生命，这个过程叫什么？", "新陈代谢"],
         "common_errors": {"繁殖": "繁殖也是特征，但不是最基本的", "生长": "生长是代谢的结果"},
         "tags": ["生物", "会考"], "concept_note": "新陈代谢是生物最基本的特征。"},
        {"id": "seed-bio-2", "topic": "生态系统", "grade": "初二", "difficulty": 2,
         "question": "生态系统由哪两部分组成？", "answer": "生物部分和非生物部分",
         "alternatives": ["生物和非生物"],
         "steps": ["生物部分：植物、动物、微生物", "非生物部分：阳光、空气、水、土壤等", "两者缺一不可"],
         "socratic_hints": ["一个池塘里除了鱼和水草还有什么？", "水、阳光、空气这些属于什么？", "生物部分和非生物部分"],
         "common_errors": {"生物": "还有非生物部分", "生产者消费者": "那是生物部分的分类"},
         "tags": ["生物", "会考"], "concept_note": "生态系统=生物部分+非生物部分。"},
    ],
    "geography": [
        {"id": "seed-geo-1", "topic": "地图", "grade": "初二", "difficulty": 1,
         "question": "地图三要素是什么？", "answer": "比例尺、方向、图例和注记",
         "alternatives": ["比例尺 方向 图例和注记"],
         "steps": ["比例尺表示图上距离与实际距离之比", "方向：上北下南左西右东", "图例和注记帮助读图"],
         "socratic_hints": ["看地图需要知道哪些基本要素？", "地图上怎么知道实际距离？怎么辨认方向？", "比例尺、方向、图例和注记"],
         "common_errors": {"比例尺": "还有方向和图例", "经线纬线": "经线纬线不是地图三要素"},
         "tags": ["地理", "会考"], "concept_note": "地图三要素：比例尺、方向、图例和注记。"},
        {"id": "seed-geo-2", "topic": "地球", "grade": "初二", "difficulty": 2,
         "question": "地球的形状是什么？", "answer": "两极稍扁、赤道略鼓的不规则球体",
         "alternatives": ["不规则球体", "两极稍扁赤道略鼓"],
         "steps": ["地球不是完美的球体", "两极稍微扁平", "赤道部分略微鼓起"],
         "socratic_hints": ["地球是完美的球形吗？", "从卫星照片看地球两极和赤道有什么不同？", "两极稍扁、赤道略鼓的不规则球体"],
         "common_errors": {"圆形": "地球是球体不是圆形", "球形": "不是完美的球形"},
         "tags": ["地理", "会考"], "concept_note": "地球：两极稍扁、赤道略鼓的不规则球体。"},
    ],
}


# ── 缓存管理 ──────────────────────────────────────────────────
def cache_path(subject: str) -> Path:
    return CACHE_DIR / f"{subject}.json"


def load_cache(subject: str) -> list:
    """加载缓存题目，缓存为空则用种子题初始化"""
    path = cache_path(subject)
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            pass
    # 首次使用：用种子题初始化
    seeds = SEEDS.get(subject, [])
    save_cache(subject, seeds)
    return seeds


def save_cache(subject: str, problems: list):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path(subject).write_text(json.dumps(problems, ensure_ascii=False, indent=2))


def get_problems(subject: str, count: int = 1, exclude_ids: set | None = None, topic: str | None = None) -> list:
    """获取题目：先从缓存取，不够就 AI 生成"""
    problems = load_cache(subject)
    candidates = problems
    if exclude_ids:
        candidates = [p for p in candidates if p["id"] not in exclude_ids]
    if topic:
        candidates = [p for p in candidates if topic in p.get("topic", "") or topic in p.get("tags", [])]

    if len(candidates) >= count:
        return rnd.sample(candidates, count)

    # 缓存不够，AI 生成
    needed = count - len(candidates)
    print(f"\n{Color.CYAN}🤖 正在生成新题目…{Color.RESET}")
    for _ in range(needed):
        new_p = _generate(subject, topic)
        if new_p:
            problems.append(new_p)
            candidates.append(new_p)

    if problems != load_cache(subject):  # 有新增
        save_cache(subject, problems)

    return rnd.sample(candidates, min(count, len(candidates))) if candidates else []


def get_all_problems(subject: str) -> list:
    """获取某科目的所有可用题目（缓存+种子）"""
    return load_cache(subject)


def get_topics(subject: str) -> list:
    """获取某科目所有已有主题"""
    topics = set()
    for p in load_cache(subject):
        topics.add(p["topic"])
    return sorted(topics)


def _generate(subject: str, topic: str | None = None) -> dict | None:
    """调用 sgpt 生成一道题（完整含提示、错误分支、步骤）"""
    name = SUBJECT_NAMES.get(subject, "数学")
    tag = SUBJECT_TAGS.get(subject, "gen")

    if not topic:
        existing = load_cache(subject)
        topics = sorted(set(p["topic"] for p in existing))
        topic = topics[len(topics) // 2] if topics else "综合"

    timestamp = int(time.time())
    rnd.seed(timestamp)
    difficulty = rnd.choice([1, 2, 3])

    prompt = (
        "你是一位中国初中" + name + "老师。出一道初中" + name + "题。\n"
        f"主题：{topic}。难度：{'简单' if difficulty == 1 else '中等' if difficulty == 2 else '较难'}({difficulty}/3)。\n"
        "只输出一行JSON，不要markdown，不要换行。格式：\n"
        '{"id":"xxx","topic":"xxx","grade":"初一","difficulty":1,"question":"题目","answer":"答案","alternatives":["备选"],'
        '"steps":["步骤1","步骤2"],"socratic_hints":["提示1（模糊）","提示2（更具体）","提示3（接近答案）"],'
        '"common_errors":{"错误1":"反馈1","错误2":"反馈2","错误3":"反馈3"},"tags":["自动生成"],"concept_note":"一句话"}\n'
        f'id用：{tag}-gen-{timestamp}\n'
        "要求：socratic_hints必须正好3条，逐步引导但不直接给答案。common_errors至少3条。"
    )

    SGPT = "/home/zzk/.local/bin/sgpt"
    try:
        result = sp.run([SGPT, prompt], capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            return None
        text = " ".join(l for l in result.stdout.split("\n") if not l.startswith("Warning:")).strip()
        text = text.replace("```json", "").replace("```", "").strip()
        problem = json.loads(text)
        required = ["id", "question", "answer", "steps", "socratic_hints", "common_errors"]
        if not all(f in problem for f in required):
            return None

        # 清理 LaTeX
        for field in ["question", "answer", "concept_note"]:
            if field in problem:
                problem[field] = latex_to_plain(problem[field])
        if "steps" in problem:
            problem["steps"] = [latex_to_plain(s) for s in problem["steps"]]
        if "socratic_hints" in problem:
            problem["socratic_hints"] = [latex_to_plain(h) for h in problem["socratic_hints"]]
        if "common_errors" in problem:
            problem["common_errors"] = {latex_to_plain(k): latex_to_plain(v) for k, v in problem["common_errors"].items()}

        # 补全可选字段
        problem.setdefault("topic", topic)
        problem.setdefault("grade", "初二")
        problem.setdefault("difficulty", 2)
        problem.setdefault("alternatives", [])
        problem.setdefault("tags", [topic, "自动生成"])
        problem.setdefault("concept_note", "")
        while len(problem.get("socratic_hints", [])) < 3:
            problem["socratic_hints"].append("再想想，你离答案很近了！")
        return problem
    except Exception:
        return None
