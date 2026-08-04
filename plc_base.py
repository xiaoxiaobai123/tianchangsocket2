from pyModbusTCP.client import ModbusClient
import log_config
from threading import Lock
logger = log_config.setup_logging()
class PLCBase:
    """Modbus TCP communication class for PLC using pymodbus."""
    def __init__(self, plc_ip: str, port: int = 502):
        self.plc_ip = plc_ip
        self.port = port
        self.client = None
        self.connected = False
        self.lock = Lock()
        self._connect()
    def _connect(self):
        try:
            self.client = ModbusClient(host=self.plc_ip, port=self.port, auto_open=True, timeout=1)
            self.connected = self.client.open()
            if self.connected:
                logger.info(f"Successfully connected to PLC at address {self.plc_ip}")
                print(f"PLC communication established {self.plc_ip}")
            else:
                logger.error(f"Failed to connect to PLC at address {self.plc_ip}")
                print("Failed to establish PLC communication")
        except Exception as e:
            logger.exception(f"Error connecting to PLC: {e}")
            self.connected = False

    def _ensure_connection(self):
        if not self.connected:
            logger.info("Connection lost. Attempting to reconnect...")
            self._connect()
        return self.connected

    def read_status(self, address, count=1):
        with self.lock:
            if not self._ensure_connection():
                logger.error("Failed to read status: PLC not connected")
                return None

            try:
                if count <= 125:
                    registers = self.client.read_holding_registers(address, count)
                    if registers is not None:
                        return registers[0] if count == 1 else registers
                    else:
                        logger.error(f"Failed to read status from PLC at address {address} with count {count}")
                        return None
                else:
                    max_registers = 125
                    filedata = []
                    start_address = address
                    remaining_count = count

                    while remaining_count > 0:
                        read_count = min(max_registers, remaining_count)
                        registers = self.client.read_holding_registers(start_address, read_count)
                        if registers is None:
                            logger.error(
                                f"Failed to read status from PLC at address {start_address} with count {read_count}")
                            return None
                        filedata.extend(registers)
                        start_address += read_count
                        remaining_count -= read_count

                    return filedata[0] if count == 1 else filedata

            except Exception as e:
                logger.exception(f"Error reading status from PLC: {e}")
                self.connected = False
                return None

    def write_status(self, address, value):
        with self.lock:
            if not self._ensure_connection():
                logger.error("Failed to write status: PLC not connected")
                return False

            try:
                if address in [124, 125, 126]:
                    if not (-32768 <= value <= 32767):
                        logger.exception(
                            f"Error: reg_value out of range for signed register (valid from -32768 to 32767): {value}")
                        return False
                    if value < 0:
                        value = 65536 + value
                else:
                    if not (0 <= value <= 65535):
                        logger.exception(
                            f"Error: reg_value out of range for unsigned register (valid from 0 to 65535): {value}")
                        return False

                result = self.client.write_single_register(address, value)
                return result
            except Exception as e:
                logger.exception(f"Error writing status to PLC: {e}")
                self.connected = False
                return False

    def write_multiple_registers(self, address, values):
        with self.lock:
            if not self._ensure_connection():
                logger.error("Failed to write multiple registers: PLC not connected")
                return False

            try:
                max_registers = 123
                start_address = address
                remaining_values = values

                while remaining_values:
                    write_values = remaining_values[:max_registers]
                    processed_values = []
                    for value in write_values:
                        if value < 0:
                            value = 65536 + value
                        processed_values.append(value)

                    result = self.client.write_multiple_registers(start_address, processed_values)
                    if not result:
                        logger.error(
                            f"Failed to write values to PLC at address {start_address} with values {processed_values}")
                        return False

                    start_address += len(write_values)
                    remaining_values = remaining_values[max_registers:]

                return True
            except Exception as e:
                logger.exception(f"Error writing multiple registers to PLC: {e}")
                self.connected = False
                return False

    def close(self):
        """
        Close the Modbus client connection.
        """
        if self.client.is_open:  # 注意这里没有括号
            self.client.close()
            logger.info("PLC connection closed")
        else:
            logger.warning("PLC connection already closed")