from sensor_adapters import TemperatureSensor


class RetryDecorator(TemperatureSensor):
    def __init__(self, wrapped, retries=3):
        self._wrapped = wrapped
        self._retries = retries

    def open(self):
        if hasattr(self._wrapped, 'open'):
            self._wrapped.open()

    def close(self):
        if hasattr(self._wrapped, 'close'):
            self._wrapped.close()

    def get_temperature(self):
        for _ in range(self._retries + 1):
            temp = self._wrapped.get_temperature()
            if temp is not None:
                return temp
        return None


class FallbackDecorator(TemperatureSensor):
    def __init__(self, sensors):
        if not sensors:
            raise ValueError("FallbackDecorator requires at least one sensor")
        self._sensors = sensors

    def open(self):
        for sensor in self._sensors:
            if hasattr(sensor, 'open'):
                try:
                    sensor.open()
                except Exception as e:
                    print(f"Warning: could not open {type(sensor).__name__}: {e}")

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
                    print(f"Using fallback sensor #{i + 1}")
                return temp
        return None
