import os
import sys
import re
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
# ==================== 专门给打包工具看的“欺骗性”导入 ====================
# 动态 exec 调用的子脚本里用到的标准库或第三方库，必须在这里显式写一遍
import filecmp
import shutil
# 如果你的 nfo 编辑、剧照修复等脚本里还用到了其他模块（比如 xml.etree.ElementTree），也一并写在这里：
# import xml.etree.ElementTree 
# =====================================================================

# ==================== 解决高分屏模糊问题 ====================
try:
    from ctypes import windll
    # 优先尝试 Windows 10/11 的 Per-Monitor V2 模式，让缩放更清晰且尺寸更准确
    try:
        windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass  # 兼容非 Windows 系统或不支持的旧环境

# 全局按钮列表，用于在运行时禁用/启用，防止重复触发
all_buttons = []

class TextRedirector:
    """线程安全的标准输出重定向器，用于将 print 信息实时冲刷到 Tkinter Text 组件"""
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, str_val):
        # 使用 after 确保在主线程中安全更新 UI
        self.text_widget.after(0, lambda: self._insert(str_val))

    def _insert(self, str_val):
        self.text_widget.insert(tk.END, str_val)
        self.text_widget.see(tk.END)

    def flush(self):
        pass

def replace_var(code, var_name, new_value):
    """利用正则精准替换脚本中的配置项，支持字符串路径、整型数字和布尔值（修复缩进丢失Bug）"""
    # 使用 () 将行首的缩进空格捕获为第 1 个分组
    pattern = rf'^(\s*){var_name}\s*=\s*.*$'
    
    if isinstance(new_value, bool):
        # \\1 代表把原本匹配到的缩进空格，原封不动地放回新代码行首
        return re.sub(pattern, f'\\1{var_name} = {new_value}', code, flags=re.MULTILINE)
    elif isinstance(new_value, int):
        return re.sub(pattern, f'\\1{var_name} = {new_value}', code, flags=re.MULTILINE)
    else:
        # 处理 Windows 路径中的反斜杠，使其在 re.sub 和 Python 源码中表现正常
        escaped_value = new_value.replace('\\', '\\\\')
        return re.sub(pattern, f'\\1{var_name} = r"{escaped_value}"', code, flags=re.MULTILINE)
    
def set_buttons_state(state):
    """切换所有按钮的状态"""
    for btn in all_buttons:
        try:
            btn.config(state=state)
        except:
            pass

def run_script_backend(script_name, replacements):
    """核心：动态读取、修改并在独立线程中执行目标脚本"""
    def target():
        set_buttons_state(tk.DISABLED)
        try:
            # 兼容 PyInstaller 打包后的临时路径机制
            if getattr(sys, 'frozen', False):
                base_dir = sys._MEIPASS
            else:
                base_dir = os.path.dirname(os.path.abspath(__file__))
            
            # 【核心修改点】：指向子文件夹 function 内的脚本
            file_path = os.path.join(base_dir, "function", script_name)
            if not os.path.exists(file_path):
                print(f"❌ 错误：找不到内置脚本文件 [{file_path}]，请确认打包配置！")
                return
            
            with open(file_path, 'r', encoding='utf-8') as f:
                code_content = f.read()
            
            # 注入 GUI 界面上的最新配置值
            for var_name, val in replacements.items():
                code_content = replace_var(code_content, var_name, val)
            
            print(f"\n🚀 [任务启动] 开始执行模块: {script_name}")
            print("=" * 60)
            
            # 伪造 __name__ == '__main__' 执行脚本
            exec(code_content, {'__name__': '__main__'})
            
            print("=" * 60)
            print(f"✅ [任务成功] 模块 {script_name} 已执行完毕！")
        except Exception as e:
            import traceback
            print(f"\n❌ [运行异常] 执行崩溃，详细错误堆栈如下：\n{traceback.format_exc()}")
        finally:
            set_buttons_state(tk.NORMAL)

    threading.Thread(target=target, daemon=True).start()

