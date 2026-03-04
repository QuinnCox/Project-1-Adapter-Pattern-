from sensor_adapters import TemperatureSensor


class RetryDecorator(TemperatureSensor):
    def __init__(self, wrapped: TemperatureSensor, retries: int = 3):
        self._wrapped = wrapped
        self._retries = retries

    def open(self):
        if hasattr(self._wrapped, 'open'):
            self._wrapped.open()

    def close(self):
        if hasattr(self._wrapped, 'close'):
            self._wrapped.close()

    def get_temperature(self):
        # Initial attempt
        temp = self._wrapped.get_temperature()
        if temp is not None:
            return temp
            
        # Retry attempts
        for retry_num in range(self._retries):
            temp = self._wrapped.get_temperature()
            if temp is not None:
                return temp
                
        return None


class FallbackDecorator(TemperatureSensor):
    def __init__(self, sensors: list[TemperatureSensor]):
        if not sensors:
            raise ValueError("FallbackDecorator requires at least one sensor")
        self._sensors = sensors

    def open(self):
        for sensor in self._sensors:
            if hasattr(sensor, 'open'):
                try:
                    sensor.open()
                except Exception as e:
                    print(f"[FallbackDecorator] Warning: Failed to open sensor {type(sensor).__name__}: {e}")

    def close(self):
        for sensor in self._sensors:
            if hasattr(sensor, 'close'):
                try:
                    sensor.close()
                except Exception:
                    pass

    def get_temperature(self):
        for i, sensor in enumerate(self._sensors):
            temp = sensor.get_temperature()
            if temp is not None:
                if i > 0:
                    print(f"[FallbackDecorator] Using fallback sensor #{i + 1}")
                return temp
        return None