sequenceDiagram
participant App as Base.py (Main Loop)
participant TS as TemperatureSensor (interface)
participant ADSA as ADS1110Adapter
participant ADC as ADS1110Driver

App->>TS: get_temperature()
TS->>ADSA: get_temperature()
ADSA->>ADC: read_raw()
ADC-->>ADSA: raw ADC counts (signed)
alt raw is not None
  ADSA->>ADSA: raw_to_voltage()
  ADSA->>ADSA: voltage -> mV -> °C (LM35)
  ADSA-->>App: temperature (°C)
else raw missing
  ADSA-->>App: None
end