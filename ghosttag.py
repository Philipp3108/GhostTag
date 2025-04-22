from collections import Counter
from PIL import Image, ImageTk
import math, os
import numpy as np
from numpy import random
import tkinter as tk
from tkinter import filedialog
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinterdnd2 import DND_FILES, TkinterDnD

def watermarkImage(image, pattern):
    if image.mode != 'RGB':
        image = image.convert('RGB')
    pixelMap = image.load()
    img = Image.new(image.mode, image.size)
    pixelsNew = img.load()
    for i in range(img.size[0]):
        for j in range(img.size[1]):
            if pattern[j % len(pattern)][i % len(pattern[0])] == 0:
                pixelsNew[i, j] = (math.floor(pixelMap[i, j][0] / 2) * 2,
                                   math.floor(pixelMap[i, j][1] / 2) * 2,
                                   math.floor(pixelMap[i, j][2] / 2) * 2)
            else:
                pixelsNew[i, j] = (math.floor(pixelMap[i, j][0] / 2) * 2 + 1,
                                   math.floor(pixelMap[i, j][1] / 2) * 2 + 1,
                                   math.floor(pixelMap[i, j][2] / 2) * 2 + 1)
    return img

def showWatermark(pattern, size):
    img = Image.new(mode="RGB", size=(size, size))
    pixelsNew = img.load()
    for i in range(img.size[0]):
        for j in range(img.size[1]):
            pixelsNew[i, j] = (255, 255, 255) if pattern[j % len(pattern)][i % len(pattern[0])] == 0 else (0, 0, 0)
    img.show()

def checkPattern(image, pattern):
    pixelMap = image.load()
    checkCount = 0
    for i in range(image.size[0]):
        for j in range(image.size[1]):
            if pattern[j % len(pattern)][i % len(pattern[0])] == pixelMap[i, j][0] % 2 == pixelMap[i, j][1] % 2 == pixelMap[i, j][2] % 2:
                checkCount += 1
    return checkCount >= image.size[0] * image.size[1] * 0.9

def getPattern(img, size, strength):
    width, height = img.size
    pixels = img.load()
    width_step = max(1, int(width / (10 / strength)))
    height_step = max(1, int(height / (10 / strength)))

    patternarr = []
    for y in range(0, height - size + 1, height_step):
        for x in range(0, width - size + 1, width_step):
            block = pixels[y:y+size, x:x+size, 0] % 2
            pattern_tuple = tuple(map(tuple, block))
            patternarr.append(pattern_tuple)

    c = Counter(patternarr)
    most_common_pattern = c.most_common(1)[0][0]
    most_common_pattern_array = np.array(most_common_pattern)

    if checkPattern(img, most_common_pattern_array):
        return most_common_pattern_array
    else:
        return 0

def getTextFromImage(img, strength):
    width, height = img.size
    pixels = img.load()
    block_width = 8
    max_chars = 100
    binary_blocks = []
    width_step = max(1, int(width / (10 / strength)))
    height_step = max(1, int(height / (10 / strength)))

    for x_offset in range(0, width - block_width + 1, width_step):
        for y_offset in range(0, height - max_chars + 1, height_step):
            bits = []
            for i in range(max_chars):
                for j in range(block_width):
                    pixel = pixels[x_offset + j, y_offset + i]
                    bits.append(pixel[0] % 2)
            block_tuple = tuple(bits)
            binary_blocks.append(block_tuple)

    c = Counter(binary_blocks)
    most_common_bits = c.most_common(1)[0][0]

    binary = ''.join(str(bit) for bit in most_common_bits)
    text = ""
    for i in range(0, len(binary), 8):
        byte = binary[i:i+8]
        if len(byte) < 8:
            break
        char = chr(int(byte, 2))
        if ord(char) < 9 or ord(char) > 126:
            print(f"Invalid character detected: {char} ({ord(char)}) – aborting")
            break
        text += char
        if text.endswith("|||"):
            text = text[:-3]
            break

    print("Extracted text (raw):", repr(text))
    return text

def textToBinary(text):
    return ''.join(format(ord(x), '08b') for x in text)

def binaryToPattern(binary):
    array = list(binary)
    pattern = np.array(array, dtype=int).reshape(-1, 8)
    return pattern

def textToImage(image, text):
    text += "|||"
    binary = textToBinary(text)
    pattern = binaryToPattern(binary)
    return watermarkImage(image, pattern)

def saveImage(image, filename):
    image.save(filename + ".png")

def showImage(image):
    image.show()

