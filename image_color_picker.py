"""
图像取色工具 - Image Color Picker Tool

一个基于Python和tkinter的GUI应用程序，用于打开BMP图像文件并提取像素点的颜色信息。

A Python tkinter-based GUI application for opening BMP image files and extracting pixel color information.

Features:
- 支持1280x1024分辨率的BMP图像文件 / Support for 1280x1024 BMP image files
- 图像预览和缩放功能 / Image preview and zoom functionality
- 鼠标点击获取像素颜色 / Mouse click to get pixel color
- 显示RGB和HSV颜色值 / Display RGB and HSV color values
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import colorsys
import os

class ImageColorPicker:
    def __init__(self, root):
        self.root = root
        self.root.title("图像取色工具 - Image Color Picker")
        self.root.geometry("1400x900")
        
        # 变量初始化
        self.image = None
        self.photo = None
        self.zoom_factor = 1.0
        self.canvas_image = None
        
        self.setup_ui()
        
    def setup_ui(self):
        """设置用户界面"""
        # 主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 顶部控制面板
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 文件选择按钮
        ttk.Button(control_frame, text="选择BMP图像", command=self.open_image).pack(side=tk.LEFT, padx=(0, 10))
        
        # 缩放控制
        ttk.Label(control_frame, text="缩放:").pack(side=tk.LEFT, padx=(0, 5))
        self.zoom_var = tk.StringVar(value="100%")
        zoom_combo = ttk.Combobox(control_frame, textvariable=self.zoom_var, values=["25%", "50%", "75%", "100%", "125%", "150%", "200%"], width=8, state="readonly")
        zoom_combo.pack(side=tk.LEFT, padx=(0, 10))
        zoom_combo.bind("<<ComboboxSelected>>", self.on_zoom_change)
        
        # 重置缩放按钮
        ttk.Button(control_frame, text="重置缩放", command=self.reset_zoom).pack(side=tk.LEFT)
        
        # 主内容区域
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # 左侧：图像显示区域
        left_frame = ttk.LabelFrame(content_frame, text="图像预览", padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # 创建画布和滚动条
        canvas_frame = ttk.Frame(left_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(canvas_frame, bg="white", cursor="crosshair")
        
        # 滚动条
        v_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        h_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        
        self.canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # 布局滚动条和画布
        self.canvas.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)
        
        # 绑定鼠标事件
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        
        # 右侧：颜色信息显示区域
        right_frame = ttk.LabelFrame(content_frame, text="颜色信息", padding=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, ipadx=20)
        
        # 当前像素坐标
        ttk.Label(right_frame, text="像素坐标:", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
        self.coord_label = ttk.Label(right_frame, text="X: -, Y: -", font=("Arial", 10))
        self.coord_label.pack(anchor=tk.W, pady=(0, 15))
        
        # RGB值显示
        ttk.Label(right_frame, text="RGB值:", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
        
        rgb_frame = ttk.Frame(right_frame)
        rgb_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(rgb_frame, text="R:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.r_label = ttk.Label(rgb_frame, text="-", font=("Arial", 10))
        self.r_label.grid(row=0, column=1, sticky=tk.W, padx=(0, 15))
        
        ttk.Label(rgb_frame, text="G:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5))
        self.g_label = ttk.Label(rgb_frame, text="-", font=("Arial", 10))
        self.g_label.grid(row=1, column=1, sticky=tk.W, padx=(0, 15))
        
        ttk.Label(rgb_frame, text="B:").grid(row=2, column=0, sticky=tk.W, padx=(0, 5))
        self.b_label = ttk.Label(rgb_frame, text="-", font=("Arial", 10))
        self.b_label.grid(row=2, column=1, sticky=tk.W, padx=(0, 15))
        
        # RGB十六进制值
        ttk.Label(right_frame, text="十六进制:", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(10, 5))
        self.hex_label = ttk.Label(right_frame, text="#------", font=("Arial", 10))
        self.hex_label.pack(anchor=tk.W, pady=(0, 15))
        
        # HSV值显示
        ttk.Label(right_frame, text="HSV值:", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
        
        hsv_frame = ttk.Frame(right_frame)
        hsv_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(hsv_frame, text="H:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.h_label = ttk.Label(hsv_frame, text="-", font=("Arial", 10))
        self.h_label.grid(row=0, column=1, sticky=tk.W)
        
        ttk.Label(hsv_frame, text="S:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5))
        self.s_label = ttk.Label(hsv_frame, text="-", font=("Arial", 10))
        self.s_label.grid(row=1, column=1, sticky=tk.W)
        
        ttk.Label(hsv_frame, text="V:").grid(row=2, column=0, sticky=tk.W, padx=(0, 5))
        self.v_label = ttk.Label(hsv_frame, text="-", font=("Arial", 10))
        self.v_label.grid(row=2, column=1, sticky=tk.W)
        
        # 颜色预览
        ttk.Label(right_frame, text="颜色预览:", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(15, 5))
        self.color_preview = tk.Frame(right_frame, width=100, height=60, bg="white", relief=tk.SUNKEN, bd=2)
        self.color_preview.pack(pady=(0, 15))
        self.color_preview.pack_propagate(False)
        
        # 状态标签
        self.status_label = ttk.Label(right_frame, text="请选择BMP图像文件", foreground="gray")
        self.status_label.pack(anchor=tk.W, pady=(20, 0))
        
    def open_image(self):
        """打开图像文件"""
        file_path = filedialog.askopenfilename(
            title="选择BMP图像文件",
            filetypes=[("BMP files", "*.bmp"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                # 打开并验证图像
                image = Image.open(file_path)
                
                # 检查是否为BMP格式
                if not file_path.lower().endswith('.bmp'):
                    messagebox.showwarning("警告", "建议使用BMP格式的图像文件。")
                
                # 检查分辨率（可选警告）
                width, height = image.size
                if width != 1280 or height != 1024:
                    response = messagebox.askyesno(
                        "分辨率确认", 
                        f"图像分辨率为 {width}x{height}，不是期望的 1280x1024。\n是否继续？"
                    )
                    if not response:
                        return
                
                self.image = image
                self.zoom_factor = 1.0
                self.zoom_var.set("100%")
                self.display_image()
                self.status_label.config(text=f"已加载: {os.path.basename(file_path)} ({width}x{height})")
                
            except Exception as e:
                messagebox.showerror("错误", f"无法打开图像文件:\n{str(e)}")
    
    def display_image(self):
        """显示图像到画布上"""
        if self.image is None:
            return
        
        # 计算缩放后的尺寸
        original_width, original_height = self.image.size
        new_width = int(original_width * self.zoom_factor)
        new_height = int(original_height * self.zoom_factor)
        
        # 缩放图像
        if self.zoom_factor != 1.0:
            resized_image = self.image.resize((new_width, new_height), Image.Resampling.NEAREST)
        else:
            resized_image = self.image
        
        # 转换为tkinter可用的格式
        self.photo = ImageTk.PhotoImage(resized_image)
        
        # 清除画布并显示图像
        self.canvas.delete("all")
        self.canvas_image = self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
        
        # 更新画布滚动区域
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def on_zoom_change(self, event):
        """处理缩放变化"""
        zoom_text = self.zoom_var.get()
        self.zoom_factor = float(zoom_text.rstrip('%')) / 100.0
        self.display_image()
    
    def reset_zoom(self):
        """重置缩放"""
        self.zoom_factor = 1.0
        self.zoom_var.set("100%")
        self.display_image()
    
    def on_canvas_click(self, event):
        """处理画布点击事件"""
        if self.image is None:
            return
        
        # 获取画布上的点击坐标
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        # 转换为原始图像坐标
        original_x = int(canvas_x / self.zoom_factor)
        original_y = int(canvas_y / self.zoom_factor)
        
        # 检查坐标是否在图像范围内
        width, height = self.image.size
        if 0 <= original_x < width and 0 <= original_y < height:
            # 获取像素颜色
            pixel_color = self.image.getpixel((original_x, original_y))
            
            # 处理不同的图像模式
            if self.image.mode == 'RGB':
                r, g, b = pixel_color
            elif self.image.mode == 'RGBA':
                r, g, b, a = pixel_color
            elif self.image.mode == 'L':  # 灰度图像
                r = g = b = pixel_color
            else:
                # 转换到RGB模式
                rgb_image = self.image.convert('RGB')
                r, g, b = rgb_image.getpixel((original_x, original_y))
            
            # 更新显示
            self.update_color_info(original_x, original_y, r, g, b)
    
    def update_color_info(self, x, y, r, g, b):
        """更新颜色信息显示"""
        # 更新坐标
        self.coord_label.config(text=f"X: {x}, Y: {y}")
        
        # 更新RGB值
        self.r_label.config(text=f"{r}")
        self.g_label.config(text=f"{g}")
        self.b_label.config(text=f"{b}")
        
        # 更新十六进制值
        hex_color = f"#{r:02X}{g:02X}{b:02X}"
        self.hex_label.config(text=hex_color)
        
        # 计算HSV值
        h, s, v = colorsys.rgb_to_hsv(r/255.0, g/255.0, b/255.0)
        h_deg = int(h * 360)
        s_percent = int(s * 100)
        v_percent = int(v * 100)
        
        # 更新HSV值
        self.h_label.config(text=f"{h_deg}°")
        self.s_label.config(text=f"{s_percent}%")
        self.v_label.config(text=f"{v_percent}%")
        
        # 更新颜色预览
        self.color_preview.config(bg=hex_color)
        
        # 更新状态
        self.status_label.config(text=f"颜色: RGB({r},{g},{b}) HSV({h_deg}°,{s_percent}%,{v_percent}%)")

def main():
    """主函数"""
    root = tk.Tk()
    app = ImageColorPicker(root)
    root.mainloop()

if __name__ == "__main__":
    main()
