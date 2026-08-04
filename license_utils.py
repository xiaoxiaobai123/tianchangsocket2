# license_utils.py

import hashlib
import re
import os


def get_cpu_id():
    """
    获取嵌入式设备的稳定标识符
    """
    try:
        machine_info = []

        # 1. 获取CPU信息
        try:
            with open('/proc/cpuinfo', 'r') as f:
                cpuinfo = f.read()

            # 获取处理器型号
            processor = re.search(r'Hardware\s+:\s+(.*)', cpuinfo)
            if processor:
                machine_info.append(processor.group(1))

            # 获取序列号/revision
            revision = re.search(r'Revision\s+:\s+(.*)', cpuinfo)
            if revision:
                machine_info.append(revision.group(1))
        except Exception as e:
            print(f"Warning: Could not read CPU info: {e}")

        # 2. 获取MAC地址（通常比较稳定）
        try:
            # 获取默认网络接口
            with open('/proc/net/dev', 'r') as f:
                interfaces = [line.split(':')[0].strip() for line in f.readlines()[2:]]
                # 过滤掉lo接口和无线接口
                interfaces = [iface for iface in interfaces if iface != 'lo' and not iface.startswith('wlan')]

            if interfaces:
                # 使用第一个有效的网络接口
                interface = interfaces[0]
                mac_path = f'/sys/class/net/{interface}/address'
                if os.path.exists(mac_path):
                    with open(mac_path, 'r') as f:
                        mac = f.read().strip()
                        machine_info.append(mac)
        except Exception as e:
            print(f"Warning: Could not read MAC address: {e}")

        # 3. 获取设备型号信息
        try:
            with open('/proc/device-tree/model', 'r') as f:
                model = f.read().strip('\x00')
                machine_info.append(model)
        except Exception as e:
            print(f"Warning: Could not read device model: {e}")

        # 如果没有获取到任何信息，返回None
        if not machine_info:
            return None

        # 组合所有信息并生成哈希
        machine_id = ':'.join(machine_info)
        return hashlib.sha256(machine_id.encode()).hexdigest()

    except Exception as e:
        print(f"Error getting CPU ID: {e}")
        return None


def generate_license(cpu_id):
    """
    生成许可证
    """
    if not cpu_id:
        return False

    try:
        # 生成许可证密钥
        license_key = hashlib.sha256(cpu_id.encode()).hexdigest()

        # 保存许可证
        with open('license.key', 'w') as f:
            f.write(license_key)

        return True
    except Exception as e:
        print(f"Error generating license: {e}")
        return False


def validate_license():
    """
    验证许可证
    """
    try:
        # 读取许可证
        with open('license.key', 'r') as f:
            stored_license = f.read().strip()

        # 获取当前CPU ID
        current_cpu_id = get_cpu_id()
        if not current_cpu_id:
            return False

        # 计算预期的许可证
        expected_license = hashlib.sha256(current_cpu_id.encode()).hexdigest()

        return stored_license == expected_license
    except Exception as e:
        print(f"Error validating license: {e}")
        return False