# ==================== UI 组件快捷构建函数 ====================
def add_path_row(parent, label_text, row):
    ttk.Label(parent, text=label_text).grid(row=row, column=0, sticky='w', padx=5, pady=5)
    entry = ttk.Entry(parent, width=55)
    entry.grid(row=row, column=1, sticky='ew', padx=5, pady=5)
    def browse():
        path = filedialog.askdirectory()
        if path:
            entry.delete(0, tk.END)
            entry.insert(0, os.path.normpath(path))
    btn = ttk.Button(parent, text="浏览...", command=browse)
    btn.grid(row=row, column=2, padx=5, pady=5)
    return entry

def add_text_row(parent, label_text, row, default_val=""):
    ttk.Label(parent, text=label_text).grid(row=row, column=0, sticky='w', padx=5, pady=5)
    entry = ttk.Entry(parent, width=55)
    entry.grid(row=row, column=1, columnspan=2, sticky='ew', padx=5, pady=5)
    if default_val:
        entry.insert(0, str(default_val))
    return entry

# ==================== GUI 主程序 ====================
def create_main_gui():
    root = tk.Tk()
    root.title("MovieMetadataManager")
    
    # ------------------ 自适应分辨率与居中逻辑 ------------------
    # 获取当前屏幕的分辨率
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    # 动态设定默认窗口大小（例如屏幕宽度的 65% 和高度的 75%）
    window_width = int(screen_width * 0.65)
    window_height = int(screen_height * 0.75)

    # 设定向下兼容的最小限制（兼容 1366x768 屏幕，或高缩放比例的笔记本）
    min_width = 850
    min_height = 600

    # 确保窗口大小既不小于最小值，也不大于屏幕实际可用尺寸
    window_width = max(min_width, min(window_width, screen_width))
    window_height = max(min_height, min(window_height, screen_height))

    # 计算窗口居中时的屏幕坐标
    pos_x = int((screen_width - window_width) / 2)
    pos_y = int((screen_height - window_height) / 2)

    # 应用自适应尺寸和居中坐标
    root.geometry(f"{window_width}x{window_height}+{pos_x}+{pos_y}")
    root.minsize(min_width, min_height)
    # -----------------------------------------------------------

    # 顶部分隔面板：上方放参数输入，下方放控制台日志
    main_paned = ttk.Panedwindow(root, orient=tk.VERTICAL)
    main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    # 上半部分：多选项卡 Notebook
    notebook = ttk.Notebook(main_paned)
    main_paned.add(notebook, weight=3)

    # 下半部分：公共控制台日志
    log_frame = ttk.LabelFrame(main_paned, text=" 日志 ")
    main_paned.add(log_frame, weight=2)
    
    # 【UI修改】：将背景改为白底（#ffffff），文字改为深灰色（#333333）
    log_text = tk.Text(log_frame, wrap=tk.WORD, background="#ffffff", foreground="#333333", font=("Consolas", 10))
    log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    scrollbar = ttk.Scrollbar(log_frame, command=log_text.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    log_text.config(yscrollcommand=scrollbar.set)

    # 清空日志按钮
    clear_btn = ttk.Button(log_frame, text="清空日志", command=lambda: log_text.delete('1.0', tk.END))
    clear_btn.pack(anchor='se', padx=10, pady=5)

    # 重定向标准输出
    sys.stdout = TextRedirector(log_text)
    sys.stderr = TextRedirector(log_text)

    # ------------------ Tab 1: 演员影片归类 ------------------
    t1 = ttk.Frame(notebook)
    notebook.add(t1, text=" 📂 演员影片分类 ")
    t1.columnconfigure(1, weight=1)
    
    ttk.Label(t1, text="💡 功能：按演员名对影片文件夹分类。多人参演时，拥有影片数量多的演员优先。", foreground="gray").grid(row=0, column=0, columnspan=3, sticky='w', padx=5, pady=5)
    t1_src = add_path_row(t1, "需归类影片路径:", 1)
    t1_dst = add_path_row(t1, "整理后输出路径:", 2)
    t1_min = add_text_row(t1, "最小归类视频数:", 3, "4")
    t1_col = add_text_row(t1, "零散视频合集名:", 4, "影片合集")
    
    def launch_t1():
        if not t1_src.get() or not t1_dst.get():
            messagebox.showwarning("提示", "请先选择输入和输出文件夹路径！")
            return
        run_script_backend("actor_grouper.py", {
            "SOURCE_ROOT": t1_src.get(),
            "OUTPUT_ROOT": t1_dst.get(),
            "MIN_COUNT": int(t1_min.get() if t1_min.get().isdigit() else 4),
            "COLLECTION_NAME": t1_col.get()
        })
    b1 = ttk.Button(t1, text=" 🚀 开始分类", command=launch_t1)
    b1.grid(row=5, column=0, columnspan=3, pady=15)
    all_buttons.append(b1)

    # ------------------ Tab 2: 文件夹封面管理 ------------------
    t2 = ttk.Frame(notebook)
    notebook.add(t2, text=" 🖼 文件夹封面 ")
    t2.columnconfigure(1, weight=1)
    
    ttk.Label(t2, text="💡 功能：批量将影片内的海报复制一份并重命名为文件夹名，改善 Vidhub 等播放器浏览体验。", foreground="gray").grid(row=0, column=0, columnspan=3, sticky='w', padx=5, pady=5)
    t2_dir = add_path_row(t2, "影片路径:", 1)
    
    def launch_t2_add():
        if not t2_dir.get(): return messagebox.showwarning("提示", "请选择文件夹路径！")
        run_script_backend("folder_cover_adder.py", {"TARGET_DIR": t2_dir.get()})
        
    def launch_t2_rm():
        if not t2_dir.get(): return messagebox.showwarning("提示", "请选择文件夹路径！")
        run_script_backend("folder_cover_remover.py", {"TARGET_DIR": t2_dir.get()})

    btn_frame_t2 = ttk.Frame(t2)
    btn_frame_t2.grid(row=2, column=0, columnspan=3, pady=15)
    b2_1 = ttk.Button(btn_frame_t2, text=" ➕ 批量添加封面", command=launch_t2_add)
    b2_1.pack(side=tk.LEFT, padx=5)
    b2_2 = ttk.Button(btn_frame_t2, text=" 🗑 批量清理封面", command=launch_t2_rm)
    b2_2.pack(side=tk.LEFT, padx=5)
    all_buttons.extend([b2_1, b2_2])

    # ------------------ Tab 3: 演员重命名 ------------------
    t3 = ttk.Frame(notebook)
    notebook.add(t3, text=" 🏷 演员重命名 ")
    t3.columnconfigure(1, weight=1)
    
    ttk.Label(t3, text="💡 功能：修改 NFO 文件中的演员。", foreground="gray").grid(row=0, column=0, columnspan=3, sticky='w', padx=5, pady=5)
    t3_dir = add_path_row(t3, "影片路径:", 1)
    t3_src_name = add_text_row(t3, "演员原名:", 2)
    t3_dst_name = add_text_row(t3, "演员新名:", 3)
    t3_num = add_text_row(t3, "指定番号 [可选]:", 4)
    
    def launch_t3():
        if not t3_dir.get() or not t3_src_name.get() or not t3_dst_name.get():
            return messagebox.showwarning("提示", "请完整填写路径、原人名和新人名！")
        run_script_backend("nfo_actor_renamer.py", {
            "TARGET_DIR": t3_dir.get(),
            "SEARCH_NAME": t3_src_name.get(),
            "REPLACE_NAME": t3_dst_name.get(),
            "SEARCH_NUMBER": t3_num.get()
        })
    b3 = ttk.Button(t3, text=" 🚀 开始重命名", command=launch_t3)
    b3.grid(row=5, column=0, columnspan=3, pady=15)
    all_buttons.append(b3)

    # ------------------ Tab 4: 批量替换 NFO ------------------
    t4 = ttk.Frame(notebook)
    notebook.add(t4, text=" 📝 替换 NFO")
    t4.columnconfigure(1, weight=1)
    
    ttk.Label(t4, text="💡 功能：批量复制新的 NFO 替换旧影片 NFO。", foreground="gray").grid(row=0, column=0, columnspan=3, sticky='w', padx=5, pady=5)
    t4_src = add_path_row(t4, "新 NFO 源路径:", 1)
    t4_dst = add_path_row(t4, "被覆盖影片路径:", 2)
    t4_num = add_text_row(t4, "指定番号 [可选]:", 3)
    
    def launch_t4():
        if not t4_src.get() or not t4_dst.get(): return messagebox.showwarning("提示", "路径不能为空！")
        run_script_backend("nfo_replacer.py", {
            "SOURCE_FOLDER": t4_src.get(),
            "DEST_BASE_FOLDER": t4_dst.get(),
            "SEARCH_NUMBER": t4_num.get()
        })
    b4 = ttk.Button(t4, text=" 🚀 开始替换 NFO", command=launch_t4)
    b4.grid(row=4, column=0, columnspan=3, pady=15)
    all_buttons.append(b4)

    # ------------------ Tab 5: NFO 标签与类型编辑 ------------------
    t5 = ttk.Frame(notebook)
    notebook.add(t5, text=" 🏷 标签/类型编辑 ")
    t5.columnconfigure(1, weight=1)
    
    ttk.Label(t5, text="💡 功能：批量增、删、改 NFO 文件中的 <tag> 和 <genre> 字段。", foreground="gray").grid(row=0, column=0, columnspan=3, sticky='w', padx=5, pady=5)
    t5_dir = add_path_row(t5, "影片路径:", 1)
    t5_src = add_text_row(t5, "查找 [留空则新增]:", 2)
    t5_dst = add_text_row(t5, "替换 [留空则删除]:", 3)
    t5_num = add_text_row(t5, "指定番号 [可选]:", 4)
    
    def launch_t5():
        if not t5_dir.get(): return messagebox.showwarning("提示", "目标文件夹不能为空！")
        run_script_backend("nfo_tag_genre_editor.py", {
            "TARGET_DIRECTORY": t5_dir.get(),
            "SEARCH_ITEM": t5_src.get(),
            "REPLACE_ITEM": t5_dst.get(),
            "SEARCH_NUMBER": t5_num.get()
        })
    b5 = ttk.Button(t5, text=" 🚀 开始编辑标签", command=launch_t5)
    b5.grid(row=5, column=0, columnspan=3, pady=15)
    all_buttons.append(b5)

    # ------------------ Tab 6: 提取覆盖标签 ------------------
    t6 = ttk.Frame(notebook)
    notebook.add(t6, text=" 🔄 覆盖标签 ")
    t6.columnconfigure(1, weight=1)
    
    ttk.Label(t6, text="💡 功能：批量从新 NFO 中提取 <tag>和<genre> 覆盖到旧 NFO 中，不改变其他信息。", foreground="gray").grid(row=0, column=0, columnspan=3, sticky='w', padx=5, pady=5)
    t6_src = add_path_row(t6, "NFO 提取路径:", 1)
    t6_dst = add_path_row(t6, "NFO 覆盖路径:", 2)
    t6_num = add_text_row(t6, "指定番号 [可选]:", 3)
    
    def launch_t6():
        if not t6_src.get() or not t6_dst.get(): return messagebox.showwarning("提示", "路径不能为空！")
        run_script_backend("nfo_tag_genre_overwriter.py", {
            "SOURCE_PATH": t6_src.get(),
            "TARGET_PATH": t6_dst.get(),
            "SEARCH_NUMBER": t6_num.get()
        })
    b6 = ttk.Button(t6, text=" 🚀 开始覆盖标签", command=launch_t6)
    b6.grid(row=4, column=0, columnspan=3, pady=15)
    all_buttons.append(b6)

    # ------------------ Tab 7: 剧照预览修复 ------------------
    t7 = ttk.Frame(notebook)
    notebook.add(t7, text=" 🎬 剧照修复 ")
    t7.columnconfigure(1, weight=1)
    
    ttk.Label(t7, text="💡 功能：解决电影剧照不显示问题。将 extrafanart 内图片移至 behind the scenes。", foreground="gray").grid(row=0, column=0, columnspan=3, sticky='w', padx=5, pady=5)
    t7_dir = add_path_row(t7, "影片路径:", 1)
    
    def launch_t7():
        if not t7_dir.get(): return messagebox.showwarning("提示", "路径不能为空！")
        run_script_backend("preview_fixer.py", {"BASE_PATH": t7_dir.get()})
        
    b7 = ttk.Button(t7, text=" 🚀 开始修复剧照", command=launch_t7)
    b7.grid(row=2, column=0, columnspan=3, pady=15)
    all_buttons.append(b7)

    # ------------------ Tab 8: 批量复制预告片 ------------------
    t8 = ttk.Frame(notebook)
    notebook.add(t8, text=" 🎞 分发预告片 ")
    t8.columnconfigure(1, weight=1)
    
    ttk.Label(t8, text="💡 功能：根据“番号-trailer”命名规范，批量把预告片并分发到电影目录中。", foreground="gray").grid(row=0, column=0, columnspan=3, sticky='w', padx=5, pady=5)
    t8_src = add_path_row(t8, "预告片源路径:", 1)
    t8_dst = add_path_row(t8, "影片路径:", 2)
    
    def launch_t8():
        if not t8_src.get() or not t8_dst.get(): return messagebox.showwarning("提示", "路径不能为空！")
        run_script_backend("trailer_copier.py", {
            "source_dir": t8_src.get(),
            "dest_dir": t8_dst.get()
        })
        
    b8 = ttk.Button(t8, text=" 🚀 开始分发预告片", command=launch_t8)
    b8.grid(row=3, column=0, columnspan=3, pady=15)
    all_buttons.append(b8)

    # ------------------ Tab 9: 批量同步字幕 ------------------
    t9 = ttk.Frame(notebook)
    notebook.add(t9, text=" 💬 分发字幕 ")
    t9.columnconfigure(1, weight=1)
    
    ttk.Label(t9, text="💡 功能：批量从字幕库中提取字幕，添加到对应的电影文件夹内。注意：无法识别电影是否内嵌字幕", foreground="gray").grid(row=0, column=0, columnspan=3, sticky='w', padx=5, pady=5)
    t9_src = add_path_row(t9, "字幕路径:", 1)
    t9_dst = add_path_row(t9, "影片路径:", 2)
    
    # 覆盖已有字幕的开关
    t9_overwrite = tk.BooleanVar(value=False)
    chk_overwrite = ttk.Checkbutton(t9, text=" 是否覆盖已有字幕", variable=t9_overwrite)
    chk_overwrite.grid(row=3, column=0, columnspan=3, pady=5)
    
    def launch_t9():
        if not t9_src.get() or not t9_dst.get():
            return messagebox.showwarning("提示", "请选择字幕源路径和影片目标路径！")
        run_script_backend("subtitle_adder.py", {
            "SOURCE_FOLDER": t9_src.get(),
            "DEST_BASE_FOLDER": t9_dst.get(),
            "OVERWRITE_EXISTING": t9_overwrite.get()
        })
        
    b9 = ttk.Button(t9, text=" 🚀 开始分发字幕", command=launch_t9)
    b9.grid(row=4, column=0, columnspan=3, pady=15)
    all_buttons.append(b9)

    # 启动主循环
    root.mainloop()

if __name__ == "__main__":
    create_main_gui()
