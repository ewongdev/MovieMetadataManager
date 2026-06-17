"""
actor_grouper.py
功能：按演员名对文件夹进行归类。同一影片包含多个演员时，演员参演影片数量多的优先。
"""

import os
import re
import shutil
from collections import defaultdict

# ==================== 配置区域 ====================
# 需归类文件夹路径（支持遍历其下的所有子文件夹）
SOURCE_ROOT = r"D:\归类前测试"
# 整理后文件夹路径
OUTPUT_ROOT = r"D:\归类后测试"
# 最小归类视频数（实际视频数可能会少，会被其他演员归类）
MIN_COUNT = 4
# 其他零散视频所属文件夹
COLLECTION_NAME = "影片合集"
# ==================================================

# 正则：提取 <actor> ... </actor> 区块内的 <name>...</name>
RE_ACTOR_BLOCK = re.compile(r"<actor\b[^>]*>(.*?)</actor>", re.IGNORECASE | re.DOTALL)
RE_NAME = re.compile(r"<name\b[^>]*>(.*?)</name>", re.IGNORECASE | re.DOTALL)

def extract_actor_names_from_text(text):
    """从 nfo 文本中提取所有演员名"""
    names = []
    for block in RE_ACTOR_BLOCK.findall(text):
        m = RE_NAME.search(block)
        if m:
            name = m.group(1).strip()
            if name:
                names.append(name)
    return names

def safe_move_folder(src_folder, dest_parent):
    """安全移动文件夹，重复名自动加后缀"""
    base_name = os.path.basename(src_folder.rstrip("\\/"))
    dest = os.path.join(dest_parent, base_name)
    os.makedirs(dest_parent, exist_ok=True)
    if not os.path.exists(dest):
        shutil.move(src_folder, dest)
        return dest
    i = 1
    while True:
        candidate = f"{dest} ({i})"
        if not os.path.exists(candidate):
            shutil.move(src_folder, candidate)
            return candidate
        i += 1

