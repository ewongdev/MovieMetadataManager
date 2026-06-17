"""
nfo_actor_renamer.py
功能：对某个演员名字进行修改，支持按特定番号过滤。
例如：“桥本有菜”-->“新有菜”
"""
import os

# ================= 配置区域 =================
# 1. 目标文件夹路径
TARGET_DIR = r"C:\演员名测试"
# 2. 搜索项和替换项
SEARCH_NAME = "被改人名"
REPLACE_NAME = "新人名"

# 3. 指定番号（留空则代表处理文件夹下所有的 nfo 文件）
# 例如填写 "ABC-123"，则会匹配 ABC-123, ABC-123-cd1 等
SEARCH_NUMBER = "ABC-123" 
# ============================================

def batch_replace_nfo():
    # 1. 严格拦截空值（使用 strip() 防止误输纯空格）
    if not SEARCH_NAME or not SEARCH_NAME.strip():
        print("【拦截报错】待查找的人名（SEARCH_NAME）不能为空或纯空格！")
        return
        
    if not REPLACE_NAME or not REPLACE_NAME.strip():
        print("【拦截报错】替换后的人名（REPLACE_NAME）不能为空或纯空格！")
        return

    # 2. 检查目标文件夹是否存在
    if not os.path.exists(TARGET_DIR):
        print(f"【错误】找不到目标文件夹：'{TARGET_DIR}'，请检查路径是否正确。")
        return

    # 清除名字前后的不小心留下的无用空格，并拼装成精准匹配的 XML 标签
    s_name = SEARCH_NAME.strip()
    r_name = REPLACE_NAME.strip()
    search_str = f"<name>{s_name}</name>"
    replace_str = f"<name>{r_name}</name>"
    
    # 获取并清理番号条件（转为小写方便后续无视大小写匹配）
    filter_num = SEARCH_NUMBER.strip().lower() if SEARCH_NUMBER else ""
    
    modified_files = []
    total_files = 0

    print(f"正在检索并处理 nfo 文件... (目标: 将 {search_str} 替换为 {replace_str})")
    if filter_num:
        print(f"当前已开启番号过滤，仅处理以【{SEARCH_NUMBER.strip()}】开头的文件\n")
    else:
        print("当前未指定番号，将处理目录下所有 nfo 文件\n")
    
    # 3. 递归遍历多级子文件夹
    for root, dirs, files in os.walk(TARGET_DIR):
        for file in files:
            if file.lower().endswith('.nfo'):
                
                # ==== 新增：番号过滤逻辑 ====
                # 如果设置了番号过滤，且当前文件名（转小写）不是以该番号（转小写）开头，则跳过
                if filter_num and not file.lower().startswith(filter_num):
                    continue
                # ============================

                total_files += 1
                file_path = os.path.join(root, file)
                
                # 自动尝试主流编码读取文件
                content = None
                chosen_encoding = 'utf-8'
                for encoding in ['utf-8', 'gbk', 'utf-16', 'utf-8-sig']:
                    try:
                        with open(file_path, 'r', encoding=encoding) as f:
                            content = f.read()
                        chosen_encoding = encoding
                        break
                    except (UnicodeDecodeError, PermissionError):
                        continue
                
                if content is None:
                    print(f"【警告】无法读取文件（编码未知）：{file}")
                    continue
                
                # 4. 包含目标标签时才进行修改和覆盖写入
                if search_str in content:
                    new_content = content.replace(search_str, replace_str)
                    try:
                        with open(file_path, 'w', encoding=chosen_encoding) as f:
                            f.write(new_content)
                        # 记录在多级路径下的相对文件名
                        relative_path = os.path.relpath(file_path, TARGET_DIR)
                        modified_files.append(relative_path)
                    except Exception as e:
                        print(f"【错误】写入文件失败 {file}: {e}")

    # ================= 统计输出 =================
    print("=" * 50)
    print(f"扫描完成！共检索到 {total_files} 个符合条件的 .nfo 文件。")
    print(f"成功修改了 {len(modified_files)} 个文件。")
    print("=" * 50)
    
    if modified_files:
        print("\n【修改的文件列表如下】:")
        for idx, name in enumerate(modified_files, 1):
            print(f" [{idx}] {name}")
    else:
        print(f"\n提示：没有找到包含 {search_str} 的文件。")

if __name__ == "__main__":
    try:
        batch_replace_nfo()
    except Exception as e:
        print(f"程序运行发生异常: {e}")
    finally:
        # 无论成功、失败还是被安全拦截，均保持窗口开启
        print("\n" + "-" * 50)
