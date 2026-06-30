# settings_window.py
import json
import base64
import customtkinter as ctk
from tkinter import messagebox
import ctypes
from ctypes import wintypes
from PIL import Image

class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, master, on_close_callback=None, app=None):
        super().__init__(master)
        try:
            self.iconbitmap('icon.ico')
        except:
            pass
        self.master = master
        self.app = app                 # 保存主程序实例
        self.on_close_callback = on_close_callback
        self.title("NyanMoji 设置")
        self.overrideredirect(True)          # 去掉系统标题栏
        # 获取当前主题
        self.is_dark = ctk.get_appearance_mode().lower() == "dark"
        # 根据主题设置背景色
        self.bg_color = "#2A2A3E" if self.is_dark else "#FFFFFF"
        self.fg_color = "#E0E0F0" if self.is_dark else "#222222"
        self.hover_color = "#4A4A7A" if self.is_dark else "#E8E8F0"
        self.select_color = "#6A6A9A" if self.is_dark else "#D0D0E8"
        self.scroll_bg = "#1E1E2E" if self.is_dark else "#F5F5F8"
        self.sep_color = "#3E3E55" if self.is_dark else "#E0E0E0"

        self.configure(bg=self.bg_color)
        self.configure(fg_color=self.bg_color)
        self.attributes('-alpha', 0.0)        # 初始完全透明
        self.attributes('-topmost', True)
        self.resizable(False, False)
        

        # 窗口尺寸
        self.win_width = 720
        self.win_height = 500
        self.geometry(f"{self.win_width}x{self.win_height}")

        # 动画参数
        self.anim_alpha = 0.0
        self.anim_scale = 0.6
        self.anim_running = False

        # 加载数据
        self.config = self._load_config()
        self.db = self._load_db()

        self._create_widgets()
        self._bind_drag()
        
        # 绑定 Esc 键关闭窗口
        self.bind("<Escape>", lambda e: self._start_close_animation())
        # 确保窗口能捕获键盘事件
        self.focus_force()

        self.theme_sticker_image = None   # 用于保持图片引用

        self.restart_after_close = False   # 新增标志

    # ---------- 数据加载 ----------
    def _load_config(self):
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {"theme": "dark"}

    def _load_db(self):
        try:
            with open('kaomoji_db.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}

    # ---------- 构建界面 ----------
    def _create_widgets(self):
        # 主容器（圆角背景）
        self.main_frame = ctk.CTkFrame(self, corner_radius=24, fg_color=self.bg_color, bg_color=self.bg_color)
        self.main_frame.pack(fill="both", expand=True, padx=0, pady=0)

        # 标题栏
        self.title_bar = ctk.CTkFrame(self.main_frame, height=36, fg_color="transparent")
        self.title_bar.pack(fill="x", pady=(8,0), padx=12)
        self.title_label = ctk.CTkLabel(self.title_bar, text="🐱 NyanMoji 设置",
                                        font=ctk.CTkFont(size=14, weight="bold"),
                                        text_color=self.fg_color)
        self.title_label.pack(side="left")
        self.close_btn = ctk.CTkButton(self.title_bar, text="✕", width=24, height=24,
                                    command=self._start_close_animation,
                                    fg_color="transparent", hover_color="#FFE8E8" if not self.is_dark else "#4A2A2A",
                                    text_color=self.fg_color)
        self.close_btn.pack(side="right")

        # 分割线
        ctk.CTkFrame(self.main_frame, height=1, fg_color=self.sep_color).pack(fill="x", padx=12, pady=(4,8))

        # 主体
        body_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        body_frame.pack(fill="both", expand=True, padx=12, pady=(0,12))

        # 导航
        self.nav_frame = ctk.CTkFrame(body_frame, width=140, fg_color="transparent")
        self.nav_frame.pack(side="left", fill="y", padx=(0,12))

        self.nav_buttons = []
        nav_items = ["主题", "词条管理", "导入导出", "关于"]
        self.nav_var = ctk.StringVar(value="主题")

        for item in nav_items:
            btn = ctk.CTkButton(
                self.nav_frame,
                text=item,
                anchor="w",
                fg_color="transparent",
                text_color=self.fg_color,
                hover_color=self.hover_color,
                font=ctk.CTkFont(size=13),
                corner_radius=8,
                height=36,
                command=lambda x=item: self._select_nav(x)
            )
            btn.pack(fill="x", pady=2)
            self.nav_buttons.append(btn)

        # 内容容器
        self.content_frame = ctk.CTkFrame(body_frame, fg_color="transparent")
        self.content_frame.pack(side="left", fill="both", expand=True)

        self.pages = {}
        self._create_page("主题")
        self._create_page("词条管理")
        self._create_page("导入导出")
        self._create_page("关于")
        self._select_nav("主题")

    def _create_page(self, name):
        """创建每个选项卡的内容页面"""
        page = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        if name == "主题":
            self._setup_theme_page(page)
        elif name == "词条管理":
            self._setup_manage_page(page)
        elif name == "导入导出":
            self._setup_import_page(page)
        elif name == "关于":
            self._setup_about_page(page)
        self.pages[name] = page

    def _select_nav(self, name):
        for btn in self.nav_buttons:
            if btn.cget("text") == name:
                btn.configure(fg_color=self.select_color, text_color="#000000" if not self.is_dark else "#FFFFFF")
            else:
                btn.configure(fg_color="transparent", text_color=self.fg_color)
        self._switch_page(name)

    def _switch_page(self, name):
        """显示对应页面，隐藏其他"""
        for key, page in self.pages.items():
            if key == name:
                page.pack(fill="both", expand=True)
            else:
                page.pack_forget()
    

    # ---------- 各页面内容 ----------
    def _setup_theme_page(self, parent):
        ctk.CTkLabel(parent, text="选择界面主题", font=ctk.CTkFont(size=16, weight="bold"),
                    text_color=self.fg_color).pack(anchor="w", pady=(10,20))
        self.theme_var = ctk.StringVar(value=self.config.get("theme", "dark"))
        radio_frame = ctk.CTkFrame(parent, fg_color="transparent")
        radio_frame.pack(anchor="w", pady=5)
        ctk.CTkRadioButton(radio_frame, text="亮色", variable=self.theme_var,
                        value="light", text_color=self.fg_color).pack(side="left", padx=10)
        ctk.CTkRadioButton(radio_frame, text="暗色", variable=self.theme_var,
                        value="dark", text_color=self.fg_color).pack(side="left", padx=10)
        ctk.CTkButton(parent, text="应用主题", command=self._apply_theme,
                    fg_color="#3A7EB1", text_color="white", corner_radius=8).pack(pady=20, anchor="w")
        # ---- 右下角贴纸 ----
        self.sticker_frame = ctk.CTkFrame(parent, fg_color="transparent")
        self.sticker_frame.pack(side="bottom", anchor="se", pady=50, padx=50)
        self.theme_sticker_label = ctk.CTkLabel(parent, text="")
        self.theme_sticker_label.pack()
        self.theme_sticker_label.place(relx=1.0, rely=1.0, x=-20, y=-20, anchor="se")  # 距右下角20px
        self._update_theme_sticker()   # 根据当前主题初始化

    def _update_theme_sticker(self):
        """根据当前主题显示贴纸，固定宽度 250px，高度自适应"""
        try:
            current_theme = ctk.get_appearance_mode().lower()
            img_file = "theme_dark.png" if current_theme == "dark" else "theme_light.png"
            img = Image.open(img_file)

            # 设定目标宽度（可调大）
            target_width = 250
            orig_width, orig_height = img.size
            ratio = target_width / orig_width
            target_height = int(orig_height * ratio)

            # 缩放图片
            img_resized = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
            # 创建 CTkImage，并强制指定 size
            self.theme_sticker_image = ctk.CTkImage(
                light_image=img_resized,
                dark_image=img_resized,
                size=(target_width, target_height)
            )
            self.theme_sticker_label.configure(image=self.theme_sticker_image, text="")
            # 使用 place 定位在右下角（只传位置参数）
            self.theme_sticker_label.place(
                relx=1.0, rely=1.0,
                x=-20, y=-20,
                anchor="se"
            )
        except Exception as e:
            # 后备：显示 emoji
            self.theme_sticker_label.configure(
                text="🐱" if ctk.get_appearance_mode().lower() == "dark" else "😺",
                image=None
            )
            # 使用 pack 作为后备
            self.theme_sticker_label.place_forget()
            self.theme_sticker_label.pack(side="bottom", anchor="se", pady=15, padx=15)
            print(f"主题贴纸加载失败: {e}")
    def _setup_manage_page(self, parent):
        # 配置 parent 使用 grid，并分配行权重
        parent.grid_rowconfigure(0, weight=1)   # 中间行（列表区）可拉伸
        parent.grid_rowconfigure(1, weight=0)   # 底部行固定高度
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_columnconfigure(1, weight=2)

        # ---------- 第0行：左侧类别 + 右侧词条 ----------
        # 左侧类别
        left_frame = ctk.CTkFrame(parent, fg_color="transparent")
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0,5))
        ctk.CTkLabel(left_frame, text="类别", font=ctk.CTkFont(size=12, weight="bold"),
                    text_color=self.fg_color).pack(anchor="w")
        self.category_scroll = ctk.CTkScrollableFrame(left_frame, width=120, fg_color=self.scroll_bg)
        self.category_scroll.pack(fill="both", expand=True, pady=5)
        self.category_btns = {}
        self.selected_category = None

        # 右侧词条
        right_frame = ctk.CTkFrame(parent, fg_color="transparent")
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(5,0))
        ctk.CTkLabel(right_frame, text="词条", font=ctk.CTkFont(size=12, weight="bold"),
                    text_color=self.fg_color).pack(anchor="w")
        self.entry_scroll = ctk.CTkScrollableFrame(right_frame, width=280, fg_color=self.scroll_bg)
        self.entry_scroll.pack(fill="both", expand=True, pady=5)
        self.entry_widgets = {}

        # 添加词条行（放在 right_frame 底部，用 pack）
        entry_control = ctk.CTkFrame(right_frame, fg_color="transparent")
        entry_control.pack(fill="x", pady=5, side="bottom")   # 固定在底部
        self.new_entry_entry = ctk.CTkEntry(entry_control, placeholder_text="新词条")
        self.new_entry_entry.pack(side="left", fill="x", expand=True, padx=(0,5))
        ctk.CTkButton(entry_control, text="添加", width=60, command=self._add_entry,
                    fg_color=self.select_color, text_color=self.fg_color).pack(side="left")

        # ---------- 第1行：底部操作栏 ----------
        bottom_frame = ctk.CTkFrame(parent, fg_color="transparent")
        bottom_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=5)

        self.new_cat_entry = ctk.CTkEntry(bottom_frame, placeholder_text="新类别名")
        self.new_cat_entry.pack(side="left", fill="x", expand=True, padx=(0,5))
        ctk.CTkButton(bottom_frame, text="添加类别", width=80, command=self._add_category,
                    fg_color=self.select_color, text_color=self.fg_color).pack(side="left", padx=2)
        ctk.CTkButton(bottom_frame, text="删除类别", width=80, command=self._delete_category,
                    fg_color=self.select_color, text_color=self.fg_color).pack(side="left", padx=2)
        ctk.CTkButton(bottom_frame, text="保存修改", width=80, command=self._save_db,
                    fg_color="#3A7EB1", text_color="white").pack(side="right", padx=2)

        # 刷新列表
        self._refresh_category_list()

    def _setup_import_page(self, parent):
        ctk.CTkLabel(parent, text="NyanMojiCode 是词库的编码字符串，可用于备份或分享。",
                    wraplength=500, text_color=self.fg_color).pack(pady=10)
        ctk.CTkLabel(parent, text="当前词库编码:", text_color=self.fg_color).pack(anchor="w", padx=10)
        self.code_text = ctk.CTkTextbox(parent, height=100, wrap="word", fg_color=self.scroll_bg,
                                        text_color=self.fg_color)
        self.code_text.pack(fill="both", expand=True, padx=10, pady=5)
        btn_frame = ctk.CTkFrame(parent, fg_color="transparent")
        btn_frame.pack(pady=5)
        ctk.CTkButton(btn_frame, text="导出编码 (复制)", command=self._export_code,
                    fg_color=self.select_color, text_color=self.fg_color).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="导入编码 (粘贴)", command=self._import_code,
                    fg_color=self.select_color, text_color=self.fg_color).pack(side="left", padx=5)
        self._update_code_display()

    def _setup_about_page(self, parent):
         # 加载图片（使用 CTkImage）
        from PIL import Image
        logo_img = ctk.CTkImage(Image.open('logo.jpeg'), size=(200, 80))
        logo_label = ctk.CTkLabel(parent, image=logo_img, text="")
        logo_label.pack(pady=10)
        ctk.CTkLabel(parent, text="🐱 NyanMoji 版本 1.0.0",
                    font=ctk.CTkFont(size=18, weight="bold"), text_color=self.fg_color).pack(pady=20)
        ctk.CTkLabel(parent, text="一个可爱的颜文字输入工具", wraplength=300, text_color=self.fg_color).pack(pady=5)
        ctk.CTkLabel(parent, text="使用 Python + CustomTkinter 开发", wraplength=300, text_color=self.fg_color).pack(pady=5)
        ctk.CTkLabel(parent, text="GitHub: https://github.com/few302/nyanmoji", wraplength=300, text_color=self.fg_color).pack(pady=5)
        # --- 退出按钮 ---
        ctk.CTkButton(
            parent,
            text="退出程序",
            command=self._quit_app,
            fg_color="#E74C3C",          # 红色背景
            hover_color="#C0392B",        # 深红色悬停
            text_color="white",
            corner_radius=8,
            width=120
        ).pack(pady=20)

    def _show_messagebox(self, msg_func, title, message, **kwargs):
        """
        显示消息弹窗，确保弹窗在设置窗口上方。
        msg_func: messagebox.showinfo, showwarning, showerror, askyesno 等函数
        title, message: 弹窗标题和内容
        **kwargs: 其他参数（如 parent）
        """
        # 记录当前置顶状态
        was_topmost = self.attributes('-topmost')
        # 临时取消置顶，让弹窗能浮在窗口上方
        if was_topmost:
            self.attributes('-topmost', False)
        try:
            # 默认将 parent 设为自身，使弹窗居中于设置窗口
            if 'parent' not in kwargs:
                kwargs['parent'] = self
            result = msg_func(title, message, **kwargs)
            return result
        finally:
            # 恢复置顶状态
            if was_topmost:
                self.attributes('-topmost', True)
    # ---------- 词条管理逻辑（与原一致，略作调整）----------
    def _refresh_category_list(self):
        for widget in self.category_scroll.winfo_children():
            widget.destroy()
        self.category_btns.clear()
        for cat in self.db.keys():
            btn = ctk.CTkButton(self.category_scroll, text=cat, anchor="w",
                                fg_color="transparent", text_color=self.fg_color,
                                hover_color="#D0D0E8",
                                command=lambda c=cat: self._select_category(c))
            btn.pack(fill="x", pady=1)
            self.category_btns[cat] = btn
        if self.db:
            self._select_category(list(self.db.keys())[0])

    def _select_category(self, category):
        self.selected_category = category
        for cat, btn in self.category_btns.items():
            btn.configure(fg_color="#C0C0DE" if cat == category else "transparent")
        self._refresh_entry_list()

    def _refresh_entry_list(self):
        for widget in self.entry_scroll.winfo_children():
            widget.destroy()
        self.entry_widgets.clear()
        if not self.selected_category or self.selected_category not in self.db:
            return
        for entry in self.db[self.selected_category]:
            frame = ctk.CTkFrame(self.entry_scroll, fg_color="transparent")
            frame.pack(fill="x", pady=1)
            label = ctk.CTkLabel(frame, text=entry, font=ctk.CTkFont(size=13), text_color=self.fg_color)
            label.pack(side="left", padx=5)
            edit_btn = ctk.CTkButton(frame, text="编辑", width=40, fg_color=self.scroll_bg,
                                    text_color=self.fg_color, hover_color=self.hover_color,
                                    command=lambda e=entry: self._edit_entry(e))
            edit_btn.pack(side="right", padx=2)
            del_btn = ctk.CTkButton(frame, text="删除", width=40, fg_color=self.scroll_bg,
                                    text_color=self.fg_color, hover_color="#FFD0D0" if not self.is_dark else "#6A2A2A",
                                    command=lambda e=entry: self._delete_entry(e))
            del_btn.pack(side="right", padx=2)
            self.entry_widgets[entry] = (edit_btn, del_btn)

    def _add_category(self):
        name = self.new_cat_entry.get().strip()
        if not name:
            self._show_messagebox(messagebox.showwarning, "警告", "类别名不能为空")
            return
        if name in self.db:
            self._show_messagebox(messagebox.showwarning, "警告", "类别已存在")
            return
        self.db[name] = []
        self._refresh_category_list()
        self._select_category(name)
        self.new_cat_entry.delete(0, 'end')
        print(f"✅ 已添加类别: {name}")  # 调试

    def _save_db(self):
        print("🔥 保存按钮被点击")  # 确认按钮触发
        try:
            # 检查数据库内容
            print(f"当前词库条目数: {len(self.db)}")
            # 保存
            with open('kaomoji_db.json', 'w', encoding='utf-8') as f:
                json.dump(self.db, f, indent=4, ensure_ascii=False)
            self._show_messagebox(messagebox.showinfo, "成功", "词库已保存")
            if self.on_close_callback:
                self.on_close_callback()
            print("✅ 保存成功")
        except Exception as e:
            import traceback
            traceback.print_exc()  # 打印完整堆栈
            self._show_messagebox(messagebox.showerror, "错误", f"保存失败: {e}")

    def _delete_category(self):
        if not self.selected_category:
            return
        if self._show_messagebox(messagebox.askyesno, "确认", f"删除类别 '{self.selected_category}' 及其所有词条？"):
            del self.db[self.selected_category]
            self.selected_category = None
            self._refresh_category_list()
            if self.db:
                self._select_category(list(self.db.keys())[0])
            else:
                self._refresh_entry_list()

    def _add_entry(self):
        if not self.selected_category:
            self._show_messagebox(messagebox.showwarning, "警告", "请先选择一个类别")
            return
        text = self.new_entry_entry.get().strip()
        if not text:
            self._show_messagebox(messagebox.showwarning, "警告", "词条不能为空")
            return
        self.db[self.selected_category].append(text)
        self._refresh_entry_list()
        self.new_entry_entry.delete(0, 'end')

    def _delete_entry(self, entry):
        if not self.selected_category:
            return
        if self._show_messagebox(messagebox.askyesno, "确认", f"删除词条 '{entry}'？"):
            self.db[self.selected_category].remove(entry)
            self._refresh_entry_list()

    def _edit_entry(self, entry):
        dialog = ctk.CTkInputDialog(text="编辑词条:", title="编辑词条")
        new_text = dialog.get_input()
        if new_text and new_text != entry:
            idx = self.db[self.selected_category].index(entry)
            self.db[self.selected_category][idx] = new_text
            self._refresh_entry_list()

    # ---------- 导入导出 ----------
    def _update_code_display(self):
        json_str = json.dumps(self.db, ensure_ascii=False)
        encoded = base64.b64encode(json_str.encode('utf-8')).decode('ascii')
        self.code_text.delete("1.0", "end")
        self.code_text.insert("1.0", encoded)

    def _export_code(self):
        code = self.code_text.get("1.0", "end-1c")
        if code:
            self.clipboard_clear()
            self.clipboard_append(code)
            self._show_messagebox(messagebox.showinfo, "成功", "编码已复制到剪贴板")

    def _import_code(self):
        dialog = ctk.CTkInputDialog(text="请输入 NyanMojiCode:", title="导入编码")
        code = dialog.get_input()
        if not code:
            return
        try:
            json_str = base64.b64decode(code.encode('ascii')).decode('utf-8')
            new_db = json.loads(json_str)
            if not isinstance(new_db, dict):
                raise ValueError("无效格式")
            if self._show_messagebox(messagebox.askyesno, "导入", "将完全替换当前词库，是否继续？"):
                self.db = new_db
                self._save_db()
                self._refresh_category_list()
                self._update_code_display()
                self._show_messagebox(messagebox.showinfo, "成功", "词库已更新")
        except Exception as e:
            self._show_messagebox(messagebox.showerror, "错误", f"导入失败: {e}")

    # ---------- 主题 ----------
    def _apply_theme(self):
        theme = self.theme_var.get()
        self.config['theme'] = theme
        try:
            with open('config.json', 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4)
            ctk.set_appearance_mode(theme)
            # 更新贴纸
            self._update_theme_sticker()
            # 标记需要重启窗口，然后关闭
            self.restart_after_close = True
            self._start_close_animation()
            #self._show_messagebox(messagebox.showinfo, "成功", "主题已应用")
        except Exception as e:
            self._show_messagebox(messagebox.showerror, "错误", f"保存主题失败: {e}")

    def _quit_app(self):
        """关闭整个应用程序（主窗口退出）"""
        # 可选项：如果希望退出前自动保存词库，可以取消下面的注释
        # self._save_db()
        self.master.quit()       # 结束主循环
        self.master.destroy()    # 销毁主窗口（可选，quit后仍会销毁）

    # ---------- 窗口拖拽 ----------
    def _bind_drag(self):
        self.title_bar.bind("<Button-1>", self._start_drag)
        self.title_bar.bind("<B1-Motion>", self._on_drag)

    def _start_drag(self, event):
        self._drag_x = event.x
        self._drag_y = event.y

    def _on_drag(self, event):
        dx = event.x - self._drag_x
        dy = event.y - self._drag_y
        x = self.winfo_x() + dx
        y = self.winfo_y() + dy
        self.geometry(f"+{x}+{y}")

    # ---------- 动画：打开（缩放 + 淡入） ----------
    def show(self):
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        # 起始尺寸 120%
        start_w = int(self.win_width * 1.5)
        start_h = int(self.win_height * 1.5)
        x = (screen_w - start_w) // 2
        y = (screen_h - start_h) // 2
        self.geometry(f"{start_w}x{start_h}+{x}+{y}")
        self.deiconify()
        self.attributes('-alpha', 0.1)
        self.anim_alpha = 0.1
        self.anim_scale = 1.5
        self.anim_running = True
        self._animate_open()
        self._animate_open()

    def _animate_open(self):
        if not self.anim_running:
            return
        self.anim_alpha += 0.1          # 更快
        self.anim_scale -= 0.06
        if self.anim_alpha >= 0.9:
            self.anim_alpha = 0.9
            self.anim_scale = 1.0
            self.anim_running = False
            self.attributes('-alpha', 0.9)
            # **关键修复：显式设置最终居中位置**
            screen_w = self.winfo_screenwidth()
            screen_h = self.winfo_screenheight()
            x = (screen_w - self.win_width) // 2
            y = (screen_h - self.win_height) // 2
            self.geometry(f"{self.win_width}x{self.win_height}+{x}+{y}")
            return
        self.attributes('-alpha', self.anim_alpha)
        new_w = int(self.win_width * self.anim_scale)
        new_h = int(self.win_height * self.anim_scale)
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = (screen_w - new_w) // 2
        y = (screen_h - new_h) // 2
        self.geometry(f"{new_w}x{new_h}+{x}+{y}")
        self.after(20, self._animate_open)   # 间隔缩短

    def _start_close_animation(self):
        self.anim_running = True
        self.anim_alpha = 0.9
        self.anim_scale = 1.0
        self._animate_close()

    def _animate_close(self):
        if not self.anim_running:
            return
        self.anim_alpha -= 0.15
        self.anim_scale += 0.06
        if self.anim_alpha <= 0.0:
            self.anim_alpha = 0.0
            self.anim_scale = 1.2
            self.anim_running = False
            self.attributes('-alpha', 0.0)
            if self.on_close_callback:
                self.on_close_callback()
             # 判断是否需要重启窗口
            if self.restart_after_close:
                self.restart_after_close = False
                # 延迟 100ms 后重新打开设置窗口
                if self.app:
                    self.app.root.after(100, self.app.toggle_settings)
            self.destroy()
            return
        self.attributes('-alpha', self.anim_alpha)
        new_w = int(self.win_width * self.anim_scale)
        new_h = int(self.win_height * self.anim_scale)
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = (screen_w - new_w) // 2
        y = (screen_h - new_h) // 2
        self.geometry(f"{new_w}x{new_h}+{x}+{y}")
        self.after(8, self._animate_close)
    # 外部调用关闭（例如点击关闭按钮）
    def hide(self):
        """外部调用关闭（与 toggle 配合）"""
        self._start_close_animation()