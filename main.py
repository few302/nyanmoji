"""
NyanMoji - 调试版（pynput + 弹窗焦点强制）
"""

import json
import threading
import customtkinter as ctk
from pynput import keyboard
from pynput.keyboard import Key, Controller as KeyboardController
import pyautogui
import os
from settings_window import SettingsWindow
import signal
import sys
import ctypes
from PIL import Image
import pystray

# ------------------- 配置 -------------------
TRIGGER_KEY = '/'
DB_FILE = 'kaomoji_db.json'
CONFIG_FILE = 'config.json'
MAX_CANDIDATES = 10

def load_config():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    default_config = {"theme": "dark"}
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=4)
        return default_config

config = load_config()
ctk.set_appearance_mode(config.get("theme", "dark"))
ctk.set_default_color_theme("blue")

def load_database():
    default_db = {"gaoxing":["(＾▽＾)","(*^▽^*)","ヽ(●´∀`●)ﾉ","✧(≖ ◡ ≖✿)","ヾ(＠⌒ー⌒＠)ノ","awa","uwu","ovo"],"shangxin":["(；′⌒`)","(┬┬﹏┬┬)","(｡•́︿•̀｡)","ಥ_ಥ","( p′︵‵。)"],"mao":["₍˄·͈༝·͈˄₎ฅ˒˒","=^._.^= ∫","₍˄ุ.͡˳̫.˄ุ₎","≽^•⩊•^≼","🐾 (=´∇｀=) 🐾"],"tanshou":["┐(´д`)┌","╮(╯▽╰)╭","¯\\_(ツ)_/¯"],"zan":["(•̀ᴗ•́)و ̑̑","ｂ（￣▽￣）ｄ","👍(๑•̀ㅂ•́)و✧"],"aixin":["(´▽`ʃ♡ƪ)","❤ (ɔˆз(ˆ⌣ˆc)","♡＾▽＾♡"],"kunhuo":["(￣ω￣;)","（；￣ェ￣）","┐(￣ヘ￣)┌","🤔(・_・?)"],"baituo":["(人◕ω◕)","m(_ _)m","(_ _)。゜zｚＺ"],"wuyu":["(￣～￣;)","（´-`）.｡oO","(-_-;)"],"haixiu":["(〃∀〃)","(/ω＼)","(*/ω＼*)"],"jingya":["(ﾟДﾟ≡ﾟДﾟ)","Σ(°△°|||)︴","∑(;°Д°)","（°ο°）","(°ロ°)"],"shengqi":["(｀皿´＃)","(╬◣д◢)","┗(｀Дﾟ)┓","ヽ(｀⌒´)ノ","(ᗒᗣᗕ)՞"],"shuijiao":["(￣o￣)ゞ","(－_－) zz","（U・ω・U）","（￣﹃￣）","(-.-)Zzz..."],"sikao":["(￣▽￣)σ?","（￣～￣）","（￣﹃￣）","（・＿・）","（￣＿￣）"],"deyi":["(￣▽￣)ノ","ヽ(￣▽￣)ﾉ","└(￣▽￣)┘","٩(◕‿◕)۶","（￣︶￣）"],"sajiao":["(｡♡‿♡｡)","(◕‿◕)","(ᵒ̤̑ ₀̑ ᵒ̤̑)","（´ω｀）","（＾ω＾）"],"maimeng":["(｡◕‿◕｡)","（◕‿◕）","(◠‿◠)","（＾◡＾）","(•‿•)"],"bishi":["(￣_,￣)","（￣へ￣）","（￢_￢）","（￣～￣）","（−＿−）"],"qinqin":["(^з^)-☆","(chu~)","（＾＾）人（＾＾）","(￣ε￣)","（´з｀）"],"daku":["(´；ω；｀)","（；＿；）","(´;︵;`)","（ｉДｉ）","(T_T)"],"weiqu":["(｡•́︿•̀｡)","(´;︵;`)","（；へ；）","(つ﹏⊂)","(＞﹏＜)"]}
    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(default_db, f, indent=4, ensure_ascii=False)
        return default_db

KAOMOJI_DB = load_database()
print("数据库加载完成，条目数：", len(KAOMOJI_DB))

