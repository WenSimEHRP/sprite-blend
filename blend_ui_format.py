import tkinter as tk
from tkinter import ttk, filedialog
from PIL import Image, ImageTk
from blend_ui_resources import miku_text
import os


# detect device dark mode setting
def is_dark_mode():
    try:
        from winreg import OpenKey, HKEY_CURRENT_USER, QueryValueEx
        key = OpenKey(HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
        value = QueryValueEx(key, "AppsUseLightTheme")
        return not value[0]
    except:
        return False

class UIStyles:
    class ToolTip:
        def __init__(self):
            self._font = ("tahoma", "8", "normal")
            self._light_background = "#ffffe0"
            self._dark_background = "#313143"
            self._light_foreground = "#000000"
            self._dark_foreground = "#ffffff"
            self._light_border = "#000000"
            self._dark_border = "#ffffff"
            self._is_dark_mode = False and is_dark_mode()
            self.style = ttk.Style().configure("Custom.TLabel", background=self.background, foreground=self.foreground, font=self.font)

        @property
        def font(self):
            return self._font

        @property
        def background(self):
            return self._light_background if not self._is_dark_mode else self._dark_background

        @property
        def foreground(self):
            return self._light_foreground if not self._is_dark_mode else self._dark_foreground

        @property
        def border(self):
            return self._light_border if not self._is_dark_mode else self._dark_border

class ToolTip:
    def __init__(self, widget, content, fast=False):
        self.styles = UIStyles.ToolTip()
        self.style = UIStyles.ToolTip().style
        self.widget = widget
        self.content = content
        self.tip_window = None
        self.alpha = 0.0
        self.fast = fast
        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)
        self.widget.bind("<Motion>", self.follow_mouse)

    def show_tip(self, event=None):
        if self.tip_window or not self.content:
            return
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_attributes("-alpha", 0.0)
        tw.wm_attributes("-topmost", True)
        frame = tk.Frame(tw, background=self.styles.background, relief=tk.SOLID, borderwidth=1,
                         highlightcolor=self.styles.border, highlightthickness=0)
        frame.pack(ipadx=1, padx=0, ipady=0, pady=0)

        if isinstance(self.content, str):
            label = tk.Label(frame, text=self.content, justify=tk.LEFT, foreground=self.styles.foreground,
                             background=self.styles.background, font=self.styles.font)
            label.pack(anchor="w")
        else:
            for item in self.content:
                if item is None:
                    continue
                elif isinstance(item, str):
                    label = tk.Label(frame, text=item, justify=tk.LEFT, foreground=self.styles.foreground,
                                     background=self.styles.background, font=self.styles.font)
                    label.pack(anchor=tk.W)
                elif isinstance(item, ImageTk.PhotoImage):
                    label = tk.Label(frame, image=item, background=self.styles.background)
                    label.pack(anchor=tk.W)
                elif isinstance(item, Image.Image):
                    photo = ImageTk.PhotoImage(item)
                    label = tk.Label(frame, image=photo, background=self.styles.background)
                    label.pack(anchor=tk.W)
                    label.image = photo
                elif isinstance(item, tk.Label):
                    config = item.configure()
                    new_label = tk.Label(frame)
                    for key, value in config.items():
                        try:
                            if key not in ["fg", "bg", "bd"]:
                                new_label.config(**{key: value[-1]})
                        except Exception as e:
                            raise ValueError(f"Error in setting label config: '{e}' when loading key: '{key}' with value: '{value}'")
                    # if the label has no foreground, background, or border color, set them to the default
                    new_label.config(foreground=self.styles.foreground)
                    new_label.config(background=self.styles.background)
                    new_label.config(borderwidth=0)
                    if "font" not in config or config["font"][-1] == "":
                        new_label.config(font=self.styles.font)
                    new_label.pack(anchor=tk.W)
                elif isinstance(item, ttk.Label):
                    # check if the label contains nothing, then skip it
                    # this includes the text and the image
                    if item.cget("text") == "" and item.cget("image") == "":
                        continue
                    config = item.configure()
                    new_label = ttk.Label(frame, style="Custom.TLabel")
                    for key, value in config.items():
                        try:
                            if key not in ["foreground", "background", "borderwidth", "class"]:
                                new_label.config(**{key: value[-1]})
                        except Exception as e:
                            raise ValueError(f"Error in setting label config: '{e}' when loading key: '{key}' with value: '{value}'")
                    new_label.config(foreground=self.styles.foreground)
                    new_label.config(background=self.styles.background)
                    new_label.config(borderwidth=0)
                    if "font" not in config or config["font"][-1] == "":
                        new_label.config(font=self.styles.font)
                    new_label.pack(anchor=tk.W)
                else:
                    raise ValueError(f"Unknown type in content: {item}")

        self.follow_mouse(event)
        self.fade_in()

    def fade_in(self):
        if self.tip_window:
            if self.fast: self.tip_window.after(0, self._start_fade_in)
            else: self.tip_window.after(500, self._start_fade_in)

    def _start_fade_in(self):
        if self.tip_window:
            if self.alpha > 1.0 or self.fast:
                self.alpha = 1.0
            self.alpha += 0.15
            self.tip_window.wm_attributes("-alpha", self.alpha)
            if self.alpha < 1.0:
                self.tip_window.after(25, self._start_fade_in)

    def follow_mouse(self, event):
        if self.tip_window:
            x, y = event.x_root + 20, event.y_root + 10
            self.tip_window.wm_geometry(f"+{x}+{y}")

    def hide_tip(self, event=None):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None
            self.alpha = 0.0

