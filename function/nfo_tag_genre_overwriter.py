"""
nfo_tag_genre_overwriter.py
功能：从新（或旧）的 NFO 文件中提取所有 <tag> 和 <genre> ，
并覆盖到与其同名的旧（或新） NFO 中的 <tag> 和 <genre>。
用于仅更新影片的标签与类型，而不修改其他数据。
支持指定单一影片番号进行精确修改。
"""

import os
import re

# ==================== 路径配置放在这里 ====================
# 源路径（提取该路径下的 tag 和 genre）
SOURCE_PATH = r"D:\从这个文件夹提取标签"
# 目标路径（覆盖到该路径下的同名文件）
TARGET_PATH = r"D:\把标签替换到此文件夹"

# 如果只想修改特定番号的 NFO（例如 "ABC-123"），请在引号内输入番号。
# 如果希望批量修改，请保持留空 ""。
SEARCH_NUMBER = "ABC-123"
# ==========================================================

def read_file(file_path):
    """尝试用常见编码读取文件，防止中文乱码或报错"""
    encodings = ['utf-8-sig', 'utf-8', 'gbk', 'gb18030']
    for enc in encodings:
        try:
            with open(file_path, 'r', encoding=enc) as f:
                return f.readlines(), enc
        except UnicodeDecodeError:
            continue
    raise Exception("无法识别的文件编码")

def write_file(file_path, lines, encoding):
    """将修改后的内容写回文件"""
    with open(file_path, 'w', encoding=encoding) as f:
        f.writelines(lines)

def main():
    print("正在初始化文件映射，请稍候...\n")
    
    if not os.path.exists(SOURCE_PATH) or not os.path.exists(TARGET_PATH):
        print("【错误】源路径或目标路径不存在，请检查脚本顶部的路径配置！")
        input("\n按回车键退出程序...")
        return

    success_count = 0
    failed_count = 0
    skipped_count = 0

    failed_files = []
    skipped_files = []

    # 1. 扫描目标路径中的所有 nfo 文件（大小写不敏感映射）
    target_map = {}
    for root, dirs, files in os.walk(TARGET_PATH):
        for file in files:
            if file.lower().endswith('.nfo'):
                target_map[file.lower()] = os.path.join(root, file)

    # 2. 遍历源路径并执行覆盖操作
    for root, dirs, files in os.walk(SOURCE_PATH):
        for file in files:
            if file.lower().endswith('.nfo'):
                
                # 【新增逻辑】：如果设置了 SEARCH_NUMBER，则检查文件名是否匹配
                if SEARCH_NUMBER:
                    base_name = os.path.splitext(file)[0] # 获取不带扩展名的文件名
                    # 忽略大小写进行比对，如果不匹配则直接跳过
                    if base_name.lower() != SEARCH_NUMBER.lower():
                        continue

                file_source_path = os.path.join(root, file)
                file_lower = file.lower()
                
                # 检查目标路径中是否存在同名文件，不存在则跳过
                if file_lower not in target_map:
                    skipped_count += 1
                    skipped_files.append(file_source_path)
                    continue
                
                file_target_path = target_map[file_lower]

                try:
                    # 读取源文件并提取目标标签行（保留原本的空格）
                    lines_source, enc_source = read_file(file_source_path)
                    target_lines_source = []
                    for line in lines_source:
                        if re.search(r'<(tag|genre)>', line):
                            target_lines_source.append(line)
                    
                    # 读取目标文件
                    lines_target, enc_target = read_file(file_target_path)
                    
                    # 过滤掉目标文件中原有的 tag 和 genre 行，并记录第一个标签出现的位置
                    new_lines_target = []
                    first_tag_idx = -1
                    
                    for line in lines_target:
                        if re.search(r'<(tag|genre)>', line):
                            if first_tag_idx == -1:
                                first_tag_idx = len(new_lines_target)
                            continue
                        new_lines_target.append(line)
                    
                    # 插入来自源文件的新标签
                    if first_tag_idx != -1:
                        # 如果目标文件原本就有标签，在原位置插入
                        new_lines_target[first_tag_idx:first_tag_idx] = target_lines_source
                    else:
                        # 如果目标文件原本没有标签，尝试插入到闭合根标签（如 </movie>）之前
                        insert_idx = len(new_lines_target) - 1
                        for idx in range(len(new_lines_target) - 1, -1, -1):
                            if re.match(r'^\s*</\w+>', new_lines_target[idx]):
                                insert_idx = idx
                                break
                        new_lines_target[insert_idx:insert_idx] = target_lines_source
                    
                    # 写回目标文件
                    write_file(file_target_path, new_lines_target, enc_target)
                    success_count += 1

                except Exception as e:
                    failed_count += 1
                    failed_files.append((file_source_path, str(e)))

    # 3. 打印统计结果
    print("=" * 50)
    print("运行简报：")
    if SEARCH_NUMBER:
        print(f"当前模式: 单一文件处理 (番号: {SEARCH_NUMBER})")
    else:
        print("当前模式: 批量处理")
    print(f"成功件数: {success_count}")
    print(f"失败件数: {failed_count}")
    print(f"跳过件数: {skipped_count}")
    print("=" * 50)

    if failed_files:
        print("\n【失败文件列表】:")
        for path, reason in failed_files:
            print(f" -> {path} (原因: {reason})")

    if skipped_files:
        print("\n【跳过文件列表（目标路径中未找到同名文件）】:")
        for path in skipped_files:
            print(f" -> {path}")

if __name__ == "__main__":
    main()
