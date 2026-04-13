---
marp: true
theme: default
paginate: true
---

# Observer Pattern Project
## ESOF 427 - Nick, Hayden, and Quinn

My distributed observer pattern implementation using Raspberry Pi sensors

---

## What we Built

We made a system where Raspberry Pi sensors send temperature data to a web server using the Observer pattern and some other design patterns we learned about.

The Pi runs Python code with all the patterns, and Docker just runs a simple web page that shows the data.

---

## Architecture 

```
Pi (Python) -----> Docker (Web Server)
    |                    |
    |-- Factory          |-- Socket listener  
    |-- Decorators       |-- Web page
    |-- Strategy         
    |-- Observer         
```

The Pi does all the work and sends JSON data over a TCP socket to port 8888.

---

## Design Patterns I Used

### 1. Simple Factory
Creates the right sensor based on config:

```python
sensor = SensorFactory.create_sensor({
    "mode": "dht11",  # DHT11 or ADS1110
    "pin": 21
})
```

This way we can easily switch between different sensor types.

---

### 2. Decorator Pattern  
Adds retry and fallback functionality:

```python
# Retry up to 3 times if sensor fails
sensor = RetryDecorator(sensor, retries=3)

# Use backup sensor if main one fails
backup = SensorFactory.create_sensor({"mode": "ads"})
sensor = FallbackDecorator([sensor, backup])
```

Pretty useful for when sensors are flaky.

---

### 3. Strategy Pattern
Filters data before sending it:

```python
def should_send(self, temp):
    # Only send if temperature changed by 0.5°C or more
    if abs(temp - self.last_temp) >= 0.5:
        return True
    return False
```

This reduces network traffic by only sending significant changes.

---

### 4. Observer Pattern (Distributed)
The Pi is the Subject, web server is the Observer:

```python
# Pi side
subject.attach_observer(web_observer)
subject.notify_observers(sensor_data)

# Web server receives notification via socket
```

This is the main pattern for the assignment.

---

## Files Created

**For Docker:**
- `sensor_web_server.py` - The web server that receives data
- `Dockerfile.simple` - Docker container setup  
- `docker-compose-simple.yml` - Docker service config

**For Pi:**
- `pi_sensor_client.py` - Main client with all the patterns
- Uses existing files: `sensor_factory.py`, `decorators.py`, etc.

---

## How to Run It

**Start the web server:**
```bash
docker-compose -f docker-compose-simple.yml up -d
```

**Run on Pi:**
```bash
python3 pi_sensor_client.py Pi_TeamA --web-host 2.5.5.29
```

Then check the webpage at `http://2.5.5.29:8080`

---

## Network Setup

Had some trouble figuring out the IP address. 
- 172.18.176.1
- 192.168.56.1  
- 10.66.99.1
- 2.5.5.29 
- 10.212.204.3

Used `curl` to test which one the Pi could reach.

---

## Data Format

Pi sends JSON like this:
```json
{
  "origin": "Pi_TeamA",
  "payload": {"temp": 23.5, "unit": "C"},
  "timestamp": "2026-04-02T16:15:01"
}
```

Web server responds with:
```json
{"status": "received", "timestamp": "..."}
```

---

## The Web Page

Super simple HTML table:

| Pi ID | Temperature | Time | IP |
|-------|-------------|------|-----|
| Pi_TeamA | 23.5C (74.3F) | 2026-04-02T16:15:01 | 192.168.1.5 |

Auto-refreshes every 10 seconds. Nothing fancy.

---

## Problems I Ran Into

1. **Wrong decorator parameters** - My existing `RetryDecorator` uses `retries=` not `max_retries=`
2. **Network issues** - Pi couldn't reach some of my IP addresses  
3. **Docker build errors** - Had to use different base image
4. **Too many emojis** - Made output hard to read, removed them

---

## ESOF 427 Requirements

✓ Observer pattern with attach/detach/notify  
✓ Distributed across network  
✓ Multiple design patterns working together  
✓ Real hardware (Raspberry Pi sensors)  
✓ JSON serialization  
✓ Concurrent handling (multiple Pis)

I think I got everything the assignment asked for.

---

## Testing

**Pi output looks like:**
```
Starting Raspberry Pi Sensor Client
Pi ID: Pi_TeamA
Connected to web server at 2.5.5.29:8888
Reading: 23.5C
Sent: 23.5C -> Web Server [OK]
Filtered: 23.6C (not significant change)
```

**Web page updates automatically** showing all connected Pis.

---

## Demo

The system is running live:
- Web dashboard: `http://2.5.5.29:8080`
- Pi sensors sending real temperature data
- All patterns working together

Any questions?