# -*- coding: utf-8 -*-
import socket
import json
import time
import argparse
from datetime import datetime

from Sensor_factory import SensorFactory
from Decorator import RetryDecorator, FallbackDecorator


class SensorDataDTO:
    def __init__(self, origin, temperature, unit="C", timestamp=None):
        self.origin = origin
        self.temperature = temperature
        self.unit = unit
        self.timestamp = timestamp or datetime.now().isoformat()

    def to_dict(self):
        return {
            "origin": self.origin,
            "payload": {"temp": self.temperature, "unit": self.unit},
            "timestamp": self.timestamp
        }

    def to_json(self):
        return json.dumps(self.to_dict())


class TemperatureFilter:
    def __init__(self, threshold=0.5):
        self.threshold = threshold
        self.last_sent_temp = None

    def should_send(self, current_temp):
        if self.last_sent_temp is None:
            self.last_sent_temp = current_temp
            return True
        if abs(current_temp - self.last_sent_temp) >= self.threshold:
            self.last_sent_temp = current_temp
            return True
        return False


class WebServerObserver:
    def __init__(self, web_host="localhost", web_port=8888):
        self.web_host = web_host
        self.web_port = web_port
        self.socket = None
        self.connected = False

    def connect(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10)
            self.socket.connect((self.web_host, self.web_port))
            self.connected = True
            print(f"Connected to {self.web_host}:{self.web_port}")
            return True
        except Exception as e:
            print(f"Failed to connect: {e}")
            return False

    def send_data(self, sensor_data):
        if not self.connected:
            if not self.connect():
                return False
        try:
            self.socket.send((sensor_data.to_json() + "\n").encode("utf-8"))
            response = self.socket.recv(1024)
            ack = json.loads(response.decode("utf-8"))
            if ack.get("status") == "received":
                print(f"Sent: {sensor_data.temperature:.1f}C [OK]")
                return True
            return False
        except Exception as e:
            print(f"Send failed: {e}")
            self.connected = False
            if self.socket:
                self.socket.close()
                self.socket = None
            return False

    def disconnect(self):
        if self.socket:
            try:
                self.socket.close()
            except Exception:
                pass
        self.connected = False
        print("Disconnected from web server")


class SensorSubject:
    def __init__(self, pi_id, sensor_config):
        self.pi_id = pi_id
        self.sensor = SensorFactory.create_sensor(sensor_config)
        self.filter_strategy = TemperatureFilter(threshold=0.5)
        self.observers = []
        self.readings_taken = 0
        self.readings_sent = 0
        self.readings_filtered = 0
        print(f"Initialized sensor subject for {pi_id}")

    def attach_observer(self, observer):
        if observer not in self.observers:
            self.observers.append(observer)

    def detach_observer(self, observer):
        if observer in self.observers:
            self.observers.remove(observer)

    def notify_observers(self, sensor_data):
        for observer in self.observers:
            try:
                observer.send_data(sensor_data)
            except Exception as e:
                print(f"Error notifying observer: {e}")

    def take_reading(self):
        self.readings_taken += 1
        try:
            temp = self.sensor.get_temperature()
            if temp is not None:
                print(f"Reading: {temp:.1f}C")
            else:
                print("Sensor read failed")
            return temp
        except Exception as e:
            print(f"Sensor error: {e}")
            return None

    def process_reading(self, temperature):
        if self.filter_strategy.should_send(temperature):
            sensor_data = SensorDataDTO(origin=self.pi_id, temperature=temperature, unit="C")
            self.notify_observers(sensor_data)
            self.readings_sent += 1
            return True
        print(f"Filtered: {temperature:.1f}C")
        self.readings_filtered += 1
        return False

    def start_monitoring(self, interval=2.0):
        print(f"Monitoring started (interval: {interval}s), press Ctrl+C to stop")
        try:
            while True:
                temp = self.take_reading()
                if temp is not None:
                    self.process_reading(temp)
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\nMonitoring stopped.")

    def get_statistics(self):
        rate = (self.readings_filtered / self.readings_taken * 100) if self.readings_taken > 0 else 0
        return {
            "pi_id": self.pi_id,
            "readings_taken": self.readings_taken,
            "readings_sent": self.readings_sent,
            "readings_filtered": self.readings_filtered,
            "filter_rate": f"{rate:.1f}%"
        }


def get_sensor_config(pi_id):
    if "TeamA" in pi_id:
        return {"mode": "dht11", "pin": 21, "chip": 0, "retries": 3}
    elif "TeamB" in pi_id:
        return {"mode": "ads", "lm_type": "LM35", "retries": 2,
                "fallback": {"mode": "dht11", "pin": 22, "retries": 1}}
    return {"mode": "dht11", "pin": 21, "chip": 0, "retries": 3}


def main():
    parser = argparse.ArgumentParser(description="Pi Sensor Client")
    parser.add_argument("pi_id", nargs="?", default="Pi_TeamA")
    parser.add_argument("--web-host", default="192.168.1.100")
    parser.add_argument("--web-port", type=int, default=8888)
    parser.add_argument("--interval", type=float, default=2.0)
    parser.add_argument("--config", type=str)
    args = parser.parse_args()

    if args.config:
        try:
            sensor_config = json.loads(args.config)
        except json.JSONDecodeError:
            print("Invalid JSON config")
            return
    else:
        sensor_config = get_sensor_config(args.pi_id)

    try:
        subject = SensorSubject(args.pi_id, sensor_config)
        observer = WebServerObserver(args.web_host, args.web_port)
        subject.attach_observer(observer)

        for attempt in range(5):
            if observer.connect():
                break
            print(f"Connection attempt {attempt + 1}/5 failed, retrying...")
            time.sleep(3)
        else:
            print("Could not connect to web server")
            return

        subject.start_monitoring(args.interval)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        try:
            observer.disconnect()
            stats = subject.get_statistics()
            print("\nFinal stats:")
            for k, v in stats.items():
                print(f"  {k}: {v}")
        except Exception:
            pass


if __name__ == "__main__":
    main()