class WatermarkApp:
    def __init__(self, root):
        self.root = root
        self.root.title("GhostTag")
        try:
            icon = tk.PhotoImage(file="icon.png")
            self.root.iconphoto(True, icon)
        except:
            pass

        self.root.geometry("700x700")
        self.style = style

        self.title_label = ttk.Label(root, text="🖼️ Watermark Tool", font=("Helvetica", 22, "bold"))
        self.title_label.pack(pady=20)

        self.select_btn = ttk.Button(root, text="📁 Select File", bootstyle=PRIMARY, command=self.select_file)
        self.select_btn.pack(pady=10)

        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind('<<Drop>>', self.on_drop)

        self.file_label = ttk.Label(root, text="No file selected", wraplength=600)
        self.file_label.pack(pady=5)

        self.image_label = ttk.Label(root)
        self.image_label.pack(pady=10)

        self.text_entry = ttk.Entry(root, width=50)
        self.text_entry.pack(pady=10)
        self.text_entry.insert(0, "Enter your text here...")
        self.text_entry.bind("<FocusIn>", self.clear_placeholder)

        self.button_frame = ttk.Frame(root)
        self.button_frame.pack(pady=10)

        self.embed_btn = ttk.Button(self.button_frame, text="💧 Embed Watermark", bootstyle=SUCCESS, command=self.embed_text)
        self.embed_btn.grid(row=0, column=0, padx=10)

        self.extract_btn = ttk.Button(self.button_frame, text="🔍 Extract Watermark", bootstyle=INFO, command=self.extract_text)
        self.extract_btn.grid(row=0, column=1, padx=10)

        self.save_btn = ttk.Button(self.button_frame, text="💾 Save Image", bootstyle=SECONDARY, command=self.save_image)
        self.save_btn.grid(row=0, column=2, padx=10)

        self.status_label = ttk.Label(root, text="", font=("Helvetica", 10, "italic"))
        self.status_label.pack(pady=10)

        self.dark_switch = ttk.Checkbutton(root, text="🌗 Dark Theme", command=self.toggle_theme, bootstyle="round-toggle")
        self.dark_switch.pack(pady=10)

        self.original_image = None
        self.processed_image = None
        self.current_theme = "flatly"

    def select_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp")])
        if file_path:
            self.file_label.config(text=file_path)
            self.original_image = Image.open(file_path)
            preview = self.original_image.copy()
            preview.thumbnail((300, 300))
            self.tk_image = ImageTk.PhotoImage(preview)
            self.image_label.config(image=self.tk_image)
            self.status_label.config(text="Image loaded successfully.")
        else:
            self.file_label.config(text="No file selected")

    def embed_text(self):
        if self.original_image:
            text = self.text_entry.get()
            if text:
                self.processed_image = textToImage(self.original_image.copy(), text)
                preview = self.processed_image.copy()
                preview.thumbnail((300, 300))
                self.tk_image = ImageTk.PhotoImage(preview)
                self.image_label.config(image=self.tk_image)
                self.status_label.config(text="Watermark embedded.")
            else:
                self.status_label.config(text="Please enter text first.")
        else:
            self.status_label.config(text="Please select an image first.")

    def extract_text(self):
        if self.original_image:
            extracted = getTextFromImage(self.original_image, strength=0.1)
            self.status_label.config(text=f"Extracted text: {extracted}")
        else:
            self.status_label.config(text="Please select an image first.")

    def save_image(self):
        if self.processed_image:
            file_path = filedialog.asksaveasfilename(defaultextension=".png",
                                                     filetypes=[("PNG files", "*.png")])
            if file_path:
                saveImage(self.processed_image, os.path.splitext(file_path)[0])
                self.status_label.config(text="Image saved successfully.")
        else:
            self.status_label.config(text="No processed image to save.")

    def toggle_theme(self):
        self.current_theme = "darkly" if self.current_theme == "flatly" else "flatly"
        self.style.theme_use(self.current_theme)

    def clear_placeholder(self, event):
        if self.text_entry.get() == "Enter your text here...":
            self.text_entry.delete(0, tk.END)

    def on_drop(self, event):
        file_path = event.data.strip("{}")
        if os.path.isfile(file_path):
            self.file_label.config(text=file_path)
            self.original_image = Image.open(file_path)
            preview = self.original_image.copy()
            preview.thumbnail((300, 300))
            self.tk_image = ImageTk.PhotoImage(preview)
            self.image_label.config(image=self.tk_image)
            self.status_label.config(text="Image loaded via drag & drop.")
        else:
            self.status_label.config(text="Invalid file dropped.")

# Start the app
if __name__ == "__main__":
    root = TkinterDnD.Tk()
    style = ttk.Style("flatly")
    app = WatermarkApp(root)
    root.mainloop()
