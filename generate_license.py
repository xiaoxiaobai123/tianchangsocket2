# generate_license.py

import license_utils


def main():
    # 获取CPU ID
    cpu_id = license_utils.get_cpu_id()
    if not cpu_id:
        print("Failed to get CPU ID")
        return

    print(f"CPU ID: {cpu_id}")

    # 生成许可证
    if license_utils.generate_license(cpu_id):
        print("License generated successfully")

        # 验证许可证
        if license_utils.validate_license():
            print("License validation successful")
        else:
            print("License validation failed")
    else:
        print("Failed to generate license")


if __name__ == "__main__":
    main()