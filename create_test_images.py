# 图像格式测试脚本

"""
测试图像取色器对不同格式的支持
"""

from PIL import Image
import os

def create_test_images():
    """创建不同格式的测试图像"""
    # 创建一个简单的测试图像
    width, height = 100, 100
    
    # 创建RGB图像
    test_image = Image.new('RGB', (width, height), color='red')
    
    # 在图像上绘制一些不同颜色的区域
    pixels = test_image.load()
    
    # 左上角：红色 (255, 0, 0)
    for x in range(50):
        for y in range(50):
            pixels[x, y] = (255, 0, 0)
    
    # 右上角：绿色 (0, 255, 0)
    for x in range(50, 100):
        for y in range(50):
            pixels[x, y] = (0, 255, 0)
    
    # 左下角：蓝色 (0, 0, 255)
    for x in range(50):
        for y in range(50, 100):
            pixels[x, y] = (0, 0, 255)
    
    # 右下角：黄色 (255, 255, 0)
    for x in range(50, 100):
        for y in range(50, 100):
            pixels[x, y] = (255, 255, 0)
    
    # 保存为不同格式
    formats = {
        'BMP': 'test_image.bmp',
        'JPEG': 'test_image.jpg',
        'PNG': 'test_image.png',
        'GIF': 'test_image.gif',
        'TIFF': 'test_image.tiff'
    }
    
    test_dir = 'test_images'
    if not os.path.exists(test_dir):
        os.makedirs(test_dir)
    
    for format_name, filename in formats.items():
        filepath = os.path.join(test_dir, filename)
        
        if format_name == 'GIF':
            # GIF需要转换为调色板模式
            gif_image = test_image.convert('P')
            gif_image.save(filepath)
        else:
            test_image.save(filepath)
        
        print(f"已创建测试图像: {filepath}")
    
    # 创建一个大图像测试
    large_image = Image.new('RGB', (5000, 3000), color='purple')
    large_filepath = os.path.join(test_dir, 'large_test_image.png')
    large_image.save(large_filepath)
    print(f"已创建大图像测试: {large_filepath}")

if __name__ == "__main__":
    create_test_images()
    print("\n测试图像创建完成!")
    print("您可以使用这些图像测试取色器的多格式支持功能。")
