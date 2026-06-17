"""
preview_fixer.py
功能：修复电影预览（剧照）无法显示的问题。
原理：将 extrafanart 文件夹中的图片移动到 behind the scenes 文件夹，
并删除空的 extrafanart 文件夹。
"""

import os
import shutil

# ================= 配置区域 =================
# 要处理的影片路径（支持路径下多级子文件夹）
BASE_PATH = r"D:\影片测试"
# ============================================

SOURCE_DIR = "extrafanart"
TARGET_DIR = "behind the scenes"

def main():
    if not os.path.exists(BASE_PATH):
        print(f"错误：路径不存在 -> {BASE_PATH}")
        input("按回车键退出...")
        return

    participated_count = 0
    skipped_missing = []
    skipped_mismatch = []

    print(f"开始扫描多级目录: {BASE_PATH}\n")

    # os.walk 会递归扫描包含的所有多级子目录
    for root, dirs, files in os.walk(BASE_PATH):
        has_source = False
        has_target = False

        if SOURCE_DIR in dirs:
            dirs.remove(SOURCE_DIR) 
            has_source = True
        if TARGET_DIR in dirs:
            dirs.remove(TARGET_DIR)
            has_target = True

        # 获取当前层级的文件夹名称（例如：DASS-848）
        folder_name = os.path.basename(root) or root

        # 判断当前目录是否为“影片专属层级”
        has_media = any(f.lower().endswith(('.mp4', '.mkv', '.avi', '.wmv', '.iso', '.ts', '.rmvb', '.nfo')) for f in files)
        is_leaf = len([d for d in dirs if not d.startswith('.')]) == 0
        
        is_movie_level = has_media or is_leaf

        # 如果两个文件夹都存在，执行严格匹配逻辑
        if has_source and has_target:
            source_path = os.path.join(root, SOURCE_DIR)
            target_path = os.path.join(root, TARGET_DIR)

            # 获取两个文件夹内所有的文件（排除掉可能存在的子文件夹）
            target_files = [f for f in os.listdir(target_path) if os.path.isfile(os.path.join(target_path, f))]
            source_files = [f for f in os.listdir(source_path) if os.path.isfile(os.path.join(source_path, f))]

            # 获取不含扩展名的小写文件名集合，用于精准匹配
            target_basenames = {os.path.splitext(f)[0].lower() for f in target_files}
            source_basenames = {os.path.splitext(f)[0].lower() for f in source_files}

            # 【核心修改】：严格判断（必须有文件，且文件数量相等，且无扩展名的文件名集合完全一致）
            if source_files and len(source_files) == len(target_files) and source_basenames == target_basenames:
                participated_count += 1
                
                # 条件满足，开始整体移动
                for f in source_files:
                    src_file_path = os.path.join(source_path, f)
                    dest_file_path = os.path.join(target_path, f)
                    
                    if not os.path.exists(dest_file_path):
                        print(f"✅ 移动：{src_file_path} -> {target_path}")
                        shutil.move(src_file_path, dest_file_path)
                    else:
                        print(f"⚠️ 目标已存在，跳过：{dest_file_path}")

                # 检查 extrafanart 文件夹是否为空，若为空则删除
                if not os.listdir(source_path):
                    try:
                        os.rmdir(source_path)
                        print(f"🗑️ 成功删除空文件夹：{source_path}")
                    except Exception as e:
                        print(f"❌ 无法删除空文件夹 {source_path}: {e}")
            else:
                # 数量不匹配 或 文件名不匹配，将其记录到跳过名单
                skipped_mismatch.append(f"{folder_name} (extrafanart文件数: {len(source_files)}, behind the scenes文件数: {len(target_files)})")
                    
        # 如果是影片层级，但缺少了那两个文件夹
        elif is_movie_level and root != BASE_PATH:
            if has_source or has_target:
                skipped_missing.append(f"{folder_name} (仅包含其中一个文件夹)")
            else:
                skipped_missing.append(f"{folder_name} (两个文件夹均未找到)")

    # ================= 统计与输出区域 =================
    print("\n" + "="*60)
    print("任务处理完成！详细统计信息如下：")
    print("="*60)
    print(f"📁 成功匹配并移动的 {SOURCE_DIR} 文件夹个数：{participated_count}\n")

    print("⚠️ [因不含extrafanart和behind the scenes而跳过的影片]：")
    if skipped_missing:
        for d in skipped_missing:
            print(f"  - {d}")
    else:
        print("  (无)")

    print("\n⚠️ [因两文件中文件数或文件名不匹配而跳过的影片] ：")
    if skipped_mismatch:
        for d in skipped_mismatch:
            print(f"  - {d}")
    else:
        print("  (无)")

    print("\n" + "="*60)

if __name__ == "__main__":
    main()
