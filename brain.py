import socket
import threading
import json

class Brain:
    def __init__(self):
        self._observers = []  # List of socket objects
        self._lock = threading.Lock()

    def attach(self, observer_socket):
        with self._lock:
            self._observers.append(observer_socket)
            print("[Brain] New observer registered.")

    def notify(self, data):
        """Broadcasts data to all connected observer sockets."""
        with self._lock:
            # We iterate backward to safely remove disconnected sockets
            for obs in self._observers[:]:
                try:
                    obs.sendall(json.dumps(data).encode('utf-8'))
                except Exception:
                    print("[Brain] Removing unresponsive observer.")
                    self._observers.remove(obs)

class DistributedServer:
    def __init__(self, host='0.0.0.0', port=8888):
        self.brain = Brain()
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((host, port))

    def start(self):
        self.server.listen()
        print(f"[Brain] Listening on port 8888...")
        while True:
            conn, addr = self.server.accept()
            threading.Thread(target=self.handle_client, args=(conn,), daemon=True).start()

    def handle_client(self, conn):
        with conn:
            try:
                # First message defines the role 
                raw_identity = conn.recv(1024).decode('utf-8')
                identity = json.loads(raw_identity)

                if identity.get("type") == "observer":
                    self.brain.attach(conn)
                    # Keep connection open to receive broadcasts
                    while True:
                        if not conn.recv(1024): break 
                else:
                    # Treat as Producer (Pi)
                    while True:
                        data = conn.recv(1024)
                        if not data: break
                        message = json.loads(data.decode('utf-8'))
                        print(f"[Brain] Received data from {message['origin']}")
                        self.brain.notify(message)
            except Exception as e:
                print(f"[Brain] Connection error: {e}")

if __name__ == "__main__":
    DistributedServer().start()