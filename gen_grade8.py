"""稳定批量生成八年级数学题"""
import sys, json
from pathlib import Path
sys.path.insert(0, '/home/user/socratic')

from socratic.cache import get_problems, load_cache, save_cache, set_kb_context
from socratic.kb import kb_get_content

# 加载 KB
kb = kb_get_content('math_bsd')
if not kb:
    print("KB 为空!")
    sys.exit(1)
set_kb_context(kb)

# 读取当前缓存
cache = load_cache('math')
existing_ids = {p['id'] for p in cache}
existing_qs = {p['question'] for p in cache}
print(f"当前缓存: {len(cache)} 题")

# 八年级各章，每章生成 1-2 题
chapters = [
    ("勾股定理", 1), ("实数", 2), ("一次函数", 2),
    ("二元一次方程组", 2), ("数据的分析", 1),
    ("全等三角形", 2), ("因式分解", 1),
    ("分式与分式方程", 1), ("平行四边形", 1),
    ("不等式", 1), ("平移与旋转", 1),
]

total_new = 0
for ch, count in chapters:
    # 检查此主题已有题数
    existing_count = sum(1 for p in cache if p.get("topic") == ch)
    needed = max(0, count - existing_count)
    
    if needed <= 0:
        print(f"  {ch}: 暂无 {existing_count}/{count}")
        continue
    
    print(f"  {ch}: 需要 {needed} 题... ", end="", flush=True)
    try:
        done_ids = {p['id'] for p in cache if p.get("topic") == ch}
        new_list = get_problems('math', count=needed, topic=ch, exclude_ids=done_ids)
        if new_list:
            for p in new_list:
                if p['question'] not in existing_qs:
                    cache.append(p)
                    existing_qs.add(p['question'])
                    total_new += 1
            print(f"✅ +{len(new_list)}")
        else:
            print(f"⚠ 返回空")
    except Exception as e:
        print(f"❌ {e}")

save_cache('math', cache)
print(f"\n保存: {len(cache)} 题 (新增 {total_new})")
