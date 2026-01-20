from dh11_lgpio import DHT11 as DHT
import ads1110lgpio as ADS
import lgpio
import time

class SensorReader:
    def __init__(self, dht_pin=21):
        self.dht_sensor = DHT(dht_pin, lgpio.gpiochip_open(0))
        self.ads_sensor = ADS

    def read_dht11(self):
        result = self.dht_sensor.read()
        if result.is_valid():
            return result.temperature, result.humidity
        else:
            return None, None

    def read_ads1110(self):
        try:
            handle = lgpio.i2c_open(1, ADS.ADS1110_ADDR)
            lgpio.i2c_write_byte(handle, ADS.CONFIG_VALUE)
            time.sleep(0.1)
            count, data = lgpio.i2c_read_device(handle, 2)
            if count == 2:
                raw_value = (data[0] << 8) | data[1]
                if raw_value & 0x8000:
                    raw_value -= 1 << 16
                return raw_value
            else:
                return None
        finally:
            if handle >= 0:
                lgpio.i2c_close(handle)
def main():
    if __name__ == "__main__":
        sensor_reader = SensorReader(dht_pin=21)
        try:
            while True:
                temp, humidity = sensor_reader.read_dht11()
                if temp is not None and humidity is not None:
                    print(f'DHT11 temperature: {temp}°C, humidity percent: {humidity}%')
                ads_value = sensor_reader.read_ads1110()
                if ads_value is not None:
                    print(f'ADS1110: {ads_value:04x}')
                time.sleep(1)
        except KeyboardInterrupt:
            print("sensor connection ended.")