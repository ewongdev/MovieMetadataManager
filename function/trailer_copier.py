"""
trailer_copier.py
功能：批量从A文件夹复制预告片到B文件夹（如B已存在预告片则跳过。）。
预告片命名要求：番号+“-trailer”。建议在MDCx中修改预告片命名格式。
"""

import os
import shutil
import re

def main():
# ============================= 配置区 =============================
    # 预告片路径
    source_dir = r"C:\预告片"
    # 电影文件夹路径
    dest_dir = r"C:\测试"
# ==================================================================
    # 统计数据
    success_count = 0
    skip_count = 0
    failed_files = []

    # 存储待复制的文件字典：{ "番号": [(原文件名, 原文件完整路径), ...] }
    # 使用列表结构，以支持一个番号拥有多个分段预告片（如 cd1, cd2）
    pending_files = {}

    print("正在扫描源文件夹...")
    if not os.path.exists(source_dir):
        print(f"错误: 源文件夹 {source_dir} 不存在！")
        input("\n按回车键退出程序...")
        return

    if not os.path.exists(dest_dir):
        print(f"错误: 目标文件夹 {dest_dir} 不存在！")
        input("\n按回车键退出程序...")
        return

    # 1. 遍历源文件夹，提取所有符合条件的预告片文件
    for root, dirs, files in os.walk(source_dir):
        for file in files:
            name, ext = os.path.splitext(file)
            # 检查是否为 .mp4 且以 -trailer 结尾（忽略大小写）
            if ext.lower() == '.mp4' and name.lower().endswith('-trailer'):
                # 先去掉末尾的 "-trailer"（长度为 8）
                base_name = name[:-8]
                
                # 使用正则表达式去掉可能存在的 -cd1, _cd2, cd3 等分段后缀
                # r'[-_]?cd\d+$' 可以匹配 -cd1, _cd1, cd1 等形式（忽略大小写）
                code = re.sub(r'[-_]?cd\d+$', '', base_name, flags=re.IGNORECASE)
                code = code.upper() # 统一转大写用于匹配目标文件夹
                
                if code not in pending_files:
                    pending_files[code] = []
                pending_files[code].append((file, os.path.join(root, file)))

    # 计算总文件数
    total_files = sum(len(file_list) for file_list in pending_files.values())
    
    if total_files == 0:
        print("没有在源目录中找到符合要求的文件。")
        input("\n按回车键退出程序...")
        return

    print(f"共找到 {total_files} 个预告片文件（包含分段文件），开始扫描目标文件夹并匹配...")

    # 2. 遍历目标文件夹，寻找匹配的文件夹名
    for root, dirs, files in os.walk(dest_dir):
        for dir_name in dirs:
            dir_name_upper = dir_name.upper()
            matched_codes = []
            
            # 检查是否有番号包含在该文件夹名称中
            # 使用 list(keys) 避免在循环中修改字典导致报错
            for code in list(pending_files.keys()):
                if code in dir_name_upper:
                    target_folder_path = os.path.join(root, dir_name)
                    
                    # 遍历该番号对应的所有预告片文件（将 cd1, cd2 一起复制到该文件夹）
                    for source_filename, source_path in pending_files[code]:
                        target_file_path = os.path.join(target_folder_path, source_filename)
                        
                        # 检查目标文件夹内是否已有同名文件
                        if os.path.exists(target_file_path):
                            print(f"⏭️ 跳过 (已存在同名文件): {source_filename} -> {target_folder_path}")
                            skip_count += 1
                            continue
                        
                        try:
                            # 复制文件
                            shutil.copy2(source_path, target_file_path)
                            print(f"✅ 成功: {source_filename} -> {target_folder_path}")
                            success_count += 1
                        except Exception as e:
                            print(f"❌ 复制失败: {source_filename}，错误: {e}")
                            failed_files.append(source_filename)
                    
                    # 记录匹配成功的番号
                    matched_codes.append(code)
            
            # 将已成功匹配文件夹的番号从待处理字典中移除，提高后续扫描效率
            for code in matched_codes:
                if code in pending_files:
                    del pending_files[code]
                
        # 如果所有文件都已经处理完毕，提前结束整个盘符的扫描
        if not pending_files:
            break

    # 3. 处理未能成功匹配（即在目标盘中未找到任何包含该番号的文件夹）的文件
    for code, file_list in pending_files.items():
        for filename, path in file_list:
            failed_files.append(filename)

    # 4. 打印统计结果
    print("\n" + "="*50)
    print("处理完成！统计信息如下：")
    print(f"总计预告片数: {total_files}")
    print(f"成功复制个数: {success_count}")
    print(f"跳过(已存在)个数: {skip_count}")
    print(f"失败/未找到目标个数: {len(failed_files)}")

    if failed_files:
        print("\n以下文件未能成功复制（或未在 G:\\JAV 中找到对应的番号文件夹）:")
        for f in failed_files:
            print(f" - {f}")

if __name__ == "__main__":
    main()
