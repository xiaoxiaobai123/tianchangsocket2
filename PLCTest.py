import time
from plc_manager import PLCManager, CameraResult, SystemStatus, CameraTriggerStatus, ProductType

def test_plc_manager():
    # 初始化 PLCManager
    plc_manager = PLCManager('192.168.1.10')  # 使用实际的 PLC IP 地址
    
    try:
        print("开始测试 PLCManager...")

        # 测试相机设置读取
        for camera_num in [1, 2]:
            print(f"\n测试相机 {camera_num} 设置读取:")
            settings = plc_manager.read_camera_settings(camera_num)
            for key, value in settings.items():
                print(f"  {key}: {value}")

        # 测试相机结果写入
        print("\n测试相机结果写入:")
        test_result = CameraResult(x=150.0, y=250.3, angle=30.5, result=True, area=120075, circularity=0.95)
        plc_manager.write_camera_result(1, test_result)
        print("  相机1结果已写入")

        print("\n测试相机结果写入:")
        test_result = CameraResult(x=150.4, y=350.3, angle=32.5, result=True, area=220075, circularity=2.95)
        plc_manager.write_camera_result(2, test_result)
        print("  相机2结果已写入")

        # 测试 PLC 心跳读取
        print("\n测试 PLC 心跳读取:")
        plc_heartbeat = plc_manager.read_plc_heartbeat()
        print(f"  PLC 心跳值: {plc_heartbeat}")

        # 测试系统状态写入
        print("\n测试系统状态写入:")
        for status in SystemStatus:
            plc_manager.write_system_status(status)
            print(f"  已写入系统状态: {status.name}")
            time.sleep(1)  # 等待1秒，模拟状态变化

        # 测试错误代码写入
        print("\n测试错误代码写入:")
        error_codes = [0, 1, 5, 10]
        for code in error_codes:
            plc_manager.write_error_code(code)
            print(f"  已写入错误代码: {code}")
            time.sleep(1)  # 等待1秒，模拟错误代码变化

        # 测试系统心跳切换
        print("\n测试系统心跳切换:")
        for _ in range(5):
            plc_manager.toggle_system_heartbeat()
            print("  系统心跳已切换")
            time.sleep(1)  # 等待1秒，模拟心跳

        # 测试相机状态写入
        print("\n测试相机状态写入:")
        for camera_num in [1, 2]:
            for status in CameraTriggerStatus:
                plc_manager.write_camera_status(camera_num, status)
                print(f"  已写入相机 {camera_num} 状态: {status.name}")
                time.sleep(1)  # 等待1秒，模拟状态变化

        print("\n测试完成!")

    except Exception as e:
        print(f"测试过程中发生错误: {e}")
    
    finally:
        plc_manager.close()
        print("PLC 连接已关闭")

if __name__ == "__main__":
    test_plc_manager()