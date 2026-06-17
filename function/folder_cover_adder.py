"""
folder_cover_adder.py
功能：批量为影片文件夹添加封面图。用于改善媒体库浏览体验。
说明：
此功能并非所有用户都需要!!! Emby用户可不用。
因有些播放器例如Vidhub只识别文件夹内与其同名的图片作为封片图，所以我加了此功能。

e.g. Emby不会识别二级子目录的图片，所以如果想给女优文件夹加个封面图，可以去下载她们的一张图片，然后改成女优文件夹的名字并放在女优文件夹目录中。
例如文件结构为：
"D:\影片\相泽南\相泽南.jpg"
"D:\影片\相泽南\IPX-557\IPX-557-poster.jpg"
"""

import os
import shutil

# ==================== 配置区域 ====================
# 请在下方双引号内输入你的文件夹路径
TARGET_DIR = r"D:\影片测试"
# ==================================================

def batch_copy_posters(base_dir):
    success_count = 0

    if not os.path.exists(base_dir):
        print(f"❌ 错误：目标文件夹不存在，请检查配置路径 -> {base_dir}")
        return

    # 支持的图片格式后缀
    image_extensions = ('.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif')
    # 明确需要排除的特定子文件夹名称（不区分大小写）
    exclude_folders = {'extrafanart', 'behind the scenes'}

    print("开始扫描并处理文件夹...")
    print("-" * 50)

    for dirpath, dirnames, filenames in os.walk(base_dir):
        # 1. 过滤掉明确不需要扫描的特定下级文件夹
        dirnames[:] = [d for d in dirnames if d.lower() not in exclude_folders]

        poster_file = None
        
        # 2. 寻找带有 "-poster" 的图片文件
        for filename in filenames:
            name_lower = filename.lower()
            if "-poster" in name_lower and name_lower.endswith(image_extensions):
                poster_file = filename
                break  # 如果一个文件夹内有两个带有“-poster”的图片，只取第一个

        # 3. 如果找到了海报图片
        if poster_file:
            # 满足“‘-poster’下级的文件夹不要扫描”：找到海报后，直接清空 dirnames，阻止继续向下递归
            dirnames[:] = []
            
            # 获取当前文件夹名称和图片后缀
            folder_name = os.path.basename(dirpath)
            ext = os.path.splitext(poster_file)[1]
            
            # 新的目标文件名和完整路径
            new_filename = f"{folder_name}{ext}"
            src_path = os.path.join(dirpath, poster_file)
            dst_path = os.path.join(dirpath, new_filename)
            
            # 检查同名目标文件是否已存在（存在则直接跳过，不记录）
            if os.path.exists(dst_path):
                continue
            else:
                try:
                    shutil.copy2(src_path, dst_path)
                    success_count += 1
                    print(f"[成功] 已成功复制: {new_filename}")
                except Exception:
                    continue

    # ==================== 统计报告 ====================
    print("\n" + "="*50)
    print(" 运 行 统 计 报 告")
    print("="*50)
    print(f" 成功复制数量: {success_count}")
    print("="*50)

if __name__ == "__main__":
    batch_copy_posters(TARGET_DIR)
    print("\n程序运行完毕。")
