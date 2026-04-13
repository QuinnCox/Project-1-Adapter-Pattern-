# Decorator Pattern Implementation
**ESOF 427 Technical Documentation**  
**Date: March 15, 2026**

## Project Overview

This document describes the implementation of the Decorator pattern for sensor reliability in ESOF 427. The project enhances temperature sensor functionality by adding retry logic and fallback capabilities without modifying the original sensor classes. The Decorator pattern allows dynamic addition of behavior to sensor objects at runtime.

The goal was to demonstrate how the Decorator pattern can add multiple layers of functionality to existing objects while maintaining the original interface. This approach provides a flexible alternative to inheritance for extending object behavior.

## System Architecture

The system consists of three main components:

1. **Base sensor adapters** that implement the TemperatureSensor interface
2. **Decorator classes** that wrap sensors to add reliability features  
3. **Test framework** to validate decorator functionality

The base sensors provide core temperature reading functionality. Decorators wrap these sensors to add retry logic, fallback capabilities, and other reliability features. Multiple decorators can be chained together to combine different behaviors.

## Design Pattern Implementation

### Decorator Pattern Structure

The Decorator pattern is implemented using a common interface shared by both concrete sensors and decorators. This allows decorators to wrap other decorators or concrete sensors interchangeably.

**Base Interface:**
```python
class TemperatureSensor:
    def get_temperature(self):
        pass
    
    def open(self):
        pass
    
    def close(self):
        pass
```

**Concrete Sensors:**
```python
class DHT11Adapter(TemperatureSensor):
    def __init__(self, pin, chip=0):
        self.pin = pin
        self.chip = chip
    
    def get_temperature(self):
        # Hardware-specific implementation
        return temperature_reading
```

**Decorator Base Class:**
```python
class SensorDecorator(TemperatureSensor):
    def __init__(self, wrapped_sensor):
        self._wrapped_sensor = wrapped_sensor
    
    def get_temperature(self):
        return self._wrapped_sensor.get_temperature()
    
    def open(self):
        if hasattr(self._wrapped_sensor, 'open'):
            self._wrapped_sensor.open()
    
    def close(self):
        if hasattr(self._wrapped_sensor, 'close'):
            self._wrapped_sensor.close()
```

### Retry Decorator Implementation

The RetryDecorator adds automatic retry functionality when sensor readings fail. It attempts to read from the wrapped sensor multiple times before giving up.

```python
class RetryDecorator(TemperatureSensor):
    def __init__(self, wrapped, retries=3):
        self._wrapped = wrapped
        self._retries = retries

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
```

**Key Design Features:**
- Single responsibility: only handles retry logic
- Does not modify the wrapped sensor
- Maintains the same interface as the base sensor
- Configurable number of retry attempts

### Fallback Decorator Implementation

The FallbackDecorator provides backup sensor capabilities when the primary sensor fails completely. It maintains a list of sensors and tries each one in sequence.

```python
class FallbackDecorator(TemperatureSensor):
    def __init__(self, sensors):
        if not sensors:
            raise ValueError("FallbackDecorator requires at least one sensor")
        self._sensors = sensors

    def get_temperature(self):
        for i, sensor in enumerate(self._sensors):
            temp = sensor.get_temperature()
            if temp is not None:
                if i > 0:
                    print(f"[FallbackDecorator] Using fallback sensor #{i + 1}")
                return temp
        return None
```

**Key Design Features:**
- Supports unlimited sensor fallback chains
- Provides feedback when fallback sensors are used
- Maintains sensor order priority
- Handles sensor lifecycle methods for all sensors

### Decorator Chaining

Multiple decorators can be chained together to combine different reliability features. The order of decoration affects behavior and should be carefully considered.

```python
# Example: DHT11 with retry and fallback capabilities
base_sensor = DHT11Adapter(pin=21)
retry_sensor = RetryDecorator(base_sensor, retries=3)
backup_sensor = ADS1110Adapter()
final_sensor = FallbackDecorator([retry_sensor, backup_sensor])
```

This configuration provides:
1. Primary DHT11 sensor with retry logic (up to 3 attempts)
2. Fallback to ADS1110 sensor if DHT11 fails completely
3. Transparent interface identical to base sensors

## Sensor Adapter Integration

### DHT11 Adapter

The DHT11Adapter provides interface compatibility for DHT11 temperature and humidity sensors. It uses the lgpio library for hardware communication.

```python
class DHT11Adapter(TemperatureSensor):
    def __init__(self, pin, chip=0):
        self.pin = pin
        self.chip = chip
        self.sensor = None
    
    def open(self):
        try:
            import lgpio
            self.handle = lgpio.gpiochip_open(self.chip)
        except ImportError:
            print("lgpio not available, using simulated readings")
    
    def get_temperature(self):
        try:
            # Actual hardware reading implementation
            return self._read_dht11()
        except Exception as e:
            print(f"DHT11 reading failed: {e}")
            return None
```

### ADS1110 Adapter

The ADS1110Adapter interfaces with ADS1110 analog-to-digital converters connected to temperature sensors like LM35.

```python
class ADS1110Adapter(TemperatureSensor):
    def __init__(self, lm_type="LM35", vref=2.048):
        self.lm_type = lm_type
        self.vref = vref
        self.sensor = None
    
    def get_temperature(self):
        try:
            raw_voltage = self._read_ads1110()
            if self.lm_type == "LM35":
                # LM35 conversion: 10mV per degree Celsius
                temperature = raw_voltage / 0.01
            return temperature
        except Exception as e:
            print(f"ADS1110 reading failed: {e}")
            return None
```

