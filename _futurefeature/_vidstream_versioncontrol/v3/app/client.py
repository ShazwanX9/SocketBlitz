import cv2
import socket
import logging
import threading

if __name__ == "__main__":
    from plugin import VideoPlugin
else:
    from .plugin import VideoPlugin

class Client:
    BUFFER_SIZE = 4096

    def __init__(self, client_name="", server_address="", server_port=8000, logger: logging.Logger = None) -> None:
        self.server_address = server_address
        self.server_port = server_port
        self.client_name = client_name
        self._client_socket = None
        self.logger = logger
        self._lock = threading.Lock()
        self.connected = False

    def change_name(self, client_name: str) -> None:
        self.client_name = client_name

    def change_server(self, server_address: str, server_port: int) -> None:
        self.server_address = server_address
        self.server_port = server_port

    def get_connection(self) -> bool:
        return self.connected

    def start(self):
        try:
            self._client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._client_socket.connect((self.server_address, self.server_port))
            if self.logger: self.logger.info("Connection established. Starting communication.")
            self.connected = True
        except (socket.error, OSError) as e:
            if self.logger: self.logger.error(f"Connection failed: {e}")
            self.close_conn()

    def restart_connection(self):
        self.close_conn()
        self.start()

    def close_conn(self) -> None:
        with self._lock:
            if hasattr(self, "_client_socket"):
                self._client_socket.close()
        self.connected = False

class DataHandler:
    def __init__(self, client: Client) -> None:
        self.client = client
        self.plugin = VideoPlugin()

    def get_recent_frame(self):
        return self.plugin.get_frame_value()

    def listen_server(self):
        while True:
            try:
                self.plugin.receive(self.client._client_socket)
            except (socket.error, OSError, KeyboardInterrupt, RuntimeError) as e:
                if self.client.logger: self.client.logger.error(f"Error: {e}")
            finally:
                self.client.close_conn()

if __name__ == "__main__":
    # server_address = 'localhost'
    server_address = socket.gethostname()
    server_port = 12345
    # server_address = input("SERVER ADDR: ")
    # server_port = int(input("SERVER PORT: "))
    logger = logging.getLogger(f"{__name__}.Client")

    import random
    client = Client(
        str(random.random()), 
        server_address, 
        server_port
    )
    client.start()
    data_handler = DataHandler(client)

    comm_thread = threading.Thread(
        target=data_handler.listen_server,
        args=(),
        daemon=True
    )
    comm_thread.start()

    try:
        while True:
            if data_handler.get_recent_frame() is not None:
                flipped_frame = cv2.flip(data_handler.get_recent_frame(), 1)
                cv2.imshow(f"Display window From Client{client.client_name}", flipped_frame)
                if cv2.waitKey(1) & 0xFF == ord('q'): 
                    break
        cv2.destroyAllWindows()
    except KeyboardInterrupt:
        client.logger.info("KeyboardInterrupt received. Closing connection.")