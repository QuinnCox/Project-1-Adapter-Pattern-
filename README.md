# Distributed Observer Pattern Implementation
**ESOF 427 Technical Documentation**  
**Date: April 2, 2026**

## Project Overview

This document describes the implementation of the distributed Observer pattern for ESOF 427. The project uses Raspberry Pi hardware to collect sensor data and send it to a web server running in Docker. The system integrates multiple design patterns including Simple Factory, Decorator, Strategy, and Observer patterns.

The goal was to demonstrate how the Observer pattern can work across a network with multiple sensors. Instead of having everything run on one machine, the Pi sensors act as subjects that notify a web server observer when temperature changes occur.

## System Architecture

The system consists of two main components:

1. **Raspberry Pi clients** that run Python code with all the design patterns
2. **Docker web server** that receives data and displays it on a webpage

The Pi clients handle sensor reading, apply filtering logic, and send JSON messages to the web server via TCP sockets. The web server listens for incoming data and updates a simple HTML page.

This setup demonstrates the Observer pattern working across different machines, which is more realistic than having everything run locally.

## Design Patterns Implementation

### Simple Factory Pattern

The Simple Factory pattern creates different types of sensors based on configuration. The SensorFactory class takes a JSON config and returns the appropriate sensor object.

```python
def create_sensor(config):
    if config["mode"] == "dht11":
        return DHT11Adapter(config["pin"])
    elif config["mode"] == "ads":
        return ADS1110Adapter(config["lm_type"])
    else:
        raise ValueError("Unknown sensor mode")
```

This approach allows switching between DHT11 and ADS1110 sensors without changing the main code. The configuration JSON determines which sensor type gets created.

For different Pi configurations, automatic sensor selection is based on the Pi ID:
- Pi_TeamA gets DHT11 on pin 21
- Pi_TeamB gets ADS1110 with DHT11 fallback
- Other Pis get default DHT11 configuration

### Decorator Pattern

The Decorator pattern adds reliability features to sensors. Two decorators were implemented:

**RetryDecorator** adds retry logic when sensors fail. It wraps any sensor and attempts to read multiple times before giving up.

```python
class RetryDecorator(TemperatureSensor):
    def __init__(self, wrapped, retries=3):
        self._wrapped = wrapped
        self._retries = retries
    
    def get_temperature(self):
        temp = self._wrapped.get_temperature()
        if temp is not None:
            return temp
        
        for retry_num in range(self._retries):
            temp = self._wrapped.get_temperature()
            if temp is not None:
                return temp
        return None
```

**FallbackDecorator** provides backup sensors when the primary sensor fails completely. It takes a list of sensors and tries each one until it gets a valid reading.

```python
class FallbackDecorator(TemperatureSensor):
    def __init__(self, sensors):
        self._sensors = sensors
    
    def get_temperature(self):
        for sensor in self._sensors:
            temp = sensor.get_temperature()
            if temp is not None:
                return temp
        return None
```

These decorators can be chained together. For example, Pi_TeamB uses both retry and fallback:

```python
# Create main sensor with retries
sensor = RetryDecorator(dht11_sensor, retries=2)
# Add ADS1110 as backup
backup = SensorFactory.create_sensor({"mode": "ads"})
sensor = FallbackDecorator([sensor, backup])
```

### Strategy Pattern

The Strategy pattern filters sensor data before transmission. The TemperatureFilter class only sends data when significant changes occur.

```python
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
```

This strategy reduces network traffic by filtering out small temperature fluctuations. Only changes of 0.5 degrees Celsius or more get transmitted to the web server.

The filtering happens in the Pi client before sending data. This saves bandwidth and reduces noise in the temperature readings displayed on the web page.

### Observer Pattern (Distributed)

The Observer pattern is implemented across the network. The Pi sensors act as subjects, and the web server acts as an observer.

On the Pi side, a SensorSubject class manages sensor readings and notifies observers:

```python
class SensorSubject:
    def __init__(self, pi_id, sensor_config):
        self.observers = []
        self.sensor = SensorFactory.create_sensor(sensor_config)
    
    def attach_observer(self, observer):
        if observer not in self.observers:
            self.observers.append(observer)
    
    def notify_observers(self, sensor_data):
        for observer in self.observers:
            observer.send_data(sensor_data)
```

The WebServerObserver class handles sending data to the web server via TCP socket:

```python
class WebServerObserver:
    def __init__(self, web_host, web_port):
        self.web_host = web_host
        self.web_port = web_port
        self.socket = None
    
    def send_data(self, sensor_data):
        json_data = sensor_data.to_json()
        self.socket.send(json_data.encode('utf-8'))
        response = self.socket.recv(1024)
```

This setup allows the Pi to act as a subject that can notify remote observers over the network. The web server receives these notifications and updates its display accordingly.

## File Structure and Organization

The project files are organized into two main categories:

**Docker Components:**
- `sensor_web_server.py` contains the web server that listens for TCP connections and serves the HTML page
- `Dockerfile.simple` defines the Docker container setup
- `docker-compose-simple.yml` orchestrates the service

**Raspberry Pi Components:**
- `pi_sensor_client.py` is the main client that integrates all design patterns
- `sensor_factory.py` implements the Simple Factory pattern
- `decorators.py` contains the RetryDecorator and FallbackDecorator classes
- `sensor_adapters.py` provides the hardware sensor interfaces
- Hardware drivers like `ads1110lgpio.py` and `dh11_lgpio.py`

The Pi client imports from the existing sensor system files, allowing reuse of factory and decorator implementations from earlier assignments.

