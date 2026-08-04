import os
import halcon as ha
import cv2  # Add this line
from image_processing import ImageProcessor

def process_images_in_directory(directory_path):
    image_processor = ImageProcessor()
    
    # 相机信息，你可能需要根据实际情况调整这些值
    camera_info = {
        'roi': [0, 0, 0],  # center x, center y, radius
        'params': [0, 120, 50000, 350000, 0.4, 1.0],  # gray_lower, gray_upper, area_lower, area_upper, circularity_lower, circularity_upper
        'pixel_distance': 0.1
    }

    # 遍历目录中的所有文件
    for filename in os.listdir(directory_path):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff')):
            file_path = os.path.join(directory_path, filename)
            
            try:
                # 读取图像
                image = ha.read_image(file_path)
                 
                # 处理图像
                result, result_image, result_center, result_angle = image_processor.process_outer_object_image(image, camera_info)
                
                # 输出结果
                print(f"File: {filename}")
                print(f"Result: {result}")
                print(f"Center: {result_center}")
                print(f"Angle: {result_angle}")
                print("-" * 50)

                
                # 显示图像
                cv2.imshow("Result Image", result_image)
                cv2.waitKey(0)
                cv2.destroyAllWindows()


                # 可选：保存结果图像
                # result_image_path = os.path.join(directory_path, f"result_{filename}")
                # ha.write_image(result_image, 'png', 0, result_image_path)
                
            except Exception as e:
                print(f"Error processing {filename}: {str(e)}")
                print("-" * 50)

if __name__ == '__main__':
    specific_directory = r"D:\arrch64devshare\tianchangsocket\outside"
    process_images_in_directory(specific_directory)