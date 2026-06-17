"""
nfo_tag_genre_editor.py
功能：批量或按番号修改 NFO 文件中的 <tag> 和 <genre> 字段。
支持对标签进行添加、删除和修改操作。
注意：使用 MDCx 刮削后，NFO 中 <tag> 与 <genre> 的内容相同，因为不同播放器或影视服务器
会仅选择显示二者中的一个。
"""

import os
import re

# ================= 配置区 (请在此处修改你的设定) =================

# 1. 目标文件夹路径
TARGET_DIRECTORY = r"D:\test"  

# 2. 搜索项和替换项
# 案例 A (修改): SEARCH_ITEM = "有码", REPLACE_ITEM = "无码"
# 案例 B (删除): SEARCH_ITEM = "有码", REPLACE_ITEM = ""
# 案例 C (添加): SEARCH_ITEM = "", REPLACE_ITEM = "高清"
# 引号内输入标签字段
SEARCH_ITEM = "测试有码"   
REPLACE_ITEM = "测试无码" 

# 3. 指定番号过滤
# 如果只想修改特定番号的 NFO（例如 "ABC-123"），请在引号内输入番号。
# 如果希望批量修改，请保持留空 ""。
SEARCH_NUMBER = "ABC-123"

# ==================================================================


def process_nfo(directory, search_str, replace_str, search_num=""):
    stats = {"modified_tags": 0, "deleted_tags": 0, "added_tags": 0, "errors": 0}
    modified_files_list = [] 

    print(f"🚀 开始扫描目录及其所有多级子文件夹: {directory}")
    if search_num:
        print(f"🎯 已开启番号过滤：仅处理文件名包含「{search_num}」的 NFO 文件\n")
    else:
        print("🌍 未指定番号：将批量处理目录下的所有 NFO 文件\n")
    for root_dir, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith('.nfo'):
                # --- 新增：番号过滤逻辑 ---
                if search_num and search_num.lower() not in file.lower():
                    continue  # 如果指定了番号且文件名不匹配，直接跳过当前文件
                
                filepath = os.path.join(root_dir, file)
                
                # --- 1. 尝试用不同编码读取原文件 ---
                content = None
                used_encoding = 'utf-8'
                encodings = ['utf-8', 'utf-8-sig', 'gbk', 'gb18030', 'utf-16']
                
                for enc in encodings:
                    try:
                        with open(filepath, 'r', encoding=enc) as f:
                            content = f.read()
                        used_encoding = enc
                        break
                    except (UnicodeDecodeError, LookupError):
                        continue
                
                if content is None:
                    print(f"❌ 编码异常，无法读取: {filepath}")
                    stats["errors"] += 1
                    continue

                # --- 2. 基于纯文本正则的核心处理逻辑 ---
                changed = False
                file_action = []

                # 【场景 3: 添加功能】 (搜索为空，替换有值)
                if not search_str and replace_str:
                    has_tag = re.search(rf'<tag>\s*{re.escape(replace_str)}\s*</tag>', content) is not None
                    has_genre = re.search(rf'<genre>\s*{re.escape(replace_str)}\s*</genre>', content) is not None
                    
                    # A. 插入 <tag>
                    if not has_tag:
                        tag_matches = list(re.finditer(rf'^([ \t]*)<tag>\s*(.*?)\s*</tag>(\r?\n?)', content, re.M))
                        if tag_matches:
                            # 找到最后一个 </tag>，插在它后面
                            last_match = tag_matches[-1]
                            indent = last_match.group(1)
                            nl = last_match.group(3) if last_match.group(3) else '\n'
                            end_idx = last_match.end()
                            insert_str = f"{indent}<tag>{replace_str}</tag>{nl}"
                            content = content[:end_idx] + insert_str + content[end_idx:]
                        else:
                            # 如果没有 tag，找第一个 genre 插在前面
                            genre_matches = list(re.finditer(rf'^([ \t]*)<genre>\s*(.*?)\s*</genre>(\r?\n?)', content, re.M))
                            if genre_matches:
                                first_match = genre_matches[0]
                                indent = first_match.group(1)
                                nl = first_match.group(3) if first_match.group(3) else '\n'
                                start_idx = first_match.start()
                                insert_str = f"{indent}<tag>{replace_str}</tag>{nl}"
                                content = content[:start_idx] + insert_str + content[start_idx:]
                            else:
                                # 啥都没有，插在倒数第二行（根节点前）
                                root_end_match = re.search(r'</(movie|tvshow|video)>', content)
                                if root_end_match:
                                    start_idx = root_end_match.start()
                                    content = content[:start_idx] + f"  <tag>{replace_str}</tag>\n" + content[start_idx:]
                        
                        changed = True
                        stats["added_tags"] += 1
                        if "添加" not in file_action: file_action.append("添加")

                    # B. 插入 <genre> (重新实时搜索 content，保证前后位置正确)
                    if not has_genre:
                        genre_matches = list(re.finditer(rf'^([ \t]*)<genre>\s*(.*?)\s*</genre>(\r?\n?)', content, re.M))
                        if genre_matches:
                            # 找到第一个 <genre>，插在它前面
                            first_match = genre_matches[0]
                            indent = first_match.group(1)
                            nl = first_match.group(3) if first_match.group(3) else '\n'
                            start_idx = first_match.start()
                            insert_str = f"{indent}<genre>{replace_str}</genre>{nl}"
                            content = content[:start_idx] + insert_str + content[start_idx:]
                        else:
                            # 如果没有 genre，就找最后一个 tag 插在后面
                            tag_matches = list(re.finditer(rf'^([ \t]*)<tag>\s*(.*?)\s*</tag>(\r?\n?)', content, re.M))
                            if tag_matches:
                                last_match = tag_matches[-1]
                                indent = last_match.group(1)
                                nl = last_match.group(3) if last_match.group(3) else '\n'
                                end_idx = last_match.end()
                                insert_str = f"{indent}<genre>{replace_str}</genre>{nl}"
                                content = content[:end_idx] + insert_str + content[end_idx:]
                            else:
                                root_end_match = re.search(r'</(movie|tvshow|video)>', content)
                                if root_end_match:
                                    start_idx = root_end_match.start()
                                    content = content[:start_idx] + f"  <genre>{replace_str}</genre>\n" + content[start_idx:]
                        
                        changed = True
                        stats["added_tags"] += 1
                        if "添加" not in file_action: file_action.append("添加")

                # 【场景 1 & 2: 修改或删除】 (搜索有值)
                elif search_str:
                    if not replace_str:
                        # 场景 2: 删除整行（包括行首空格和换行符）
                        tag_line_pattern = rf'^[ \t]*<tag>\s*{re.escape(search_str)}\s*</tag>[ \t]*\r?\n?'
                        genre_line_pattern = rf'^[ \t]*<genre>\s*{re.escape(search_str)}\s*</genre>[ \t]*\r?\n?'
                        
                        tag_count = len(re.findall(tag_line_pattern, content, re.M))
                        genre_count = len(re.findall(genre_line_pattern, content, re.M))
                        
                        if tag_count > 0 or genre_count > 0:
                            content = re.sub(tag_line_pattern, '', content, flags=re.M)
                            content = re.sub(genre_line_pattern, '', content, flags=re.M)
                            changed = True
                            stats["deleted_tags"] += (tag_count + genre_count)
                            file_action.append("删除")
                    else:
                        # 场景 1: 修改标签内容
                        tag_pattern = rf'<tag>\s*{re.escape(search_str)}\s*</tag>'
                        genre_pattern = rf'<genre>\s*{re.escape(search_str)}\s*</genre>'
                        
                        tag_count = len(re.findall(tag_pattern, content))
                        genre_count = len(re.findall(genre_pattern, content))
                        
                        if tag_count > 0 or genre_count > 0:
                            content = re.sub(tag_pattern, f'<tag>{replace_str}</tag>', content)
                            content = re.sub(genre_pattern, f'<genre>{replace_str}</genre>', content)
                            changed = True
                            stats["modified_tags"] += (tag_count + genre_count)
                            file_action.append("修改")

                # --- 3. 如果发生改变，原样写回（保留原编码格式） ---
                if changed:
                    try:
                        with open(filepath, 'w', encoding=used_encoding) as f:
                            f.write(content)
                        rel_path = os.path.relpath(filepath, directory)
                        modified_files_list.append(f"[{','.join(file_action)}] {rel_path}")
                    except Exception as e:
                        print(f"❌ 写入文件失败 {filepath}: {e}")
                        stats["errors"] += 1

    # ----------------- 打印最终报告 -----------------
    print("\n" + "="*50)
    print("🎉 处理完成！结果报告：")
    print("="*50)
    print(f"✅ 成功操作的NFO文件总个数: {len(modified_files_list)} 个")
    print(f"   - 累计新增标签: {stats['added_tags']} 处")
    print(f"   - 累计修改标签: {stats['modified_tags']} 处")
    print(f"   - 累计删除标签: {stats['deleted_tags']} 处")
    print(f"❌ 遇到错误的文件数: {stats['errors']} 个")
    
    if modified_files_list:
        print("\n📋 被修改过的文件列表:")
        for m_file in modified_files_list:
            print(f"   - {m_file}")
    else:
        print("\n📋 没有找到符合条件需要修改的 NFO 文件。")
    print("="*50)


if __name__ == "__main__":
    process_nfo(TARGET_DIRECTORY, SEARCH_ITEM, REPLACE_ITEM, SEARCH_NUMBER)
    print("\n")
