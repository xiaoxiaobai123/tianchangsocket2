import asyncio

from config_manager import config
from camera_base import CameraBase
import log_config
import threading

logger = log_config.setup_logging()

class CameraManager:
    def __init__(self):
        self.cameras = {}
        self.camera_locks = {}
        self._initialize_cameras()

    def _initialize_cameras(self):
        for i in range(1, 3):  # 假设我们有两个相机
            self.camera_locks[i] = threading.Lock()
            device_ip = config.get_camera_ip(i)
            net_ip = config.get_camera_host_lan(i)
            try:
                camera = CameraBase(device_ip, net_ip)
                if camera.init_camera():
                    self.cameras[i] = camera

                    logger.info(f"Camera {i} initialized successfully.")
                    self.start_grabbing(i)
                else:
                    logger.error(f"Failed to initialize Camera {i}")
            except Exception as e:
                logger.error(f"Error creating Camera {i}: {str(e)}")

    def get_camera(self, camera_num):
        return self.cameras.get(camera_num)

    def get_camera_info(self, camera_num):
        camera = self.get_camera(camera_num)
        if camera:
            return {
                "device_ip": camera.device_ip,
                "net_ip": camera.net_ip
            }
        return None   
    def capture_image(self, camera_num, is_hardware_trigger=False, max_retries=3):
        camera = self.get_camera(camera_num)
        if camera is None:
            logger.error(f"Camera {camera_num} not found.")
            return None

        with self.camera_locks[camera_num]:
            try:
                image = camera.capture_image(is_hardware_trigger=is_hardware_trigger, max_retries=max_retries)
                if image is not None:
                    logger.info(f"Image captured from Camera {camera_num}.")
                    return image
                else:
                    logger.error(f"Failed to capture image from Camera {camera_num}")
                    return None
            except Exception as e:
                logger.error(f"Error capturing image from Camera {camera_num}: {str(e)}")
                return None

    def set_exposure(self, camera_num, exposure_time):
        camera = self.get_camera(camera_num)
        if camera is None:
            logger.error(f"Camera {camera_num} not found.")
            return False

        with self.camera_locks[camera_num]:
            try:
                if camera.write_exposure_time(exposure_time):
                    logger.info(f"Exposure time set to {exposure_time} for Camera {camera_num}.")
                    return True
                else:
                    logger.error(f"Failed to set exposure time for Camera {camera_num}")
                    return False
            except Exception as e:
                logger.error(f"Error setting exposure time for Camera {camera_num}: {str(e)}")
                return False

    def start_grabbing(self, camera_num):
        camera = self.get_camera(camera_num)
        if camera is None:
            logger.error(f"Camera {camera_num} not found.")
            return False

        # with self.camera_locks[camera_num]:
        try:
            if camera.start_grabbing():
                logger.info(f"Started grabbing for Camera {camera_num}.")
                return True
            else:
                logger.error(f"Failed to start grabbing for Camera {camera_num}")
                return False
        except Exception as e:
            logger.error(f"Error starting grabbing for Camera {camera_num}: {str(e)}")
            return False

    def stop_grabbing(self, camera_num):
        camera = self.get_camera(camera_num)
        if camera is None:
            logger.error(f"Camera {camera_num} not found.")
            return False

        with self.camera_locks[camera_num]:
            try:
                if camera.stop_grabbing():
                    logger.info(f"Stopped grabbing for Camera {camera_num}.")
                    return True
                else:
                    logger.error(f"Failed to stop grabbing for Camera {camera_num}")
                    return False
            except Exception as e:
                logger.error(f"Error stopping grabbing for Camera {camera_num}: {str(e)}")
                return False
            
    def update_trigger_mode(self, camera_num, is_hardware_trigger):
        camera = self.get_camera(camera_num)
        if camera is None:
            logger.error(f"Camera {camera_num} not found.")
            return False

        with self.camera_locks[camera_num]:
            try:
                if camera.update_trigger_mode(is_hardware_trigger):
                    logger.info(f"Trigger mode updated for Camera {camera_num}.")
                    return True
                else:
                    logger.error(f"Failed to update trigger mode for Camera {camera_num}")
                    return False
            except Exception as e:
                logger.error(f"Error updating trigger mode for Camera {camera_num}: {str(e)}")
                return False

    def reinitialize_camera(self, camera_num):
        # with self.camera_locks[camera_num]:
        try:
            old_camera = self.cameras.pop(camera_num, None)
            # if old_camera:
            #     old_camera.close_camera()
            camera_ip = config.get_camera_ip(camera_num)
            host_lan = config.get_camera_host_lan(camera_num)
            new_camera = CameraBase(camera_ip, host_lan)
            if new_camera.init_camera():
                self.cameras[camera_num] = new_camera
                # self.camera_locks[camera_num] = threading.Lock()
                logger.info(f"Camera {camera_num} reinitialized successfully.")
                self.start_grabbing(camera_num)
                return True
            else:
                logger.error(f"Failed to reinitialize Camera {camera_num}")
                return False
        except Exception as e:
            logger.error(f"Error reinitializing Camera {camera_num}: {str(e)}")
            return False
    #   initialize_camera(self, camera_num):
    #     device_ip = config.get_camera_ip(camera_num)
    #     net_ip = config.get_camera_host_lan(camera_num)
    #     try:
    #         # 关闭旧相机（如果存在）
    #         old_camera = self.cameras.pop(camera_num, None)
    #         if old_camera:
    #             old_camera.close_camera()
    #
    #         # 创建新相机实例
    #         new_camera = CameraBase(device_ip, net_ip)
    #         if new_camera.init_camera():
    #             self.cameras[camera_num] = new_camera
    #             # 如果不存在锁，创建一个新的锁
    #             if camera_num not in self.camera_locks:
    #                 self.camera_locks[camera_num] = threading.Lock()
    #             logger.info(f"Camera {camera_num} reinitialized successfully.")
    #             # 重新开始抓取
    #             self.start_grabbing(camera_num)
    #             return True
    #         else:
    #             logger.error(f"Failed to reinitialize Camera {camera_num}")
    #             return False
    #     except Exception as e:
    #         logger.error(f"Error reinitializing Camera {camera_num}: {str(e)}")
    #         return False
    def close_all_cameras(self):
        for camera_num, camera in self.cameras.items():
            with self.camera_locks[camera_num]:
                try:
                    camera.close_camera()
                    logger.info(f"Camera {camera_num} closed successfully.")
                except Exception as e:
                    logger.error(f"Failed to close Camera {camera_num}: {str(e)}")
        self.cameras.clear()
        self.camera_locks.clear()
    def get_trigger_source(self, camera_num):
        camera = self.get_camera(camera_num)
        if camera is None:
            logger.error(f"Camera {camera_num} not found.")
            return None

        with self.camera_locks[camera_num]:
            try:
                trigger_source = camera.get_trigger_source()
                if trigger_source is not None:
                    # logger.info(f"Trigger mode for Camera {camera_num}: {trigger_source}")
                    return trigger_source
                else:
                    logger.error(f"Failed to get trigger source for Camera {camera_num}")
                    return None
            except Exception as e:
                logger.error(f"Error getting trigger source for Camera {camera_num}: {str(e)}")
                return None

    def get_exposure_time(self, camera_num):
        with self.camera_locks[camera_num]:
            camera = self.get_camera(camera_num)

            # 如果相机未找到，尝试重新初始化
            if camera is None:
                logger.error(f"Camera {camera_num} not found. Attempting to reinitialize.")
                if not self.reinitialize_camera(camera_num):
                    logger.error(f"Failed to reinitialize Camera {camera_num}")
                    return None
                camera = self.get_camera(camera_num)

            # 尝试获取曝光时间
            try:
                exposure_time = camera.get_exposure_time()
                if exposure_time is not None:
                    return exposure_time
            except Exception as e:
                logger.error(f"Error getting exposure time for Camera {camera_num}: {str(e)}")

            # 如果获取失败且之前没有重新初始化过，尝试重新初始化
            if camera is not None:
                logger.info(f"Failed to get exposure time. Attempting to reinitialize Camera {camera_num}")
                if self.reinitialize_camera(camera_num):
                    camera = self.get_camera(camera_num)
                    try:
                        exposure_time = camera.get_exposure_time()
                        if exposure_time is not None:
                            return exposure_time
                    except Exception as e:
                        logger.error(
                            f"Error getting exposure time after reinitialization for Camera {camera_num}: {str(e)}")
                else:
                    logger.error(f"Failed to reinitialize Camera {camera_num}")

            logger.error(f"Failed to get exposure time from Camera {camera_num}")
            return None