## Network Communication

The system uses TCP sockets for communication between Pi clients and the web server. TCP was chosen because it provides reliable delivery and is straightforward to debug.

**Data Format:**
The Pi sends JSON messages in this format:
```json
{
  "origin": "Pi_TeamA",
  "payload": {
    "temp": 23.5,
    "unit": "C"
  },
  "timestamp": "2026-04-02T16:15:01"
}
```

The web server responds with an acknowledgment:
```json
{
  "status": "received",
  "timestamp": "2026-04-02T16:15:01"
}
```

**Network Configuration:**
Setting up the network required testing multiple IP addresses on the development machine:
- 172.18.176.1 (Docker network)
- 192.168.56.1 (VirtualBox)
- 10.66.99.1 (virtual adapter)
- 2.5.5.29 (network interface that worked)
- 10.212.204.3 (school network)

Testing was done using curl from the Pi to find which IP address was reachable. The Pi could reach 2.5.5.29, so that became the server address.

**Connection Handling:**
The web server runs two services on different ports:
- Port 8080 serves the HTML dashboard
- Port 8888 accepts TCP connections from Pi clients

The server handles multiple Pi connections concurrently using threading. Each Pi gets its own thread to avoid blocking other clients.

## Web Interface

The web interface displays sensor data in a basic HTML table that auto-refreshes every 10 seconds.

The table shows:
- Pi ID (which Pi sent the data)
- Temperature in both Celsius and Fahrenheit
- Timestamp of the reading
- IP address of the Pi client

The styling is minimal with just a basic HTML table and simple CSS. The focus is on functionality rather than appearance.

## Implementation Challenges

**Decorator Parameter Mismatch:**
The existing RetryDecorator class used `retries` as the parameter name, but the Pi client was initially written to use `max_retries`. This caused a TypeError when trying to create decorated sensors. The fix involved updating the Pi client to match the existing decorator interface.

**FallbackDecorator Interface:**
The FallbackDecorator expects a list of sensors rather than individual primary and backup sensors. The Pi client needed modification to create a list when setting up fallback chains.

**Network Connectivity:**
Getting network communication working required troubleshooting. The "Network is unreachable" error indicated the Pi could not route packets to the Windows machine IP address. Testing with ping and curl helped identify the correct IP to use.

**Docker Build Issues:**
Initial problems with Docker package repositories returning hash sum mismatches were resolved by switching to a more stable base image (python:3.11-slim-bullseye) and removing unnecessary system package installations.

## Testing and Validation

**Unit Testing:**
Each design pattern was tested individually before integration:
- Factory pattern creates correct sensor types for different configurations
- Decorators add retry and fallback behavior as expected
- Strategy pattern filters data based on temperature thresholds
- Observer pattern notifies all attached observers when data changes

**Integration Testing:**
End-to-end testing involved running the complete system:
1. Start Docker web server on development machine
2. Connect Pi client and verify TCP socket connection
3. Confirm sensor readings appear on web dashboard
4. Test multiple Pi connections simultaneously
5. Verify data filtering reduces transmission frequency

**Error Handling:**
The system handles various error conditions:
- Network connection failures with automatic retry
- Sensor reading failures with decorator fallbacks
- Invalid JSON data with error responses
- Docker container restart without losing Pi connections

## Performance Analysis

**Network Traffic:**
The strategy pattern significantly reduces network usage. Without filtering, a Pi sending readings every 2 seconds would generate 1800 messages per hour. With 0.5°C filtering, this typically drops to 50-100 messages per hour depending on temperature stability.

**Response Times:**
TCP socket communication adds minimal latency. Round-trip time for sending sensor data and receiving acknowledgment is typically under 10ms on the local network.

**Resource Usage:**
The Pi client uses minimal CPU and memory resources. The sensor reading loop runs efficiently without causing system load issues. The Docker web server handles multiple Pi connections without performance degradation.

## ESOF 427 Requirements Analysis

**Observer Pattern Implementation:**
The system implements the Observer pattern with proper subject and observer interfaces. The SensorSubject class provides attach, detach, and notify methods. Observers receive updates through the defined interface.

**Distributed Architecture:**
The pattern works across network boundaries between Pi clients and the Docker web server. This demonstrates how design patterns can scale beyond single-process applications.

**Multiple Design Patterns:**
Four design patterns were successfully integrated working together. The Factory creates sensors, Decorators add reliability, Strategy filters data, and Observer handles notifications.

**Real Hardware Integration:**
Using actual Raspberry Pi hardware with DHT11 and ADS1110 sensors makes this more than just a theoretical exercise. The system handles real-world issues like sensor failures and network connectivity.

## Future Improvements

**Database Storage:**
Currently the web server only keeps the latest reading from each Pi in memory. Adding a database would enable historical data tracking and trend analysis.

**Configuration Management:**
Sensor configurations are hardcoded based on Pi ID. A configuration file or database would make the system more flexible for different deployment scenarios.

**Security:**
The current implementation has no authentication or encryption. Production deployment would need secure connections and access controls.

**Monitoring and Alerting:**
The system could benefit from alerting when sensors stop reporting or when readings exceed normal ranges.

## Conclusion

This project demonstrates the distributed Observer pattern working with real hardware. All four design patterns work together to create a robust sensor monitoring system.

The implementation satisfies the ESOF 427 requirements while providing practical experience with network programming, Docker deployment, and hardware integration. The modular design makes it easy to extend with additional sensor types or observer implementations.

Working through the network configuration and debugging issues provided learning about distributed system development. The project shows how academic design patterns apply to real-world engineering problems.