def main():
    print("开始扫描 NFO 文件...")
    nfo_files = []
    for root, dirs, files in os.walk(SOURCE_ROOT):
        for f in files:
            if f.lower().endswith(".nfo"):
                nfo_files.append(os.path.join(root, f))
    print(f"找到 {len(nfo_files)} 个 .nfo 文件，开始解析...")

    actor_to_nfos = defaultdict(set)
    nfo_to_actors = {}

    for nfo in nfo_files:
        try:
            with open(nfo, "r", encoding="utf-8", errors="ignore") as fh:
                text = fh.read()
        except Exception as e:
            print(f"无法读取文件 {nfo}: {e}")
            continue
        names = extract_actor_names_from_text(text)
        # 去重同一 nfo 内重复的演员名
        unique_names = []
        seen = set()
        for nm in names:
            nm_norm = nm.strip()
            if nm_norm and nm_norm not in seen:
                seen.add(nm_norm)
                unique_names.append(nm_norm)
        nfo_to_actors[nfo] = unique_names
        for nm in unique_names:
            actor_to_nfos[nm].add(nfo)

    # 统计满足阈值的演员
    qualified_actors = {actor: nfos for actor, nfos in actor_to_nfos.items() if len(nfos) >= MIN_COUNT}
    print(f"满足阈值（至少 {MIN_COUNT} 个 .nfo）的演员数量：{len(qualified_actors)}")

    # 为每 nfo 决定目标文件夹
    folder_move_plan = {}  # folder_path -> target_actor_or_collection
    actor_counts = {actor: len(nfos) for actor, nfos in qualified_actors.items()}

    for nfo, actors in nfo_to_actors.items():
        folder = os.path.abspath(os.path.dirname(nfo))
        if folder in folder_move_plan:
            continue
        candidates = [a for a in actors if a in qualified_actors]
        if candidates:
            candidates.sort(key=lambda a: (-actor_counts.get(a,0), a))
            folder_move_plan[folder] = candidates[0]
        else:
            folder_move_plan[folder] = COLLECTION_NAME

    # ===== 记录每个 nfo 最终归属，用于共演差异分析 =====
    nfo_final_owner = {}  # nfo path -> 最终归属演员或 COLLECTION_NAME
    for nfo in nfo_to_actors:
        folder = os.path.abspath(os.path.dirname(nfo))
        target = folder_move_plan.get(folder, COLLECTION_NAME)
        nfo_final_owner[nfo] = target

    # 执行移动
    os.makedirs(OUTPUT_ROOT, exist_ok=True)
    moved_folders = []
    moved_to_actor = defaultdict(list)
    moved_to_collection = []
    failed_moves = []
    actor_final_counts = defaultdict(int)  # 记录最终归类到演员目录的数量

    # 按路径深度倒序，避免父目录先移动
    folders_sorted = sorted(folder_move_plan.keys(), key=lambda p: p.count(os.sep), reverse=True)

    for folder in folders_sorted:
        target = folder_move_plan[folder]
        if target == COLLECTION_NAME:
            dest_parent = os.path.join(OUTPUT_ROOT, COLLECTION_NAME)
        else:
            safe_name = "".join(c for c in target if c not in r'\/:*?"<>|').strip()
            if not safe_name:
                safe_name = target.replace(" ", "_")
            dest_parent = os.path.join(OUTPUT_ROOT, safe_name)

        abs_folder = os.path.abspath(folder)
        abs_output = os.path.abspath(OUTPUT_ROOT)
        try:
            if os.path.commonpath([abs_folder, abs_output]) == abs_output:
                continue
        except:
            pass

        try:
            final_dest = safe_move_folder(abs_folder, dest_parent)
            moved_folders.append((abs_folder, final_dest))
            if target == COLLECTION_NAME:
                moved_to_collection.append(final_dest)
            else:
                moved_to_actor[target].append(final_dest)
                actor_final_counts[target] += 1
        except Exception as e:
            failed_moves.append((abs_folder, dest_parent, str(e)))

    # ===== 汇总报告 =====
    print("\n===== 归类完成汇总 =====")
    print(f"总视频数：{len(nfo_files)}")
    print(f"计划移动文件夹数：{len(folder_move_plan)}")
    print(f"成功移动文件夹数：{len(moved_folders)}")
    print(f"失败移动文件夹数：{len(failed_moves)}")
    print(f"归入演员文件夹的演员数：{len(moved_to_actor)}")
    for actor, folders in sorted(moved_to_actor.items(), key=lambda x: -len(x[1])):
        print(f"  {actor} -> {len(folders)} 个文件夹")
    print(f"归入“{COLLECTION_NAME}”的文件夹数：{len(moved_to_collection)}")

    if failed_moves:
        print("\n失败列表：")
        for src, dst, err in failed_moves:
            print(f"  {src} -> {dst}，错误：{err}")

    # ===== 共演差异报告及被抢番号 =====
    diff_actors = []
    stolen_videos = defaultdict(list)  # actor -> list of nfo 文件名（番号）

    for actor, nfos in qualified_actors.items():
        original_count = len(nfos)
        final_count = actor_final_counts.get(actor, 0)
        for nfo in nfos:
            final_owner = nfo_final_owner.get(nfo, COLLECTION_NAME)
            if final_owner != actor and final_owner != COLLECTION_NAME:
                stolen_videos[actor].append(os.path.splitext(os.path.basename(nfo))[0])
        if original_count != final_count:
            diff = original_count - final_count
            diff_actors.append((actor, original_count, final_count, diff))

    if qualified_actors:
        print("\n满足阈值的演员及对应视频数：")
        for actor, nfos in sorted(qualified_actors.items(), key=lambda x: -len(x[1])):
            print(f"  {actor} : {len(nfos)}")

    if diff_actors:
        print("\n以下是被抢的倒霉蛋：")
        for actor, original_count, final_count, diff in sorted(diff_actors, key=lambda x: -x[3]):
            print(f"  {actor} (演员视频数: {original_count} / 最终归类数: {final_count} / 被其他演员归类数: {diff})")
            if actor in stolen_videos:
                print(f"    被抢走的番号：{', '.join(stolen_videos[actor])}")

if __name__ == "__main__":
    main()
