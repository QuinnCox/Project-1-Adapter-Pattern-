import time
import sys

from sensor_adapters import DHT11Adapter, ADS1110Adapter
# Choose sensor from command line:
#   python3 Base.py dht
#   python3 Base.py ads
# Defaults to dht

def main():
    mode = "dht"
    if len(sys.argv) >= 2:
        mode = sys.argv[1].strip().lower()

    sensor = None

    try:
        if mode == "ads":
            sensor = ADS1110Adapter(lm_type="LM35")
            sensor.open()
            label = "ADS1110+LM3x"
        else:
            sensor = DHT11Adapter(pin=21, chip=0)
            label = "DHT11"

        while True:
            temp_c = sensor.get_temperature()
            if temp_c is None:
                print(f"{label}: read failed")
            else:
                temp_f = temp_c * 9.0 / 5.0 + 32.0
                print(f"{label}: {temp_c:.1f} Â°C / {temp_f:.1f} Â°F")

            time.sleep(1)

    except KeyboardInterrupt:
        print("Sensor reading stopped.")

    finally:
        if sensor is not None and hasattr(sensor, "close"):
            try:
                sensor.close()
            except Exception:
                pass


if __name__ == "__main__":
    main()
