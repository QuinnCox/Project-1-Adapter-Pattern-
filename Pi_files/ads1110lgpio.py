import lgpio
import time

# I2C address of ADS1110
ADS1110_ADDR = 0x48

# Value to write to the configuration register
CONFIG_VALUE = 0b0_00_0_11_00

class ADS1110Driver:
    def __init__(self, bus=1, addr=ADS1110_ADDR, config=CONFIG_VALUE, conv_delay=0.1):
        self.bus = bus
        self.addr = addr
        self.config = config
        self.conv_delay = conv_delay
        self.handle = -1

    def open(self):
        self.handle = lgpio.i2c_open(self.bus, self.addr)
        rc = lgpio.i2c_write_byte(self.handle, self.config)
        if rc != 0:
            self.close()
            raise IOError(f"ADS1110 config write failed (code={rc})")
        time.sleep(self.conv_delay)

    def close(self):
        if self.handle >= 0:
            lgpio.i2c_close(self.handle)
            self.handle = -1

    def read_raw(self):
        if self.handle < 0:
            raise RuntimeError("ADS1110Driver not opened. Call open() first.")

        count, data = lgpio.i2c_read_device(self.handle, 2)
        if count != 2:
            return None

        raw_value = (data[0] << 8) | data[1]
        if raw_value & 0x8000:
            raw_value -= 1 << 16
        return raw_value
