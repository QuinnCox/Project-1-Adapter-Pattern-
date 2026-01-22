from abc import ABC, abstractmethod
import lgpio

from dh11_lgpio import DHT11
import ads1110lgpio


class TemperatureSensor(ABC):
    @abstractmethod
    def get_temperature(self):
        raise NotImplementedError


class DHT11Adapter(TemperatureSensor):
    def __init__(self, pin=21, chip=0):
        self.pin = pin
        self.chip = chip
        self.gpio = lgpio.gpiochip_open(self.chip)
        self.sensor = DHT11(self.pin, self.gpio)

    def get_temperature(self):
        result = self.sensor.read()
        if result.is_valid():
            return float(result.temperature)
        return None

    def close(self):
        if self.gpio is not None:
            lgpio.gpiochip_close(self.gpio)
            self.gpio = None


class ADS1110Adapter(TemperatureSensor):  
    def __init__(self, lm_type="LM35", vref=2.048, full_scale_counts=32768):
        self.lm_type = lm_type.upper()
        self.vref = float(vref)
        self.full_scale_counts = int(full_scale_counts)

        self.driver = ads1110lgpio.ADS1110Driver()

    def open(self):
        self.driver.open()

    def close(self):
        self.driver.close()

    def _raw_to_voltage(self, raw):
        return (raw / float(self.full_scale_counts)) * self.vref

    def get_temperature(self):
        raw = self.driver.read_raw()
        if raw is None:
            return None

        voltage = self._raw_to_voltage(raw)
        mv = voltage * 1000.0
        degrees = mv / 10.0

        if self.lm_type == "LM35":
            return float(degrees)

        return None
