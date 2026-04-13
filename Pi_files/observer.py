#!/usr/bin/env python3
"""
Complete Raspberry Pi Client for Distributed Observer Pattern Assignment
Integrates Simple Factory, Decorator, Strategy, and Observer patterns
"""

import socket
import json
import time
import argparse
import threading
from datetime import datetime
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod

# Import your existing sensor system
from Sensor_factory import SensorFactory 
from decorators import RetryDecorator, FallbackDecorator


class SensorDataDTO:
    """Data Transfer Object for sensor readings"""
    
    def __init__(self, origin: str, temperature: float, unit: str = "C", timestamp: str = None):
        self.origin = origin
        self.temperature = temperature
        self.unit = unit
        self.timestamp = timestamp or datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "origin": self.origin,
            "payload": {"temp": self.temperature, "unit": self.unit},
            "timestamp": self.timestamp
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict())


class TemperatureFilter:
    """Strategy pattern for data filtering"""
    
    def __init__(self, threshold: float = 0.5):
        self.threshold = threshold
        self.last_sent_temp: Optional[float] = None
    
    def should_send(self, current_temp: float) -> bool:
        """Determine if temperature reading should be sent"""
        if self.last_sent_temp is None:
            self.last_sent_temp = current_temp
            return True
        
        if abs(current_temp - self.last_sent_temp) >= self.threshold:
            self.last_sent_temp = current_temp
            return True
        
        return False


class WebServerObserver:
    """Observer that sends data to web server via socket"""
    
    def __init__(self, web_host: str = "localhost", web_port: int = 8888):
        self.web_host = web_host
        self.web_port = web_port
        self.socket = None
        self.connected = False
        self.connection_attempts = 0
        
    def connect(self) -> bool:
        """Connect to web server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10)
            self.socket.connect((self.web_host, self.web_port))
            self.connected = True
            self.connection_attempts = 0
            print(f"Connected to web server at {self.web_host}:{self.web_port}")
            return True
        except Exception as e:
            self.connection_attempts += 1
            print(f"Failed to connect to web server: {e}")
            return False
    
    def send_data(self, sensor_data: SensorDataDTO) -> bool:
        """Send sensor data to web server"""
        if not self.connected:
            if not self.connect():
                return False
        
        try:
            json_data = sensor_data.to_json()
            self.socket.send(json_data.encode('utf-8'))
            
            # Wait for acknowledgment
            response = self.socket.recv(1024)
            ack = json.loads(response.decode('utf-8'))
            
            if ack.get("status") == "received":
                print(f"Sent: {sensor_data.temperature:.1f}C -> Web Server [OK]")
                return True
            else:
                print(f"Unexpected response: {ack}")
                return False
                
        except Exception as e:
            print(f"Failed to send data: {e}")
            self.connected = False
            if self.socket:
                self.socket.close()
                self.socket = None
            return False
    
    def disconnect(self):
        """Disconnect from web server"""
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        self.connected = False
        print("Disconnected from web server")


class SensorSubject:
    """Subject in Observer pattern - manages sensor readings and notifications"""
    
    def __init__(self, pi_id: str, sensor_config: Dict[str, Any]):
        self.pi_id = pi_id
        self.sensor_config = sensor_config
        
        # Create sensor using Simple Factory pattern
        self.sensor = SensorFactory.create_sensor(sensor_config)
        
        # Apply Decorator patterns for reliability
        if sensor_config.get('retries', 0) > 0:
            self.sensor = RetryDecorator(self.sensor, retries=sensor_config['retries'])
        
        if 'fallback' in sensor_config:
            fallback_sensor = SensorFactory.create_sensor(sensor_config['fallback'])
            # FallbackDecorator expects a list of sensors
            self.sensor = FallbackDecorator([self.sensor, fallback_sensor])
        
        # Strategy pattern for filtering
        self.filter_strategy = TemperatureFilter(threshold=0.5)
        
        self.observers = []
        
        # Statistics
        self.readings_taken = 0
        self.readings_sent = 0
        self.readings_filtered = 0
        
        print(f"Sensor Subject initialized for {pi_id}")
        print(f"   Sensor Config: {sensor_config}")
    
    def attach_observer(self, observer):
        """Attach an observer"""
        if observer not in self.observers:
            self.observers.append(observer)
            print(f"Observer attached: {type(observer).__name__}")
    
    def detach_observer(self, observer):
        """Detach an observer"""
        if observer in self.observers:
            self.observers.remove(observer)
            print(f"Observer detached: {type(observer).__name__}")
    
    def notify_observers(self, sensor_data: SensorDataDTO):
        """Notify all observers with new sensor data"""
        print(f"Notifying {len(self.observers)} observers...")
        for observer in self.observers:
            try:
                observer.send_data(sensor_data)
            except Exception as e:
                print(f"Error notifying observer: {e}")
    
    def take_reading(self) -> Optional[float]:
        """Take a sensor reading using the configured sensor"""
        try:
            self.readings_taken += 1
            temperature = self.sensor.get_temperature()
            
            if temperature is not None:
                print(f"Reading: {temperature:.1f}C")
                return temperature
            else:
                print("Sensor reading failed")
                return None
                
        except Exception as e:
            print(f"Sensor error: {e}")
            return None
    
    def process_reading(self, temperature: float) -> bool:
        """Process a temperature reading using strategy pattern"""
        if self.filter_strategy.should_send(temperature):
            # Create DTO
            sensor_data = SensorDataDTO(
                origin=self.pi_id,
                temperature=temperature,
                unit="C"
            )
            
            self.notify_observers(sensor_data)
            self.readings_sent += 1
            return True
        else:
            print(f"Filtered: {temperature:.1f}C (not significant change)")
            self.readings_filtered += 1
            return False
    
    def start_monitoring(self, interval: float = 2.0):
        """Start continuous sensor monitoring"""
        print(f"Starting monitoring (interval: {interval}s)")
        print("   Press Ctrl+C to stop")
        
        try:
            while True:
                # Take reading
                temperature = self.take_reading()
                
                if temperature is not None:
                    self.process_reading(temperature)
                
                # Wait for next reading
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print(f"\nMonitoring stopped by user")
        except Exception as e:
            print(f"Monitoring error: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get monitoring statistics"""
        filter_rate = (self.readings_filtered / self.readings_taken * 100) if self.readings_taken > 0 else 0
        
        return {
            "pi_id": self.pi_id,
            "readings_taken": self.readings_taken,
            "readings_sent": self.readings_sent,
            "readings_filtered": self.readings_filtered,
            "filter_rate": f"{filter_rate:.1f}%",
            "observers": len(self.observers)
        }