class InputState:
    def __init__(self):
        self.active = False
        self.buffer = ""
        self.keyboard_ctrl = KeyboardController()

state = InputState()

class NyanMojiApp:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.withdraw()
        try:
            self.root.iconbitmap('icon.ico')          # Windows 专用
        except:
            pass
        self.popup = None
        self.settings_window = None          
        self.modifiers = {'ctrl': False, 'shift': False, 'alt': False} 
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.pack(fill="both", expand=True)
        # 加一张背景图
        bg_img = ctk.CTkImage(Image.open('nyafu.jpeg'), size=(400, 400))
        bg_label = ctk.CTkLabel(self.main_frame, image=bg_img, text="")
        bg_label.pack()

    def show_popup(self, candidates, x, y):
        print("show_popup 被调用，候选数：", len(candidates))
        if self.popup:
            self.popup.close()
        self.popup = NyanMojiPopup(self.root, candidates, x, y, on_close=self.on_popup_closed)

    def update_popup(self, candidates):
        if self.popup:
            self.popup.update_candidates(candidates)

    def close_popup(self):
        if self.popup:
            self.popup.close()

    def on_popup_closed(self):
        self.popup = None

    def toggle_settings(self):
        # 清理无效或已隐藏的窗口
        if self.settings_window is not None:
            try:
                if self.settings_window.winfo_exists():
                    if self.settings_window.winfo_ismapped():
                        # 如果正在显示，则关闭（触发销毁动画）
                        self.settings_window.hide()
                        return
                    else:
                        # 存在但未映射（不正常状态），直接销毁
                        self.settings_window.destroy()
                self.settings_window = None
            except Exception:
                self.settings_window = None

        # 创建新窗口
        self.settings_window = SettingsWindow(self.root, on_close_callback=self.reload_database, app=self)
        self.settings_window.show()
        print("✅ 设置窗口已打开")

    def reload_database(self):
        """设置窗口保存后重新加载数据库"""
        global KAOMOJI_DB
        KAOMOJI_DB = load_database()
        print("数据库已重新加载，条目数：", len(KAOMOJI_DB))
    def run(self):
        self.root.mainloop()

