from camera_manager import CameraManager
from config_manager import config
import time

def test_camera_manager():
    print("开始测试 CameraManager 功能")

    # 初始化 CameraManager
    camera_manager = CameraManager()
    print("CameraManager 初始化完成")

    # 测试获取相机
    for i in range(1, 3):
        camera = camera_manager.get_camera(i)
        if camera:
            print(f"成功获取相机 {i}")
            camera_info = camera_manager.get_camera_info(i)
            print(f"相机 {i} Device IP: {camera_info['device_ip']}")
            print(f"相机 {i} Net IP: {camera_info['net_ip']}")
        else:
            print(f"无法获取相机 {i}")

    # 测试设置曝光时间
    for i in range(1, 3):
        print(f"\n测试设置相机 {i} 的曝光时间")
        exposure_time = 100  # 假设设置为100ms
        success = camera_manager.set_exposure(i, exposure_time)
        if success:
            print(f"成功设置相机 {i} 的曝光时间为 {exposure_time}ms")
        else:
            print(f"设置相机 {i} 的曝光时间失败")

    # 测试设置触发模式
    for i in range(1, 3):
        print(f"\n测试设置相机 {i} 的触发模式")
        is_hardware_trigger = False  # 假设设置为软件触发
        success = camera_manager.update_trigger_mode(i, is_hardware_trigger)
        if success:
            print(f"成功设置相机 {i} 的触发模式为{'硬件' if is_hardware_trigger else '软件'}触发")
        else:
            print(f"设置相机 {i} 的触发模式失败")

    # 测试启动 grabbing
    for i in range(1, 3):
        print(f"\n测试启动相机 {i} 的 grabbing")
        success = camera_manager.start_grabbing(i)
        if success:
            print(f"成功启动相机 {i} 的 grabbing")
        else:
            print(f"启动相机 {i} 的 grabbing 失败")

    # 测试捕获图像
    for i in range(1, 3):
        print(f"\n测试相机 {i} 捕获图像")
        image = camera_manager.capture_image(i)
        if image is not None:
            print(f"成功从相机 {i} 捕获图像")
            # 这里可以添加图像保存或显示的代码
        else:
            print(f"从相机 {i} 捕获图像失败")

    # 测试停止 grabbing
    for i in range(1, 3):
        print(f"\n测试停止相机 {i} 的 grabbing")
        success = camera_manager.stop_grabbing(i)
        if success:
            print(f"成功停止相机 {i} 的 grabbing")
        else:
            print(f"停止相机 {i} 的 grabbing 失败")

    # 测试重新初始化相机
    for i in range(1, 3):
        print(f"\n测试重新初始化相机 {i}")
        success = camera_manager.reinitialize_camera(i)
        if success:
            print(f"成功重新初始化相机 {i}")
        else:
            print(f"重新初始化相机 {i} 失败")

    # 关闭所有相机
    print("\n关闭所有相机")
    camera_manager.close_all_cameras()
    print("所有相机已关闭")

if __name__ == "__main__":
    test_camera_manager()