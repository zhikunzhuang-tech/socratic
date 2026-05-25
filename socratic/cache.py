"""问题缓存 — 管理 AI 生成题目的缓存 + 种子题"""
import json
import random as rnd
import subprocess as sp
import time
from pathlib import Path
from .utils import DATA_DIR, Color, latex_to_plain
from .wiki_math import is_available as wiki_available, get_grade as wiki_get_grade, get_wiki_context

CACHE_DIR = DATA_DIR / "cache"

SUBJECT_NAMES = {"math": "数学", "english": "英语", "physics": "物理", "chinese": "语文", "biology": "生物", "geography": "地理", "claude": "Claude Code", "hermes": "Hermes Agent", "cmd": "常用命令"}
SUBJECT_TAGS = {"math": "math", "english": "eng", "physics": "phy", "chinese": "chn", "biology": "bio", "geography": "geo", "claude": "claude", "hermes": "hermes", "cmd": "cmd"}


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
    "cmd": [
        {"id": "seed-cmd-1", "topic": "文件导航", "grade": "入门", "difficulty": 1,
         "question": "ls 命令的作用是什么？", "answer": "列出当前目录下的文件和目录",
         "alternatives": [], "steps": [], "socratic_hints": [], "common_errors": {},
         "tags": ["Linux", "入门"], "concept_note": "ls = list，最常用的查看命令。"},
        {"id": "seed-cmd-2", "topic": "文件导航", "grade": "入门", "difficulty": 1,
         "question": "cd 命令的作用是什么？", "answer": "切换当前工作目录",
         "alternatives": [], "steps": [], "socratic_hints": [], "common_errors": {},
         "tags": ["Linux", "入门"], "concept_note": "cd = change directory。"},
        {"id": "seed-cmd-3", "topic": "文件导航", "grade": "入门", "difficulty": 1,
         "question": "pwd 命令的作用是什么？", "answer": "显示当前工作目录的完整路径",
         "alternatives": [], "steps": [], "socratic_hints": [], "common_errors": {},
         "tags": ["Linux", "入门"], "concept_note": "pwd = print working directory。"},
        {"id": "seed-cmd-4", "topic": "文件操作", "grade": "入门", "difficulty": 1,
         "question": "cp 命令的作用是什么？", "answer": "复制文件或目录（cp -r 递归复制目录）",
         "alternatives": [], "steps": [], "socratic_hints": [], "common_errors": {},
         "tags": ["Linux", "入门"], "concept_note": "cp = copy，-r 递归复制目录。"},
        {"id": "seed-cmd-5", "topic": "文件操作", "grade": "入门", "difficulty": 1,
         "question": "mv 命令的作用是什么？", "answer": "移动文件/目录，也可用于重命名（mv old.txt new.txt）",
         "alternatives": [], "steps": [], "socratic_hints": [], "common_errors": {},
         "tags": ["Linux", "入门"], "concept_note": "mv = move，改名也是它。"},
        {"id": "seed-cmd-6", "topic": "文件操作", "grade": "入门", "difficulty": 1,
         "question": "rm 命令的作用是什么？", "answer": "删除文件或目录（rm -rf 递归强制删除，需谨慎）",
         "alternatives": [], "steps": [], "socratic_hints": [], "common_errors": {},
         "tags": ["Linux", "入门"], "concept_note": "rm = remove，-rf 非常危险，小心使用。"},
        {"id": "seed-cmd-7", "topic": "文件操作", "grade": "入门", "difficulty": 1,
         "question": "touch 命令的作用是什么？", "answer": "创建空文件或更新文件的时间戳",
         "alternatives": [], "steps": [], "socratic_hints": [], "common_errors": {},
         "tags": ["Linux", "入门"], "concept_note": "touch 新建文件或刷新时间戳。"},
        {"id": "seed-cmd-8", "topic": "文件操作", "grade": "入门", "difficulty": 1,
         "question": "mkdir 命令的作用是什么？", "answer": "创建目录（mkdir -p 递归创建多级目录）",
         "alternatives": [], "steps": [], "socratic_hints": [], "common_errors": {},
         "tags": ["Linux", "入门"], "concept_note": "mkdir = make directory，-p 创建父目录。"},
        {"id": "seed-cmd-9", "topic": "文件查看", "grade": "入门", "difficulty": 1,
         "question": "cat 命令的作用是什么？", "answer": "显示文件全部内容，也可用于合并多个文件",
         "alternatives": [], "steps": [], "socratic_hints": [], "common_errors": {},
         "tags": ["Linux", "入门"], "concept_note": "cat = concatenate，查看/合并文件。"},
        {"id": "seed-cmd-10", "topic": "文件查看", "grade": "入门", "difficulty": 1,
         "question": "less 命令的作用是什么？", "answer": "分页浏览文件内容，可上下滚动（q 退出）",
         "alternatives": [], "steps": [], "socratic_hints": [], "common_errors": {},
         "tags": ["Linux", "入门"], "concept_note": "less 比 cat 更适合大文件，按 q 退出。"},
        {"id": "seed-cmd-11", "topic": "文件查看", "grade": "入门", "difficulty": 1,
         "question": "head 命令的作用是什么？", "answer": "显示文件的前 N 行（默认 10 行，head -n 20 显示前 20 行）",
         "alternatives": [], "steps": [], "socratic_hints": [], "common_errors": {},
         "tags": ["Linux", "入门"], "concept_note": "head 看文件开头，tail 看结尾。"},
        {"id": "seed-cmd-12", "topic": "文件查看", "grade": "入门", "difficulty": 1,
         "question": "tail -f 命令的作用是什么？", "answer": "实时跟踪文件末尾新增的内容（常用于监控日志）",
         "alternatives": [], "steps": [], "socratic_hints": [], "common_errors": {},
         "tags": ["Linux", "入门"], "concept_note": "tail -f 实时跟踪日志，Ctrl+C 退出。"},
        {"id": "seed-cmd-13", "topic": "文本搜索", "grade": "入门", "difficulty": 1,
         "question": "grep 命令的作用是什么？", "answer": "在文件中搜索匹配的文本模式（grep \"error\" log.txt）",
         "alternatives": [], "steps": [], "socratic_hints": [], "common_errors": {},
         "tags": ["Linux", "入门"], "concept_note": "grep 文本搜索，-R 递归 -n 行号 -i 忽略大小写。"},
        {"id": "seed-cmd-14", "topic": "文件搜索", "grade": "入门", "difficulty": 1,
         "question": "find 命令的作用是什么？", "answer": "按文件名/类型/大小等条件搜索文件（find . -name \"*.txt\"）",
         "alternatives": [], "steps": [], "socratic_hints": [], "common_errors": {},
         "tags": ["Linux", "入门"], "concept_note": "find 搜文件，-name 按名 -type f 文件 -type d 目录。"},
        {"id": "seed-cmd-15", "topic": "权限管理", "grade": "进阶", "difficulty": 2,
         "question": "chmod 755 file 的含义是什么？", "answer": "所有者可读写执行(7)，同组用户可读执行(5)，其他人可读执行(5)",
         "alternatives": [], "steps": [], "socratic_hints": [], "common_errors": {},
         "tags": ["Linux", "进阶"], "concept_note": "chmod 三位数 = owner/group/others，r=4 w=2 x=1。"},
        {"id": "seed-cmd-16", "topic": "权限管理", "grade": "进阶", "difficulty": 2,
         "question": "chown 命令的作用是什么？", "answer": "更改文件或目录的所有者和所属组（chown user:group file）",
         "alternatives": [], "steps": [], "socratic_hints": [], "common_errors": {},
         "tags": ["Linux", "进阶"], "concept_note": "chown = change owner。"},
        {"id": "seed-cmd-17", "topic": "进程管理", "grade": "入门", "difficulty": 1,
         "question": "ps aux 命令显示什么？", "answer": "当前系统中所有运行进程的详细状态（用户、PID、CPU、内存等）",
         "alternatives": [], "steps": [], "socratic_hints": [], "common_errors": {},
         "tags": ["Linux", "入门"], "concept_note": "ps aux 查看所有进程，grep 过滤。"},
        {"id": "seed-cmd-18", "topic": "进程管理", "grade": "入门", "difficulty": 1,
         "question": "top 命令的作用是什么？", "answer": "实时动态显示系统进程和资源占用（CPU/内存），按 q 退出",
         "alternatives": [], "steps": [], "socratic_hints": [], "common_errors": {},
         "tags": ["Linux", "入门"], "concept_note": "top 实时监控，q 退出，k 可杀进程。"},
        {"id": "seed-cmd-19", "topic": "进程管理", "grade": "入门", "difficulty": 1,
         "question": "kill 命令的作用是什么？", "answer": "向进程发送信号，通常用于终止进程（kill PID 或 kill -9 PID 强制终止）",
         "alternatives": [], "steps": [], "socratic_hints": [], "common_errors": {},
         "tags": ["Linux", "入门"], "concept_note": "kill 终止进程，-9 强制终止。"},
        {"id": "seed-cmd-20", "topic": "磁盘管理", "grade": "入门", "difficulty": 1,
         "question": "df -h 命令显示什么？", "answer": "磁盘分区使用情况（可用/已用/总空间），-h 表示人类可读格式",
         "alternatives": [], "steps": [], "socratic_hints": [], "common_errors": {},
         "tags": ["Linux", "入门"], "concept_note": "df -h 看磁盘空间，free -h 看内存。"},
        {"id": "seed-cmd-21", "topic": "磁盘管理", "grade": "入门", "difficulty": 1,
         "question": "du -sh dir/ 命令的作用是什么？", "answer": "显示指定目录占用的磁盘空间大小（-s 汇总，-h 人类可读）",
         "alternatives": [], "steps": [], "socratic_hints": [], "common_errors": {},
         "tags": ["Linux", "入门"], "concept_note": "du -sh 看目录占了多少空间。"},
        {"id": "seed-cmd-22", "topic": "系统帮助", "grade": "入门", "difficulty": 1,
         "question": "man ls 命令的作用是什么？", "answer": "打开 ls 命令的详细手册页面（按 q 退出）",
         "alternatives": [], "steps": [], "socratic_hints": [], "common_errors": {},
         "tags": ["Linux", "入门"], "concept_note": "man = manual，每个命令的自带说明书。"},
        {"id": "seed-cmd-23", "topic": "Shell 基础", "grade": "入门", "difficulty": 1,
         "question": "Shell 中管道 | 的作用是什么？", "answer": "将前一个命令的输出作为后一个命令的输入（如 ps aux | grep nginx）",
         "alternatives": [], "steps": [], "socratic_hints": [], "common_errors": {},
         "tags": ["Shell", "入门"], "concept_note": "管道 | 串联命令，> 写入文件，>> 追加。"},
        {"id": "seed-cmd-24", "topic": "Shell 基础", "grade": "入门", "difficulty": 1,
         "question": "重定向符号 > 和 >> 的区别是什么？", "answer": "> 覆盖写入文件，>> 追加到文件末尾",
         "alternatives": [], "steps": [], "socratic_hints": [], "common_errors": {},
         "tags": ["Shell", "入门"], "concept_note": "> 覆盖，>> 追加，注意别用错。"},
        {"id": "seed-cmd-25", "topic": "网络操作", "grade": "入门", "difficulty": 1,
         "question": "ping 命令的作用是什么？", "answer": "测试与目标主机的网络连通性和延迟",
         "alternatives": [], "steps": [], "socratic_hints": [], "common_errors": {},
         "tags": ["网络", "入门"], "concept_note": "ping 测连通性，Ctrl+C 停止。"},
        {"id": "seed-cmd-26", "topic": "网络操作", "grade": "入门", "difficulty": 1,
         "question": "ssh user@host 命令的作用是什么？", "answer": "通过 SSH 协议安全远程登录到目标主机",
         "alternatives": [], "steps": [], "socratic_hints": [], "common_errors": {},
         "tags": ["网络", "入门"], "concept_note": "ssh = secure shell，远程登录工具。"},
        {"id": "seed-cmd-27", "topic": "vi 编辑器", "grade": "入门", "difficulty": 1,
         "question": "要进入 vi 的插入模式输入文字，按哪个键？", "answer": "i（按 i 进入插入模式，按 Esc 退出到命令模式）",
         "alternatives": [], "steps": [], "socratic_hints": [], "common_errors": {},
         "tags": ["vi", "入门"], "concept_note": "vi 两模式：命令模式和插入模式，i 进入，Esc 退出。"},
        {"id": "seed-cmd-28", "topic": "vi 编辑器", "grade": "入门", "difficulty": 1,
         "question": "在 vi 中如何保存文件并退出？", "answer": "在命令模式下输入 :wq（w=write 保存，q=quit 退出）",
         "alternatives": [], "steps": [], "socratic_hints": [], "common_errors": {},
         "tags": ["vi", "入门"], "concept_note": ":wq 保存退出，:q! 不保存强制退出。"},
        {"id": "seed-cmd-29", "topic": "git 版本控制", "grade": "入门", "difficulty": 1,
         "question": "git add 的作用是什么？", "answer": "将文件更改添加到暂存区（staging area），准备提交",
         "alternatives": [], "steps": [], "socratic_hints": [], "common_errors": {},
         "tags": ["git", "入门"], "concept_note": "git add → 暂存区 → git commit → 本地仓库。"},
        {"id": "seed-cmd-30", "topic": "git 版本控制", "grade": "入门", "difficulty": 1,
         "question": "git commit 的作用是什么？", "answer": "将暂存区的更改提交到本地仓库，创建一次版本快照",
         "alternatives": [], "steps": [], "socratic_hints": [], "common_errors": {},
         "tags": ["git", "入门"], "concept_note": "git commit -m \"message\" 创建版本快照。"},
        {"id": "seed-cmd-31", "topic": "git 版本控制", "grade": "入门", "difficulty": 1,
         "question": "git status 显示什么信息？", "answer": "当前工作目录的状态：已修改/已暂存/未跟踪的文件",
         "alternatives": [], "steps": [], "socratic_hints": [], "common_errors": {},
         "tags": ["git", "入门"], "concept_note": "git status 查看状态，改没改一眼明了。"},
        {"id": "seed-cmd-32", "topic": "git 版本控制", "grade": "入门", "difficulty": 1,
         "question": "git log 命令的作用是什么？", "answer": "显示提交历史记录，包括作者、日期、提交信息",
         "alternatives": [], "steps": [], "socratic_hints": [], "common_errors": {},
         "tags": ["git", "入门"], "concept_note": "git log 看历史，--oneline 简洁，-p 看详情。"},
        {"id": "seed-cmd-33", "topic": "git 版本控制", "grade": "进阶", "difficulty": 2,
         "question": "git branch 命令的作用是什么？", "answer": "查看、创建、删除分支（git branch new-branch 创建，-d 删除）",
         "alternatives": [], "steps": [], "socratic_hints": [], "common_errors": {},
         "tags": ["git", "进阶"], "concept_note": "git branch 管分支，checkout 切换，merge 合并。"},
        {"id": "seed-cmd-34", "topic": "git 版本控制", "grade": "进阶", "difficulty": 2,
         "question": "git clone 命令的作用是什么？", "answer": "将远程仓库完整复制到本地（git clone <repo-url>）",
         "alternatives": [], "steps": [], "socratic_hints": [], "common_errors": {},
         "tags": ["git", "进阶"], "concept_note": "git clone 下载整个仓库到本地。"},
        {"id": "seed-cmd-35", "topic": "Shell 基础", "grade": "入门", "difficulty": 1,
         "question": "sudo 命令的作用是什么？", "answer": "以超级用户（root）权限执行命令",
         "alternatives": [], "steps": [], "socratic_hints": [], "common_errors": {},
         "tags": ["Shell", "入门"], "concept_note": "sudo = superuser do，临时获取管理员权限。"},
    ],
    "claude": [
        {"id": "seed-claude-1", "topic": "基本命令", "grade": "入门", "difficulty": 1,
         "question": "/init 命令的作用是什么？", "answer": "扫描项目并自动生成 CLAUDE.md 文件（项目记忆文档）",
         "alternatives": ["扫描项目生成 CLAUDE.md"],
         "steps": ["在项目根目录运行 /init", "Claude 分析项目结构、技术栈、依赖", "自动生成包含项目描述的 CLAUDE.md"],
         "socratic_hints": ["这个命令是 /i 开头的，和初始化有关", "它会分析你的项目结构", "生成的是 CLAUDE.md 文件"],
         "common_errors": {"初始化项目代码": "/init 不修改代码，只生成文档", "新建项目": "这不是脚手架命令，而是文档生成"},
         "tags": ["命令", "入门"], "concept_note": "/init 是进入项目的第一步，自动生成记忆文件。"},
        {"id": "seed-claude-2", "topic": "模型管理", "grade": "入门", "difficulty": 1,
         "question": "/model 命令可以切换到哪些模型？", "answer": "Sonnet、Opus、Haiku 三种",
         "alternatives": ["Sonnet Opus Haiku"],
         "steps": ["输入 /model", "选择目标模型", "确认后立即切换"],
         "socratic_hints": ["Claude 模型家族有哪些系列？", "Opus 最强，Haiku 最快，中间是？", "Sonnet / Opus / Haiku"],
         "common_errors": {"GPT-4": "这是 Anthropic 的模型，不是 OpenAI", "Claude 3": "已升级为 4.x 系列"},
         "tags": ["命令", "配置"], "concept_note": "Opus=最强，Sonnet=均衡，Haiku=最快。"},
        {"id": "seed-claude-3", "topic": "会话管理", "grade": "入门", "difficulty": 2,
         "question": "/compact 命令的作用是什么？", "answer": "压缩当前会话上下文，将冗长历史提炼为摘要以释放 token 空间",
         "alternatives": ["压缩上下文释放空间"],
         "steps": ["会话较长时，token 消耗增大", "运行 /compact 将历史对话总结为摘要", "释放出的空间可继续工作"],
         "socratic_hints": ["这个命令和「压缩」有关", "它处理的是对话历史", "目的是让 Claude 能继续处理更多内容"],
         "common_errors": {"清理缓存文件": "/compact 压缩的是对话上下文，不是文件缓存", "清空对话": "/clear 才是清空，/compact 保留摘要"},
         "tags": ["命令", "进阶"], "concept_note": "/compact 避免达到上下文上限，保持长会话流畅。"},
        {"id": "seed-claude-4", "topic": "会话管理", "grade": "入门", "difficulty": 1,
         "question": "/clear 命令的作用是什么？", "answer": "清空整个对话历史，释放全部上下文窗口，相当于从头开始新会话",
         "alternatives": ["清空对话历史"],
         "steps": ["运行 /clear", "所有对话历史被清除", "上下文窗口重置为空", "可以开始全新讨论"],
         "socratic_hints": ["clear 是什么意思？", "清空，但清空什么？", "对话历史全部删除，从头开始"],
         "common_errors": {"关闭程序": "/clear 不退出 Claude Code，只清空对话", "/compact": "/compact 保留摘要，/clear 全部清空"},
         "tags": ["命令", "入门"], "concept_note": "/clear = 硬重置，/compact = 压缩保留摘要。"},
        {"id": "seed-claude-5", "topic": "会话管理", "grade": "入门", "difficulty": 2,
         "question": "/resume 命令的作用是什么？", "answer": "列出历史会话并选择恢复，可以从中断的地方继续之前的对话",
         "alternatives": ["恢复历史会话"],
         "steps": ["输入 /resume", "浏览历史会话列表", "选择目标会话", "从上次中断处继续"],
         "socratic_hints": ["resume 在英文里是「恢复」的意思", "恢复什么？", "之前的会话——没做完的事不用重来"],
         "common_errors": {"新建会话": "/resume 是恢复旧会话", "只能恢复上一次": "可以选择任意历史会话"},
         "tags": ["命令", "入门"], "concept_note": "/resume 让长期任务不怕中断，随时接上。"},
        {"id": "seed-claude-6", "topic": "会话管理", "grade": "进阶", "difficulty": 2,
         "question": "/fork 命令的作用是什么？", "answer": "从当前对话位置分叉出一个实验性分支会话，原会话不受影响",
         "alternatives": ["创建对话实验分支"],
         "steps": ["在当前对话位置运行 /fork", "创建新分支会话", "在新分支中尝试不同方案", "原会话保持不变"],
         "socratic_hints": ["fork 在 git 里是什么意思？", "分叉！出一个分支", "可以在分支上试东试西，主干不影响"],
         "common_errors": {"复制文件": "/fork 分叉的是对话，不是代码", "创建新窗口": "分支会话在同一终端管理"},
         "tags": ["命令", "进阶"], "concept_note": "/fork = 对话实验分支，试错无压力。"},
        {"id": "seed-claude-7", "topic": "CLI 参数", "grade": "进阶", "difficulty": 2,
         "question": "claude -p \"prompt\" 中的 -p 参数的含义是什么？", "answer": "print mode — 非交互式单次查询，输出结果后退出",
         "alternatives": ["print 模式"],
         "steps": ["-p 后跟查询文本", "Claude 执行查询并输出结果", "不进入交互模式，直接退出"],
         "socratic_hints": ["-p 代表 print，打印输出", "和交互模式相反", "适合脚本/CI 中使用"],
         "common_errors": {"project": "-p 是 print 不是 project", "python": "不是 Python 模式"},
         "tags": ["CLI", "进阶"], "concept_note": "claude -p 用于脚本和 CI，输出后自动退出。"},
        {"id": "seed-claude-8", "topic": "CLI 参数", "grade": "进阶", "difficulty": 2,
         "question": "claude -c 参数的作用是什么？", "answer": "继续最近一次会话（continue），自动恢复上次中断的对话",
         "alternatives": ["继续上次会话"],
         "steps": ["直接运行 claude -c 启动", "无需浏览历史会话", "自动加载最近一次对话"],
         "socratic_hints": ["-c 是哪个单词的缩写？", "continue！", "继续上一次没做完的事"],
         "common_errors": {"创建新会话": "-c 是恢复旧会话", "/resume": "-c 是 CLI 方式，/resume 是交互方式"},
         "tags": ["CLI", "进阶"], "concept_note": "claude -c 最快恢复上次会话，不经过菜单。"},
        {"id": "seed-claude-9", "topic": "交互技巧", "grade": "入门", "difficulty": 1,
         "question": "在 Claude Code 中输入 @ + 文件路径的作用是什么？", "answer": "触发文件自动补全，将指定文件作为上下文引用",
         "alternatives": ["文件自动补全"],
         "steps": ["输入 @ 符号", "Claude 自动列出项目文件", "选择文件将其内容纳入上下文"],
         "socratic_hints": ["@ 和路径有关", "你会看到文件列表弹出来", "选中文件后 Claude 就能看到该文件内容"],
         "common_errors": {"创建文件": "@ 是引用现有文件，不会创建", "删除文件": "引用不会删除文件"},
         "tags": ["交互", "入门"], "concept_note": "@ 符号是 Claude Code 中最常用的文件引用方式。"},
        {"id": "seed-claude-10", "topic": "监控诊断", "grade": "入门", "difficulty": 1,
         "question": "/cost 命令显示什么信息？", "answer": "当前会话的 token 消耗量和 API 费用估算",
         "alternatives": ["token 消耗和费用"],
         "steps": ["输入 /cost", "查看输入/输出 token 数", "查看对应的费用估算"],
         "socratic_hints": ["cost 是「花费」的意思", "花什么？", "token 和钱"],
         "common_errors": {"查看价格": "显示的是实际用量和费用，不是定价表", "只显示金额": "也显示 token 数"},
         "tags": ["监控", "入门"], "concept_note": "/cost 实时查看花费，心中有数。"},
        {"id": "seed-claude-11", "topic": "监控诊断", "grade": "入门", "difficulty": 1,
         "question": "/context 命令的作用是什么？", "answer": "可视化显示当前上下文窗口的使用情况（百分比图形），帮你判断是否需要 /compact",
         "alternatives": ["显示上下文用量"],
         "steps": ["输入 /context", "查看彩色使用率图表", "判断是否需要压缩"],
         "socratic_hints": ["你知道上下文窗口还剩多少吗？", "有个命令可以直观显示", "不用猜，/context 一目了然"],
         "common_errors": {"清理上下文": "/context 只显示不清理，清理用 /compact", "显示文件路径": "显示的是 token 用量"},
         "tags": ["监控", "入门"], "concept_note": "/context 可视化 token 消耗，快满了就 /compact。"},
        {"id": "seed-claude-12", "topic": "监控诊断", "grade": "进阶", "difficulty": 2,
         "question": "/doctor 命令的作用是什么？", "answer": "诊断安装环境、网络连接、认证状态和 MCP 配置问题",
         "alternatives": ["诊断环境和配置"],
         "steps": ["输入 /doctor", "自动检查各项配置", "列出问题及修复建议"],
         "socratic_hints": ["doctor 是医生", "医生干什么？", "检查身体——这里检查配置是否有问题"],
         "common_errors": {"修复 bug": "/doctor 诊断环境，不修复代码", "健康检查": "确实是健康检查，但是针对环境"},
         "tags": ["监控", "进阶"], "concept_note": "/doctor 出问题时先看它，省去自查时间。"},
        {"id": "seed-claude-13", "topic": "监控诊断", "grade": "进阶", "difficulty": 2,
         "question": "/usage 命令显示什么？", "answer": "显示套餐用量详情：各会话/子代理/缓存命中/长上下文的消耗占比和优化建议",
         "alternatives": ["套餐用量和优化建议"],
         "steps": ["输入 /usage", "查看各类消耗占比", "参考优化建议降低浪费"],
         "socratic_hints": ["usage = 使用量", "看看是什么在吃掉你的配额？", "还能给出优化建议"],
         "common_errors": {"/cost": "/usage 是套餐级别统计，/cost 是当前会话", "只显示总用量": "有详细分类和优化提示"},
         "tags": ["监控", "进阶"], "concept_note": "/usage = 套餐级用量 + 省钱建议。"},
        {"id": "seed-claude-14", "topic": "MCP 扩展", "grade": "进阶", "difficulty": 3,
         "question": "/mcp 命令在 Claude Code 中的作用是什么？", "answer": "管理 MCP（Model Context Protocol）服务器的连接，可添加、移除、重连外部工具",
         "alternatives": ["管理 MCP 服务器连接"],
         "steps": ["输入 /mcp 打开 MCP 管理面板", "可查看已连接和可用的 MCP 服务器", "选择添加/移除/重连"],
         "socratic_hints": ["MCP 是什么的缩写？", "它让 Claude 可以调用外部工具", "比如连接 GitHub、数据库、文件系统等"],
         "common_errors": {"模型参数": "MCP 不是 model parameters", "多任务处理": "那是 /agents"},
         "tags": ["MCP", "进阶"], "concept_note": "MCP 让 Claude 突破内置工具限制，连接外部服务。"},
        {"id": "seed-claude-15", "topic": "MCP 扩展", "grade": "进阶", "difficulty": 2,
         "question": "/skills 命令的作用是什么？", "answer": "列出所有可用的 Skills（技能），包括内置和用户自定义的",
         "alternatives": ["列出可用技能"],
         "steps": ["输入 /skills", "浏览可用技能列表", "了解每个技能的功能"],
         "socratic_hints": ["Claude 有很多内置「技能」", "怎么知道有哪些？", "用 /skills 查看全部"],
         "common_errors": {"安装技能": "/skills 查看列表，安装用 /plugin", "执行技能": "/skills 只是查看"},
         "tags": ["MCP", "入门"], "concept_note": "/skills 查看可用技能库存，按需调用。"},
        {"id": "seed-claude-16", "topic": "项目管理", "grade": "进阶", "difficulty": 2,
         "question": "/diff 命令在 Claude Code 中的作用是什么？", "answer": "显示当前会话中所有文件变更的交互式差异对比视图",
         "alternatives": ["显示文件变更差异"],
         "steps": ["输入 /diff", "查看所有变更文件列表", "逐文件查看 diff 对比"],
         "socratic_hints": ["你有改动文件但不知道改了哪里？", "diff 就是对比", "交互式的，可以逐个文件看"],
         "common_errors": {"提交代码": "/diff 只显示变更，提交用 /commit", "git diff": "和 git diff 类似，但内置在 Claude 中"},
         "tags": ["项目", "进阶"], "concept_note": "/diff 查看所有变更，确认后 /commit 提交。"},
        {"id": "seed-claude-17", "topic": "项目管理", "grade": "进阶", "difficulty": 3,
         "question": "/commit 命令做什么？", "answer": "自动分析变更内容，生成规范的 git commit message 并执行提交",
         "alternatives": ["自动生成提交信息并提交"],
         "steps": ["运行 /commit", "Claude 分析变更 diff", "自动生成 commit message", "执行 git commit"],
         "socratic_hints": ["提交代码要写 message", "Claude 能不能帮我写？", "能！/commit 全自动"],
         "common_errors": {"只生成信息": "/commit 会实际执行提交", "需要手动写消息": "消息由 AI 自动生成"},
         "tags": ["项目", "进阶"], "concept_note": "/commit = AI 写提交信息 + 执行提交，一步到位。"},
        {"id": "seed-claude-18", "topic": "工作模式", "grade": "进阶", "difficulty": 2,
         "question": "/plan 模式是什么？", "answer": "只读规划模式：Claude 只能浏览和分析代码，不能编辑文件，用于设计方案",
         "alternatives": ["只读规划模式"],
         "steps": ["输入 /plan 进入规划模式", "Claude 浏览代码、分析架构", "制定实施方案", "确认方案后 /execute 执行"],
         "socratic_hints": ["开工前先干什么？", "先做计划", "/plan 模式下 Claude 只看不改"],
         "common_errors": {"编辑文件": "/plan 模式下不能修改文件", "自动退出": "需要 /execute 才会开始改代码"},
         "tags": ["工作模式", "进阶"], "concept_note": "/plan 只看不做，/execute 开始动手。"},
        {"id": "seed-claude-19", "topic": "工作模式", "grade": "入门", "difficulty": 1,
         "question": "/effort 命令设置什么？", "answer": "设置推理深度级别：low（最快）、medium、high、xhigh（最强）、max（最大努力）",
         "alternatives": ["推理深度级别"],
         "steps": ["输入 /effort", "选择推理级别", "更高级别 = 更深入思考但更慢"],
         "socratic_hints": ["effort = 努力程度", "越努力越聪明但也越慢", "5 个级别可选"],
         "common_errors": {"切换模型": "/effort 调推理深度，不换模型", "low 就是差": "low 只是思考少，简单任务够了"},
         "tags": ["工作模式", "入门"], "concept_note": "effort = 思考深度，从 low 到 max 五档。"},
        {"id": "seed-claude-20", "topic": "快捷键", "grade": "入门", "difficulty": 1,
         "question": "在 Claude Code 中按 Esc 键会做什么？", "answer": "取消当前正在生成的回复",
         "alternatives": ["取消当前生成"],
         "steps": ["Claude 正在生成回复时", "按 Esc 键", "生成立即停止"],
         "socratic_hints": ["「太慢了不想等了」按啥？", "「说错了赶紧停」按啥？", "Esc = 紧急停止"],
         "common_errors": {"退出程序": "Esc 是取消生成，退出用 Ctrl+D", "暂停生成": "是取消不是暂停，不能恢复"},
         "tags": ["快捷键", "入门"], "concept_note": "Esc = 紧急刹车，取消当前输出。"},
        {"id": "seed-claude-21", "topic": "快捷键", "grade": "入门", "difficulty": 1,
         "question": "在 Claude Code 中按 Tab 键做什么？", "answer": "触发自动补全（命令/文件路径）或切换 thinking 显示",
         "alternatives": ["自动补全或切换 thinking"],
         "steps": ["输入命令或路径时按 Tab", "自动补全或显示候选项", "也可切换 thinking 模式显示"],
         "socratic_hints": ["补全键在终端里是哪个？", "Tab！", "还能切换 thinking 显示"],
         "common_errors": {"插入制表符": "Claude Code 中 Tab 不插入空格", "只补全": "还能切换 thinking"},
         "tags": ["快捷键", "入门"], "concept_note": "Tab = 补全 + thinking 切换。"},
        {"id": "seed-claude-22", "topic": "快捷键", "grade": "入门", "difficulty": 1,
         "question": "Ctrl+D 在 Claude Code 中的作用是什么？", "answer": "退出 Claude Code 程序",
         "alternatives": ["退出程序"],
         "steps": ["按 Ctrl+D", "确认退出", "关闭 Claude Code"],
         "socratic_hints": ["想退出程序，除了输入 /exit 还能按什么？", "Ctrl + 哪个键？", "D！就像 bash 里退出一样"],
         "common_errors": {"删除": "Ctrl+D 不删除内容", "取消生成": "取消生成是 Esc"},
         "tags": ["快捷键", "入门"], "concept_note": "Ctrl+D = 退出 Claude Code。"},
        {"id": "seed-claude-23", "topic": "交互技巧", "grade": "入门", "difficulty": 1,
         "question": "在 Claude Code 中输入 ! + 命令（如 !ls）的作用是什么？", "answer": "直接在终端中执行该命令并输出结果，不经过 Claude 处理",
         "alternatives": ["直接执行终端命令"],
         "steps": ["输入 ! 后跟命令", "命令直接在终端执行", "输出结果显示在界面中"],
         "socratic_hints": ["想直接运行一个 shell 命令不用问 Claude？", "前面加个感叹号就行", "!ls 就是直接 ls"],
         "common_errors": {"AI 执行": "!command 不走 AI，直接执行 shell", "Claude 会分析": "! 前缀的命令不经过 AI 处理"},
         "tags": ["交互", "入门"], "concept_note": "!command = 直接跑命令，绕过 AI。"},
        {"id": "seed-claude-24", "topic": "交互技巧", "grade": "入门", "difficulty": 1,
         "question": "在 Claude Code 中输入 # + 文本（如 #记住）的作用是什么？", "answer": "快速将文本添加到 CLAUDE.md 记忆文件中",
         "alternatives": ["快速添加记忆"],
         "steps": ["输入 # 后跟文本", "回车", "文本自动追加到 CLAUDE.md"],
         "socratic_hints": ["想让 Claude 记住一件事，一句话搞定？", "#记住这件事", "# 是快速记忆入口"],
         "common_errors": {"注释": "# 在 Claude Code 中是记忆命令，不是代码注释", "永久存储": "写入 CLAUDE.md"},
         "tags": ["交互", "入门"], "concept_note": "#文本 = 一句话写入项目记忆。"},
        {"id": "seed-claude-25", "topic": "项目管理", "grade": "进阶", "difficulty": 2,
         "question": "/review 命令在 Claude Code 中做什么？", "answer": "审查当前 PR 或变更差异，提供代码评审意见",
         "alternatives": ["代码评审"],
         "steps": ["输入 /review", "Claude 分析 diff", "给出评审意见和改进建议"],
         "socratic_hints": ["提交前想让人看看代码？", "不用找人，Claude 帮你审", "/review 就是代码审查"],
         "common_errors": {"提交代码": "/review 只审不提交", "运行测试": "/test 运行测试，/review 审代码"},
         "tags": ["项目", "进阶"], "concept_note": "/review = AI 代码审查，提交前的质检。"},
        {"id": "seed-claude-26", "topic": "项目管理", "grade": "进阶", "difficulty": 3,
         "question": "/pr-comments 命令做什么？", "answer": "拉取 GitHub PR 上的 review 评论，逐个分析并自动处理每条反馈",
         "alternatives": ["处理 PR 评审意见"],
         "steps": ["输入 /pr-comments <PR号>", "Claude 拉取所有评审意见", "逐条分析并修改代码"],
         "socratic_hints": ["PR 上有人提了 review 意见", "一条条处理很烦？", "Claude 帮你自动处理"],
         "common_errors": {"只拉取评论": "会分析并自动修改代码", "只处理一条": "处理所有评论"},
         "tags": ["项目", "进阶"], "concept_note": "/pr-comments = 自动处理所有 PR 评审意见。"},
        {"id": "seed-claude-27", "topic": "任务管理", "grade": "进阶", "difficulty": 2,
         "question": "/tasks 命令的作用是什么？", "answer": "列出和管理所有正在运行的后台任务",
         "alternatives": ["管理后台任务"],
         "steps": ["输入 /tasks", "查看所有后台任务状态", "可取消或查看进度"],
         "socratic_hints": ["同时跑了好几个任务", "怎么管理它们？", "/tasks 查看和控制"],
         "common_errors": {"任务清单": "是后台运行的任务，不是 TODO 列表", "/agents": "/agents 是子代理管理"},
         "tags": ["任务", "进阶"], "concept_note": "/tasks = 后台任务控制面板。"},
        {"id": "seed-claude-28", "topic": "任务管理", "grade": "进阶", "difficulty": 3,
         "question": "/batch 命令在 Claude Code 中做什么？", "answer": "在 5-30 个并行 git worktree 中大规模执行批量变更，适合跨文件重构",
         "alternatives": ["大规模批量变更"],
         "steps": ["输入 /batch <任务>", "创建多个 git worktree", "并行执行变更", "合并结果"],
         "socratic_hints": ["要改 100 个文件怎么最快？", "不要一个个来", "/batch 并行批量改"],
         "common_errors": {"单文件修改": "/batch 是为大规模变更设计的", "顺序执行": "并行 worktree 执行"},
         "tags": ["任务", "进阶"], "concept_note": "/batch = 大规模并行重构，最多 30 路。"},
        {"id": "seed-claude-29", "topic": "安全审查", "grade": "进阶", "difficulty": 3,
         "question": "/security-review 命令做什么？", "answer": "扫描当前分支的变更，检测安全漏洞（注入、XSS、敏感数据泄露等）",
         "alternatives": ["安全审查代码变更"],
         "steps": ["输入 /security-review", "Claude 分析 diff", "输出安全漏洞及修复建议"],
         "socratic_hints": ["写完代码担心安全？", "不用找安全专家", "/security-review 自动扫"],
         "common_errors": {"/review": "/review 是代码质量审查，/security-review 专注安全", "全面渗透测试": "是针对变更的安全扫描"},
         "tags": ["安全", "进阶"], "concept_note": "/security-review = 提交前的安全门禁。"},
        {"id": "seed-claude-30", "topic": "配置管理", "grade": "进阶", "difficulty": 2,
         "question": "CLAUDE.md 文件在 Claude Code 中的作用是什么？", "answer": "项目级持久记忆文件：存储项目描述、技术栈、编码规则、开发模式等，每会话自动加载",
         "alternatives": ["项目持久记忆文件"],
         "steps": ["在项目根目录创建 CLAUDE.md", "描述项目信息和规则", "Claude 在会话开始时自动读取"],
         "socratic_hints": ["Claude 怎么记住这个项目的特殊要求？", "有个文件专门干这个", "CLAUDE.md！每会话都加载"],
         "common_errors": {"README": "CLAUDE.md 是给 AI 看的，README 是给人看的", "一次性配置": "需要持续更新维护"},
         "tags": ["配置", "进阶"], "concept_note": "CLAUDE.md = 项目说明书，AI 每会话必读。"},
    ],
    "hermes": [
        {"id": "seed-hermes-1", "topic": "核心概念", "grade": "入门", "difficulty": 1,
         "question": "Hermes Agent 是由哪个组织开发的开源项目？", "answer": "Nous Research（开源 MIT 协议，GitHub 134k+ stars）",
         "alternatives": ["Nous Research"],
         "steps": ["Nous Research 是一个 AI 研究组织", "2025 年开源了 Hermes Agent", "采用 MIT 开源协议，社区活跃"],
         "socratic_hints": ["不是 Anthropic、不是 OpenAI", "一家 AI 研究组织，名字和希腊神话有关", "Nous = 希腊语的「理性/智慧」"],
         "common_errors": {"Anthropic": "Anthropic 开发的是 Claude，不是 Hermes", "MiniMax": "MiniMax 有 MaxHermes 产品，但 Hermes Agent 本身是 Nous Research 开源的"},
         "tags": ["概念", "入门"], "concept_note": "Hermes Agent = Nous Research 开源的自我进化 AI Agent。"},
        {"id": "seed-hermes-2", "topic": "核心概念", "grade": "入门", "difficulty": 1,
         "question": "Hermes Agent 最大的特点是什么？", "answer": "自我进化的闭环学习系统：完成任务 → 自动提炼技能 → 技能自我改进 → 跨会话复用",
         "alternatives": ["自我进化的闭环学习"],
         "steps": ["完成复杂任务（5 次以上工具调用）", "Agent 自动提炼关键步骤写成 Skill 文档", "使用过程中发现过时/错误会自动修补", "curator 命令定期审查和整理 Skills"],
         "socratic_hints": ["它不是固定能力的 Agent", "它用完之后会自动总结经验", "经验会保存下来，下次直接复用"],
         "common_errors": {"对话机器人": "它不是聊天机器人，是自主执行任务的 Agent", "代码补全工具": "它不是编程助手，是通用 Agent"},
         "tags": ["概念", "入门"], "concept_note": "核心差异：能力随使用持续生长，非出厂固定。"},
        {"id": "seed-hermes-3", "topic": "安装部署", "grade": "入门", "difficulty": 1,
         "question": "Hermes Agent 的运行环境要求是什么？", "answer": "Python 3.11+，Linux/macOS/WSL2，最低 $5 VPS 或 Modal/Daytona 等 serverless 平台",
         "alternatives": ["Python 3.11+"],
         "steps": ["克隆 GitHub 仓库", "安装 Python 3.11+ 依赖", "配置 API provider", "运行 hermes 启动"],
         "socratic_hints": ["需要什么编程语言？", "Python！哪个版本？", "3.11 以上就行，一台便宜 VPS 就能跑"],
         "common_errors": {"Windows 原生": "不支持 Windows，需要 WSL2", "需要 GPU": "不需要，CPU 即可"},
         "tags": ["安装", "入门"], "concept_note": "Python 3.11+，Linux/WSL2，$5 VPS 就能跑。"},
        {"id": "seed-hermes-4", "topic": "Skills 系统", "grade": "进阶", "difficulty": 2,
         "question": "Hermes Agent 的自主 Skills 创建机制是什么？", "answer": "完成任务（5 次以上工具调用）后自动提炼为可复用 Skill 文档，使用中检测过时/不完整会自动修补",
         "alternatives": ["自动提炼 Skill 并自我改进"],
         "steps": ["执行复杂任务", "Agent 分析执行轨迹，提炼关键步骤", "生成 Skill 文档保存到 skills 目录", "后续任务自动匹配并加载相关 Skill"],
         "socratic_hints": ["想象你做完一件复杂的事后写笔记", "Agent 帮你做了这件事，但它自己写", "写好后下次遇到类似任务直接复用"],
         "common_errors": {"需要人工编写": "完全由 Agent 自主生成", "生成后不变": "会根据新反馈持续迭代"},
         "tags": ["Skills", "进阶"], "concept_note": "Skills = Agent 自动总结的经验文档，持续迭代。"},
        {"id": "seed-hermes-5", "topic": "Skills 系统", "grade": "进阶", "difficulty": 2,
         "question": "hermes curator 命令的作用是什么？", "answer": "审查、合并、归档和清理 Agent 自动创建的 Skills，防止技能库膨胀和过时",
         "alternatives": ["审查和整理 Skills"],
         "steps": ["所有 Agent 自创的 Skills 定期审查", "合并重复或相似的技能", "归档过时的，删除无用的"],
         "socratic_hints": ["curator 在英文里是「馆长」的意思", "博物馆馆长干什么？整理收藏品", "这里整理的是 Skills 收藏"],
         "common_errors": {"创建新 Skill": "curator 是管理已有 Skills，不是创建", "删除所有 Skills": "会保留有用的，只清理冗余"},
         "tags": ["Skills", "进阶"], "concept_note": "curator = Skills 管家，防止技能库膨胀。"},
        {"id": "seed-hermes-6", "topic": "持久记忆", "grade": "入门", "difficulty": 1,
         "question": "Hermes Agent 如何在跨会话间保持记忆？", "answer": "通过 MEMORY.md 文件存储 Agent 提炼的关键事实，定期提醒用户回顾和更新",
         "alternatives": ["MEMORY.md 持久化记忆"],
         "steps": ["Agent 在对话中识别值得记住的信息", "写入 MEMORY.md 文件", "新会话自动加载", "定期 nudges 提醒用户更新旧记忆"],
         "socratic_hints": ["文件名叫什么？和记忆有关", "MEMORY.md！", "Agent 自己写、自己读、定期提醒更新"],
         "common_errors": {"数据库": "使用简单的 Markdown 文件", "不提醒更新": "有定期 nudges 机制"},
         "tags": ["记忆", "入门"], "concept_note": "MEMORY.md = Agent 的知识库，自动读写。"},
        {"id": "seed-hermes-7", "topic": "多平台支持", "grade": "入门", "difficulty": 1,
         "question": "Hermes Agent 支持多少个消息平台？", "answer": "20+ 平台：Telegram、Discord、Slack、WhatsApp、Signal、飞书、钉钉、微信、QQ、企业微信等",
         "alternatives": ["20 多个消息平台"],
         "steps": ["同一套 Gateway 进程管理所有平台", "每个平台通过插件接入", "一个 Agent 实例可同时服务多个平台"],
         "socratic_hints": ["你平时用什么聊天工具？", "微信、Telegram、Discord？", "它都支持，而且一个 Gateway 搞定所有"],
         "common_errors": {"只能在终端使用": "支持 Web 和 20+ 聊天平台", "每个平台需要单独部署": "一个 Gateway 管理所有"},
         "tags": ["平台", "入门"], "concept_note": "一个 Agent，20+ 平台同时在线。"},
        {"id": "seed-hermes-8", "topic": "终端界面", "grade": "进阶", "difficulty": 2,
         "question": "hermes --tui 启动的是什么？", "answer": "基于 React/Ink 的全功能交互式终端界面，有粘性输入框、实时 token 流、子代理监控面板",
         "alternatives": ["React/Ink 交互式终端"],
         "steps": ["运行 hermes --tui", "启动 Ink 渲染的终端 UI", "支持实时 token 显示、git 分支、秒表计时"],
         "socratic_hints": ["TUI 是什么的缩写？", "Terminal User Interface", "它是基于什么前端框架？React 的终端版"],
         "common_errors": {"Web 界面": "TUI 是终端界面，不是浏览器", "只能命令行交互": "TUI 模式有完整交互面板"},
         "tags": ["TUI", "进阶"], "concept_note": "hermes --tui = 终端里的完整 Agent 驾驶舱。"},
        {"id": "seed-hermes-9", "topic": "模型接入", "grade": "进阶", "difficulty": 2,
         "question": "Hermes Agent 支持哪些 AI 模型提供商？", "answer": "20+ 提供商：Nous Portal(400+)、OpenRouter(200+)、Anthropic、OpenAI、Gemini、AWS Bedrock、Ollama 等",
         "alternatives": ["20 多个模型提供商"],
         "steps": ["配置文件中指定 provider", "支持多个 provider 切换", "无需修改代码即可换模型"],
         "socratic_hints": ["开源项目的特点就是灵活", "能接哪些？大的小的都行", "从 Anthropic 到本地 Ollama 全支持"],
         "common_errors": {"只能用 OpenAI": "支持 20+ 提供商", "换模型要重新配置": "改一行配置即可切换"},
         "tags": ["模型", "进阶"], "concept_note": "不限模型，20+ 提供商随意切换。"},
        {"id": "seed-hermes-10", "topic": "工具系统", "grade": "进阶", "difficulty": 3,
         "question": "Hermes Agent 的并发工具执行是什么意思？", "answer": "最多 8 个线程池 Worker 并行执行工具调用，而非逐一顺序执行，大幅提升效率",
         "alternatives": ["ThreadPoolExecutor 并行执行"],
         "steps": ["任务需要多次工具调用", "ThreadPoolExecutor 分配 8 个 Worker", "并行执行，汇总结果"],
         "socratic_hints": ["你同时做三件事快还是做一件再做下一件？", "并发 = 同时进行", "最多 8 个并行 Worker"],
         "common_errors": {"顺序执行": "Hermes 是并发执行，效率更高", "只能工具之间顺序": "8 个并行 Worker"},
         "tags": ["工具", "进阶"], "concept_note": "8 路并行工具调用 = 速度快 8 倍。"},
        {"id": "seed-hermes-11", "topic": "插件系统", "grade": "进阶", "difficulty": 2,
         "question": "如何给 Hermes Agent 添加自定义功能？", "answer": "将 Python 文件放入 ~/.hermes/plugins/ 目录，无需 fork 源码，支持工具/命令/钩子/仪表板等类型",
         "alternatives": ["~/.hermes/plugins/ 插件目录"],
         "steps": ["在 ~/.hermes/plugins/ 创建 Python 文件", "定义工具/命令/hooks/TUI面板", "重启 Hermes 自动加载"],
         "socratic_hints": ["放在哪个目录？", "~/.hermes/plugins/", "不需要改源码，丢进去就行"],
         "common_errors": {"需要 fork 源码": "插件系统无需修改核心代码", "仅支持工具": "支持工具/命令/钩子/仪表板/平台"},
         "tags": ["插件", "进阶"], "concept_note": "插件即文件，丢进 plugins 目录就生效。"},
        {"id": "seed-hermes-12", "topic": "终端后端", "grade": "进阶", "difficulty": 2,
         "question": "Hermes Agent 支持哪些终端执行环境？", "answer": "6 种：本地终端、Docker 容器、SSH 远程、Daytona、Singularity、Modal（serverless）",
         "alternatives": ["本地/Docker/SSH/Daytona/Singularity/Modal"],
         "steps": ["默认本地终端", "Docker 提供隔离环境", "SSH 执行远程命令", "Modal 支持 serverless 部署"],
         "socratic_hints": ["不只是本地", "Docker？SSH？", "共 6 种，从本机到云端全覆盖"],
         "common_errors": {"只支持本地": "6 种后端包括 Docker、SSH、serverless", "不支持远程": "SSH 后端支持远程执行"},
         "tags": ["终端", "进阶"], "concept_note": "6 种终端后端：本地 → 容器 → 远程 → 云。"},
        {"id": "seed-hermes-13", "topic": "安全特性", "grade": "进阶", "difficulty": 3,
         "question": "Hermes Agent 有哪些安全防护措施？", "answer": "PII 脱敏、密钥正则脱敏、SSRF 防护、时序攻击缓解、tar 遍历防护、跨会话隔离",
         "alternatives": ["多层安全防护"],
         "steps": ["PII 脱敏：自动检测和遮蔽个人信息", "密钥脱敏：正则匹配 API key 等", "SSRF 防护：防止内网探测", "跨会话隔离：会话间数据不泄露"],
         "socratic_hints": ["安全有哪些方面？", "防止隐私泄露、防止攻击", "6 层防护，面面俱到"],
         "common_errors": {"不需要安全配置": "这些是内置的自动防护", "只有密钥保护": "PII、SSRF、时序攻击都涵盖"},
         "tags": ["安全", "进阶"], "concept_note": "内置 6 层安全防护，无需额外配置。"},
        {"id": "seed-hermes-14", "topic": "语音模式", "grade": "入门", "difficulty": 1,
         "question": "Hermes Agent 的语音模式如何工作？", "answer": "支持按住说话（push-to-talk）+ Whisper 语音转文字 + Discord 语音频道，说完自动转为文本交给 Agent 处理",
         "alternatives": ["push-to-talk + Whisper 转录"],
         "steps": ["按下说话键", "Whisper 实时转录", "文本送入 Agent 处理", "结果返回给用户"],
         "socratic_hints": ["用嘴说话比打字快多了", "语音转文字用的是什么模型？", "Whisper！OpenAI 开源的"],
         "common_errors": {"需要额外安装": "Whisper 是内置依赖", "只能文字回复": "可以文字回复，也可以 TTS 读出"},
         "tags": ["语音", "入门"], "concept_note": "按住说话 → Whisper 转录 → Agent 处理。"},
        {"id": "seed-hermes-15", "topic": "社区生态", "grade": "入门", "difficulty": 1,
         "question": "Hermes Agent 的 GitHub 仓库地址是什么？", "answer": "github.com/NousResearch/hermes-agent（MIT 开源，134k+ stars）",
         "alternatives": ["NousResearch/hermes-agent"],
         "steps": ["GitHub 搜索 hermes-agent", "确认是 NousResearch 组织名下", "MIT 协议，可自由使用和修改"],
         "socratic_hints": ["组织名叫什么？", "Nous Research", "仓库名？hermes-agent"],
         "common_errors": {"hermes": "仓库名是 hermes-agent，不是 hermes", "MiniMax/hermes": "不是 MiniMax，是 NousResearch"},
         "tags": ["社区", "入门"], "concept_note": "NousResearch/hermes-agent，MIT 开源。"},
        {"id": "seed-hermes-16", "topic": "社区生态", "grade": "入门", "difficulty": 1,
         "question": "Hermes Agent 的软件许可证是什么？", "answer": "MIT 开源协议——可自由使用、修改、分发，商业用途也允许",
         "alternatives": ["MIT"],
         "steps": ["MIT 是最宽松的开源协议之一", "允许商业使用", "允许修改和再分发", "只需保留版权声明"],
         "socratic_hints": ["免费吗？", "不仅免费，还能商用", "MIT 协议 = 几乎无限制"],
         "common_errors": {"GPL": "Hermes 使用 MIT 协议，比 GPL 更宽松", "不开源": "开源且 MIT 协议"},
         "tags": ["社区", "入门"], "concept_note": "MIT 开源 = 随便用，商用也 OK。"},
        {"id": "seed-hermes-17", "topic": "Skills 系统", "grade": "进阶", "difficulty": 2,
         "question": "GEPA（Genetic-Pareto Prompt Evolution）是什么？", "answer": "Hermes 自进化研究框架：用遗传算法自动优化 Agent 的 prompt、技能描述和工具说明（ICLR 2026 Oral）",
         "alternatives": ["遗传算法优化 Prompt"],
         "steps": ["分析 Agent 执行轨迹", "用遗传算法生成 Prompt 变体", "Pareto 最优选择"],
         "socratic_hints": ["有没有比手工调 prompt 更自动的方法？", "让 AI 自己调自己的提示词", "用遗传算法，像进化一样"],
         "common_errors": {"深度强化学习": "GEPA 比 GRPO 少 35 倍训练数据，效果还更好", "纯手工调优": "全自动化"},
         "tags": ["Skills", "进阶"], "concept_note": "GEPA = AI 自动进化自己的提示词。"},
        {"id": "seed-hermes-18", "topic": "上下文管理", "grade": "进阶", "difficulty": 2,
         "question": "Hermes Agent 如何处理长对话的上下文问题？", "answer": "内置上下文压缩功能，达到阈值时自动压缩历史对话，保留关键信息",
         "alternatives": ["上下文自动压缩"],
         "steps": ["检测上下文长度", "达到配置阈值", "自动压缩/摘要历史"],
         "socratic_hints": ["对话太长怎么办？", "自动压缩！", "不用手动 /compact，自动完成"],
         "common_errors": {"直接截断": "是智能压缩不是截断", "需要手动触发": "自动检测并压缩"},
         "tags": ["上下文", "进阶"], "concept_note": "上下文自动压缩，长对话不断片。"},
        {"id": "seed-hermes-19", "topic": "搜索功能", "grade": "进阶", "difficulty": 2,
         "question": "Hermes Agent 如何搜索历史会话？", "answer": "FTS5 全文搜索引擎索引所有历史会话，支持 LLM 摘要搜索结果",
         "alternatives": ["FTS5 全文搜索"],
         "steps": ["输入搜索请求", "FTS5 全文索引快速检索", "LLM 对结果做摘要"],
         "socratic_hints": ["上次让 AI 做的一件事怎么找？", "全文搜索所有会话", "不只找出来，还用 AI 总结"],
         "common_errors": {"只能搜文件名": "FTS5 搜的是对话内容", "简单关键字": "有 LLM 摘要，比关键词智能"},
         "tags": ["搜索", "进阶"], "concept_note": "FTS5 + LLM 摘要，找不到的对话都能找到。"},
        {"id": "seed-hermes-20", "topic": "搜索功能", "grade": "进阶", "difficulty": 2,
         "question": "Honcho 集成在 Hermes Agent 中的作用是什么？", "answer": "辩证式用户建模：构建跨会话的持久用户身份模型，理解用户偏好和行为模式",
         "alternatives": ["用户身份和行为建模"],
         "steps": ["跨会话收集用户行为数据", "构建用户模型", "后续会话自动适配用户风格"],
         "socratic_hints": ["AI 能不能越来越懂我？", "有个专门的模块做这件事", "Honcho 建模你的习惯和偏好"],
         "common_errors": {"等于 MEMORY.md": "Honcho 是行为模型，MEMORY.md 是事实存储", "聊天机器人记忆": "是结构化用户模型"},
         "tags": ["模型", "进阶"], "concept_note": "Honcho 让你用得越久，AI 越懂你。"},
    ],
}


