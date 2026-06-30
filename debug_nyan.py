import json
import threading
import customtkinter as ctk
from pynput import keyboard
from pynput.keyboard import Key, Controller
import pyautogui

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# 假数据库
KAOMOJI_DB = {"高兴": ["(＾▽＾)", "(*^▽^*)"]}

state = {"active": False, "buffer": "", "popup": None}
keyboard_ctrl = Controller()

# ---------- 主线程根窗口 ----------
class App:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.withdraw()
        self.pending = None
        print("[App] 根窗口已创建，主循环即将开始...")

    def schedule_popup(self, candidates, x, y):
        print(f"[App] 收到弹窗请求，候选数={len(candidates)}，坐标=({x},{y})")
        self.pending = (candidates, x, y)
        self.root.after(0, self.create_popup)

    def create_popup(self):
        print("[App] 正在主线程中创建弹窗...")
        if self.pending is None:
            return
        candidates, x, y = self.pending
        self.pending = None
        try:
            popup = ctk.CTkToplevel(self.root)
            popup.title("Test")
            popup.geometry(f"300x200+{x}+{y}")
            popup.attributes('-topmost', True)
            label = ctk.CTkLabel(popup, text="如果你看到这个，弹窗创建成功！")
            label.pack(pady=50)
            popup.focus_force()
            print("[App] 弹窗已创建并显示")
            state["popup"] = popup
        except Exception as e:
            print(f"[App] 创建弹窗失败: {e}")

    def run(self):
        self.root.mainloop()

# ---------- 键盘监听 ----------
def on_press(key):
    if hasattr(key, 'char') and key.char is not None:
        state.buffer += key.char.lower()   # 转小写
    if state["popup"] is not None:
        return
    try:
        if hasattr(key, 'char') and key.char == '/':
            state["active"] = True
            state["buffer"] = ""
            print("[监听] 触发 '/'，进入激活状态")
        elif state["active"]:
            if hasattr(key, 'char') and key.char is not None:
                state["buffer"] += key.char
                print(f"[监听] 当前 buffer: '{state['buffer']}'")
            elif key == Key.space or key == Key.enter:
                print(f"[监听] 收到结束键，buffer='{state['buffer']}'")
                if state["buffer"] in KAOMOJI_DB:
                    candidates = KAOMOJI_DB[state["buffer"]]
                    x, y = pyautogui.position()
                    print(f"[监听] 匹配成功，请求弹窗...")
                    app.schedule_popup(candidates, x, y)
                else:
                    print("[监听] 无匹配关键词")
                    state["active"] = False
            elif key == Key.esc:
                state["active"] = False
                print("[监听] ESC 取消激活")
    except Exception as e:
        print(f"[监听] 异常: {e}")

def start_listener():
    print("[监听] 后台监听线程已启动")
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()

# ---------- 启动 ----------
if __name__ == "__main__":
    print("🐱 NyanMoji 调试模式")
    app = App()
    threading.Thread(target=start_listener, daemon=True).start()
    app.run()