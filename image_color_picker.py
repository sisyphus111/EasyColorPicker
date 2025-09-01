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
from PIL import Image, ImageTk, ImageGrab
import colorsys
import os
import json
import csv
import xml.etree.ElementTree as ET
from datetime import datetime
import sys
import platform
import threading
import time

class ImageColorPicker:
    def __init__(self, root):
        self.root = root
        self.root.title("图像取色工具 - Image Color Picker")
        
        # DPI感知和缩放配置
        self.setup_dpi_awareness()
        
        # 计算界面缩放因子
        self.ui_scale = self.get_ui_scale_factor()
        
        # 设置窗口大小（根据缩放调整）
        window_width = int(1400 * self.ui_scale)
        window_height = int(900 * self.ui_scale)
        self.root.geometry(f"{window_width}x{window_height}")
        
        # 设置最小窗口大小
        min_width = int(1000 * self.ui_scale)
        min_height = int(700 * self.ui_scale)
        self.root.minsize(min_width, min_height)
        
        # 变量初始化
        self.image = None
        self.photo = None
        self.zoom_factor = 1.0
        self.canvas_image = None
        
        # 颜色记录列表
        self.color_records = []
        
        # 悬浮窗相关变量
        self.floating_window = None
        self.is_floating_mode = False
        self.screen_capture = None
        self.floating_timer = None
        
        # 配置样式
        self.setup_styles()
        
        self.setup_ui()
    
    def setup_dpi_awareness(self):
        """设置DPI感知"""
        try:
            if platform.system() == "Windows":
                # Windows DPI感知
                import ctypes
                from ctypes import wintypes
                
                # 设置DPI感知
                try:
                    ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
                except:
                    try:
                        ctypes.windll.user32.SetProcessDPIAware()  # fallback
                    except:
                        pass
                        
                # 告诉tkinter使用系统DPI
                self.root.tk.call('tk', 'scaling', self.get_system_dpi_scale())
        except:
            pass
    
    def get_system_dpi_scale(self):
        """获取系统DPI缩放因子"""
        try:
            if platform.system() == "Windows":
                import ctypes
                # 获取DPI
                dpi = ctypes.windll.user32.GetDpiForSystem()
                return dpi / 96.0  # 96 DPI是标准DPI
            else:
                # 对于非Windows系统，返回默认值
                return 1.0
        except:
            return 1.0
    
    def get_ui_scale_factor(self):
        """计算UI缩放因子"""
        try:
            # 获取屏幕DPI
            dpi = self.root.winfo_fpixels('1i')
            # 标准DPI是72
            base_dpi = 72.0
            scale = dpi / base_dpi
            
            # 限制缩放范围
            scale = max(0.8, min(scale, 2.5))
            
            return scale
        except:
            return 1.0
    
    def setup_styles(self):
        """设置样式"""
        style = ttk.Style()
        
        # 获取基础字体大小
        base_font_size = int(9 * self.ui_scale)
        title_font_size = int(12 * self.ui_scale)
        small_font_size = int(8 * self.ui_scale)
        
        # 确保字体大小不小于最小值
        base_font_size = max(base_font_size, 8)
        title_font_size = max(title_font_size, 10)
        small_font_size = max(small_font_size, 7)
        
        # 配置字体
        self.fonts = {
            'default': ('Segoe UI', base_font_size),
            'title': ('Segoe UI', title_font_size, 'bold'),
            'small': ('Segoe UI', small_font_size),
            'button': ('Segoe UI', base_font_size),
            'label': ('Segoe UI', base_font_size)
        }
        
        # 应用样式
        style.configure('Title.TLabel', font=self.fonts['title'])
        style.configure('Small.TLabel', font=self.fonts['small'])
        style.configure('Info.TLabel', font=self.fonts['default'])
        
        # 按钮样式
        button_padding = (int(8 * self.ui_scale), int(4 * self.ui_scale))
        style.configure('Custom.TButton', font=self.fonts['button'], padding=button_padding)
        
    def setup_ui(self):
        """设置用户界面"""
        # 主框架
        padding = int(10 * self.ui_scale)
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=padding, pady=padding)
        
        # 顶部控制面板
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(0, padding))
        
        # 文件选择按钮
        btn_padding = int(10 * self.ui_scale)
        open_btn = ttk.Button(control_frame, text="选择图像文件", command=self.open_image, style='Custom.TButton')
        open_btn.pack(side=tk.LEFT, padx=(0, btn_padding))
        
        # 缩放控制
        zoom_label = ttk.Label(control_frame, text="缩放:", font=self.fonts['label'])
        zoom_label.pack(side=tk.LEFT, padx=(0, int(5 * self.ui_scale)))
        
        self.zoom_var = tk.StringVar(value="100%")
        combo_width = max(8, int(8 * self.ui_scale))
        zoom_combo = ttk.Combobox(control_frame, textvariable=self.zoom_var, 
                                 values=["25%", "50%", "75%", "100%", "125%", "150%", "200%", "300%", "400%"], 
                                 width=combo_width, state="readonly", font=self.fonts['default'])
        zoom_combo.pack(side=tk.LEFT, padx=(0, btn_padding))
        zoom_combo.bind("<<ComboboxSelected>>", self.on_zoom_change)
        
        # 重置缩放按钮
        reset_btn = ttk.Button(control_frame, text="重置缩放", command=self.reset_zoom, style='Custom.TButton')
        reset_btn.pack(side=tk.LEFT)
        
        # 添加分隔符
        separator_padding = btn_padding
        separator = ttk.Separator(control_frame, orient=tk.VERTICAL)
        separator.pack(side=tk.LEFT, fill=tk.Y, padx=separator_padding)
        
        # 颜色记录管理按钮
        clear_btn = ttk.Button(control_frame, text="清空记录", command=self.clear_records, style='Custom.TButton')
        clear_btn.pack(side=tk.LEFT, padx=(0, int(5 * self.ui_scale)))
        
        export_btn = ttk.Button(control_frame, text="导出记录", command=self.export_records, style='Custom.TButton')
        export_btn.pack(side=tk.LEFT)
        
        # 添加另一个分隔符
        separator2 = ttk.Separator(control_frame, orient=tk.VERTICAL)
        separator2.pack(side=tk.LEFT, fill=tk.Y, padx=separator_padding)
        
        # 悬浮窗模式按钮
        self.floating_btn = ttk.Button(control_frame, text="启动悬浮窗", command=self.toggle_floating_mode, style='Custom.TButton')
        self.floating_btn.pack(side=tk.LEFT)
        
        # 主内容区域
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # 左侧：图像显示区域
        left_padding = int(10 * self.ui_scale)
        left_frame = ttk.LabelFrame(content_frame, text="图像预览", padding=left_padding)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, padding))
        
        # 创建画布和滚动条
        canvas_frame = ttk.Frame(left_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(canvas_frame, bg="white", cursor="crosshair")
        
        # 滚动条（根据缩放调整大小）
        scrollbar_width = max(16, int(16 * self.ui_scale))
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
        right_width = max(200, int(220 * self.ui_scale))
        right_frame = ttk.LabelFrame(content_frame, text="颜色信息", padding=left_padding)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, ipadx=int(20 * self.ui_scale))
        right_frame.configure(width=right_width)
        
        # 当前像素坐标
        coord_title = ttk.Label(right_frame, text="像素坐标:", font=self.fonts['title'])
        coord_title.pack(anchor=tk.W, pady=(0, int(5 * self.ui_scale)))
        
        self.coord_label = ttk.Label(right_frame, text="X: -, Y: -", font=self.fonts['default'])
        self.coord_label.pack(anchor=tk.W, pady=(0, int(15 * self.ui_scale)))
        
        # RGB值显示
        rgb_title = ttk.Label(right_frame, text="RGB值:", font=self.fonts['title'])
        rgb_title.pack(anchor=tk.W, pady=(0, int(5 * self.ui_scale)))
        
        rgb_frame = ttk.Frame(right_frame)
        rgb_frame.pack(fill=tk.X, pady=(0, int(10 * self.ui_scale)))
        
        # RGB标签布局
        label_font = self.fonts['default']
        ttk.Label(rgb_frame, text="R:", font=label_font).grid(row=0, column=0, sticky=tk.W, padx=(0, int(5 * self.ui_scale)))
        self.r_label = ttk.Label(rgb_frame, text="-", font=label_font)
        self.r_label.grid(row=0, column=1, sticky=tk.W, padx=(0, int(15 * self.ui_scale)))
        
        ttk.Label(rgb_frame, text="G:", font=label_font).grid(row=1, column=0, sticky=tk.W, padx=(0, int(5 * self.ui_scale)))
        self.g_label = ttk.Label(rgb_frame, text="-", font=label_font)
        self.g_label.grid(row=1, column=1, sticky=tk.W, padx=(0, int(15 * self.ui_scale)))
        
        ttk.Label(rgb_frame, text="B:", font=label_font).grid(row=2, column=0, sticky=tk.W, padx=(0, int(5 * self.ui_scale)))
        self.b_label = ttk.Label(rgb_frame, text="-", font=label_font)
        self.b_label.grid(row=2, column=1, sticky=tk.W, padx=(0, int(15 * self.ui_scale)))
        
        # RGB十六进制值
        hex_title = ttk.Label(right_frame, text="十六进制:", font=self.fonts['title'])
        hex_title.pack(anchor=tk.W, pady=(int(10 * self.ui_scale), int(5 * self.ui_scale)))
        
        self.hex_label = ttk.Label(right_frame, text="#------", font=self.fonts['default'])
        self.hex_label.pack(anchor=tk.W, pady=(0, int(15 * self.ui_scale)))
        
        # HSV值显示
        hsv_title = ttk.Label(right_frame, text="HSV值:", font=self.fonts['title'])
        hsv_title.pack(anchor=tk.W, pady=(0, int(5 * self.ui_scale)))
        
        hsv_frame = ttk.Frame(right_frame)
        hsv_frame.pack(fill=tk.X, pady=(0, int(10 * self.ui_scale)))
        
        ttk.Label(hsv_frame, text="H:", font=label_font).grid(row=0, column=0, sticky=tk.W, padx=(0, int(5 * self.ui_scale)))
        self.h_label = ttk.Label(hsv_frame, text="-", font=label_font)
        self.h_label.grid(row=0, column=1, sticky=tk.W)
        
        ttk.Label(hsv_frame, text="S:", font=label_font).grid(row=1, column=0, sticky=tk.W, padx=(0, int(5 * self.ui_scale)))
        self.s_label = ttk.Label(hsv_frame, text="-", font=label_font)
        self.s_label.grid(row=1, column=1, sticky=tk.W)
        
        ttk.Label(hsv_frame, text="V:", font=label_font).grid(row=2, column=0, sticky=tk.W, padx=(0, int(5 * self.ui_scale)))
        self.v_label = ttk.Label(hsv_frame, text="-", font=label_font)
        self.v_label.grid(row=2, column=1, sticky=tk.W)
        
        # 颜色预览
        preview_title = ttk.Label(right_frame, text="颜色预览:", font=self.fonts['title'])
        preview_title.pack(anchor=tk.W, pady=(int(15 * self.ui_scale), int(5 * self.ui_scale)))
        
        preview_width = int(100 * self.ui_scale)
        preview_height = int(60 * self.ui_scale)
        self.color_preview = tk.Frame(right_frame, width=preview_width, height=preview_height, 
                                     bg="white", relief=tk.SUNKEN, bd=2)
        self.color_preview.pack(pady=(0, int(15 * self.ui_scale)))
        self.color_preview.pack_propagate(False)
        
        # 状态标签
        self.status_label = ttk.Label(right_frame, text="请选择图像文件", 
                                     foreground="gray", font=self.fonts['small'])
        self.status_label.pack(anchor=tk.W, pady=(int(20 * self.ui_scale), 0))
        
        # 颜色记录计数
        self.record_count_label = ttk.Label(right_frame, text="已记录颜色: 0", 
                                           foreground="blue", font=self.fonts['small'])
        self.record_count_label.pack(anchor=tk.W, pady=(int(5 * self.ui_scale), 0))
        
    def open_image(self):
        """打开图像文件"""
        file_path = filedialog.askopenfilename(
            title="选择图像文件",
            filetypes=[
                ("所有支持的图像", "*.bmp;*.jpg;*.jpeg;*.png;*.gif;*.tiff;*.tif;*.webp;*.ico"),
                ("BMP files", "*.bmp"),
                ("JPEG files", "*.jpg;*.jpeg"),
                ("PNG files", "*.png"),
                ("GIF files", "*.gif"),
                ("TIFF files", "*.tiff;*.tif"),
                ("WebP files", "*.webp"),
                ("Icon files", "*.ico"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            try:
                # 打开并验证图像
                image = Image.open(file_path)
                
                # 检查图像格式并给出提示
                format_name = image.format or "Unknown"
                self.show_format_info(file_path, format_name)
                
                # 获取图像尺寸
                width, height = image.size
                
                # 检查图像大小，如果太大则询问是否需要预处理
                max_display_size = 4096  # 最大显示尺寸
                if width > max_display_size or height > max_display_size:
                    response = messagebox.askyesno(
                        "大图像处理", 
                        f"图像尺寸较大 ({width}x{height})，这可能影响性能。\n"
                        f"建议的最大显示尺寸为 {max_display_size}x{max_display_size}。\n\n"
                        "是否要创建预览版本以提高性能？\n"
                        "（原始图像的取色精度不会受影响）"
                    )
                    if response:
                        # 创建缩放版本用于显示
                        display_image = self.create_display_version(image, max_display_size)
                        self.image = image  # 保存原始图像用于精确取色
                        self.display_image_obj = display_image  # 用于显示的图像
                    else:
                        self.image = image
                        self.display_image_obj = image
                else:
                    self.image = image
                    self.display_image_obj = image
                
                # 转换为RGB模式以确保兼容性
                if self.image.mode not in ('RGB', 'RGBA'):
                    try:
                        self.image = self.image.convert('RGB')
                        if hasattr(self, 'display_image_obj') and self.display_image_obj != self.image:
                            self.display_image_obj = self.display_image_obj.convert('RGB')
                    except Exception as e:
                        messagebox.showwarning("转换警告", f"图像模式转换时出现问题: {str(e)}")
                
                self.current_image_file = os.path.basename(file_path)
                self.zoom_factor = 1.0
                self.zoom_var.set("100%")
                self.display_image()
                
                # 更新状态信息
                size_info = f"{width}x{height}"
                if hasattr(self, 'display_image_obj') and self.display_image_obj != self.image:
                    display_width, display_height = self.display_image_obj.size
                    size_info += f" (显示: {display_width}x{display_height})"
                
                status_text = f"已加载: {os.path.basename(file_path)} ({size_info}) - {format_name}格式"
                self.status_label.config(text=status_text)
                
            except Exception as e:
                messagebox.showerror("错误", f"无法打开图像文件:\n{str(e)}\n\n支持的格式: BMP, JPEG, PNG, GIF, TIFF, WebP, ICO")
    
    def create_display_version(self, image, max_size):
        """创建用于显示的缩放版本"""
        width, height = image.size
        
        # 计算缩放比例
        scale = min(max_size / width, max_size / height)
        
        if scale < 1.0:
            new_width = int(width * scale)
            new_height = int(height * scale)
            
            # 使用高质量的缩放算法
            display_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            return display_image
        
        return image
    
    def show_format_info(self, file_path, format_name):
        """显示图像格式信息"""
        format_tips = {
            'BMP': '位图格式，无压缩，适合精确取色',
            'JPEG': 'JPEG格式，有损压缩，颜色可能有轻微变化',
            'PNG': 'PNG格式，无损压缩，支持透明度',
            'GIF': 'GIF格式，调色板模式，颜色数量有限',
            'TIFF': 'TIFF格式，高质量，支持多种色彩模式',
            'WEBP': 'WebP格式，现代压缩格式',
            'ICO': '图标格式，通常尺寸较小'
        }
        
        tip = format_tips.get(format_name, '未知格式')
        
        # 如果不是BMP格式，显示提示信息
        if format_name != 'BMP':
            messagebox.showinfo(
                "格式信息", 
                f"检测到 {format_name} 格式图像\n\n"
                f"说明: {tip}\n\n"
                "程序已自动处理格式兼容性。"
            )
    
    def display_image(self):
        """显示图像到画布上"""
        if not hasattr(self, 'display_image_obj') or self.display_image_obj is None:
            return
        
        # 使用显示图像对象进行显示
        display_img = self.display_image_obj
        
        # 计算缩放后的尺寸
        original_width, original_height = display_img.size
        new_width = int(original_width * self.zoom_factor)
        new_height = int(original_height * self.zoom_factor)
        
        # 选择合适的重采样方法
        if self.zoom_factor > 1.0:
            # 放大时使用NEAREST保持像素锐利
            resample_method = Image.Resampling.NEAREST
        elif self.zoom_factor < 0.5:
            # 大幅缩小时使用LANCZOS获得更好质量
            resample_method = Image.Resampling.LANCZOS
        else:
            # 中等缩放使用BILINEAR平衡质量和性能
            resample_method = Image.Resampling.BILINEAR
        
        # 缩放图像
        if self.zoom_factor != 1.0:
            resized_image = display_img.resize((new_width, new_height), resample_method)
        else:
            resized_image = display_img
        
        # 转换为tkinter可用的格式
        self.photo = ImageTk.PhotoImage(resized_image)
        
        # 清除画布并显示图像
        self.canvas.delete("all")
        self.canvas_image = self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
        
        # 更新画布滚动区域
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        
        # 更新画布的滚动增量（根据缩放调整）
        scroll_increment = max(1, int(20 * self.zoom_factor))
        self.canvas.configure(xscrollincrement=scroll_increment, yscrollincrement=scroll_increment)
    
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
        
        # 如果使用了显示版本的图像，需要转换坐标
        if hasattr(self, 'display_image_obj') and self.display_image_obj != self.image:
            # 计算从显示图像到原始图像的坐标映射
            display_width, display_height = self.display_image_obj.size
            original_width, original_height = self.image.size
            
            # 考虑缩放因子
            display_x = canvas_x / self.zoom_factor
            display_y = canvas_y / self.zoom_factor
            
            # 转换到原始图像坐标
            scale_x = original_width / display_width
            scale_y = original_height / display_height
            
            original_x = int(display_x * scale_x)
            original_y = int(display_y * scale_y)
        else:
            # 直接转换为原始图像坐标
            original_x = int(canvas_x / self.zoom_factor)
            original_y = int(canvas_y / self.zoom_factor)
        
        # 检查坐标是否在原始图像范围内
        width, height = self.image.size
        if 0 <= original_x < width and 0 <= original_y < height:
            # 从原始图像获取像素颜色
            pixel_color = self.image.getpixel((original_x, original_y))
            
            # 处理不同的图像模式
            if self.image.mode == 'RGB':
                r, g, b = pixel_color
            elif self.image.mode == 'RGBA':
                r, g, b, a = pixel_color
                # 处理透明度，将其与白色背景混合
                alpha = a / 255.0
                r = int(r * alpha + 255 * (1 - alpha))
                g = int(g * alpha + 255 * (1 - alpha))
                b = int(b * alpha + 255 * (1 - alpha))
            elif self.image.mode == 'L':  # 灰度图像
                r = g = b = pixel_color
            elif self.image.mode == 'P':  # 调色板模式（如GIF）
                # 转换为RGB模式获取颜色
                rgb_image = self.image.convert('RGB')
                r, g, b = rgb_image.getpixel((original_x, original_y))
            else:
                # 其他模式，尝试转换到RGB
                try:
                    rgb_image = self.image.convert('RGB')
                    r, g, b = rgb_image.getpixel((original_x, original_y))
                except Exception as e:
                    messagebox.showerror("错误", f"无法获取该位置的颜色: {str(e)}")
                    return
            
            # 更新显示（使用原始坐标）
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
        
        # 添加到颜色记录
        self.add_color_record(x, y, r, g, b, h_deg, s_percent, v_percent, hex_color)
    
    def add_color_record(self, x, y, r, g, b, h, s, v, hex_color):
        """添加颜色记录"""
        record = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'sequence': len(self.color_records) + 1,
            'position': {'x': x, 'y': y},
            'rgb': {'r': r, 'g': g, 'b': b},
            'hsv': {'h': h, 's': s, 'v': v},
            'hex': hex_color,
            'image_file': getattr(self, 'current_image_file', 'Unknown')
        }
        
        self.color_records.append(record)
        self.update_record_count()
    
    def update_record_count(self):
        """更新记录计数显示"""
        count = len(self.color_records)
        self.record_count_label.config(text=f"已记录颜色: {count}")
    
    def clear_records(self):
        """清空颜色记录"""
        if self.color_records:
            response = messagebox.askyesno("确认", "确定要清空所有颜色记录吗？")
            if response:
                self.color_records.clear()
                self.update_record_count()
                messagebox.showinfo("提示", "颜色记录已清空")
        else:
            messagebox.showinfo("提示", "没有颜色记录需要清空")
    
    def export_records(self):
        """导出颜色记录"""
        if not self.color_records:
            messagebox.showwarning("警告", "没有颜色记录可以导出")
            return
        
        # 创建导出选项窗口
        export_window = tk.Toplevel(self.root)
        export_window.title("导出颜色记录")
        
        # 根据UI缩放调整窗口大小
        window_width = int(450 * self.ui_scale)
        window_height = int(400 * self.ui_scale)
        export_window.geometry(f"{window_width}x{window_height}")
        export_window.resizable(False, False)
        export_window.transient(self.root)
        export_window.grab_set()
        
        # 居中显示
        offset_x = int(100 * self.ui_scale)
        offset_y = int(100 * self.ui_scale)
        export_window.geometry("+%d+%d" % (
            self.root.winfo_rootx() + offset_x,
            self.root.winfo_rooty() + offset_y
        ))
        
        # 主框架
        padding = int(15 * self.ui_scale)
        main_frame = ttk.Frame(export_window, padding=padding)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(main_frame, text="选择导出格式", font=self.fonts['title'])
        title_label.pack(pady=(0, int(20 * self.ui_scale)))
        
        # 格式选择框架
        format_padding = int(10 * self.ui_scale)
        format_frame = ttk.LabelFrame(main_frame, text="文件格式", padding=format_padding)
        format_frame.pack(fill=tk.BOTH, expand=True, pady=(0, int(20 * self.ui_scale)))
        
        # 格式选择
        format_var = tk.StringVar(value="json")
        
        formats = [
            ("JSON格式", "json", "适合程序读取，包含完整信息"),
            ("CSV格式", "csv", "适合Excel打开，表格形式"),
            ("XML格式", "xml", "结构化标记语言格式"),
            ("文本格式", "txt", "简单的文本列表格式")
        ]
        
        option_spacing = int(3 * self.ui_scale)
        desc_padding = int(20 * self.ui_scale)
        
        for name, value, desc in formats:
            option_frame = ttk.Frame(format_frame)
            option_frame.pack(fill=tk.X, pady=option_spacing)
            
            radio_btn = ttk.Radiobutton(option_frame, text=name, variable=format_var, 
                                       value=value, style='Custom.TRadiobutton')
            radio_btn.pack(anchor=tk.W)
            
            desc_label = ttk.Label(option_frame, text=desc, font=self.fonts['small'], foreground="gray")
            desc_label.pack(anchor=tk.W, padx=(desc_padding, 0))
        
        # 信息显示
        info_text = f"当前共有 {len(self.color_records)} 条颜色记录"
        info_label = ttk.Label(main_frame, text=info_text, foreground="blue", font=self.fonts['default'])
        info_label.pack(pady=(0, int(20 * self.ui_scale)))
        
        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        def do_export():
            format_type = format_var.get()
            export_window.destroy()
            self.save_records(format_type)
        
        def do_cancel():
            export_window.destroy()
        
        # 按钮（注意顺序：取消在左，导出在右）
        cancel_btn = ttk.Button(button_frame, text="取消", command=do_cancel, style='Custom.TButton')
        cancel_btn.pack(side=tk.LEFT)
        
        export_btn = ttk.Button(button_frame, text="导出", command=do_export, style='Custom.TButton')
        export_btn.pack(side=tk.RIGHT)
        
        # 设置默认焦点和回车键绑定
        export_btn.focus_set()
        export_window.bind('<Return>', lambda e: do_export())
        export_window.bind('<Escape>', lambda e: do_cancel())
    
    def save_records(self, format_type):
        """保存颜色记录到文件"""
        # 文件类型映射
        file_types = {
            'json': [("JSON files", "*.json"), ("All files", "*.*")],
            'csv': [("CSV files", "*.csv"), ("All files", "*.*")],
            'xml': [("XML files", "*.xml"), ("All files", "*.*")],
            'txt': [("Text files", "*.txt"), ("All files", "*.*")]
        }
        
        # 默认文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        default_name = f"color_records_{timestamp}.{format_type}"
        
        # 选择保存位置
        file_path = filedialog.asksaveasfilename(
            title="保存颜色记录",
            defaultextension=f".{format_type}",
            filetypes=file_types[format_type],
            initialfile=default_name
        )
        
        if file_path:
            try:
                if format_type == 'json':
                    self.export_to_json(file_path)
                elif format_type == 'csv':
                    self.export_to_csv(file_path)
                elif format_type == 'xml':
                    self.export_to_xml(file_path)
                elif format_type == 'txt':
                    self.export_to_txt(file_path)
                
                messagebox.showinfo("成功", f"颜色记录已导出到:\n{file_path}")
                
            except Exception as e:
                messagebox.showerror("错误", f"导出失败:\n{str(e)}")
    
    def export_to_json(self, file_path):
        """导出为JSON格式"""
        export_data = {
            'export_info': {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'total_records': len(self.color_records),
                'tool_version': '1.0',
                'format': 'JSON'
            },
            'color_records': self.color_records
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
    
    def export_to_csv(self, file_path):
        """导出为CSV格式"""
        with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            
            # 写入表头
            headers = [
                '序号', '时间戳', '图像文件', 'X坐标', 'Y坐标',
                'R值', 'G值', 'B值', '十六进制',
                'H值(度)', 'S值(%)', 'V值(%)'
            ]
            writer.writerow(headers)
            
            # 写入数据
            for record in self.color_records:
                row = [
                    record['sequence'],
                    record['timestamp'],
                    record['image_file'],
                    record['position']['x'],
                    record['position']['y'],
                    record['rgb']['r'],
                    record['rgb']['g'],
                    record['rgb']['b'],
                    record['hex'],
                    record['hsv']['h'],
                    record['hsv']['s'],
                    record['hsv']['v']
                ]
                writer.writerow(row)
    
    def export_to_xml(self, file_path):
        """导出为XML格式"""
        root = ET.Element('ColorRecords')
        
        # 添加导出信息
        export_info = ET.SubElement(root, 'ExportInfo')
        ET.SubElement(export_info, 'Timestamp').text = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ET.SubElement(export_info, 'TotalRecords').text = str(len(self.color_records))
        ET.SubElement(export_info, 'ToolVersion').text = '1.0'
        ET.SubElement(export_info, 'Format').text = 'XML'
        
        # 添加颜色记录
        records_elem = ET.SubElement(root, 'Records')
        
        for record in self.color_records:
            record_elem = ET.SubElement(records_elem, 'ColorRecord')
            record_elem.set('sequence', str(record['sequence']))
            
            ET.SubElement(record_elem, 'Timestamp').text = record['timestamp']
            ET.SubElement(record_elem, 'ImageFile').text = record['image_file']
            
            position_elem = ET.SubElement(record_elem, 'Position')
            ET.SubElement(position_elem, 'X').text = str(record['position']['x'])
            ET.SubElement(position_elem, 'Y').text = str(record['position']['y'])
            
            rgb_elem = ET.SubElement(record_elem, 'RGB')
            ET.SubElement(rgb_elem, 'R').text = str(record['rgb']['r'])
            ET.SubElement(rgb_elem, 'G').text = str(record['rgb']['g'])
            ET.SubElement(rgb_elem, 'B').text = str(record['rgb']['b'])
            ET.SubElement(rgb_elem, 'Hex').text = record['hex']
            
            hsv_elem = ET.SubElement(record_elem, 'HSV')
            ET.SubElement(hsv_elem, 'H').text = str(record['hsv']['h'])
            ET.SubElement(hsv_elem, 'S').text = str(record['hsv']['s'])
            ET.SubElement(hsv_elem, 'V').text = str(record['hsv']['v'])
        
        # 写入文件
        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ", level=0)
        tree.write(file_path, encoding='utf-8', xml_declaration=True)
    
    def export_to_txt(self, file_path):
        """导出为文本格式"""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("颜色记录导出文件\n")
            f.write("=" * 50 + "\n")
            f.write(f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"记录总数: {len(self.color_records)}\n")
            f.write("=" * 50 + "\n\n")
            
            for i, record in enumerate(self.color_records, 1):
                f.write(f"记录 #{i}\n")
                f.write(f"时间: {record['timestamp']}\n")
                f.write(f"图像文件: {record['image_file']}\n")
                f.write(f"位置: ({record['position']['x']}, {record['position']['y']})\n")
                f.write(f"RGB: ({record['rgb']['r']}, {record['rgb']['g']}, {record['rgb']['b']})\n")
                f.write(f"HSV: ({record['hsv']['h']}°, {record['hsv']['s']}%, {record['hsv']['v']}%)\n")
                f.write(f"十六进制: {record['hex']}\n")
                f.write("-" * 30 + "\n\n")
    
    def toggle_floating_mode(self):
        """切换悬浮窗模式"""
        if not self.is_floating_mode:
            self.start_floating_mode()
        else:
            self.stop_floating_mode()
    
    def start_floating_mode(self):
        """启动悬浮窗模式"""
        try:
            self.is_floating_mode = True
            self.floating_btn.config(text="停止悬浮窗")
            
            # 创建悬浮窗
            self.create_floating_window()
            
            # 隐藏主窗口（可选）
            self.root.withdraw()
            
            # 开始屏幕捕获循环
            self.start_screen_capture()
            
        except Exception as e:
            messagebox.showerror("错误", f"启动悬浮窗失败:\n{str(e)}")
            self.stop_floating_mode()
    
    def stop_floating_mode(self):
        """停止悬浮窗模式"""
        self.is_floating_mode = False
        self.floating_btn.config(text="启动悬浮窗")
        
        # 停止定时器
        if self.floating_timer:
            self.root.after_cancel(self.floating_timer)
            self.floating_timer = None
        
        # 关闭悬浮窗
        if self.floating_window:
            self.floating_window.destroy()
            self.floating_window = None
        
        # 显示主窗口
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
    
    def create_floating_window(self):
        """创建悬浮窗"""
        self.floating_window = tk.Toplevel(self.root)
        self.floating_window.title("屏幕取色器")
        
        # 窗口设置
        window_width = int(280 * self.ui_scale)
        window_height = int(200 * self.ui_scale)
        self.floating_window.geometry(f"{window_width}x{window_height}")
        
        # 窗口属性设置
        self.floating_window.attributes('-topmost', True)  # 置顶
        self.floating_window.attributes('-alpha', 0.9)     # 半透明
        self.floating_window.resizable(False, False)
        
        # 设置窗口位置（屏幕右上角）
        screen_width = self.floating_window.winfo_screenwidth()
        x = screen_width - window_width - 50
        y = 50
        self.floating_window.geometry(f"+{x}+{y}")
        
        # 窗口关闭事件
        self.floating_window.protocol("WM_DELETE_WINDOW", self.stop_floating_mode)
        
        self.setup_floating_ui()
    
    def setup_floating_ui(self):
        """设置悬浮窗界面"""
        # 主框架
        padding = int(10 * self.ui_scale)
        main_frame = ttk.Frame(self.floating_window, padding=padding)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(main_frame, text="屏幕取色器", font=self.fonts['title'])
        title_label.pack(pady=(0, int(10 * self.ui_scale)))
        
        # 鼠标位置显示
        self.mouse_pos_label = ttk.Label(main_frame, text="位置: (0, 0)", font=self.fonts['default'])
        self.mouse_pos_label.pack(anchor=tk.W)
        
        # 颜色信息框架
        color_frame = ttk.LabelFrame(main_frame, text="颜色信息", padding=int(5 * self.ui_scale))
        color_frame.pack(fill=tk.BOTH, expand=True, pady=(int(5 * self.ui_scale), 0))
        
        # RGB显示
        self.floating_rgb_label = ttk.Label(color_frame, text="RGB: (0, 0, 0)", font=self.fonts['default'])
        self.floating_rgb_label.pack(anchor=tk.W)
        
        # 十六进制显示
        self.floating_hex_label = ttk.Label(color_frame, text="HEX: #000000", font=self.fonts['default'])
        self.floating_hex_label.pack(anchor=tk.W)
        
        # 颜色预览
        preview_size = int(40 * self.ui_scale)
        self.floating_color_preview = tk.Frame(color_frame, width=preview_size, height=preview_size, 
                                              bg="black", relief=tk.SUNKEN, bd=2)
        self.floating_color_preview.pack(pady=(int(5 * self.ui_scale), 0))
        self.floating_color_preview.pack_propagate(False)
        
        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(int(10 * self.ui_scale), 0))
        
        # 取色按钮
        capture_btn = ttk.Button(button_frame, text="取色 (Ctrl+Click)", 
                                command=self.manual_capture_color, style='Custom.TButton')
        capture_btn.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 关闭按钮
        close_btn = ttk.Button(button_frame, text="关闭", 
                              command=self.stop_floating_mode, style='Custom.TButton')
        close_btn.pack(side=tk.RIGHT, padx=(int(5 * self.ui_scale), 0))
        
        # 绑定全局热键
        self.floating_window.bind('<Control-Button-1>', self.on_floating_click)
        self.floating_window.focus_set()
    
    def start_screen_capture(self):
        """开始屏幕捕获循环"""
        if self.is_floating_mode and self.floating_window:
            try:
                # 获取鼠标位置
                x = self.floating_window.winfo_pointerx()
                y = self.floating_window.winfo_pointery()
                
                # 更新鼠标位置显示
                if hasattr(self, 'mouse_pos_label'):
                    self.mouse_pos_label.config(text=f"位置: ({x}, {y})")
                
                # 捕获鼠标位置的颜色
                try:
                    # 使用PIL的ImageGrab捕获屏幕
                    screenshot = ImageGrab.grab()
                    
                    # 确保坐标在屏幕范围内
                    if 0 <= x < screenshot.width and 0 <= y < screenshot.height:
                        # 获取像素颜色
                        pixel_color = screenshot.getpixel((x, y))
                        
                        if len(pixel_color) >= 3:
                            r, g, b = pixel_color[:3]
                            
                            # 更新悬浮窗显示
                            self.update_floating_display(r, g, b)
                    
                except Exception as e:
                    print(f"屏幕捕获错误: {e}")
                
                # 继续捕获（每50毫秒更新一次）
                self.floating_timer = self.root.after(50, self.start_screen_capture)
                
            except Exception as e:
                print(f"捕获循环错误: {e}")
                self.stop_floating_mode()
    
    def update_floating_display(self, r, g, b):
        """更新悬浮窗颜色显示"""
        try:
            # 更新RGB显示
            if hasattr(self, 'floating_rgb_label'):
                self.floating_rgb_label.config(text=f"RGB: ({r}, {g}, {b})")
            
            # 更新十六进制显示
            hex_color = f"#{r:02X}{g:02X}{b:02X}"
            if hasattr(self, 'floating_hex_label'):
                self.floating_hex_label.config(text=f"HEX: {hex_color}")
            
            # 更新颜色预览
            if hasattr(self, 'floating_color_preview'):
                self.floating_color_preview.config(bg=hex_color)
            
        except Exception as e:
            print(f"更新显示错误: {e}")
    
    def manual_capture_color(self):
        """手动捕获当前鼠标位置的颜色并记录"""
        try:
            # 获取当前鼠标位置
            x = self.floating_window.winfo_pointerx()
            y = self.floating_window.winfo_pointery()
            
            # 捕获屏幕
            screenshot = ImageGrab.grab()
            
            # 确保坐标在屏幕范围内
            if 0 <= x < screenshot.width and 0 <= y < screenshot.height:
                # 获取像素颜色
                pixel_color = screenshot.getpixel((x, y))
                
                if len(pixel_color) >= 3:
                    r, g, b = pixel_color[:3]
                    
                    # 计算HSV值
                    h, s, v = colorsys.rgb_to_hsv(r/255.0, g/255.0, b/255.0)
                    h_deg = int(h * 360)
                    s_percent = int(s * 100)
                    v_percent = int(v * 100)
                    
                    # 十六进制值
                    hex_color = f"#{r:02X}{g:02X}{b:02X}"
                    
                    # 添加到颜色记录（标记为屏幕取色）
                    record = {
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'sequence': len(self.color_records) + 1,
                        'position': {'x': x, 'y': y},
                        'rgb': {'r': r, 'g': g, 'b': b},
                        'hsv': {'h': h_deg, 's': s_percent, 'v': v_percent},
                        'hex': hex_color,
                        'image_file': 'Screen Capture'  # 标记为屏幕截图
                    }
                    
                    self.color_records.append(record)
                    self.update_record_count()
                    
                    # 显示成功提示
                    self.show_capture_notification(hex_color)
                    
        except Exception as e:
            messagebox.showerror("错误", f"取色失败:\n{str(e)}")
    
    def on_floating_click(self, event):
        """处理悬浮窗的Ctrl+点击事件"""
        self.manual_capture_color()
    
    def show_capture_notification(self, hex_color):
        """显示取色成功通知"""
        try:
            # 创建临时通知窗口
            notification = tk.Toplevel(self.floating_window)
            notification.title("取色成功")
            
            # 窗口设置
            notification.geometry("200x80")
            notification.attributes('-topmost', True)
            notification.attributes('-alpha', 0.8)
            notification.resizable(False, False)
            
            # 设置位置（悬浮窗下方）
            if self.floating_window:
                x = self.floating_window.winfo_x()
                y = self.floating_window.winfo_y() + self.floating_window.winfo_height() + 10
                notification.geometry(f"+{x}+{y}")
            
            # 内容
            label = ttk.Label(notification, text=f"已记录颜色\n{hex_color}", 
                             font=self.fonts['default'], anchor=tk.CENTER)
            label.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
            
            # 自动关闭
            notification.after(2000, notification.destroy)
            
        except Exception as e:
            print(f"通知显示错误: {e}")

def main():
    """主函数"""
    # 创建根窗口
    root = tk.Tk()
    
    # 在Windows上启用高DPI支持
    try:
        if platform.system() == "Windows":
            # 告诉Windows我们是DPI感知的
            root.wm_attributes('-toolwindow', False)
            
            # 设置高DPI支持
            try:
                import ctypes
                ctypes.windll.shcore.SetProcessDpiAwareness(1)
            except:
                pass
                
    except Exception as e:
        print(f"DPI设置警告: {e}")
    
    # 创建应用程序
    app = ImageColorPicker(root)
    
    # 启动主循环
    root.mainloop()

if __name__ == "__main__":
    main()
