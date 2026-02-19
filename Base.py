import time
import sys
import json

from Sensor_Factory import SensorFactory
from sensor_adapters import TemperatureSensor


DEFAULT_CONFIGS = {
    "dht": {
        "mode": "dht11",
        "pin": 21,
        "chip": 0,
    },
    "ads": {
        "mode": "ads",
        "lm_type": "LM35",
    },
}

LABELS = {
    "dht": "DHT11",
    "ads": "ADS1110+LM3x",
}


def load_config(path: str | None, mode: str) -> dict:
    """
    Load configuration from a JSON file if *path* is given,
    otherwise fall back to the built-in default for *mode*.
    """
    if path:
        with open(path, "r") as f:
            return json.load(f)
    return DEFAULT_CONFIGS.get(mode, DEFAULT_CONFIGS["dht"])


def main():

    mode = "dht"
    config_path = None

    args = sys.argv[1:]
    if "--config" in args:
        idx = args.index("--config")
        config_path = args[idx + 1]
    elif args:
        mode = args[0].strip().lower()

    config = load_config(config_path, mode)

    label = LABELS.get(config.get("mode", mode), config.get("mode", mode).upper())

    sensor: TemperatureSensor = SensorFactory.create_sensor(config)

    try:
        while True:
            temp_c = sensor.get_temperature()
            if temp_c is None:
                print(f"{label}: read failed")
            else:
                temp_f = temp_c * 9.0 / 5.0 + 32.0
                print(f"{label}: {temp_c:.1f} °C / {temp_f:.1f} °F")

            time.sleep(1)

    except KeyboardInterrupt:
        print("\nSensor reading stopped.")

    finally:
        if hasattr(sensor, "close"):
            try:
                sensor.close()
            except Exception:
                pass


if __name__ == "__main__":
    main()