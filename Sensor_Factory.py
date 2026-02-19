import json
from sensor_adapters import TemperatureSensor, DHT11Adapter, ADS1110Adapter


class FallbackTemperatureSensor(TemperatureSensor):

    def __init__(self, primary: TemperatureSensor, secondary: TemperatureSensor):
        self.primary = primary
        self.secondary = secondary

    def get_temperature(self):
        value = self.primary.get_temperature()
        if value is not None:
            return value
        print("[FallbackTemperatureSensor] Primary sensor failed, trying secondary...")
        return self.secondary.get_temperature()

    def close(self):
        for sensor in (self.primary, self.secondary):
            if hasattr(sensor, "close"):
                try:
                    sensor.close()
                except Exception:
                    pass


class SensorFactory:
    @staticmethod
    def _build_single(config: dict) -> TemperatureSensor:
        mode = config.get("mode", "dht11").strip().lower()

        if mode == "ads":
            lm_type = config.get("lm_type", "LM35")
            vref = config.get("vref", 2.048)
            sensor = ADS1110Adapter(lm_type=lm_type, vref=vref)
            sensor.open()
            return sensor

        elif mode == "dht11":
            pin = config.get("pin", 21)
            chip = config.get("chip", 0)
            return DHT11Adapter(pin=pin, chip=chip)

        else:
            raise ValueError(f"Unknown sensor mode: '{mode}'. Expected 'dht11' or 'ads'.")

    @staticmethod
    def create_sensor(config: dict) -> TemperatureSensor:

        primary = SensorFactory._build_single(config)

        fallback_cfg = config.get("fallback")
        if fallback_cfg:
            secondary = SensorFactory._build_single(fallback_cfg)
            return FallbackTemperatureSensor(primary, secondary)

        return primary

    @staticmethod
    def create_sensor_from_file(path: str) -> TemperatureSensor:
        with open(path, "r") as f:
            config = json.load(f)
        return SensorFactory.create_sensor(config)