class ImagePageImage:
    def __init__(self, image: Image.Image, thumbnail_size=None, thumbnail_scale=None):
        if not isinstance(image, Image.Image):
            raise ValueError("image must be a PIL Image object.")
        if thumbnail_size is None and thumbnail_scale is None:
            thumbnail_size = 300
        if thumbnail_size is not None and thumbnail_scale is not None:
            raise ValueError("Only one of thumbnail_size and thumbnail_scale can be specified.")

        self.thumbnail_size = thumbnail_size
        self.thumbnail_scale = thumbnail_scale
        self.image = image
        self.orig_image = ImageTk.PhotoImage(self.image)
        self._image_size = None
        self._2x_image_2x = None
        self._thumbnail = None
        self._thumbnail_versus_orig_size = None

    @property
    def image_size(self) -> tuple:
        if self._image_size is None:
            self._image_size = (self.image.size[0], self.image.size[1])
        return self._image_size

    @property
    def image_2x(self) -> ImageTk.PhotoImage:
        if self._2x_image_2x is None:
            resized_image = self.image.copy().resize(tuple([x*2 for x in self.image_size]), Image.LANCZOS)
            self._2x_image_2x = ImageTk.PhotoImage(resized_image)
        return self._2x_image_2x

    @property
    def thumbnail_versus_orig_size(self) -> float:
        if self._thumbnail_versus_orig_size is None:
            if self.thumbnail_size is not None:
                self._thumbnail_versus_orig_size = self.thumbnail_size / self.image_size[0] if self.image_size[0] > self.thumbnail_size else 1
            else:
                self._thumbnail_versus_orig_size = self.thumbnail_scale
        return self._thumbnail_versus_orig_size

    @property
    def thumbnail(self) -> ImageTk.PhotoImage:
        if self._thumbnail is None:
            if self.thumbnail_size is not None:
                new_width = min(self.image_size[0], self.thumbnail_size)
                if self.image_size[0] > self.thumbnail_size:
                    new_height = int(self.image_size[1] * self.thumbnail_size / self.image_size[0])
                else:
                    new_height = self.image_size[1]
                resized_image = self.image.copy().resize((new_width, new_height), Image.LANCZOS)
            else:
                new_size = tuple([int(x * self.thumbnail_scale) for x in self.image_size])
                resized_image = self.image.copy().resize(new_size, Image.LANCZOS)
            self._thumbnail = ImageTk.PhotoImage(resized_image)
        return self._thumbnail

class PageLayout:
    def __init__(self, parent, title=None):
        self.title = title if title else "New Page"
        self.frame = ttk.Frame(parent, padding="10", relief="groove")
        self.frame.pack(expand=True, fill='both')
        self.label = tk.Label(self.frame, text=self.title)
        self.label.pack(anchor="w")

class TextboxWithPlaceholder(ttk.Entry):
    def __init__(self, parent, placeholder, width, *args, **kwargs):
        self.placeholder = placeholder
        self.style_name = f"Placeholder.TEntry.{id(self)}"

        # 定义样式
        self.style = ttk.Style()
        self.style.configure(self.style_name, foreground="grey")

        # 复制 TEntry 样式布局
        original_layout = self.style.layout('TEntry')
        self.style.layout(self.style_name, original_layout)

        # 确保在初始化 ttk.Entry 之前设置样式
        kwargs["style"] = self.style_name
        kwargs["width"] = width

        super().__init__(parent, *args, **kwargs)

        self.insert(0, self.placeholder)
        self.bind("<FocusIn>", self._clear_placeholder)
        self.bind("<FocusOut>", self._add_placeholder)

    def _clear_placeholder(self, event):
        if self.get() == self.placeholder:
            self.style.configure(self.style_name, foreground="black")
            self.delete(0, tk.END)

    def _add_placeholder(self, event):
        if not self.get():
            self.style.configure(self.style_name, foreground="grey")
            self.insert(0, self.placeholder)