def get_sensor_config(pi_id: str) -> Dict[str, Any]:
    """Get sensor configuration based on Pi ID"""
    if "TeamA" in pi_id:
        return {
            "mode": "dht11",
            "pin": 21,
            "chip": 0,
            "retries": 3
        }
    elif "TeamB" in pi_id:
        return {
            "mode": "ads",
            "lm_type": "LM35",
            "retries": 2,
            "fallback": {
                "mode": "dht11",
                "pin": 22,
                "retries": 1
            }
        }
    else:
        # Default configuration
        return {
            "mode": "dht11",
            "pin": 21,
            "chip": 0,
            "retries": 3
        }


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Raspberry Pi Sensor Client with Design Patterns')
    parser.add_argument('pi_id', nargs='?', default='Pi_TeamA',
                       help='Pi identifier (e.g., Pi_TeamA, Pi_TeamB)')
    parser.add_argument('--web-host', default='192.168.1.100',
                       help='Web server hostname or IP address')
    parser.add_argument('--web-port', type=int, default=8888,
                       help='Web server port')
    parser.add_argument('--interval', type=float, default=2.0,
                       help='Sensor reading interval in seconds')
    parser.add_argument('--config', type=str,
                       help='Custom sensor configuration JSON')
    
    args = parser.parse_args()
    
    print("Starting Raspberry Pi Sensor Client")
    print("=" * 50)
    print(f"Pi ID: {args.pi_id}")
    print(f"Web Server: {args.web_host}:{args.web_port}")
    print(f"Interval: {args.interval}s")
    print("=" * 50)
    
    # Get sensor configuration
    if args.config:
        try:
            sensor_config = json.loads(args.config)
        except json.JSONDecodeError:
            print("Invalid JSON configuration")
            return
    else:
        sensor_config = get_sensor_config(args.pi_id)
    
    try:
        # Create sensor subject with Observer pattern
        sensor_subject = SensorSubject(args.pi_id, sensor_config)
        
        web_observer = WebServerObserver(args.web_host, args.web_port)
        
        # Attach observer to subject (Observer pattern)
        sensor_subject.attach_observer(web_observer)
        
        # Test connection to web server
        print("Testing connection to web server...")
        max_retries = 5
        for attempt in range(max_retries):
            if web_observer.connect():
                break
            print(f"Connection attempt {attempt + 1}/{max_retries} failed, retrying in 3 seconds...")
            time.sleep(3)
        else:
            print("Failed to connect to web server after all retries")
            print("   Please check:")
            print("   1. Web server is running")
            print("   2. IP address is correct")
            print("   3. Port is not blocked by firewall")
            return
        
        # Start monitoring
        sensor_subject.start_monitoring(args.interval)
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Cleanup and show statistics
        try:
            if 'web_observer' in locals():
                web_observer.disconnect()
            
            if 'sensor_subject' in locals():
                stats = sensor_subject.get_statistics()
                print("\nFinal Statistics:")
                for key, value in stats.items():
                    print(f"   {key}: {value}")
        except:
            pass


if __name__ == "__main__":
    main()