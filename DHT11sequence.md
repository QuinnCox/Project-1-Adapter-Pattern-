sequenceDiagram
autonumber
participant App as Base.py (Main Loop)
participant TS as TemperatureSensor (interface)
participant DHTA as DHT11Adapter
participant DHT as DHT11 Driver

App->>TS: get_temperature()
TS->>DHTA: get_temperature()
DHTA->>DHT: read()
DHT-->>DHTA: DHT11Result
alt result valid
  DHTA-->>App: temperature (°C)
else invalid
  DHTA-->>App: None
end