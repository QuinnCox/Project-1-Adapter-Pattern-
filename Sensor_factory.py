import json
from sensor_adapters import TemperatureSensor, DHT11Adapter, ADS1110Adapter
from Decorator import RetryDecorator, FallbackDecorator


class SensorFactory:
    @staticmethod
    def _build_single(config: dict) -> TemperatureSensor:
        mode = config.get("mode", "dht11").strip().lower()

        if mode == "ads":
            lm_type = config.get("lm_type", "LM35")
            vref = config.get("vref", 2.048)
            sensor = ADS1110Adapter(lm_type=lm_type, vref=vref)
            try:
                sensor.open()
                return sensor
            except Exception as e:
                return sensor

        elif mode == "dht11":
            pin = config.get("pin", 21)
            chip = config.get("chip", 0)
            try:
                sensor = DHT11Adapter(pin=pin, chip=chip)
                return sensor
            except Exception as e:
                return DHT11Adapter(pin=pin, chip=chip)

        else:
            raise ValueError(f"Unknown sensor mode: '{mode}'. Expected 'dht11' or 'ads'.")

    @staticmethod
    def create_sensor(config: dict) -> TemperatureSensor:
        # Build the primary sensor
        primary = SensorFactory._build_single(config)
        
        # Apply retry decorator if configured
        retries = config.get("retries", 3)
        if retries > 0:
            primary = RetryDecorator(primary, retries=retries)
            print(f"[SensorFactory] Applied RetryDecorator with {retries} retries")

        # Check for fallback sensors
        fallback_configs = config.get("fallbacks", [])
        if fallback_configs:
            # Build all sensors
            all_sensors = [primary]
            
            for fallback_config in fallback_configs:
                fallback_sensor = SensorFactory._build_single(fallback_config)
                fallback_retries = fallback_config.get("retries", retries)
                if fallback_retries > 0:
                    fallback_sensor = RetryDecorator(fallback_sensor, retries=fallback_retries)
                all_sensors.append(fallback_sensor)
            
            print(f"[SensorFactory] Created fallback chain with {len(all_sensors)} sensors")
            return FallbackDecorator(all_sensors)

        fallback_cfg = config.get("fallback")
        if fallback_cfg:
            secondary = SensorFactory._build_single(fallback_cfg)
            fallback_retries = fallback_cfg.get("retries", retries)
            if fallback_retries > 0:
                secondary = RetryDecorator(secondary, retries=fallback_retries)
            
            print("[SensorFactory] Created two-sensor fallback")
            return FallbackDecorator([primary, secondary])

        return primary

    @staticmethod
    def create_sensor_from_file(path: str) -> TemperatureSensor:
        """Convenience helper: load JSON config from *path* then call create_sensor."""
        with open(path, "r") as f:
            config = json.load(f)
        return SensorFactory.create_sensor(config)