class NyanMojiPopup:
    def __init__(self, master, candidates, x, y, on_close):
        print("弹窗初始化")
        self.master = master
        self.candidates = candidates
        self.selected_index = 0
        self.on_close = on_close

        is_dark = ctk.get_appearance_mode().lower() == "dark"
        card_color = "#2A2A3C" if is_dark else "#FFFFFF"
        text_color = "#E0E0F0" if is_dark else "#222233"
        hover_color = "#4A4A7A" if is_dark else "#E0E0F0"
        number_color = "#AAAAFF" if is_dark else "#6666AA"

        self.window = ctk.CTkToplevel(master)
        self.window.title("NyanMoji")
        self.window.overrideredirect(True)
        self.window.attributes('-topmost', True)
        self.window.configure(fg_color=card_color)
        self.window.attributes('-alpha', 0.92)
        self.window.geometry(f"+{x+10}+{y+15}")

        # 强制捕获所有输入
        self.window.grab_set()
        # 只要窗口获得焦点就强制保持
        self.window.bind("<FocusIn>", lambda e: self.window.focus_force())

        # ---- UI 布局 ----
        self.main_frame = ctk.CTkFrame(self.window, corner_radius=20, fg_color=card_color, border_width=0)
        self.main_frame.pack(fill="both", expand=True, padx=0, pady=0)
        self.inner_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.inner_frame.pack(padx=8, pady=8, fill="both", expand=True)

        self.title_label = ctk.CTkLabel(
            self.inner_frame,
            text="🐱 NyanMoji",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#8888AA" if is_dark else "#666688"
        )
        self.title_label.pack(pady=(4, 2), padx=4, anchor="w")

        self.separator = ctk.CTkFrame(self.inner_frame, height=1, fg_color="#3E3E55" if is_dark else "#DDDDEE")
        self.separator.pack(fill="x", padx=4, pady=(0, 4))

        self.scroll_frame = ctk.CTkScrollableFrame(
            self.inner_frame,
            width=280,
            height=min(220, len(candidates) * 38 + 6),
            corner_radius=10,
            fg_color="transparent",
            scrollbar_button_color="#4A4A6A" if is_dark else "#CCCCDD",
            scrollbar_button_hover_color="#6A6A8A" if is_dark else "#AAAAAA"
        )
        self.scroll_frame.pack(padx=2, pady=(0, 4), fill="both", expand=True)
        # 滚动条抢焦点时立刻抢回
        self.scroll_frame.bind("<FocusIn>", lambda e: self.window.focus_force())

        self.button_widgets = []
        self._build_buttons(candidates)

        # ---- 键盘绑定（全部绑定在窗口上） ----
        self.window.bind("<Up>", lambda e: self.move_selection(-1))
        self.window.bind("<Down>", lambda e: self.move_selection(1))
        self.window.bind("<Left>", lambda e: self.move_selection(-1))
        self.window.bind("<Right>", lambda e: self.move_selection(1))
        self.window.bind("<Return>", lambda e: self.confirm())
        self.window.bind("<Escape>", lambda e: self.close())
        for i in range(1, 10):
            self.window.bind(str(i), lambda e, idx=i-1: self.select_index(idx))

        # 最后强制窗口获得焦点
        self.window.focus_force()
        print("弹窗初始化完成")

    def _build_buttons(self, candidates):
        for btn in self.button_widgets:
            btn.destroy()
        self.button_widgets.clear()
        self.selected_index = 0

        is_dark = ctk.get_appearance_mode().lower() == "dark"
        text_color = "#E0E0F0" if is_dark else "#222233"
        hover_color = "#4A4A7A" if is_dark else "#E0E0F0"
        number_color = "#AAAAFF" if is_dark else "#6666AA"

        for i, kao in enumerate(candidates):
            item_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
            item_frame.pack(pady=1, padx=3, fill="x")

            num_label = ctk.CTkLabel(
                item_frame,
                text=f"{i+1}.",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=number_color,
                width=20,
                anchor="e"
            )
            num_label.pack(side="left", padx=(2, 4))

            btn = ctk.CTkButton(
                item_frame,
                text=kao,
                font=ctk.CTkFont(size=14, family="Segoe UI Emoji"),
                anchor="w",
                fg_color="transparent",
                hover_color=hover_color,
                text_color=text_color,
                corner_radius=8,
                height=34,
                command=lambda idx=i: self.select_index(idx)
            )
            btn.pack(side="left", fill="x", expand=True)
            btn.bind("<Enter>", lambda e, idx=i: self.set_hover(idx))
            # 按钮抢焦点时立刻抢回
            btn.bind("<FocusIn>", lambda e: self.window.focus_force())
            self.button_widgets.append(btn)

        self.update_selection()
        new_height = min(220, len(candidates) * 38 + 6)
        self.scroll_frame.configure(height=new_height)

    def update_candidates(self, new_candidates):
        self.candidates = new_candidates
        self._build_buttons(new_candidates)

    def set_hover(self, index):
        self.selected_index = index
        self.update_selection()
        self.window.focus_force()

    def select_index(self, index):
        if 0 <= index < len(self.candidates):
            self.selected_index = index
            self.confirm()

    def update_selection(self):
        is_dark = ctk.get_appearance_mode().lower() == "dark"
        for i, btn in enumerate(self.button_widgets):
            if i == self.selected_index:
                btn.configure(
                    fg_color="#5A5A9A" if is_dark else "#CCCCFF",
                    text_color="#FFFFFF" if is_dark else "#000000"
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color="#E0E0F0" if is_dark else "#222233"
                )

        # ---- 滚动到选中项 ----
        if not self.button_widgets:
            return

        try:
            # 获取滚动框架内部的 Canvas
            canvas = self.scroll_frame._parent_canvas

            # 获取所有子控件的边界
            bbox = canvas.bbox("all")
            if not bbox or bbox[3] <= 0:
                return

            total_height = bbox[3]
            viewport_height = canvas.winfo_height()
            if viewport_height <= 0:
                return

            # 获取选中按钮相对于滚动框架顶部的距离
            selected_btn = self.button_widgets[self.selected_index]
            # 按钮的父级是 item_frame，我们需要累加父级的 y 坐标
            parent_frame = selected_btn.master
            parent_y = parent_frame.winfo_y()
            btn_y = selected_btn.winfo_y()
            y = parent_y + btn_y

            # 计算滚动比例，使选中项出现在可视区域的 1/3 位置
            fraction = y / total_height
            fraction -= (viewport_height / total_height) * 0.3
            fraction = max(0.0, min(1.0, fraction))

            # 应用滚动
            canvas.yview_moveto(fraction)
        except Exception as e:
            print(f"滚动候选项失败: {e}")

    def move_selection(self, delta):
        new_idx = self.selected_index + delta
        if 0 <= new_idx < len(self.candidates):
            self.selected_index = new_idx
            self.update_selection()
            self.window.focus_force()

    def confirm(self):
        if not self.candidates:
            return
        selected_kao = self.candidates[self.selected_index]
        buffer_copy = state.buffer
        self.window.grab_release()
        self.window.destroy()
        if self.on_close:
            self.on_close()
        self.master.after(20, lambda: self._do_replace(selected_kao, buffer_copy))

    def _do_replace(self, kaomoji, buffer):
        delete_count = 1 + len(buffer)
        for _ in range(delete_count):
            state.keyboard_ctrl.press(Key.backspace)
            state.keyboard_ctrl.release(Key.backspace)
        state.keyboard_ctrl.type(kaomoji)
        state.buffer = ""
        state.active = False

    def close(self):
        self.window.grab_release()
        self.window.destroy()
        state.buffer = ""
        state.active = False
        if self.on_close:
            self.on_close()

