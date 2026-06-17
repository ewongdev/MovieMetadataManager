"""
subtitle_adder.py
功能：批量从字幕库文件夹中提取字幕，为影片添加字幕文件（无法识别原影片是否包含内嵌字幕）。
如原文件夹已存在字幕文件，可通过配置区选择是否覆盖（默认不覆盖）。
"""

import os
import shutil
import re
from pathlib import Path

# ============================= 配置区 =============================
# 1. 设置来字幕库文件夹路径（字幕所在文件夹，支持多级子目录扫描）
SOURCE_FOLDER = r"D:\字幕库"
# 2. 设置目标文件夹路径
DEST_BASE_FOLDER = r"D:\影片测试"

# 3. 遇到已存在字幕的处理方式：True = 覆盖，False = 跳过
OVERWRITE_EXISTING = False
# ==================================================================

# 支持的字幕后缀列表
SUBTITLE_EXTENSIONS = [
    '.srt', '.vtt', '.webvtt', '.ass', '.ssa', '.lrc', '.txt', 
    '.sbv', '.ttml', '.dfxp', '.scc', '.cap', '.stl', '.itt', 
    '.xml', '.tdf', '.sub', '.idx', '.sup', '.sst', '.son'
]

def main():
    success_count = 0
    fail_count = 0
    skip_no_folder_count = 0
    skip_existing_count = 0  # 记录因已存在而跳过的数量

    print("开始读取目标磁盘结构 (这可能需要几秒钟，请稍候)...")
    
    # 验证目标路径有效性
    dest_base_path = Path(DEST_BASE_FOLDER)
    if not dest_base_path.exists():
        print(f"❌ 错误: 目标根文件夹不存在: {DEST_BASE_FOLDER}")
        input("\n程序已暂停。[按下回车键(Enter)] 可关闭此窗口...")
        return

    # 【优化1】：将所有目标子目录一次性拉取到内存中
    all_dest_folders = [f for f in dest_base_path.rglob('*') if f.is_dir()]
    
    print("目标磁盘结构读取完毕！开始扫描来源字幕文件夹...")

    # 验证来源路径有效性
    source_path = Path(SOURCE_FOLDER)
    if not source_path.exists():
        print(f"❌ 错误: 来源文件夹不存在: {SOURCE_FOLDER}")
        input("\n程序已暂停。[按下回车键(Enter)] 可关闭此窗口...")
        return

    # 【优化2】：深度递归扫描来源文件夹（包括根目录及所有多级子目录）
    source_files = [
        f for f in source_path.rglob('*') 
        if f.is_file() and f.suffix.lower() in SUBTITLE_EXTENSIONS
    ]

    print(f"共扫描到 {len(source_files)} 个符合条件的字幕文件。开始深度匹配并处理...\n" + "-"*50)

    for file_path in source_files:
        # 提取纯番号：使用正则去除第一个点之后的所有内容，兼容 "ABF-196.zh.srt" 格式
        base_name = re.sub(r'\..*$', '', file_path.name)
        file_name = file_path.name

        # 在内存中匹配目标文件夹 (支持 "番号 "开头或完全等于"番号")
        matching_folders = [
            folder for folder in all_dest_folders
            if folder.name == base_name or folder.name.startswith(f"{base_name} ")
        ]

        if matching_folders:
            for folder in matching_folders:
                target_file_path = folder / file_name

                # 检查是否存在旧字幕及是否需要跳过
                if target_file_path.exists() and not OVERWRITE_EXISTING:
                    print(f"⏭️ [跳过]: 目标已存在该字幕，未覆盖 -> {folder.name} 中的 {file_name}")
                    skip_existing_count += 1
                    continue

                try:
                    # 使用 copy2 可以保留文件的原始元数据（如创建、修改时间）
                    shutil.copy2(file_path, target_file_path)
                    
                    # 获取父级目录名用于日志展示
                    parent_name = folder.parent.name if folder.parent != dest_base_path.parent else "根目录"
                    print(f"✅ [复制成功]: ...\\{parent_name}\\{folder.name} <- {file_name}")
                    success_count += 1
                except Exception as e:
                    print(f"❌ [复制失败]: {folder.name} 中的 {file_name} ({str(e)})")
                    fail_count += 1
        else:
            print(f"⏭️ [跳过]: 未在目标目录找到与 '{base_name}' 匹配的文件夹。")
            skip_no_folder_count += 1

    # --- 统计报告输出 ---
    print("\n" + "-"*50)
    print("🎉 字幕批量同步处理完毕！统计结果如下：")
    print(f"  ▶ 成功同步字幕: {success_count} 个文件")
    
    if fail_count > 0:
        print(f"  ▶ 复制失败: {fail_count} 个文件 (请检查权限或文件占用)")
    else:
        print(f"  ▶ 复制失败: {fail_count} 个文件")
        
    print(f"  ▶ 目标已存在且跳过: {skip_existing_count} 个文件")
    print(f"  ▶ 找不到对应目录跳过: {skip_no_folder_count} 个文件")
    print("-" * 50)

if __name__ == "__main__":
    main()
