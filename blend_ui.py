import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk  # 导入 PIL 模块
from blend_ui_format import *
import json

class MainWindow:

    def __init__(self, window):
        self.window = window
        self.window.title('Blend UI')
        self.window.geometry('400x300')
        self.window.update_idletasks()
        self.window_height = self.window.winfo_height()
        self.window_width = self.window.winfo_width()

        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(expand=True, fill='both')

        self.main_page = ttk.Frame(self.notebook)
        self.notebook.add(self.main_page, text='Blender')
        MainPage(self.main_page)

        self.image_page = ttk.Frame(self.notebook)
        self.notebook.add(self.image_page, text='Images')
        ImagePage(self.image_page)

        self.about_page = ttk.Frame(self.notebook)
        self.notebook.add(self.about_page, text='About')
        AboutPage(self.about_page)

    def show_message(self):
        messagebox.showinfo('Message', 'Hello, Blend UI!')

if __name__ == '__main__':
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
    except FileNotFoundError:
        messagebox.showerror("Error", "config.json not found, creating new one")
        config = {"theme": "light"}
        with open("config.json", "w") as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        messagebox.showerror("Error", f"Error loading config.json: {e}")
        print(f"Error loading config.json: {e}")
    MainWindow(tk.Tk()).window.mainloop()
