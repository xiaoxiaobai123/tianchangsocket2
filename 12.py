import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os

def generate_company_name_image(width=2570, height=280, font_size=100, background_color=(7, 25, 142), text_color=(255,255,255)):
    # 创建一个空白图像
    image = Image.new('RGB', (width, height), color=background_color)
    draw = ImageDraw.Draw(image)

    # 使用当前目录的SimHei.ttf
    current_dir = os.path.dirname(os.path.abspath(__file__))
    font_path = os.path.join(current_dir, 'SimHei.ttf')
    try:
        font = ImageFont.truetype(font_path, font_size)
    except IOError:
        print(f"无法找到字体文件: {font_path}")
        print("使用默认字体")
        font = ImageFont.load_default()

    # 绘制文本
    text = "扬州友阳机电有限公司"
    
    # 使用 font.getbbox() 代替 draw.textsize()
    bbox = font.getbbox(text)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    position = ((width - text_width) // 2, (height - text_height) // 2)
    draw.text(position, text, font=font, fill=text_color)

    # 转换为OpenCV格式并保存
    cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    cv2.imwrite('company_name.png', cv_image)
    print("公司名称图片已生成: company_name.png")

# 生成图片
generate_company_name_image()
