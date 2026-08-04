import cv2
import halcon as ha
from image_processing import ImageProcessor, ProcessResult  # 假设您已将之前的代码保存在 image_processor.py 文件中

# 创建 ImageProcessor 实例
processor = ImageProcessor()

# 图像路径
image_path = r"D:\emgucv\vsproject\opencvcsharpfirst\bin\Debug\Cam1BiGCircle20000\5555.bmp"

# 读取图像
# 使用 OpenCV 读取图像
cv_image = cv2.imread(image_path)
# 将 OpenCV 图像转换为 HALCON 图像
halcon_image = ha.himage_from_numpy_array (cv_image)

# 相机信息（这里使用示例值，您需要根据实际情况调整）
camera_info = {
    'roi': [0, 0, 0],  # 使用默认值（图像中心）
    'params': [0, 150, 0, 0, 0, 1]  # 示例参数值 灰度上下限，面积上下限，圆度上下限
}

# 处理大圆图像
result, processed_image, center, angle = processor.process_small_circle_image(halcon_image, camera_info)
rgb565_image = processor.convert_to_rgb565(processed_image)
processor.save_rgb565_with_header(rgb565_image, 'output_image.rgb565')
# 输出结果
print(f"处理结果: {result.name}")

if result == ProcessResult.OK:
    print(f"中心坐标: {center}, 角度: {angle}")
else:
    print("无有效的中心坐标和角度")

# 如果需要保存处理后的图像
if processed_image is not None:
    cv2.imwrite("processed_555.bmp", processed_image)
    print("处理后的图像已保存为 processed_555.bmp")

 