# ------------------- 键盘监听器（pynput，不启用suppress） -------------------
def on_press(key):
    global app
    if not app:
        return

    try:
        # 如果弹窗存在，我们完全放行，因为弹窗自己处理键盘事件
        if app.popup is not None:
            return

        # ---- 修饰键状态 ----
        if key == Key.alt_l or key == Key.alt_r:
            app.modifiers['alt'] = True
            return
        # 如果你还保留了 Ctrl/Shift，也一起更新
        elif key == Key.ctrl_l or key == Key.ctrl_r:
            app.modifiers['ctrl'] = True
            return
        elif key == Key.shift_l or key == Key.shift_r:
            app.modifiers['shift'] = True
            return
        
        # 打印调试信息（仅打印字母和特殊键）
        # print(f"按键: {key}")

        # 检测快捷键 Alt+N
        if hasattr(key, 'char') and key.char is not None:
            if key.char == 'n' and app.modifiers.get('alt'):
                app.root.after(0, app.toggle_settings)
                # 返回 False 可阻止该按键继续传递（但不会影响系统）
                return False

        # 触发键 '/'
        if hasattr(key, 'char') and key.char == TRIGGER_KEY:
            print("触发 / 键")
            state.active = True
            state.buffer = ""
            return

        if not state.active:
            return

        # 激活状态下处理拼音
        if hasattr(key, 'char') and key.char is not None:
            char = key.char.lower()
            if char.isalpha():
                state.buffer += char
                print(f"当前缓冲区: {state.buffer}")
                if state.buffer in KAOMOJI_DB:
                    candidates = KAOMOJI_DB[state.buffer][:MAX_CANDIDATES]
                    print(f"匹配成功，候选: {candidates}")
                    x, y = pyautogui.position()
                    app.root.after(0, lambda: app.show_popup(candidates, x, y))
                else:
                    print("无匹配，关闭弹窗")
                    app.root.after(0, app.close_popup)
                return
            else:
                # 非字母（空格、标点等）取消激活
                print("非字母，取消激活")
                app.root.after(0, app.close_popup)
                state.active = False
                state.buffer = ""
                return

        elif key == Key.backspace:
            if state.buffer:
                state.buffer = state.buffer[:-1]
                print(f"退格后缓冲区: {state.buffer}")
                if state.buffer in KAOMOJI_DB:
                    candidates = KAOMOJI_DB[state.buffer][:MAX_CANDIDATES]
                    x, y = pyautogui.position()
                    app.root.after(0, lambda: app.show_popup(candidates, x, y))
                else:
                    app.root.after(0, app.close_popup)
            else:
                app.root.after(0, app.close_popup)
                state.active = False
            return

        elif key == Key.esc:
            print("取消激活 (Esc)")
            app.root.after(0, app.close_popup)
            state.active = False
            state.buffer = ""
            return

    except Exception as e:
        print(f"[监听错误] {e}")

