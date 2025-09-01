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
import json
import csv
import xml.etree.ElementTree as ET
from datetime import datetime

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
        
        # 颜色记录列表
        self.color_records = []
        
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
        
        # 添加分隔符
        ttk.Separator(control_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        # 颜色记录管理按钮
        ttk.Button(control_frame, text="清空记录", command=self.clear_records).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="导出记录", command=self.export_records).pack(side=tk.LEFT)
        
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
        
        # 颜色记录计数
        self.record_count_label = ttk.Label(right_frame, text="已记录颜色: 0", foreground="blue")
        self.record_count_label.pack(anchor=tk.W, pady=(5, 0))
        
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
                self.current_image_file = os.path.basename(file_path)
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
        export_window.geometry("450x400")
        export_window.resizable(False, False)
        export_window.transient(self.root)
        export_window.grab_set()
        
        # 居中显示
        export_window.geometry("+%d+%d" % (
            self.root.winfo_rootx() + 100,
            self.root.winfo_rooty() + 100
        ))
        
        main_frame = ttk.Frame(export_window, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(main_frame, text="选择导出格式", font=("Arial", 12, "bold"))
        title_label.pack(pady=(0, 20))
        
        # 格式选择框架
        format_frame = ttk.LabelFrame(main_frame, text="文件格式", padding=10)
        format_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # 格式选择
        format_var = tk.StringVar(value="json")
        
        formats = [
            ("JSON格式", "json", "适合程序读取，包含完整信息"),
            ("CSV格式", "csv", "适合Excel打开，表格形式"),
            ("XML格式", "xml", "结构化标记语言格式"),
            ("文本格式", "txt", "简单的文本列表格式")
        ]
        
        for name, value, desc in formats:
            option_frame = ttk.Frame(format_frame)
            option_frame.pack(fill=tk.X, pady=3)
            
            radio_btn = ttk.Radiobutton(option_frame, text=name, variable=format_var, value=value)
            radio_btn.pack(anchor=tk.W)
            
            desc_label = ttk.Label(option_frame, text=desc, foreground="gray", font=("Arial", 8))
            desc_label.pack(anchor=tk.W, padx=(20, 0))
        
        # 信息显示
        info_label = ttk.Label(main_frame, text=f"当前共有 {len(self.color_records)} 条颜色记录", 
                              foreground="blue", font=("Arial", 9))
        info_label.pack(pady=(0, 20))
        
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
        cancel_btn = ttk.Button(button_frame, text="取消", command=do_cancel)
        cancel_btn.pack(side=tk.LEFT)
        
        export_btn = ttk.Button(button_frame, text="导出", command=do_export)
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

def main():
    """主函数"""
    root = tk.Tk()
    app = ImageColorPicker(root)
    root.mainloop()

if __name__ == "__main__":
    main()
