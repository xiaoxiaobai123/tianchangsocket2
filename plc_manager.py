from enum import Enum
from typing import Dict, Any, NamedTuple
from plc_base import PLCBase
import struct
import threading
class CameraStatus(Enum):
    IDLE = 0
    READING_DATA = 1
    PROCESSING_DATA = 2
    TASK_COMPLETED = 3
    START_TASK = 10
    START_LOOP = 11

class ProductType(Enum):
    NONE = 0
    OUTER_OBJECT = 1
    INNER_OBJECT = 2

class SystemStatus(Enum):
    STARTING = 0
    IDLE = 1
    PROCESSING = 2
    ERROR = 3

class CameraTriggerStatus(Enum):
    DISCONNECTED = 0
    HARDWARE_TRIGGER = 1
    SOFTWARE_TRIGGER = 2

class ROI(NamedTuple):
    x: int
    y: int
    diameter: int

class CameraResult(NamedTuple):
    x: float
    y: float
    angle: float
    result: bool
    area: int
    circularity: float
class Endian(Enum):
    LITTLE = 'little'
    BIG = 'big'
class PLCManager:
    def __init__(self, ip: str, port: int = 502,endian: Endian = Endian.LITTLE):
        self.plc = PLCBase(ip, port)
        self.endian = endian
        self._init_registers()

        self.lock = threading.Lock()
    def _init_registers(self):
        self.camera_registers = {
            1: {
                'read': {
                    'status': 1, 'trigger': 10, 'exposure': 11, 'pixel_distance': 12,
                    'product_type': 14, 'gray_upper': 15, 'gray_lower': 16,
                    'area_upper': 17, 'area_lower': 19, 'circularity_upper': 21, 'circularity_lower': 23,
                    'roi_x': 25, 'roi_y': 26, 'roi_diameter': 27
                },
                'write': {
                    'output_x': 70,
                    'output_y': 74,
                    'output_angle': 78,
                    'result': 82,
                    'area': 83,
                    'circularity': 85
                }
            },
            2: {
                'read': {
                    'status': 2, 'trigger': 30, 'exposure': 31, 'pixel_distance': 32,
                    'product_type': 34, 'gray_upper': 35, 'gray_lower': 36,
                    'area_upper': 37, 'area_lower': 39, 'circularity_upper': 41, 'circularity_lower': 43,
                    'roi_x': 45, 'roi_y': 46, 'roi_diameter': 47
                },
                'write': {
                    'output_x': 90,  # 假设相机2的写入寄存器从170开始
                    'output_y': 94,
                    'output_angle': 98,
                    'result': 102,
                    'area': 103,
                    'circularity': 105
                }
            }
        }
        self.system_registers = {
            'plc_heartbeat': 50,
            'system_status': 120,
            'error_code': 121,
            'system_heartbeat': 122,
            'camera1_trigger_status': 123,
            'camera2_trigger_status': 124,
            'camera1_status': 1,
            'camera2_status': 2
        }

    def read_camera_settings(self, camera_num: int) -> Dict[str, Any]:
        with self.lock:
            registers = self.camera_registers[camera_num]['read']
            data = {}
            for key, register in registers.items():
                if key in ['area_upper', 'area_lower']:
                    data[key] = self._read_uint32(register)
                elif key in ['circularity_upper', 'circularity_lower', 'pixel_distance']:
                    data[key] = self._read_float(register)
                else:
                    data[key] = self.plc.read_status(register)
            return self._parse_camera_settings(data)

    def _parse_camera_settings(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'status': CameraStatus(data['status']),
            'trigger_mode': CameraTriggerStatus(data['trigger']),
            'exposure_time': data['exposure'],
            'pixel_distance': data['pixel_distance'],
            'product_type': ProductType(data['product_type']),
            'gray_upper': data['gray_upper'],
            'gray_lower': data['gray_lower'],
            'area_upper': data['area_upper'],
            'area_lower': data['area_lower'],
            'circularity_upper': data['circularity_upper'],
            'circularity_lower': data['circularity_lower'],
            'roi_x': data['roi_x'],
            'roi_y': data['roi_y'],
            'roi_diameter': data['roi_diameter']
        }

    def _write_double(self, register: int, value: float) -> None:
        # 将 double 转换为 IEEE 754 格式的字节（小端序）
        packed = struct.pack('<d', value)

        # 将字节转换为 16 位整数列表
        words = [
            (packed[1] << 8) | packed[0],
            (packed[3] << 8) | packed[2],
            (packed[5] << 8) | packed[4],
            (packed[7] << 8) | packed[6]
        ]

        # 将每个 16 位整数写入对应的 D 寄存器
        for i, word in enumerate(words):
            self.plc.write_status(register + i, word)

    def write_camera_result(self, camera_num: int, result: CameraResult) -> None:
        with self.lock:
            registers = self.camera_registers[camera_num]['write']
            self._write_double(registers['output_x'], result.x)
            self._write_double(registers['output_y'], result.y)
            self._write_double(registers['output_angle'], result.angle)
            self.plc.write_status(registers['result'], 1 if result.result else 2)
            self._write_uint32(registers['area'], result.area)
            self._write_float(registers['circularity'], result.circularity)

    def _write_uint32(self, register: int, value: int) -> None:
        self.plc.write_status(register, value & 0xFFFF)
        self.plc.write_status(register + 1, (value >> 16) & 0xFFFF)

    def _write_float(self, register: int, value: float) -> None:
        packed = struct.pack('<f', value)
        self.plc.write_status(register, (packed[1] << 8) | packed[0])
        self.plc.write_status(register + 1, (packed[3] << 8) | packed[2])
     

    def read_plc_heartbeat(self) -> int:
        return self.plc.read_status(self.system_registers['plc_heartbeat'])

    def write_system_status(self, status: SystemStatus) -> None:
        self.plc.write_status(self.system_registers['system_status'], status.value)

    def write_error_code(self, error_code: int) -> None:
        self.plc.write_status(self.system_registers['error_code'], error_code)

    def write_system_heartbeat(self, value: int) -> None:
        self.plc.write_status(self.system_registers['system_heartbeat'], value)

    def write_camera_status(self, camera_num: int, status: CameraTriggerStatus) -> None:
        with self.lock:
            register = self.system_registers[f'camera{camera_num}_status']
            self.plc.write_status(register, status.value)

    def toggle_system_heartbeat(self) -> None:
        current_heartbeat = self.plc.read_status(self.system_registers['system_heartbeat'])
        self.write_system_heartbeat(1 - current_heartbeat)

    def _read_uint32(self, register: int) -> int:
        low_word = self.plc.read_status(register)
        high_word = self.plc.read_status(register + 1)
        if self.endian == Endian.LITTLE:
            return (high_word << 16) | low_word
        else:  # BIG endian
            return (low_word << 16) | high_word

 

    def _read_float(self, register: int) -> float:
        value = self._read_uint32(register)
        return struct.unpack('!f', struct.pack('!I', value))[0]


    def close(self) -> None:
        self.plc.close()