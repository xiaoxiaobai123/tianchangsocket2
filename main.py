import asyncio
from task_manager import TaskManager
from plc_manager import PLCManager
from camera_manager import CameraManager
from image_processing import ImageProcessor
from config_manager import config
import log_config

async def main():
    logger = log_config.setup_logging()
    
    plc_manager = PLCManager(config.get_plc_ip())
    camera_manager = CameraManager()
    image_processor = ImageProcessor()
    
    task_manager = TaskManager(plc_manager, camera_manager, image_processor, config, logger)
    
    await task_manager.run()

if __name__ == "__main__":
    asyncio.run(main())