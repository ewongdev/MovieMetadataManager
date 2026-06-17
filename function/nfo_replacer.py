"""
nfo_replacer.py
功能：批量复制新的 NFO 文件到旧影片文件夹中，旧 NFO 会被替换。
用于更新媒体库的 NFO 。支持批量或指定番号替换。
"""

import os
import re
import shutil

# ==================== 1. 配置区域 ====================
# 新 NFO 文件夹路径（支持遍历其下的所有子文件夹）
SOURCE_FOLDER = r"D:\新NFO"
# 目标文件夹路径
DEST_BASE_FOLDER = r"D:\旧电影文件夹"
# 指定要处理的番号（例如 "ABC-123"）。
# 如果留空 ""，则自动执行全局批量替换；如果填写，则仅替换该番号及其分卷（如 -cd1, -cd2）
SEARCH_NUMBER = "ABC-123" 
# =====================================================

def main():
    # 初始化计数器
    replace_count = 0          # 成功替换计数
    add_count = 0              # 成功添加计数
    fail_count = 0             # 复制失败计数
    skip_no_folder_count = 0   # 跳过（找不到目录）计数
    skip_filter_count = 0      # 【新增】因未匹配指定番号而跳过的计数

    print("开始读取目标磁盘结构 (这可能需要几秒钟，请稍候)...")
    
    # 【核心优化 1】：一次性将目标目录下所有子文件夹载入内存
    all_dest_folders = []
    for root, dirs, _ in os.walk(DEST_BASE_FOLDER):
        for d in dirs:
            all_dest_folders.append({
                "full_path": os.path.join(root, d),
                "name": d,
                "parent_name": os.path.basename(root)
            })

    print("磁盘结构读取完毕！开始深度匹配...")
    if SEARCH_NUMBER:
        print(f"▶ 过滤模式已开启：仅处理番号为 '{SEARCH_NUMBER}' 的相关文件。")
    print("-" * 50)

    # 【深度遍历】：获取源文件夹及其所有子文件夹下的所有 .nfo 文件
    source_files = []
    for root, _, files in os.walk(SOURCE_FOLDER):
        for file in files:
            if file.lower().endswith('.nfo'):
                source_files.append({
                    "full_path": os.path.join(root, file),
                    "name": file
                })

    # 开始循环处理每一个源 nfo 文件
    for s_file in source_files:
        file_name = s_file["name"]
        original_base_name = os.path.splitext(file_name)[0]
        
        # 使用正则表达式提取真实番号。去掉结尾的 -cd1, -cd2 等
        real_base_name = re.sub(r'-cd\d+$', '', original_base_name, flags=re.IGNORECASE)

        # ====================================================
        # 【新增逻辑】：特定番号过滤
        # 如果 SEARCH_NUMBER 不为空，且当前文件真实番号不匹配，则跳过
        if SEARCH_NUMBER and real_base_name.lower() != SEARCH_NUMBER.lower():
            skip_filter_count += 1
            continue
        # ====================================================

        # 【核心优化 2】：在内存中匹配目标文件夹
        matching_folders = [
            f for f in all_dest_folders 
            if f["name"].startswith(f"{real_base_name} ") or f["name"] == real_base_name
        ]

        # 【单一判断】：只要找到匹配的子文件夹，就进行复制
        if matching_folders:
            for folder in matching_folders:
                target_file_path = os.path.join(folder["full_path"], file_name)

                # 在复制前，先判断目标文件是否存在，以此区分是“替换”还是“添加”
                is_existing = os.path.isfile(target_file_path)

                try:
                    shutil.copy2(s_file["full_path"], target_file_path)
                    
                    if is_existing:
                        print(f"[成功替换]: ...\\{folder['parent_name']}\\{folder['name']} 中的旧版 {file_name}")
                        replace_count += 1
                    else:
                        print(f"[成功添加]: ...\\{folder['parent_name']}\\{folder['name']} 放入新版 {file_name}")
                        add_count += 1
                        
                except Exception as e:
                    print(f"[复制失败]: {folder['name']} 中的 {file_name} (原因: {e})")
                    fail_count += 1
        else:
            print(f"[跳过]: 未在目标目录找到与 '{real_base_name}' 匹配的文件夹。")
            skip_no_folder_count += 1

    # --- 统计报告输出 ---
    print("\n" + "-" * 50)
    print("🎉 深度批量处理执行完毕！统计结果如下：")
    print(f"  ▶ 成功替换: {replace_count} 个文件 (目标原本存在旧文件)")
    print(f"  ▶ 成功添加: {add_count} 个文件 (目标原本无同名文件)")
    print(f"  ▶ 复制失败: {fail_count} 个文件" + (" (请检查权限或文件占用)" if fail_count > 0 else ""))
    print(f"  ▶ 跳过未建档: {skip_no_folder_count} 次 (找不到匹配的目录)")
    
    if SEARCH_NUMBER:
        print(f"  ▶ 因未匹配指定番号被过滤: {skip_filter_count} 个 NFO 文件")
        
    print("-" * 50)


if __name__ == "__main__":
    try:
        main()
    except Exception as big_e:
        print(f"运行过程中发生致命错误: {big_e}")