# ── 缓存管理 ──────────────────────────────────────────────────
def cache_path(subject: str) -> Path:
    return CACHE_DIR / f"{subject}.json"


# 知识库上下文（由 CLI 设置，AI 出题时注入提示词）
_kb_context: str | None = None


def set_kb_context(text: str | None):
    global _kb_context
    _kb_context = text


def get_kb_context() -> str | None:
    return _kb_context


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

    if not candidates:
        print(f"{Color.YELLOW}⚠ AI 生成失败，请检查网络或稍后重试{Color.RESET}")
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


def _repair_json(text: str) -> str | None:
    """修复 AI 返回的常见 JSON 格式问题：未转义引号、截断等。"""
    import re

    # 1. 找到最外层 { }
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    text = text[start:end + 1]

    # 2. 已知的合法 key 列表，用于定位值边界
    known_keys = [
        "question", "answer", "alternatives", "steps",
        "socratic_hints", "common_errors", "concept_note",
        "focus", "question_type", "rationale", "id", "topic",
        "grade", "difficulty", "tags",
    ]

    # 3. 逐个 key 安全提取，重建干净 JSON
    result = {}
    pos = 0
    while pos < len(text):
        # 跳过空白和逗号
        while pos < len(text) and text[pos] in " \t\n\r,":
            pos += 1
        if pos >= len(text) or text[pos] == "}":
            break

        # 匹配 key: "xxx"
        key_match = re.match(r'"([^"]+)"\s*:\s*', text[pos:])
        if not key_match:
            # 可能是数组成员，跳过
            pos += 1
            continue
        key = key_match.group(1)
        pos += key_match.end()

        if pos >= len(text):
            break

        if text[pos] == '"':
            # 字符串值：找到结束引号（后面跟 , 或 }）
            pos += 1  # skip opening quote
            val_start = pos
            escaped_val = []
            while pos < len(text):
                ch = text[pos]
                if ch == '\\' and pos + 1 < len(text):
                    escaped_val.append(ch)
                    escaped_val.append(text[pos + 1])
                    pos += 2
                elif ch == '"':
                    # 检查后面是否 , 或 }（表示值结束）
                    after = pos + 1
                    while after < len(text) and text[after] in " \t\n\r":
                        after += 1
                    if after < len(text) and text[after] in ",}]":
                        pos += 1  # skip closing quote
                        break
                    else:
                        # 字符串内的未转义引号，转义它
                        escaped_val.append('\\')
                        escaped_val.append('"')
                        pos += 1
                else:
                    escaped_val.append(ch)
                    pos += 1
            result[key] = "".join(escaped_val)
        elif text[pos] == "[":
            # 数组值：找到匹配的 ]，安全提取字符串元素
            depth = 1
            pos += 1
            arr_items = []
            while pos < len(text) and depth > 0:
                ch = text[pos]
                if ch == "[":
                    depth += 1
                    pos += 1
                elif ch == "]":
                    depth -= 1
                    if depth == 0:
                        pos += 1
                        break
                    pos += 1
                elif ch == '"':
                    # 提取数组内的字符串元素（处理未转义引号）
                    pos += 1
                    elem_chars = []
                    while pos < len(text):
                        if text[pos] == '\\' and pos + 1 < len(text):
                            elem_chars.append(text[pos])
                            elem_chars.append(text[pos + 1])
                            pos += 2
                        elif text[pos] == '"':
                            # 检查后面是逗号还是 ]
                            after = pos + 1
                            while after < len(text) and text[after] in " \t\n\r":
                                after += 1
                            if after < len(text) and text[after] in ",]":
                                pos += 1
                                arr_items.append("".join(elem_chars))
                                break
                            else:
                                elem_chars.append('\\')
                                elem_chars.append('"')
                                pos += 1
                        else:
                            elem_chars.append(text[pos])
                            pos += 1
                    # 跳过逗号
                    while pos < len(text) and text[pos] in " \t\n\r," and text[pos] != "]":
                        pos += 1
                else:
                    pos += 1
            result[key] = arr_items
        elif text[pos] == "{":
            # 嵌套对象（如 common_errors）：匹配括号，递归提取键值对
            depth = 1
            pos += 1
            obj_start = pos
            while pos < len(text) and depth > 0:
                if text[pos] == "{":
                    depth += 1
                elif text[pos] == "}":
                    depth -= 1
                if depth > 0:
                    pos += 1
            obj_text = text[obj_start:pos]
            pos += 1
            # 安全提取嵌套对象的键值对
            pairs = {}
            ip = 0
            while ip < len(obj_text):
                while ip < len(obj_text) and obj_text[ip] in " \t\n\r,":
                    ip += 1
                if ip >= len(obj_text):
                    break
                # 匹配 key
                km = re.match(r'"([^"]+)"\s*:\s*', obj_text[ip:])
                if not km:
                    ip += 1
                    continue
                nkey = km.group(1)
                ip += km.end()
                if ip >= len(obj_text):
                    break
                if obj_text[ip] == '"':
                    ip += 1
                    nval_chars = []
                    while ip < len(obj_text):
                        if obj_text[ip] == '\\' and ip + 1 < len(obj_text):
                            nval_chars.append(obj_text[ip])
                            nval_chars.append(obj_text[ip + 1])
                            ip += 2
                        elif obj_text[ip] == '"':
                            after = ip + 1
                            while after < len(obj_text) and obj_text[after] in " \t\n\r":
                                after += 1
                            if after >= len(obj_text) or obj_text[after] in ",}":
                                ip += 1
                                pairs[nkey] = "".join(nval_chars)
                                break
                            else:
                                nval_chars.append('\\')
                                nval_chars.append('"')
                                ip += 1
                        else:
                            nval_chars.append(obj_text[ip])
                            ip += 1
                else:
                    ip += 1
            result[key] = pairs
        else:
            # 数字/布尔/null
            m = re.match(r'(-?\d+\.?\d*|true|false|null)', text[pos:])
            if m:
                if key in known_keys:
                    val = m.group(1)
                    result[key] = int(val) if val.isdigit() else (
                        float(val) if "." in val else
                        True if val == "true" else
                        False if val == "false" else None
                    )
                pos += m.end()
            else:
                pos += 1

    if not result:
        return None

    # 验证必须有 core 字段
    core = {"question", "answer"}
    if not core.issubset(result.keys()):
        return None

    return json.dumps(result, ensure_ascii=False)


