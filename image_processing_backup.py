import cv2
import json
import numpy as np
import os
import subprocess
import tempfile
class ImageProcessor:
    def __init__(self,app_instance=None):
        self.app_instance = app_instance
        self.feh_processes = []
    def get_screen_resolution(self):
        cmd = "xrandr | grep '*' | awk '{print $1}'"
        output = subprocess.check_output(cmd, shell=True).decode().strip()
        width, height = map(int, output.split('x'))
        return width, height        
    def get_roi(self, image):
        _, mask = cv2.threshold(image, 50, 255, cv2.THRESH_BINARY)
        roi = cv2.bitwise_and(image, image, mask=mask)
        return roi

    def load_roi_coordinates_from_file(self, camera_ip):
        # 根据相机的IP地址构建文件名
        filename = f"roi_coordinates_{camera_ip.replace('.', '_')}.json"
        
        # 从JSON文件中读取ROI坐标
        with open(filename, "r") as file:
            roi_coordinates = json.load(file)
        return roi_coordinates
    
    def extract_features_and_threshold_for_roi(self, image, camera_ip):
         # Allow the user to select ROI
        roi_coordinates = self.load_roi_coordinates_from_file(camera_ip)
        
        # 使用加载的坐标从图像中提取ROI
        roi = image[int(roi_coordinates["y1"]):int(roi_coordinates["y2"]), 
                    int(roi_coordinates["x1"]):int(roi_coordinates["x2"])]
        _, thresh = cv2.threshold(roi, 150, 255, cv2.THRESH_BINARY_INV)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3,3))
        morphed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        return roi,thresh, morphed

    def calculate_area(self, image):
        return cv2.countNonZero(image)


    def filter_long_edges(self, edges_image, min_length=5):
        """Filter out short edges and keep only the long ones."""
        kernel = np.ones((1, min_length), np.uint8)
        closed = cv2.morphologyEx(edges_image, cv2.MORPH_CLOSE, kernel)
        opened = cv2.morphologyEx(closed, cv2.MORPH_OPEN, kernel)
        return opened

    def detect_edges(self, image, camera_ip, min_length=5):
        roi_coordinates = self.load_roi_coordinates_from_file(camera_ip)
        roi = image[int(roi_coordinates["y1"]):int(roi_coordinates["y2"]), 
                int(roi_coordinates["x1"]):int(roi_coordinates["x2"])]

    
    # Since the image is already grayscale, we don't need to convert it again
    # edges = cv2.Canny(roi, 100, 200)

    
    # 双边滤波
        #  roi = cv2.bilateralFilter(roi, 9, 30, 3)
    # 均值滤波
        thresh_03 = cv2.blur(roi, (3, 3))

        # 执行 Sobel 边缘检测
        thresh_04 = cv2.Sobel(thresh_03, cv2.CV_64F, 1, 0, ksize=3)

        # 将结果取绝对值并转换为 8 位无符号整数
        thresh_05 = cv2.convertScaleAbs(thresh_04)


        
    # 自适应阈值二值化
        #   thresh_04 = cv2.adaptiveThreshold(thresh_03, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 15, 2)
        #  filtered_edges = ~thresh_04
        edges = cv2.Canny(thresh_05, 50, 200) 
        filtered_edges = self.filter_long_edges(edges, min_length)
        edge_count = np.sum(filtered_edges > 0)
        return roi, filtered_edges, edge_count

    def resize_image(self, image, scale_factor):
    	try:
        	width = int(image.shape[1] * scale_factor)
        	height = int(image.shape[0] * scale_factor)
        	dimensions = (width, height)
        	return cv2.resize(image, dimensions, interpolation=cv2.INTER_AREA)   
    	except Exception as e:	
            print(f"Error during resize_image: {e}") 
    def show_images_in_terminal(self, img1, img2):
        # 保存图像到临时文件
        img1_path = "img1.png"
        img2_path = "img2.png"
        
        cv2.imwrite(img1_path, img1)
        cv2.imwrite(img2_path, img2)
        # 使用img2txt将图像转化为ASCII
        terminal_width = os.get_terminal_size().columns  # 获取终端宽度
        image_width = terminal_width // 2 - 2  # 分两边显示，中间留2个字符的空间作为分割线

        ascii_img1 = subprocess.getoutput(f'img2txt --width={image_width} {img1_path}')
        ascii_img2 = subprocess.getoutput(f'img2txt --width={image_width} {img2_path}')

        # 组合两个图像的ASCII输出
        ascii_img1_lines = ascii_img1.split('\n')
        ascii_img2_lines = ascii_img2.split('\n')

        combined_ascii = ''
        for line1, line2 in zip(ascii_img1_lines, ascii_img2_lines):
            combined_ascii += line1 + "||" + line2 + "\n"

        # 清空屏幕并打印组合后的ASCII图像
        os.system('clear')
        print(combined_ascii)            
    def process_and_display_with_scale(self, img_01, img_02, camera_ip_01, camera_ip_02, scale_factor=1.0):
   #     screen_width, screen_height = self.get_screen_resolution()
        
   #     half_width = screen_width // 2
  #      for p in self.feh_processes:
  #          p.terminate()	
   #     self.feh_processes = []  # Reset the list
        img_01_resized = self.resize_image(img_01,0.4)
        img_02_resized = self.resize_image(img_02,0.4)
        self.show_images_in_terminal(img_01_resized,img_02_resized)
    #    img_height, img_width, _ = img_01_resized.shape
     #   half_screen_width = screen_width // 2
      #  x_offset_for_second_image = half_screen_width + (half_screen_width - img_width) // 2
    # Save images to temp files
       # tmp_img1 = tempfile.NamedTemporaryFile(suffix=".png", delete=False).name
        #tmp_img2 = tempfile.NamedTemporaryFile(suffix=".png", delete=False).name

 #       cv2.imwrite(tmp_img1, img_01_resized)
 #       cv2.imwrite(tmp_img2, img_02_resized)

    # Use feh to display images on left and right side of the screen
        #p1 = subprocess.Popen(['feh', '--geometry', f'{img_width}x{img_height}+0+0', tmp_img1])
        #p2 = subprocess.Popen(['feh', '--geometry', f'{img_width}x{img_height}+{x_offset_for_second_image}+0', tmp_img2])
        #self.feh_processes.extend([p1, p2])
#        self.app_instance.update_camera_images(img_01_resized, img_02_resized)        
        gray1_image,edge1_image,edge1_count = self.detect_edges(img_01_resized,camera_ip_01,min_length=5)
        gray2_image,edge2_image,edge2_count = self.detect_edges(img_02_resized,camera_ip_02,min_length=5)
      
        #self.app_instance.update_camera_images(gray1_image, gray2_image)
        result = True if edge1_count > edge2_count else False
        #return result, edge1_image, edge2_image
        return result, gray1_image, gray2_image
    def binarize_image(self,image, threshold=50):
        _, binarized = cv2.threshold(image, threshold, 255, cv2.THRESH_BINARY)
        return binarized
 