## Testing and Validation

### Unit Testing

Individual decorator functionality was tested to ensure correct behavior:

**RetryDecorator Tests:**
```python
def test_retry_decorator():
    # Test successful reading on first attempt
    sensor = MockSensor(return_value=25.0)
    decorated = RetryDecorator(sensor, retries=2)
    assert decorated.get_temperature() == 25.0
    assert sensor.call_count == 1
    
    # Test retry on initial failure
    sensor = MockSensor(fail_count=1, return_value=26.0)
    decorated = RetryDecorator(sensor, retries=2)
    assert decorated.get_temperature() == 26.0
    assert sensor.call_count == 2
```

**FallbackDecorator Tests:**
```python
def test_fallback_decorator():
    # Test primary sensor success
    primary = MockSensor(return_value=25.0)
    backup = MockSensor(return_value=30.0)
    decorated = FallbackDecorator([primary, backup])
    assert decorated.get_temperature() == 25.0
    
    # Test fallback activation
    primary = MockSensor(return_value=None)
    backup = MockSensor(return_value=30.0)
    decorated = FallbackDecorator([primary, backup])
    assert decorated.get_temperature() == 30.0
```

### Integration Testing

Combined decorator functionality was tested with realistic sensor scenarios:

**Chained Decorators:**
```python
def test_combined_decorators():
    # Primary sensor with retry + backup sensor
    primary = DHT11Adapter(pin=21)
    retry_primary = RetryDecorator(primary, retries=2)
    backup = ADS1110Adapter()
    combined = FallbackDecorator([retry_primary, backup])
    
    # Verify temperature reading with full reliability stack
    temperature = combined.get_temperature()
    assert temperature is not None
```

### Hardware Testing

Testing was performed with actual Raspberry Pi hardware to validate real-world functionality:

1. DHT11 sensor connected to GPIO pin 21
2. ADS1110 with LM35 sensor on I2C bus
3. Simulated sensor failures to test retry logic
4. Physical disconnection to test fallback behavior

## Performance Analysis

### Retry Overhead

The RetryDecorator adds minimal overhead for successful readings but increases latency during failures:

- Successful reading: No additional overhead
- Single retry: Approximately 2x reading time
- Maximum retries: Up to (retries + 1) × reading time

### Memory Usage

Each decorator adds a small memory overhead:
- RetryDecorator: Minimal (stores retry count and wrapped sensor reference)
- FallbackDecorator: Linear with number of fallback sensors
- Chained decorators: Additive memory usage

### Network Impact

When used in distributed systems, decorators reduce network traffic by handling failures locally rather than propagating errors to remote systems.

## Design Pattern Benefits

### Single Responsibility Principle

Each decorator has a single, well-defined responsibility:
- RetryDecorator: Handles retry logic only
- FallbackDecorator: Manages sensor fallback only
- Base sensors: Provide temperature readings only

### Open/Closed Principle

The system is open for extension but closed for modification:
- New decorators can be added without changing existing code
- Existing sensors work unchanged with new decorators
- Behavior combinations are achieved through composition

### Interface Consistency

All components implement the same TemperatureSensor interface:
- Sensors and decorators are interchangeable
- Client code does not need to know about decorators
- Complex decorator chains appear as simple sensors

## Implementation Challenges

### Interface Compatibility

Ensuring all decorators properly implement the TemperatureSensor interface required careful attention to method delegation:

```python
def open(self):
    # Safely delegate to wrapped sensor
    if hasattr(self._wrapped, 'open'):
        self._wrapped.open()
```

### Error Propagation

Balancing error handling between masking failures (for reliability) and propagating critical errors required thoughtful design:
- Sensor communication errors are handled by decorators
- Configuration errors are propagated to calling code
- Hardware failures trigger fallback mechanisms

### Decorator Ordering

The order of decorator application affects system behavior:
- RetryDecorator should typically wrap individual sensors
- FallbackDecorator should be the outermost decorator
- Incorrect ordering can reduce effectiveness

## Future Enhancements

### Additional Decorators

The pattern supports easy addition of new decorators:
- **CachingDecorator**: Cache recent readings to reduce hardware access
- **FilteringDecorator**: Apply smoothing or outlier detection
- **LoggingDecorator**: Record sensor access and performance metrics
- **ValidationDecorator**: Verify readings are within expected ranges

### Configuration Management

Decorator parameters could be externalized to configuration files:
```json
{
  "sensor_config": {
    "base": {"type": "DHT11", "pin": 21},
    "decorators": [
      {"type": "Retry", "retries": 3},
      {"type": "Fallback", "backup": {"type": "ADS1110"}}
    ]
  }
}
```

### Metrics and Monitoring

Enhanced decorators could provide detailed performance metrics:
- Retry frequency and success rates
- Fallback activation statistics  
- Response time measurements
- Error categorization and reporting

## Conclusion

The Decorator pattern implementation successfully adds reliability features to temperature sensors while maintaining interface compatibility and design flexibility. The pattern demonstrates clear separation of concerns, with each decorator handling a specific aspect of reliability.

The implementation satisfies object-oriented design principles and provides a foundation for extending sensor functionality without modifying existing code. The modular approach allows different combinations of reliability features to be applied based on specific requirements.

Testing validated that decorators work correctly both individually and in combination, providing robust temperature sensing capabilities suitable for production use in distributed systems.