def _generate(subject: str, topic: str | None = None) -> dict | None:
    """两阶段出题：Idea → Generator，产出更高质量题目"""
    name = SUBJECT_NAMES.get(subject, "数学")
    tag = SUBJECT_TAGS.get(subject, "gen")

    if not topic:
        existing = load_cache(subject)
        topics = sorted(set(p["topic"] for p in existing))
        topic = topics[len(topics) // 2] if topics else "综合"

    timestamp = int(time.time())
    rnd.seed(timestamp)
    difficulty = rnd.choice([1, 2, 3])

    # ── Claude 科目专用出题 ──
    if subject == "claude":
        return _generate_claude(subject, tag, topic, difficulty, timestamp)

    # ── Hermes 科目专用出题 ──
    if subject == "hermes":
        return _generate_hermes(subject, tag, topic, difficulty, timestamp)

    diff_label = "简单" if difficulty == 1 else "中等" if difficulty == 2 else "较难"
    # math 科目优先用 wiki-math 的教材年级
    if subject == "math" and wiki_available():
        grade = wiki_get_grade(topic) or "初二"
    else:
        grade = "初一" if difficulty <= 1 else "初二" if difficulty <= 2 else "初三"
    qid = f"{tag}-gen-{timestamp}"

    SGPT = "sgpt"

    # ── Stage 1: Idea Agent（出题规划） ──
    # 分析已有题目，确保新题不重复
    existing = load_cache(subject)
    existing_topics = set(p["topic"] for p in existing)
    existing_questions = [p["question"][:30] for p in existing[-10:]]

    print(f"\n{Color.CYAN}🤖 正在规划新题目（第一阶段：出题构思）…{Color.RESET}")

    kb_text = get_kb_context()
    kb_hint = f"\n\n请严格根据以下教材内容出题：\n{kb_text[:2000]}\n" if kb_text else ""

    # ── math 科目：自动加载 wiki-math 上下文 ──
    wiki_hint = ""
    if subject == "math" and wiki_available():
        wiki_text = get_wiki_context(topic)
        if wiki_text:
            wiki_hint = f"\n\n请严格根据以下教材内容出题（这些内容来自人教版课本知识库）：\n{wiki_text[:2500]}\n"
            if not kb_hint:
                kb_hint = wiki_hint
            else:
                kb_hint = wiki_hint + "\n（用户自定义知识库已同时加载，优先参考教材知识库）"

    idea_prompt = (
        f"你是一位初中{name}出题规划师。请为一道{name}题做规划。\n"
        f"主题范围：{topic}。难度：{diff_label}({difficulty}/3)。\n"
        f"已考过的主题：{', '.join(list(existing_topics)[:8]) or '无'}。\n"
        f"最近出过的题：{', '.join(existing_questions) or '无'}。\n"
        f"{kb_hint}\n"
        "请输出一行JSON规划，不要markdown，格式：\n"
        '{"focus":"具体考察点（与已考过的区分开）","question_type":"计算|概念|应用","rationale":"为什么出这道题"}\n'
        "要求：focus 要具体，不要和已考主题重复太多次。"
    )

    try:
        result = sp.run([SGPT, idea_prompt], capture_output=True, text=True, timeout=20)
        if result.returncode != 0:
            print(f"{Color.YELLOW}⚠ 出题构思失败，尝试降级出题：{result.stderr.strip()[:200]}{Color.RESET}")
            return _generate_fallback(subject, topic, tag, timestamp, difficulty, grade, qid)
        idea_text = " ".join(l for l in result.stdout.split("\n") if not l.startswith("Warning:")).strip()
        idea_text = idea_text.replace("```json", "").replace("```", "").strip()
        idea = json.loads(idea_text)
        focus = idea.get("focus", topic)
    except Exception as e:
        print(f"{Color.YELLOW}⚠ 出题构思异常，跳过规划阶段：{e}{Color.RESET}")
        focus = topic

    # ── Stage 2: Generator（出题执行） ──
    print(f"{Color.GREEN}✅ 构思完成，正在生成题目（第二阶段：出题执行）…{Color.RESET}")
    gen_prompt = (
        f"你是一位初中{name}老师。请根据以下出题规划出一道具体的{name}题。\n"
        f"主题：{topic}\n具体考察点：{focus}\n难度：{diff_label}({difficulty}/3)\n年级：{grade}\n"
        f"{wiki_hint}\n"
        "只输出一行JSON，不要markdown，不要换行。格式：\n"
        '{"question":"题目","answer":"正确答案","alternatives":["备选格式1"],'
        '"steps":["步骤1","步骤2","步骤3"],'
        '"socratic_hints":["提示1（模糊引导思路）","提示2（更具体指出关键）","提示3（接近答案但不说答案）"],'
        '"common_errors":{"错误答案1":"针对性反馈","错误答案2":"针对性反馈","错误答案3":"针对性反馈"},'
        '"concept_note":"一句话核心概念"}\n'
        "要求：\n"
        "- socratic_hints必须正好3条，逐步引导但不直接给答案\n"
        "- common_errors至少3条常见错误\n"
        "- 题目要有新意，不要和提示中的示例重复"
    )

    try:
        result = sp.run([SGPT, gen_prompt], capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            print(f"{Color.YELLOW}⚠ AI 出题失败：{result.stderr.strip()[:200]}{Color.RESET}")
            return _generate_fallback(subject, topic, tag, timestamp, difficulty, grade, qid)
        text = " ".join(l for l in result.stdout.split("\n") if not l.startswith("Warning:")).strip()
        text = text.replace("```json", "").replace("```", "").strip()
        try:
            problem = json.loads(text)
        except json.JSONDecodeError as e:
            repaired = _repair_json(text)
            if repaired:
                try:
                    problem = json.loads(repaired)
                    print(f"{Color.DIM}  JSON 修复成功{Color.RESET}")
                except json.JSONDecodeError:
                    print(f"{Color.YELLOW}⚠ AI 返回格式异常：{e}{Color.RESET}")
                    return _generate_fallback(subject, topic, tag, timestamp, difficulty, grade, qid)
            else:
                print(f"{Color.YELLOW}⚠ AI 返回格式异常：{e}{Color.RESET}")
                return _generate_fallback(subject, topic, tag, timestamp, difficulty, grade, qid)
        required = ["question", "answer", "steps", "socratic_hints", "common_errors"]
        if not all(f in problem for f in required):
            missing = [f for f in required if f not in problem]
            print(f"{Color.YELLOW}⚠ AI 生成题目缺少字段：{missing}{Color.RESET}")
            return _generate_fallback(subject, topic, tag, timestamp, difficulty, grade, qid)

        # 组装完整题目
        problem["id"] = qid
        problem["topic"] = topic
        problem["grade"] = grade
        problem["difficulty"] = difficulty
        problem.setdefault("alternatives", [])
        problem.setdefault("tags", [topic, "自动生成"])
        problem.setdefault("concept_note", "")
        problem["focus"] = focus
        while len(problem.get("socratic_hints", [])) < 3:
            problem["socratic_hints"].append("再想想，你离答案很近了！")

        # 清理 LaTeX
        problem["question"] = latex_to_plain(problem["question"])
        problem["answer"] = latex_to_plain(problem["answer"])
        problem["concept_note"] = latex_to_plain(problem.get("concept_note", ""))
        problem["steps"] = [latex_to_plain(s) for s in problem["steps"]]
        problem["socratic_hints"] = [latex_to_plain(h) for h in problem["socratic_hints"]]
        problem["common_errors"] = {latex_to_plain(k): latex_to_plain(v) for k, v in problem["common_errors"].items()}

        return problem
    except Exception as e:
        print(f"{Color.YELLOW}⚠ AI 出题异常：{e}{Color.RESET}")
        return _generate_fallback(subject, topic, tag, timestamp, difficulty, grade, qid)


def _generate_fallback(subject, topic, tag, timestamp, difficulty, grade, qid) -> dict | None:
    """单阶段降级：一步生成（当两阶段失败时）"""
    prompt = (
        "你是一位中国初中" + SUBJECT_NAMES.get(subject, "数学") + "老师。出一道初中题。\n"
        f"主题：{topic}。难度：{'简单' if difficulty == 1 else '中等' if difficulty == 2 else '较难'}({difficulty}/3)。\n"
        "只输出一行JSON，不要markdown，不要换行。格式：\n"
        '{"question":"题目","answer":"答案","alternatives":["备选"],'
        '"steps":["步骤1","步骤2"],"socratic_hints":["提示1","提示2","提示3"],'
        '"common_errors":{"错1":"反馈1","错2":"反馈2","错3":"反馈3"},"concept_note":"一句话"}\n'
        "要求：socratic_hints必须3条，common_errors至少3条。"
    )
    try:
        result = sp.run(["sgpt", prompt], capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            print(f"{Color.YELLOW}⚠ 降级出题也失败：{result.stderr.strip()[:200]}{Color.RESET}")
            return None
        text = " ".join(l for l in result.stdout.split("\n") if not l.startswith("Warning:")).strip()
        text = text.replace("```json", "").replace("```", "").strip()
        try:
            problem = json.loads(text)
        except json.JSONDecodeError as e:
            repaired = _repair_json(text)
            if repaired:
                try:
                    problem = json.loads(repaired)
                    print(f"{Color.DIM}  降级 JSON 修复成功{Color.RESET}")
                except json.JSONDecodeError:
                    print(f"{Color.YELLOW}⚠ 降级出题 JSON 异常：{e}{Color.RESET}")
                    return None
            else:
                print(f"{Color.YELLOW}⚠ 降级出题 JSON 异常：{e}{Color.RESET}")
                return None
        required = ["question", "answer", "steps", "socratic_hints", "common_errors"]
        if not all(f in problem for f in required):
            missing = [f for f in required if f not in problem]
            print(f"{Color.YELLOW}⚠ 降级出题缺少字段：{missing}{Color.RESET}")
            return None
        problem["id"] = qid
        problem["topic"] = topic
        problem["grade"] = grade
        problem["difficulty"] = difficulty
        problem.setdefault("alternatives", [])
        problem.setdefault("tags", [topic, "自动生成"])
        problem.setdefault("concept_note", "")
        while len(problem.get("socratic_hints", [])) < 3:
            problem["socratic_hints"].append("再想想！")
        problem["question"] = latex_to_plain(problem["question"])
        problem["answer"] = latex_to_plain(problem["answer"])
        return problem
    except Exception as e:
        print(f"{Color.YELLOW}⚠ 降级出题异常：{e}{Color.RESET}")
        return None


# ── Claude 科目专用 AI 出题 ────────────────────────────────────────

CLAUDE_MODULES = {
    "Slash Commands": "内置斜杠命令（/help, /clear, /model 等）、技能命令、插件命令、MCP 提示词命令",
    "Memory": "CLAUDE.md 记忆文件、记忆优先级、Auto Memory、规则系统",
    "Skills": "SKILL.md 技能定义、渐进式加载、参数替换、内置技能",
    "Subagents": "子代理配置、工具权限、内置子代理、Agent Teams",
    "MCP": "Model Context Protocol、MCP 服务器、传输类型、MCP 提示词",
    "Hooks": "事件驱动钩子、工具钩子、会话钩子、生命周期钩子",
    "Plugins": "插件系统、LSP 支持、插件市场、userConfig",
    "Checkpoints": "检查点、撤销/恢复、分支探索",
    "Advanced": "规划模式、扩展思考、自动模式、后台任务、权限模式、CLI 模式、工作树、远程控制",
    "CLI": "CLI 命令行标志、Print 模式、输出格式",
    "综合": "跨模块综合知识",
}

CLAUDE_GRADES = {1: "入门", 2: "进阶", 3: "高级"}


def _generate_claude(subject: str, tag: str, topic: str, difficulty: int, timestamp: int) -> dict | None:
    """为 claude 科目 AI 出题（单阶段，英文/双语）"""
    import subprocess as sp
    import json as _json

    grade = CLAUDE_GRADES.get(difficulty, "入门")
    qid = f"{tag}-gen-{timestamp}"
    level_name = grade

    module_info = CLAUDE_MODULES.get(topic, "Claude Code 相关知识")
    existing = load_cache(subject)
    existing_questions = [p["question"][:40] for p in existing[-5:]]

    prompt = f"""You are a Claude Code expert and quiz creator. Create a quiz question about Claude Code.

Topic: {topic}
Difficulty level: {level_name} ({difficulty}/3)
What this topic covers: {module_info}
Recent questions on this topic: {', '.join(existing_questions) or 'None yet'}

Requirements:
1. The question should test practical knowledge of Claude Code
2. For difficulty 1 (入门): basic command names, concepts, simple recall
3. For difficulty 2 (进阶): understanding relationships, configuration, best practices  
4. For difficulty 3 (高级): advanced features, edge cases, integration patterns
5. Write the question in Chinese (题目用中文)
6. Answers can include English terms (命令/概念用英文)

Output ONLY valid JSON, no markdown, no explanation. Format:
{{"question":"题目内容（中文）","answer":"正确答案","alternatives":["备选答案1","备选答案2"],"steps":["步骤1","步骤2","步骤3"],"socratic_hints":["提示1（模糊引导）","提示2（更具体）","提示3（接近答案）"],"common_errors":{{"错误答案1":"针对性反馈","错误答案2":"针对性反馈","错误答案3":"针对性反馈"}},"concept_note":"一句话核心概念","tags":["{topic}","{grade}"]}}
"""

    print(f"\n{Color.CYAN}🤖 正在为 [{topic}] 生成 Claude Code 题目…{Color.RESET}")

    try:
        result = sp.run(["sgpt", prompt], capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            return _generate_claude_fallback(topic, tag, grade, difficulty, timestamp)

        text = " ".join(l for l in result.stdout.split("\n") if not l.startswith("Warning:")).strip()
        text = text.replace("```json", "").replace("```", "").strip()
        problem = _json.loads(text)

        required = ["question", "answer", "steps", "socratic_hints", "common_errors"]
        if not all(f in problem for f in required):
            return _generate_claude_fallback(topic, tag, grade, difficulty, timestamp)

        problem["id"] = qid
        problem["topic"] = topic
        problem["grade"] = grade
        problem["difficulty"] = difficulty
        problem.setdefault("alternatives", [])
        problem.setdefault("tags", [topic, "AI生成"])
        problem.setdefault("concept_note", "")
        while len(problem.get("socratic_hints", [])) < 3:
            problem["socratic_hints"].append("再想想，你离答案很近了！")

        # 清理（没有 LaTeX 但保留兼容）
        problem["question"] = latex_to_plain(problem["question"])
        problem["answer"] = latex_to_plain(problem["answer"])
        problem["concept_note"] = latex_to_plain(problem.get("concept_note", ""))
        problem["steps"] = [latex_to_plain(s) for s in problem["steps"]]
        problem["socratic_hints"] = [latex_to_plain(h) for h in problem["socratic_hints"]]
        problem["common_errors"] = {latex_to_plain(k): latex_to_plain(v) for k, v in problem["common_errors"].items()}

        print(f"{Color.GREEN}✅ 新题生成成功！{Color.RESET}")
        return problem
    except Exception:
        return _generate_claude_fallback(topic, tag, grade, difficulty, timestamp)


def _generate_claude_fallback(topic: str, tag: str, grade: str, difficulty: int, timestamp: int) -> dict | None:
    """Claude 出题降级方案"""
    import subprocess as sp
    import json as _json

    qid = f"{tag}-gen-{timestamp}"
    prompt = f"""You are a Claude Code expert. Create a quiz question about Claude Code.

Topic: {topic}
Level: {grade} ({difficulty}/3)
Output ONLY valid JSON: {{"question":"...","answer":"...","alternatives":[],"steps":["1","2","3"],"socratic_hints":["hint1","hint2","hint3"],"common_errors":{{"wrong":"feedback"}},"concept_note":"..."}}
"""

    try:
        result = sp.run(["sgpt", prompt], capture_output=True, text=True, timeout=20)
        if result.returncode != 0:
            return None
        text = " ".join(l for l in result.stdout.split("\n") if not l.startswith("Warning:")).strip()
        text = text.replace("```json", "").replace("```", "").strip()
        problem = _json.loads(text)

        required = ["question", "answer", "steps", "socratic_hints", "common_errors"]
        if not all(f in problem for f in required):
            return None

        problem["id"] = qid
        problem["topic"] = topic
        problem["grade"] = grade
        problem["difficulty"] = difficulty
        problem.setdefault("alternatives", [])
        problem.setdefault("tags", [topic, "AI生成"])
        problem.setdefault("concept_note", "")
        while len(problem.get("socratic_hints", [])) < 3:
            problem["socratic_hints"].append("再想想！")

        problem["question"] = latex_to_plain(problem["question"])
        problem["answer"] = latex_to_plain(problem["answer"])
        return problem
    except Exception:
        return None


# ── Hermes 科目专用 AI 出题 ──────────────────────────────────────

HERMES_MODULES = {
    "CLI与基础": "hermes 命令、全局标志、安装、启动、退出、帮助",
    "斜杠命令": "/new, /model, /help, /retry, /undo, /compress, /rollback 等会话内命令",
    "配置": "config.yaml 各个配置段、.env 环境变量、hermes config 系列命令",
    "提供商": "20+ LLM 提供商（OpenRouter、Anthropic、OpenAI、DeepSeek、Google 等）",
    "工具集": "20+ 工具集（file、web、browser、terminal、code_execution、delegation 等）",
    "网关平台": "Telegram、Discord、Slack、WhatsApp、Signal、Email 等 15+ 消息平台",
    "技能系统": "Skills 的创建、安装、搜索、发布、更新、管理",
    "MCP": "Model Context Protocol 服务器管理、工具注入",
    "会话管理": "会话的创建、恢复、浏览、导出、删除、分叉",
    "记忆系统": "跨会话持久化记忆、用户画像、Auto Memory、记忆提供商",
    "Cron 与 Webhook": "定时任务、Webhook 订阅、事件驱动触发",
    "配置文件": "config.yaml 结构、hermes config 系列命令、环境变量",
    "语音与转录": "语音输入（STT）和语音输出（TTS）配置和使用",
    "Profiles": "多配置隔离、Profile 创建/克隆/切换/导出",
    "凭证池": "API 密钥轮换、多凭证管理、认证",
    "高级功能": "Worktree、子代理、后台任务、检查点、压缩、协作",
    "开发与贡献": "添加工具、添加斜杠命令、测试、项目结构、PR 规范",
    "故障排除": "常见问题排查、日志查看、配置检查、平台特定问题",
    "综合": "跨模块综合知识",
}

HERMES_GRADES = {1: "入门", 2: "进阶", 3: "高级"}


def _generate_hermes(subject: str, tag: str, topic: str, difficulty: int, timestamp: int) -> dict | None:
    """为 hermes 科目 AI 出题"""
    import subprocess as sp
    import json as _json

    grade = HERMES_GRADES.get(difficulty, "入门")
    qid = f"{tag}-gen-{timestamp}"
    module_info = HERMES_MODULES.get(topic, "Hermes Agent 相关知识")
    existing = load_cache(subject)
    existing_questions = [p["question"][:40] for p in existing[-5:]]

    prompt = f"""You are a Hermes Agent expert and quiz creator. Create a quiz question about Hermes Agent (the open-source AI agent framework by Nous Research).

Topic: {topic}
Difficulty level: {grade} ({difficulty}/3)
What this topic covers: {module_info}
Recent questions on this topic: {', '.join(existing_questions) or 'None yet'}

Requirements:
1. The question should test practical knowledge of Hermes Agent
2. For difficulty 1 (入门): basic commands, concepts, simple recall
3. For difficulty 2 (进阶): understanding relationships, configuration, best practices
4. For difficulty 3 (高级): advanced features, edge cases, integration patterns
5. Write the question in Chinese (题目用中文)
6. Answers can include English terms (命令/概念用英文)
7. Focus on accurate, factual information about Hermes Agent

Output ONLY valid JSON, no markdown, no explanation. Format:
{{"question":"题目内容（中文）","answer":"正确答案","alternatives":["备选答案1","备选答案2"],"steps":["步骤1","步骤2","步骤3"],"socratic_hints":["提示1（模糊引导）","提示2（更具体）","提示3（接近答案）"],"common_errors":{{"错误答案1":"针对性反馈","错误答案2":"针对性反馈","错误答案3":"针对性反馈"}},"concept_note":"一句话核心概念","tags":["{topic}","{grade}"]}}
"""

    print(f"\n{Color.CYAN}🤖 正在为 [{topic}] 生成 Hermes 题目…{Color.RESET}")

    try:
        result = sp.run(["sgpt", prompt], capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            return _generate_hermes_fallback(topic, tag, grade, difficulty, timestamp)

        text = " ".join(l for l in result.stdout.split("\n") if not l.startswith("Warning:")).strip()
        text = text.replace("```json", "").replace("```", "").strip()
        problem = _json.loads(text)

        required = ["question", "answer", "steps", "socratic_hints", "common_errors"]
        if not all(f in problem for f in required):
            return _generate_hermes_fallback(topic, tag, grade, difficulty, timestamp)

        problem["id"] = qid
        problem["topic"] = topic
        problem["grade"] = grade
        problem["difficulty"] = difficulty
        problem.setdefault("alternatives", [])
        problem.setdefault("tags", [topic, "AI生成"])
        problem.setdefault("concept_note", "")
        while len(problem.get("socratic_hints", [])) < 3:
            problem["socratic_hints"].append("再想想，你离答案很近了！")

        problem["question"] = latex_to_plain(problem["question"])
        problem["answer"] = latex_to_plain(problem["answer"])
        problem["concept_note"] = latex_to_plain(problem.get("concept_note", ""))
        problem["steps"] = [latex_to_plain(s) for s in problem["steps"]]
        problem["socratic_hints"] = [latex_to_plain(h) for h in problem["socratic_hints"]]
        problem["common_errors"] = {latex_to_plain(k): latex_to_plain(v) for k, v in problem["common_errors"].items()}

        print(f"{Color.GREEN}✅ 新题生成成功！{Color.RESET}")
        return problem
    except Exception:
        return _generate_hermes_fallback(topic, tag, grade, difficulty, timestamp)


def _generate_hermes_fallback(topic: str, tag: str, grade: str, difficulty: int, timestamp: int) -> dict | None:
    """Hermes 出题降级方案"""
    import subprocess as sp
    import json as _json

    qid = f"{tag}-gen-{timestamp}"
    prompt = f"""You are a Hermes Agent expert. Create a quiz question about Hermes Agent.

Topic: {topic}
Level: {grade} ({difficulty}/3)
Output ONLY valid JSON: {{"question":"...","answer":"...","alternatives":[],"steps":["1","2","3"],"socratic_hints":["hint1","hint2","hint3"],"common_errors":{{"wrong":"feedback"}},"concept_note":"..."}}
"""

    try:
        result = sp.run(["sgpt", prompt], capture_output=True, text=True, timeout=20)
        if result.returncode != 0:
            return None
        text = " ".join(l for l in result.stdout.split("\n") if not l.startswith("Warning:")).strip()
        text = text.replace("```json", "").replace("```", "").strip()
        problem = _json.loads(text)

        required = ["question", "answer", "steps", "socratic_hints", "common_errors"]
        if not all(f in problem for f in required):
            return None

        problem["id"] = qid
        problem["topic"] = topic
        problem["grade"] = grade
        problem["difficulty"] = difficulty
        problem.setdefault("alternatives", [])
        problem.setdefault("tags", [topic, "AI生成"])
        problem.setdefault("concept_note", "")
        while len(problem.get("socratic_hints", [])) < 3:
            problem["socratic_hints"].append("再想想！")

        problem["question"] = latex_to_plain(problem["question"])
        problem["answer"] = latex_to_plain(problem["answer"])
        return problem
    except Exception:
        return None
