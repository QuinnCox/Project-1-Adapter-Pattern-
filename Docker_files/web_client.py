import socket
import json

def start_web_observer():
    # Connect to the 'brain' service name defined in docker-compose 
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('brain', 8888))

    # Register as an observer 
    registration = json.dumps({"type": "observer"})
    client.sendall(registration.encode('utf-8'))
    print("[Web] Registered as Observer. Waiting for data...")

    while True:
        try:
            data = client.recv(1024)
            if data:
                message = json.loads(data.decode('utf-8'))
                # In a real scenario, this would update your dashboard [cite: 5]
                print(f"\n[Web Display] {message['timestamp']}")
                print(f"Source: {message['origin']} | Temp: {message['payload']['temp']}C")
        except Exception as e:
            print(f"[Web] Lost connection: {e}")
            break

if __name__ == "__main__":
    start_web_observer()