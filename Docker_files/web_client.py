import socket
import json


def start_web_observer():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(("brain", 8888))

    client.sendall(json.dumps({"type": "observer"}).encode("utf-8"))
    print("Registered as observer, waiting for data...")

    buffer = ""
    while True:
        try:
            data = client.recv(1024)
            if not data:
                break
            buffer += data.decode("utf-8")
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                message = json.loads(line)
                print(f"\n[Web Display] {message['timestamp']}")
                print(f"Source: {message['origin']} | Temp: {message['payload']['temp']}C")
        except Exception as e:
            print(f"Lost connection: {e}")
            break


if __name__ == "__main__":
    start_web_observer()
