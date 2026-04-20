# Observer Pattern Implementation (Distributed)

## Overview
This branch extends the system to demonstrate a distributed Observer pattern. The Raspberry Pi acts as the Subject and sends temperature readings to a web server Observer over a TCP socket. The web server runs in Docker.

This branch also integrates Simple Factory, Decorator, and Strategy patterns from previous assignments.

## Patterns Used
- **Simple Factory** (`Sensor_factory.py`) — creates sensor objects from JSON config
- **Decorator** (`Decorator.py`) — adds retry and fallback behavior to sensors
- **Strategy** (`observer.py: TemperatureFilter`) — only sends data when temp changes by ≥ 0.5°C
- **Observer** (`observer.py: SensorSubject / WebServerObserver`) — Pi notifies web server when readings pass the filter

## Architecture
Raspberry Pi                    Docker (any machine)

observer.py                     brain.py
SensorSubject (Subject)  -->  DistributedServer
WebServerObserver             Brain (broadcasts to observers)
web_client.py (Observer display)

Pi sends newline-delimited JSON over TCP to port 8888. The Brain server broadcasts it to any connected web clients.

## Running It

**Start Docker services:**
```bash
cd Docker_files
docker-compose up -d
```

**Run on Pi:**
```bash
python3 observer.py Pi_TeamA --web-host <server-ip> --web-port 8888
```

Use `Pi_TeamA` for DHT11 on pin 21, `Pi_TeamB` for ADS1110 with DHT11 fallback.

## Data Format
```json
{
  "origin": "Pi_TeamA",
  "payload": {"temp": 23.5, "unit": "C"},
  "timestamp": "2026-04-02T16:15:01"
}
```

## Diagrams
See `Documentation/Observer.md` for the full pattern walkthrough.
