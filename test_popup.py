import customtkinter as ctk
ctk.set_appearance_mode("dark")

root = ctk.CTk()
root.title("测试窗口")
root.geometry("300x200+500+300")
label = ctk.CTkLabel(root, text="如果你看到这个，说明窗口正常")
label.pack(pady=50)
root.mainloop()