class MainPage(PageLayout):
    class LoadImage:
        def __init__(self, parent, message):
            self._image = None

            self.image_wrapper = ttk.Frame(parent)
            self.image_wrapper.pack(anchor="w")

            self.image_path_frame = ttk.Frame(self.image_wrapper)
            self.image_path_frame.pack(anchor="w")

            self.file_manager_button = ttk.Button(self.image_path_frame, text="\U0001F4C2", command=self.open_file_manager, width=3)
            self.file_manager_button.pack(side="left")
            ToolTip(self.file_manager_button, "Open file manager")

            self.load_image_button = ttk.Button(self.image_path_frame, text="Load", command=self.load_image, width=5)
            self.load_image_button.pack(side="left")
            ToolTip(self.load_image_button, "Refresh and load image")

            self.image_path_entry = TextboxWithPlaceholder(self.image_path_frame, placeholder=message, width=75)
            self.image_path_entry.pack(side="left")

            self.image_entry_tooltip_label_text = ttk.Label(text="Enter the path of the image you want to blend\nExample: D:\\Data\\Pictures\\Screenshots\\wood.png")
            self.image_entry_tooltip_label = ttk.Label(text="No image loaded")
            ToolTip(self.image_path_entry, (self.image_entry_tooltip_label_text,
                                            self.image_entry_tooltip_label))

        def load_image(self):
            filename = self.image_path_entry.get()
            base_filename = os.path.basename(filename)
            try:
                with Image.open(filename) as img:
                    self.thumb_image = ImagePageImage(img.copy())
                    self.image_entry_tooltip_label.config(image=self.thumb_image.thumbnail)
                    self.image_entry_tooltip_label.image = self.thumb_image  # 防止图像被垃圾回收
                    self.image_entry_tooltip_label_text.config(text=f"Size: {self.thumb_image.image_size} Scale:{100*self.thumb_image.thumbnail_versus_orig_size:.2f}%")
            except FileNotFoundError:
                self.image_entry_tooltip_label.config(text=f"Error: File \"{base_filename}\" not found")
            except Exception as e:
                self.image_entry_tooltip_label.config(text=f"Error when opening file \"{base_filename}\": {type(e).__name__}")

        def open_file_manager(self):
            file_path = filedialog.askopenfilename(filetypes=[("PNG files", "*.png"), ("All files", "*.*")])
            if file_path:
                self.image_path_entry.delete(0, tk.END)
                self.image_path_entry.insert(0, file_path)


    def __init__(self, parent):
        super().__init__(parent, "Image Blender")
        ToolTip(self.label, "This is the main page")

        self.image1 = self.LoadImage(self.frame, "First image to blend...")
        self.LoadImage(self.frame, "Second image to blend...")
        self.LoadImage(self.frame, "Third image to blend...")

        self.blend_button = ttk.Button(self.frame, text="Blend!")
        self.blend_button.pack(anchor="w", pady=10)

class ImagePage(PageLayout):

    def __init__(self, parent):
        super().__init__(parent, "Images")
        ToolTip(self.label, "This is the images page")

        with Image.open("wood.png") as f:
        # with Image.open("D:/Data/Pictures/Screenshots/屏幕截图 2024-03-23 004426.png") as f:
            self.images = ImagePageImage(f.copy())
        self.image_label = ttk.Label(self.frame, image=self.images.image_2x)
        self.image_label.pack(anchor=tk.W)
        ToolTip(self.image_label, (f"Original Size: {self.images.image_size} Scale:{100*self.images.thumbnail_versus_orig_size:.2f}%", self.images.thumbnail))
        self.image_label.image = self.images.image_2x

class AboutPage(PageLayout):
    def __init__(self, parent):
        super().__init__(parent, "About")
        ToolTip(self.label, "About this program")
        self.lookatme = ttk.Label(master=self.frame, text="Look at me!")
        self.mikutext = ttk.Label(text=miku_text, font=("tahoma", "4", "normal"))
        ToolTip(self.lookatme, ("Look who this is!", "Copyright (C) Crypton Future Media, Inc. All rights reserved.", self.mikutext))
        self.lookatme.pack(anchor="w")
        self.about_text = ttk.Label(self.frame, wraplength=500, justify="left",
text=
"""
blend_ui.py is the gui wrapper of blend.py.
blend.py is a simple program that blends two images together, and outputs one image and several sets of recolour indexes.

The MIT License

Copyright (c) 2024 Jeremy Gao

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
""")
        self.about_text.pack(anchor="w")
