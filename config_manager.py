# config_manager.py

import json

class ConfigManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance.load_config()
        return cls._instance

    def load_config(self, config_file='config.json'):
        with open(config_file, 'r') as f:
            self.config = json.load(f)

    def get_camera_ip(self, camera_num):
        return self.config['cameras'][f'camera{camera_num}']['ip']

    def get_camera_host_lan(self, camera_num):
        return self.config['cameras'][f'camera{camera_num}']['host_lan']

    def get_plc_ip(self):
        return self.config['plc']['ip']

# 创建一个全局实例
config = ConfigManager()