"""
folder_cover_remover.py
功能：批量删除由 folder_cover_adder.py 生成的同名封面图（支持文件夹改名后清理）。
说明：通过比对文件内容，只要发现同目录下有与 "-poster" 海报完全一模一样的图片，就将其视为生成的冗余文件并删除。
"""

import os
import filecmp

# ==================== 配置区域 ====================
# 请在下方双引号内输入你的文件夹路径
TARGET_DIR = r"D:\影片测试"
# ==================================================

def batch_delete_images_by_content(base_dir):
    success_count = 0

    if not os.path.exists(base_dir):
        print(f"❌ 错误：目标文件夹不存在，请检查配置路径 -> {base_dir}")
        return

    # 支持的图片格式后缀
    image_extensions = ('.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif')
    # 明确需要排除的特定子文件夹名称（不区分大小写）
    exclude_folders = {'extrafanart', 'behind the scenes'}

    print("开始扫描并清理文件夹封面...")
    print("-" * 50)

    for dirpath, dirnames, filenames in os.walk(base_dir):
        # 1. 过滤掉明确不需要扫描的特定下级文件夹
        dirnames[:] = [d for d in dirnames if d.lower() not in exclude_folders]

        poster_file = None
        
        # 2. 寻找带有 "-poster" 的海报源文件
        for filename in filenames:
            name_lower = filename.lower()
            if "-poster" in name_lower and name_lower.endswith(image_extensions):
                poster_file = filename
                break

        # 3. 如果找到了海报图片，开始同目录比对
        if poster_file:
            # 停止向下递归
            dirnames[:] = []
            
            poster_path = os.path.join(dirpath, poster_file)
            
            # 遍历同目录下的所有其他图片
            for filename in filenames:
                # 跳过海报文件本身
                if filename == poster_file:
                    continue
                    
                name_lower = filename.lower()
                if name_lower.endswith(image_extensions):
                    check_path = os.path.join(dirpath, filename)
                    
                    try:
                        # 核心逻辑：使用 filecmp.cmp 比对两个文件是否完全相同 (shallow=False 表示不仅比对属性，还严格比对文件内容)
                        if filecmp.cmp(poster_path, check_path, shallow=False):
                            os.remove(check_path)
                            success_count += 1
                            print(f"[成功清理] 删除复制图: {filename}")
                    except Exception as e:
                        print(f"❌ [清理失败] 无法处理 {check_path}，原因: {e}")

    # ==================== 统计报告 ====================
    print("\n" + "="*50)
    print(" 运 行 统 计 报 告")
    print("="*50)
    print(f" 成功清理数量: {success_count}")
    print("="*50)

if __name__ == "__main__":
    batch_delete_images_by_content(TARGET_DIR)
    print("\n程序运行完毕。")
