import asyncio
from typing import Dict, Any, Tuple
from datetime import datetime
import os
import sys
import cv2
import halcon as ha
from plc_manager import CameraStatus, ProductType, SystemStatus, CameraTriggerStatus, CameraResult
from image_processing import ProcessResult

class TaskManager:
    def __init__(self, plc_manager, camera_manager, image_processor, config, logger):
        self.plc_manager = plc_manager
        self.camera_manager = camera_manager
        self.image_processor = image_processor
        self.config = config
        self.logger = logger
        self.camera_results = {1: None, 2: None}
        # 图片保存目录：打包运行时取可执行文件所在目录，源码运行时取本文件所在目录
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        self.capture_output_dir = os.path.join(base_dir, 'captured_images')
        # 存图配置：config.json 无 capture_images 段时默认关闭(客户现场安全)
        capture_cfg = {}
        try:
            if hasattr(self.config, 'config'):
                capture_cfg = self.config.config.get('capture_images', {}) or {}
        except Exception:
            capture_cfg = {}
        self.capture_enabled = bool(capture_cfg.get('enabled', False))
        self.capture_save_raw = bool(capture_cfg.get('save_raw', True))
        self.capture_save_marked = bool(capture_cfg.get('save_marked', True))
        self.capture_only_ng = bool(capture_cfg.get('only_ng', False))
        self.logger.info(f"Capture images: enabled={self.capture_enabled}, "
                         f"raw={self.capture_save_raw}, marked={self.capture_save_marked}, "
                         f"only_ng={self.capture_only_ng}")

    async def run(self):
        self.logger.info("Task Manager started")
        tasks = [
            asyncio.create_task(self.camera_task(1)),
            asyncio.create_task(self.camera_task(2))
        ]
        await asyncio.gather(*tasks)

    async def camera_task(self, camera_num: int):
        while True:
            try:
                await self.process_camera(camera_num)
            except Exception as e:
                self.logger.error(f"Error processing camera {camera_num}: {str(e)}")
            await asyncio.sleep(0.1)  # 避免过于频繁的读取

    async def process_camera(self, camera_num: int):
        settings = await self.read_plc_settings(camera_num)
        status = settings['status']

        current_trigger_source = self.camera_manager.get_trigger_source(camera_num)

        if status == CameraStatus.START_LOOP:
            # 循环模式：强制使用软件触发
            if current_trigger_source != 7:  # 7 表示软件触发
                await self.update_camera_trigger_mode(camera_num, is_hardware_trigger=False)
            is_hardware_trigger = False
        elif status == CameraStatus.START_TASK:
            # 单次任务：根据设置决定触发模式
            is_hardware_trigger = settings.get('trigger_mode') == CameraTriggerStatus.HARDWARE_TRIGGER
            new_trigger_mode = 0 if is_hardware_trigger else 7  # 0 表示硬件触发，7 表示软件触发
            if current_trigger_source != new_trigger_mode:
                await self.update_camera_trigger_mode(camera_num, is_hardware_trigger)
        else:
            # 其他状态，不改变触发模式
            is_hardware_trigger = (current_trigger_source == 0)

        # 设置曝光时间
        if 'exposure_time' in settings:
            current_exposure_time = self.camera_manager.get_exposure_time(camera_num)
            new_exposure_time = settings['exposure_time']

            if current_exposure_time != new_exposure_time and new_exposure_time != 0:
                await self.set_camera_exposure(camera_num, new_exposure_time)

        if status == CameraStatus.START_TASK:
            await self.process_single_capture(camera_num, settings, is_hardware_trigger)
        elif status == CameraStatus.START_LOOP:
            await self.process_continuous_capture(camera_num, settings, is_hardware_trigger)

    async def read_plc_settings(self, camera_num: int) -> Dict[str, Any]:
        try:
            return await asyncio.to_thread(self.plc_manager.read_camera_settings, camera_num)
        except Exception as e:
            self.logger.error(f"Error reading PLC settings for camera {camera_num}: {str(e)}")
            return {}

    async def process_single_capture(self, camera_num: int, settings: Dict[str, Any], is_hardware_trigger: bool):
        self.logger.info(f"Starting single capture for camera {camera_num}")
        await asyncio.to_thread(self.plc_manager.write_camera_status, camera_num, CameraStatus.IDLE)

        result = await self.capture_and_process_image(camera_num, settings, is_hardware_trigger)

        self.camera_results[camera_num] = result
        await self.write_result_to_plc(camera_num, result)
        await self.process_combined_results()
        await asyncio.to_thread(self.plc_manager.write_camera_status, camera_num, CameraStatus.TASK_COMPLETED)
        self.logger.info(f"Single capture completed for camera {camera_num}")

    async def process_continuous_capture(self, camera_num: int, settings: Dict[str, Any], is_hardware_trigger: bool):
        self.logger.info(f"Starting continuous capture for camera {camera_num}")

        while True:
            try:
                # 每次循环开始时读取最新的设置
                new_settings = await self.read_plc_settings(camera_num)

                # 检查是否需要继续循环模式
                if new_settings['status'] != CameraStatus.START_LOOP:
                    self.logger.info(f"Stopping continuous capture for camera {camera_num}")
                    await asyncio.to_thread(self.plc_manager.write_camera_status, camera_num, CameraStatus.IDLE)
                    break

                # 应用新的曝光时间设置
                await self.apply_camera_settings(camera_num, new_settings)

                # 使用更新后的设置捕获和处理图像
                result = await self.capture_and_process_image(camera_num, new_settings, is_hardware_trigger)

                # 更新结果并写入PLC
                self.camera_results[camera_num] = result
                await self.write_result_to_plc(camera_num, result)
                await self.process_combined_results()

                # 短暂暂停，让出控制权
                await asyncio.sleep(0.01)  # 10毫秒的暂停，可以根据需要调整

            except Exception as e:
                self.logger.error(f"Error in continuous capture for camera {camera_num}: {str(e)}")
                await asyncio.sleep(1)  # 错误发生时稍长的暂停

        self.logger.info(f"Continuous capture ended for camera {camera_num}")

    async def capture_and_process_image(self, camera_num: int, settings: Dict[str, Any], is_hardware_trigger: bool):
        self.logger.debug(f"Capturing image for camera {camera_num}")

        image = await asyncio.to_thread(self.camera_manager.capture_image, camera_num, is_hardware_trigger)
        if image is None:
            self.logger.error(f"Failed to capture image for camera {camera_num}")
            return None

        # 存图开关关闭时完全跳过；only_ng 模式下原图先留在内存，等结果出来再决定
        timestamp = None
        raw_image = None
        if self.capture_enabled:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            raw_image = image
            if self.capture_save_raw and not self.capture_only_ng:
                await asyncio.to_thread(self.save_capture_image, raw_image, camera_num, timestamp, "raw")

        image = ha.himage_from_numpy_array(image)
        camera_info = self.convert_settings_to_camera_info(settings)

        if settings['product_type'] == ProductType.OUTER_OBJECT:
            self.logger.debug(f"Processing large circle image for camera {camera_num}")
            result = await asyncio.to_thread(self.image_processor.process_outer_object_image, image, camera_info)
        elif settings['product_type'] == ProductType.INNER_OBJECT:
            self.logger.debug(f"Processing small circle image for camera {camera_num}")
            result = await asyncio.to_thread(self.image_processor.process_inner_object_image, image, camera_info)
        else:
            self.logger.error(f"Unknown product type for camera {camera_num}")
            return None

        # 保存带标注的结果图；only_ng 模式只在结果非OK时补存原图和标注图
        if self.capture_enabled and result is not None:
            if self.capture_only_ng:
                if result[0] != ProcessResult.OK:
                    if self.capture_save_raw:
                        await asyncio.to_thread(self.save_capture_image, raw_image, camera_num, timestamp, "raw")
                    if self.capture_save_marked:
                        await asyncio.to_thread(self.save_capture_image, result[1], camera_num, timestamp, "marked")
            elif self.capture_save_marked:
                await asyncio.to_thread(self.save_capture_image, result[1], camera_num, timestamp, "marked")

        return result

    def save_capture_image(self, image, camera_num: int, timestamp: str, image_type: str):
        # 保存失败只记录日志，不影响主流程
        try:
            if image is None:
                self.logger.error(f"Cannot save {image_type} image for camera {camera_num}: image is None")
                return

            # Halcon 图像转为 numpy 数组
            if not hasattr(image, 'shape'):
                image = ha.himage_as_numpy_array(image)

            day_dir = timestamp[:8]
            output_dir = os.path.join(self.capture_output_dir, day_dir, image_type)
            os.makedirs(output_dir, exist_ok=True)

            output_path = os.path.join(output_dir, f"{timestamp}_camera{camera_num}_{image_type}.png")
            if cv2.imwrite(output_path, image):
                self.logger.info(f"Saved {image_type} image: {output_path}")
            else:
                self.logger.error(f"Failed to save {image_type} image: {output_path}")
        except Exception as e:
            self.logger.error(f"Error saving {image_type} image for camera {camera_num}: {str(e)}")

    async def write_result_to_plc(self, camera_num: int, result: Tuple[ProcessResult, Any, Tuple[float, float], float]):
        if result is None:
            self.logger.error(f"No valid result to write to PLC for camera {camera_num}")
            return

        process_result, _, center, degree = result
        camera_result = CameraResult(
            x=center[0],
            y=center[1],
            angle=degree,
            result=process_result == ProcessResult.OK,
            area=0,  # 使用 0 替代
            circularity=0.0  # 使用 0.0 替代，因为 CameraResult 中 circularity 是 float 类型
        )

        try:
            await asyncio.to_thread(self.plc_manager.write_camera_result, camera_num, camera_result)
            self.logger.debug(f"Result written to PLC for camera {camera_num}")
        except Exception as e:
            self.logger.error(f"Error writing result to PLC for camera {camera_num}: {str(e)}")

    async def update_camera_trigger_mode(self, camera_num: int, is_hardware_trigger: bool):
        try:
            await asyncio.to_thread(self.camera_manager.update_trigger_mode, camera_num, is_hardware_trigger)
            self.logger.info(f"Camera {camera_num} trigger mode updated to {'hardware' if is_hardware_trigger else 'software'}")
        except Exception as e:
            self.logger.error(f"Error updating trigger mode for camera {camera_num}: {str(e)}")

    async def set_camera_exposure(self, camera_num: int, exposure_time: float):
        try:
            await asyncio.to_thread(self.camera_manager.set_exposure, camera_num, exposure_time)
            self.logger.info(f"Camera {camera_num} exposure time set to {exposure_time}")
        except Exception as e:
            self.logger.error(f"Error setting exposure for camera {camera_num}: {str(e)}")

    async def process_combined_results(self):
        # 直接传递所有结果，包括 None 值
        combined_image = await asyncio.to_thread(
            self.image_processor.process_and_combine_images,
            self.camera_results
        )
        rgb565_image = self.image_processor.convert_to_rgb565(combined_image)
        self.image_processor.save_rgb565_with_header(rgb565_image, 'output_image.rgb565')
        # 保存合并后的图像
        # timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # output_filename = f'combined_output_{timestamp}.jpg'
        # await asyncio.to_thread(cv2.imwrite, output_filename, combined_image)
        # self.logger.info(f"Saved combined result image as {output_filename}")
        #
        # # 记录处理的摄像头情况
        # total_cameras = len(self.camera_results)
        # valid_cameras = sum(1 for result in self.camera_results.values() if result is not None)
        # self.logger.info(f"Processed images: {valid_cameras} valid out of {total_cameras} total cameras")

        # 重置结果
        # self.camera_results = {1: None, 2: None}

    def convert_settings_to_camera_info(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        camera_info = {
            'roi': [
                settings.get('roi_x', 0),
                settings.get('roi_y', 0),
                settings.get('roi_diameter', 0)
            ],
            'params': [
                settings.get('gray_lower', 0),
                settings.get('gray_upper', 255),
                settings.get('area_lower', 0),
                settings.get('area_upper', 0),
                settings.get('circularity_lower', 0),
                settings.get('circularity_upper', 1)
            ],
            'pixel_distance': settings.get('pixel_distance', 1)  # 添加pixel_distance
        }
        return camera_info

    async def update_system_status(self, status: SystemStatus):
        try:
            await asyncio.to_thread(self.plc_manager.write_system_status, status.value)
            self.logger.info(f"System status updated to {status.name}")
        except Exception as e:
            self.logger.error(f"Error updating system status: {str(e)}")

    async def handle_error(self, error_code: int):
        try:
            await asyncio.to_thread(self.plc_manager.write_error_code, error_code)
            await self.update_system_status(SystemStatus.ERROR)
            self.logger.error(f"System error occurred. Error code: {error_code}")
        except Exception as e:
            self.logger.error(f"Error handling system error: {str(e)}")

    async def apply_camera_settings(self, camera_num: int, settings: Dict[str, Any]):
        # 只应用曝光时间
        if 'exposure_time' in settings:
            current_exposure_time = self.camera_manager.get_exposure_time(camera_num)
            new_exposure_time = settings['exposure_time']
            if current_exposure_time != new_exposure_time and new_exposure_time != 0:
                await self.set_camera_exposure(camera_num, new_exposure_time)