from enum import Enum


import cv2
import time
import numpy as np
import os
import math
import log_config
import halcon as ha
logger = log_config.setup_logging()


class ProcessResult(Enum):
    OK = 1
    NG = 2
    EXCEPTION = 3
class ImageProcessor:
    def __init__(self):        
        self.TEMPLATE_PATH = "outsideshape.ncm"  # 替换为实际的固定路径
        #外部物体默认参数
        self.OUTER_OBJECT_PARAMS = {
            'gray': (0, 120),
            'area': (50000, 350000),
            'circularity': (0.4, 1.0)
        }
        #内部物体默认参数
        self.INNER_OBJECT_PARAMS = {
            'gray': (0, 120),
            'area': (160000, 180000),
            'circularity': (0.4, 1.0)
        }

        try:
            self.Model_ID = self._load_ncc_template()
            logger.info(f"Successfully loaded Halcon template from {self.TEMPLATE_PATH}")
        except Exception as e:
            logger.error(f"Failed to load Halcon template from {self.TEMPLATE_PATH}: {str(e)}")
            

    def _load_ncc_template(self):
        template = ha.read_ncc_model(self.TEMPLATE_PATH)
        return template
    def get_roi(self, image):
        _, mask = cv2.threshold(image, 50, 255, cv2.THRESH_BINARY)
        roi = cv2.bitwise_and(image, image, mask=mask)
        return roi

    def get_roi_info(self, roi, image_width, image_height):
        default_x = image_width // 2
        default_y = image_height // 2
        default_r = min(image_width, image_height) // 4 + 200
        return (roi[0] if roi[0] != 0 else default_x,
                roi[1] if roi[1] != 0 else default_y,
                roi[2] if roi[2] != 0 else default_r)

    def validate_and_adjust_param(self, value, default, min_val, max_val):
        if value == 0:
            return default
        if min_val <= value <= max_val:
            return value
        logger.warning(
            f"Parameter value {value} is outside the valid range [{min_val}, {max_val}]. Adjusting to the nearest valid value.")
        return max(min_val, min(value, max_val))

    def get_image_params(self, params, is_inner_object=False):
        default_params = self.INNER_OBJECT_PARAMS if is_inner_object else self.OUTER_OBJECT_PARAMS

        gray_lower = self.validate_and_adjust_param(params[0], default_params['gray'][0], 0, 255)
        gray_upper = self.validate_and_adjust_param(params[1], default_params['gray'][1], 0, 255)
        area_lower = self.validate_and_adjust_param(params[2], default_params['area'][0], 0, float('inf'))
        area_upper = self.validate_and_adjust_param(params[3], default_params['area'][1], 0, float('inf'))
        circularity_lower = self.validate_and_adjust_param(params[4], default_params['circularity'][0], 0, 1)
        circularity_upper = self.validate_and_adjust_param(params[5], default_params['circularity'][1], 0, 1)

        # Ensure lower bounds don't exceed upper bounds
        gray_lower, gray_upper = self._adjust_bounds(gray_lower, gray_upper, 'gray', default_params['gray'])
        area_lower, area_upper = self._adjust_bounds(area_lower, area_upper, 'area', default_params['area'])
        circularity_lower, circularity_upper = self._adjust_bounds(circularity_lower, circularity_upper, 'circularity',
                                                                   default_params['circularity'])

        return {
            'gray': (gray_lower, gray_upper),
            'area': (area_lower, area_upper),
            'circularity': (circularity_lower, circularity_upper)
        }

    def _adjust_bounds(self, lower, upper, param_name, default_values):
        if lower > upper:
            logger.warning(
                f"{param_name.capitalize()} lower bound ({lower}) is greater than upper bound ({upper}). Adjusting to default values.")
            return default_values
        return lower, upper

    def process_outer_object(self,image, roi, params):
        try:
            
            opencvimage = ha.himage_as_numpy_array(image)
            # Save the image using cv2
            
            roi_x, roi_y, roi_radius = roi
            roi_circle = ha.gen_circle(roi_y, roi_x, roi_radius)
            num_channels = ha.count_channels(image)
            if num_channels[0] > 1:  # 直接使用返回值，不需要 len()
                gray_image = ha.rgb1_to_gray(image)
            else:
                gray_image = image
            reduced_image = ha.reduce_domain(gray_image, roi_circle)

            
            # Read the shape model
            #model_id = ha.read_shape_model("outsideshape.shm")
            row, column, angle, score = ha.find_ncc_model(reduced_image, self.Model_ID, math.radians(0),
                                                          math.radians(360), 0.67, 1, 0.5, 'true', 0)
            # row, column, angle, score = ha.find_shape_model(
            #     reduced_image, model_id, math.radians(0), math.radians(360), 0.4, 1, 0.5, 'least_squares', [7, 1], 0.75
            # )
            # # Set shape model parameters
            # ha.set_generic_shape_model_param(model_id, 'border_shape_models', 'false')
            # ha.set_generic_shape_model_param(model_id, 'min_score', 0.7)

            # # Find the shape model in the image
            # match_result_id, num_match_result = ha.find_generic_shape_model(reduced_image, model_id)

            if len(score) != 1:
                logger.info(f"No match found or multiple matches found. num_match_result: {len(score)}")
                return opencvimage, (999, 999), 999, 999,0
            #match_contour = ha.get_shape_model_contours(model_id, 1)
            # Get the match results
             

            #hom_mat2d = ha.vector_angle_to_rigid(0, 0, 0, row, column, angle)
            #trans_contours = ha.affine_trans_contour_xld(match_contour, hom_mat2d)

            # 坐标变换
            # match_transformed_ref_y = column[0] - center_x  # col 从左到右
            # match_transformed_ref_x = center_y - row[0]  # row 从上到下

    

            # # 角度处理
            # angle_deg = math.degrees(angle[0])
            # if angle_deg > 180:
            #     angle_deg -= 360

            # 绘制匹配结果
            #painted_match_image = ha.paint_xld(trans_contours, image, (0, 255, 0))
 
                    # 转换为OpenCV图像
            #opencvimage = ha.himage_as_numpy_array(painted_match_image)
            # if num_channels[0] == 1:
            #     # 如果是单通道图像，转换为3通道
            #     opencvimage = cv2.cvtColor(opencvimage, cv2.COLOR_GRAY2BGR)
            # elif num_channels[0] == 3:
            #     # 如果已经是3通道，确保通道顺序正确（BGR）
            #     opencvimage = cv2.cvtColor(opencvimage, cv2.COLOR_RGB2BGR)


            # 如果需要，可以在这里对OpenCV图像进行进一步处理
            # 例如，添加文本显示匹配位置和角度
            # cv2.putText(opencvimage, f"({match_transformed_ref_x:.2f}, {match_transformed_ref_y:.2f})", 
            #             (int(column[0]), int(row[0])), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
            # cv2.putText(opencvimage, f"{angle_deg:.2f} deg", 
            #             (int(column[0]), int(row[0])+20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

            return opencvimage, (row[0], column[0]), angle[0], score[0],len(score)

        except Exception as e:
                logger.error(f"Error in matchshape: {str(e)}")
                return opencvimage, (999, 999), 999,999, 0        
        

    def process_inner_object(self, image, roi, params):
        
        roi_x, roi_y, roi_radius = roi

        roi_circle = ha.gen_circle(roi_y, roi_x, roi_radius)
        reduced_image = ha.reduce_domain(image, roi_circle)
        gray_image = ha.rgb1_to_gray(reduced_image)
        
        binary_image = ha.threshold(gray_image, params['gray'][0], params['gray'][1])
        
        eroded_image = ha.erosion_circle(binary_image, 1.5)
        
        connected_regions = ha.connection(eroded_image)
        filled_regions = ha.fill_up(connected_regions)

        selected_regions = ha.select_shape(filled_regions, ['area', 'circularity'], 'and',
                                           [params['area'][0], params['circularity'][0]],
                                           [params['area'][1], params['circularity'][1]])

        count = ha.count_obj(selected_regions)
        if ha.count_obj(selected_regions) != 1:
            return image, 999,999, (999, 999), 999, 999
        
        row, column, radius = ha.smallest_circle(selected_regions)
        selected_regions_area = ha.area_center(selected_regions)
        selected_regions_circularity = ha.circularity(selected_regions)
        angle = ha.orientation_region(selected_regions)
        return image, selected_regions_area[0][0], selected_regions_circularity[0],(row[0], column[0]), radius[0], angle

    def draw_results(self, image, center, radius, angle_rad, roi, params, selected_area, selected_circularity, result,
                     is_inner_object=False):
        if isinstance(image, np.ndarray):
            opencv_image = image
        else:
            # Convert HALCON image to OpenCV image
            opencv_image = ha.himage_as_numpy_array(image)
        
        if len(opencv_image.shape) == 2:
            opencv_image = cv2.cvtColor(opencv_image, cv2.COLOR_GRAY2BGR)
        height, width = opencv_image.shape[:2]
        # 绘制十字线
        cv2.line(opencv_image, (0, height // 2), (width, height // 2), (255, 255, 0), 3)  # 黄色横线
        cv2.line(opencv_image, (width // 2, 0), (width // 2, height), (255, 255, 0), 3)  # 黄色竖线
        cv2.circle(opencv_image, (roi[0], roi[1]), roi[2], (255, 0, 255), 10)  # 紫色 ROI 圆

        # 只有当 center 不是 (999, 999) 时才绘制绿色圆和红色圆心
        if center != (999, 999):
            cv2.circle(opencv_image, (int(center[0]), int(center[1])), int(radius), (0, 255, 0), 2)  # 绿色圆
            cv2.circle(opencv_image, (int(center[0]), int(center[1])), 5, (0, 0, 255), -1)  # 红色圆心

            if not is_inner_object:
                angle_deg = np.degrees(angle_rad)
                arrow_length = 300
                end_point = (
                    int(center[0] + arrow_length * np.cos(angle_rad)),
                    int(center[1] - arrow_length * np.sin(angle_rad))
                )
                cv2.arrowedLine(opencv_image, (int(center[0]), int(center[1])), end_point, (255, 0, 0), 10)
                cv2.putText(opencv_image, f"{float(angle_deg):.2f}",
                            (int(center[0]) + 10, int(center[1]) + 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

        self._draw_info_text(opencv_image, roi, params, selected_area, selected_circularity, center)
        
        self._draw_result_text(opencv_image, result, center)
        return opencv_image
    def _draw_info_text(self, image, roi, params, selected_area, selected_circularity, center):
        height, width = image.shape[:2]
        result_center = self.convert_to_center_coordinates(center, (width, height))
        
        info_lines = [
            f"ROI: x={roi[0]}, y={roi[1]}, r={roi[2]}",
            f"Gray: {params['gray'][0]}-{params['gray'][1]}",
            f"Area: {params['area'][0]}-{params['area'][1]}",
            f"Circularity: {params['circularity'][0]:.2f}-{params['circularity'][1]:.2f}",
            f"Selected: Area={selected_area:.0f}, Circularity={selected_circularity:.4f}",
            f"Center: x={result_center[0]:.0f}, y={result_center[1]:.0f}"  # 使用转换后的坐标
        ]
        for i, line in enumerate(info_lines):
            cv2.putText(image, line, (10, 30 + i * 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    def _draw_result_text(self, image, result, center):
        if result == ProcessResult.OK:
            result_text = "OK"
            result_color = (0, 255, 0)  # 绿色
            # 保持原来的位置
            position = (int(center[0]) - 20, int(center[1]) + 40)
        else:
            if result == ProcessResult.NG:
                result_text = "NG"
                result_color = (0, 0, 255)  # 红色
            else:  # ProcessResult.EXCEPTION
                result_text = "Exception"
                result_color = (255, 0, 0)  # 蓝色

            # 计算图像中心
            height, width = image.shape[:2]
            position = (width // 2, height // 2)

        # 获取文本大小
        text_size = cv2.getTextSize(result_text, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)[0]

        # 调整位置使文本居中
        text_x = position[0] - text_size[0] // 2
        text_y = position[1] + text_size[1] // 2

        cv2.putText(image, result_text,
                    (text_x, text_y),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, result_color, 2)

    def process_outer_object_image(self, image, camera_info):
        start_time = time.time()  # 记录开始时间
        try:
            width, height = ha.get_image_size(image)
            roi = self.get_roi_info(camera_info.get('roi', [0, 0, 0]), width[0], height[0])
            params = self.get_image_params(camera_info.get('params', [0] * 6))
            pixel_distance = camera_info.get('pixel_distance', 1)  # 获取pixel_distance
            logger.info(f"处理外部物体图像，ROI: (x={roi[0]}, y={roi[1]}, r={roi[2]}), "
                        f"参数：灰度范围 {params['gray']}, "
                        f"面积范围 {params['area']}, "
                        f"圆度范围 {params['circularity']}, "
                        f"像素距离 {pixel_distance}")

            processed_image, (row, column), phi,score,num_match_result = self.process_outer_object(image, roi, params)
            
            logger.info(f"外部物体处理结果: row={row}, column={column}, phi={phi}, score={score}, num_match_result={num_match_result}")

            if phi == 999:
                logger.error(f"外部物体：未找到符合条件的图像:")
                result = ProcessResult.NG
                center = (999, 999)
                angle = 999
            else:
                center = (column, row)
                angle = phi
                result = ProcessResult.OK

        except Exception as e:
            logger.error(f"处理外部物体图像时发生错误: {str(e)}")
            result = ProcessResult.EXCEPTION
            center = (999, 999)
            angle = 999
            radius = 999
            processed_image = image

        finally:
            result_image = self.draw_results(processed_image, center, 999, angle, roi, params, 
                                             999, 999, result, is_inner_object=False)

            result_center = center
            result_angle = angle

            if result == ProcessResult.OK:
                result_center = self.convert_to_center_coordinates(center, (width[0], height[0]))
                result_center = (result_center[0] * pixel_distance, result_center[1] * pixel_distance)
                result_angle = np.degrees(angle)
                logger.info(f"result_center: {result_center}, result_angle: {result_angle}")
                # 将负角度转换为正角度 + 180
                # if result_angle < 0:
                #     result_angle += 180
            execution_time = time.time() - start_time
            logger.info(f"外部物体图像处理完成，执行时间：{execution_time:.3f}秒")
            return result, result_image, result_center, result_angle

 

    def process_inner_object_image(self, image, camera_info):
        try:
            width, height = ha.get_image_size(image)
            roi = self.get_roi_info(camera_info.get('roi', [0, 0, 0]), width[0], height[0])
            params = self.get_image_params(camera_info.get('params', [0] * 6), is_inner_object=True)
            pixel_distance = camera_info.get('pixel_distance', 1)  # 获取pixel_distance
            logger.info(f"处理内部物体图像，ROI: (x={roi[0]}, y={roi[1]}, r={roi[2]}), "
                        f"参数：灰度范围 {params['gray']}, "
                        f"面积范围 {params['area']}, "
                        f"圆度范围 {params['circularity']}, "
                        f"像素距离 {pixel_distance}")

            processed_image, selected_regions_area,circularity, (row, column), radius, angle = self.process_inner_object(image, roi, params)

            if selected_regions_area == 999:
                logger.error(f"内部物体：未找到符合条件的图像:")
                result = ProcessResult.NG
                center = (999, 999)
                angle = 999
            else:
                center = (column, row)

                result = ProcessResult.OK

        except Exception as e:
            logger.error(f"处理内部物体图像时发生错误: {str(e)}")
            result = ProcessResult.EXCEPTION
            center = (999, 999)
            angle = 999
            radius = 999
            processed_image = image

        finally:
            result_image = self.draw_results(processed_image, center, radius, angle, roi, params, 
                                             selected_regions_area, circularity, result)
                        # 只在结果为OK时进行坐标转换
            if result == ProcessResult.OK:
                center = self.convert_to_center_coordinates(center, (width[0], height[0]))
                center = (center[0] * pixel_distance, center[1] * pixel_distance)
                result_angle = np.degrees(angle)
                # 将负角度转换为正角度 + 180
                if result_angle < 0:
                    result_angle += 360
            else:
                result_angle = 999
            return result, result_image, center, result_angle

    def _set_default_values(self):
        return 999, (999, 999), 999, 999, 999, 999
    

    def convert_to_center_coordinates(self, point, image_size):
    # """
    # 将 Halcon 坐标系（左上角为原点）转换为以图像中心为原点的坐标系
    # """
        center_x = image_size[0] / 2
        center_y = image_size[1] / 2
    
        new_x = point[0] - center_x
        new_y = center_y - point[1]  # 注意 y 轴方向相反
    
        return (new_x, new_y)
    
    def convert_to_rgb565(self,image):
        # """
        # 将OpenCV的BGR图像转换为RGB565格式。   
        # 参数:
        #     image (numpy.ndarray): 输入图像，BGR格式。    
        # 返回:
        #     numpy.ndarray: RGB565格式的图像。
        # """
        # 确保图像不为空
        if image is None:
            return None
        if not isinstance(image, np.ndarray):
            try:
                image = ha.himage_as_numpy_array(image)
            except:
                logger.info(f"无法将输入图像转换为numpy数组，当前类型为: {type(image).__name__}")
        # BGR到RGB的转换
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)  
        # RGB到RGB565的转换
        r = (image_rgb[:, :, 0] >> 3).astype(np.uint16)  # Red, 右移3位
        g = (image_rgb[:, :, 1] >> 2).astype(np.uint16)  # Green, 右移2位
        b = (image_rgb[:, :, 2] >> 3).astype(np.uint16)  # Blue, 右移3位    
        # 合并为RGB565
        rgb565 = (r << 11) | (g << 5) | b   
        return rgb565   
    def save_rgb565_with_header(self,image, filename):
        # """
        # 将RGB565图像保存到文件，文件头包含图像宽度和高度。

        # 参数:
        #     image (numpy.ndarray): RGB565格式的图像。
        #     filename (str): 保存的文件名。
        # """
        height, width = image.shape
        header = np.array([width, height], dtype=np.int32)
        with open(filename, 'wb') as f:
            f.write(header.tobytes())
            f.write(image.tobytes())

    @classmethod
    def add_result_bar(cls, image, result):
        logger.debug(f"Entering add_result_bar method")
        logger.debug(f"Image shape: {image.shape}, dtype: {image.dtype}")
        logger.debug(f"Result type: {type(result)}, value: {result}")

        height, width = image.shape[:2]
        bar_height = 90

        if isinstance(result, ProcessResult):
            if result == ProcessResult.OK:
                color = [0, 255, 0]  # 绿色
            elif result == ProcessResult.NG:
                color = [0, 0, 255]  # 红色
            else:
                color = [128, 128, 128]  # 灰色
        else:
            logger.warning(f"Unexpected result type: {type(result)}. Using default color.")
            color = [128, 128, 128]  # 默认灰色

        # 确保 bar 的数据类型与 image 一致
        bar = np.full((bar_height, width, 3), color, dtype=image.dtype)



        try:
            result_image = cv2.vconcat([image, bar])
            return result_image
        except Exception as e:
            logger.error(f"Error in add_result_bar: {str(e)}")
            logger.error(f"Image shape: {image.shape}, Bar shape: {bar.shape}")
            # 如果拼接失败，返回原图
            return image

    @staticmethod
    def combine_images(images):
        assert len(images) == 2, "Expected exactly two images"
        
        height, width = images[0].shape[:2]
        combined = np.zeros((height, width * 2 + 10, 3), dtype=np.uint8)
        
        # 放置左图
        combined[:height, :width] = images[0]
        
        # 放置右图
        combined[:height, width + 10:] = images[1]
        
        # 添加分隔线
        cv2.line(combined, (width + 5, 0), (width + 5, height), (255, 255, 255), 2)
        
        return combined

    @staticmethod
    def add_company_name(image):
        # 读取预生成的公司名称图片
        current_dir = os.path.dirname(os.path.abspath(__file__))
        company_name_path = os.path.join(current_dir, 'company_name.png')

        if not os.path.exists(company_name_path):
            raise FileNotFoundError(f"公司名称图片未找到: {company_name_path}")

        company_bar = cv2.imread(company_name_path)

        if company_bar is None:
            raise ValueError(f"无法读取公司名称图片: {company_name_path}")

        # 获取输入图像和公司名称图片的尺寸
        image_height, image_width = image.shape[:2]
        company_bar_height, company_bar_width = company_bar.shape[:2]

        # 如果输入图像的宽度与公司名称图片不同，则调整公司名称图片的宽度
        if image_width != company_bar_width:
            scale_factor = image_width / company_bar_width
            new_height = int(company_bar_height * scale_factor)
            company_bar = cv2.resize(company_bar, (image_width, new_height), interpolation=cv2.INTER_AREA)

        # 垂直连接公司名称条和原图像
        return cv2.vconcat([company_bar, image])

    @classmethod
    def process_and_combine_images(cls, results):
        images = []
        target_size = (1024, 1280)  # 设置目标尺寸，根据需要调整
        for camera_num, result in results.items():
            if result is None:
                img = np.full((*target_size, 3), [0, 255, 0], dtype=np.uint8)
                process_result = ProcessResult.EXCEPTION
            else:
                process_result, result_image, _, _ = result
                img = result_image

            try:
                img = cls.add_result_bar(img, process_result)
            except Exception as e:
                logger.error(f"Error in add_result_bar for camera {camera_num}: {str(e)}")

            images.append(img)

        try:
            combined_image = cls.combine_images(images)
            final_image = cls.add_company_name(combined_image)
            return final_image
        except Exception as e:
            logger.error(f"Error in combining images or adding company name: {str(e)}")
            return images[0] if images else None