def on_release(key):
    global app
    if app is None:
        return
    try:
        if key == Key.alt_l or key == Key.alt_r or key == Key.alt:
            app.modifiers['alt'] = False
        elif key == Key.ctrl_l or key == Key.ctrl_r:
            app.modifiers['ctrl'] = False
        elif key == Key.shift_l or key == Key.shift_r:
            app.modifiers['shift'] = False
    except Exception as e:
        print(f"on_release 错误: {e}")

def start_keyboard_listener():
    import time
    while True:
        try:
            with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
                listener.join()
        except Exception as e:
            print(f"⚠️ 监听器崩溃: {e}，正在重启...")
            time.sleep(0.5)   # 避免疯狂重启

def quit_app(app, icon=None):
    """退出程序，同时停止托盘图标"""
    if icon:
        icon.stop()
    app.root.quit()
    app.root.destroy()
    # 强制结束所有线程（可选）
    os._exit(0)

def create_tray_icon(app):
    """创建系统托盘图标"""
    global tray_icon
    # 尝试加载 icon.png，失败则生成默认图标
    try:
        image = Image.open("icon.png")
    except FileNotFoundError:
        # 生成一个简单的蓝色方块作为后备图标
        image = Image.new('RGB', (64, 64), color='#D0D0E8')
        from PIL import ImageDraw
        draw = ImageDraw.Draw(image)
        draw.text((10, 10), "🐱", fill="white")

    # 定义右键菜单项
    menu = pystray.Menu(
        pystray.MenuItem("打开设置", lambda: app.root.after(0, app.toggle_settings)),
        pystray.MenuItem("退出", lambda: quit_app(app, tray_icon))
    )

    # 创建图标对象，左键单击也触发打开设置
    tray_icon = pystray.Icon(
        "NyanMoji",          # 内部名称
        image,
        "NyanMoji 正在运行喵~",          # 提示文字（鼠标悬停）
        menu,
        on_click=lambda icon, item: app.root.after(0, app.toggle_settings)   # 左键单击打开设置
    )

    # 在后台线程运行，避免阻塞 Tkinter 主循环
    threading.Thread(target=tray_icon.run, daemon=True).start()
    return tray_icon
# ------------------- 启动入口 -------------------
def main():
    print(r"""
  _   _                   __  __       _ _
 | \ | |                 |  \/  |     (_|_)
 |  \| |_   _  __ _ _ __ | \  / | ___  _ _
 | . ` | | | |/ _` | '_ \  |\/| |/ _ \| | |
 | |\  | |_| | (_| | | | | |  | | (_) | | |
 |_| \_|\__, |\__,_|_| |_|_|  |_|\___/| |_|
         __/ |                        _/ |
        |___/                        |__/
    """)
    print("🐱 NyanMoji 调试版")
    print(f"   当前主题：{config.get('theme', 'dark')}")
    print("   在任意输入框中输入 '/拼音'，候选窗会实时出现。")
    print("   → 按数字键 1-9 直接选择，或方向键+回车确认。")
    print("   → 按 Esc 或输入其他字符取消。")
    print("   按 Alt+N 可打开主页。\n")
    #print("请在终端中观察调试输出，以定位问题。\n")

    global app
    app = NyanMojiApp()
    threading.Thread(target=start_keyboard_listener, daemon=True).start()
    # 启动后自动打开设置窗口（方便新用户配置）
    app.toggle_settings()
    # 创建系统托盘图标
    create_tray_icon(app)
    # 禁用 Ctrl+C 退出（Windows 和 Unix 通用方式）
    if sys.platform == 'win32':
        # Windows: 完全禁用控制台 Ctrl+C 处理
        ctypes.windll.kernel32.SetConsoleCtrlHandler(None, True)
    else:
        # Unix/Linux/macOS: 忽略 SIGINT 信号
        signal.signal(signal.SIGINT, signal.SIG_IGN)
    app.run()

if __name__ == "__main__":
    app = None
    tray_icon = None
    main()