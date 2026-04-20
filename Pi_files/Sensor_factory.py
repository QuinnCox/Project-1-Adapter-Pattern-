import json
from sensor_adapters import TemperatureSensor, DHT11Adapter, ADS1110Adapter
from Decorator import RetryDecorator, FallbackDecorator


class SensorFactory:
    @staticmethod
    def _build_single(config):
        mode = config.get("mode", "dht11").strip().lower()

        if mode == "ads":
            sensor = ADS1110Adapter(
                lm_type=config.get("lm_type", "LM35"),
                vref=config.get("vref", 2.048)
            )
            sensor.open()
            return sensor

        elif mode == "dht11":
            return DHT11Adapter(
                pin=config.get("pin", 21),
                chip=config.get("chip", 0)
            )

        else:
            raise ValueError(f"Unknown sensor mode: '{mode}'")

    @staticmethod
    def create_sensor(config):
        primary = SensorFactory._build_single(config)

        retries = config.get("retries", 3)
        if retries > 0:
            primary = RetryDecorator(primary, retries=retries)

        fallback_configs = config.get("fallbacks", [])
        if fallback_configs:
            all_sensors = [primary]
            for fb_cfg in fallback_configs:
                fb_sensor = SensorFactory._build_single(fb_cfg)
                fb_retries = fb_cfg.get("retries", retries)
                if fb_retries > 0:
                    fb_sensor = RetryDecorator(fb_sensor, retries=fb_retries)
                all_sensors.append(fb_sensor)
            return FallbackDecorator(all_sensors)

        fallback_cfg = config.get("fallback")
        if fallback_cfg:
            secondary = SensorFactory._build_single(fallback_cfg)
            fb_retries = fallback_cfg.get("retries", retries)
            if fb_retries > 0:
                secondary = RetryDecorator(secondary, retries=fb_retries)
            return FallbackDecorator([primary, secondary])

        return primary

    @staticmethod
    def create_sensor_from_file(path):
        with open(path, "r") as f:
            config = json.load(f)
        return SensorFactory.create_sensor(config)
