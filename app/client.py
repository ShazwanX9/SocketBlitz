import os
import time
import socket
import threading
import logging

class Client:
    BUFFER_SIZE = 1024
    DELIMITER = "://"
    FILE_SENDING_HEADER = "FILE"+DELIMITER

    def __init__(self, client_name="", server_address="", server_port=8000) -> None:
        self.client_name = client_name
        self.dir_to_download = f"./{self.client_name}/"
        self.server_address = server_address
        self.server_port = server_port
        self._client_socket = None
        self.logger = self.setup_logger()
        self._lock = threading.Lock()
        self._is_receiving_file = False
        self._stop_event = threading.Event()
        self.connected = False

    def change_name(self, client_name: str) -> None:
        self.client_name = client_name

    def change_server(self, server_address: str, server_port: int) -> None:
        self.server_address = server_address
        self.server_port = server_port

    def change_download_dir(self, newpath: str) -> None:
        self.dir_to_download = newpath

    def get_sendfile_format(self, filepath: str) -> str:
        return self.FILE_SENDING_HEADER+filepath

    def get_connection(self) -> bool:
        return self.connected

    def setup_logger(self) -> logging.Logger:
        logger = logging.getLogger(f"{__name__}.Client")
        formatter = logging.Formatter('[%(levelname)s] %(message)s')
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        logger.setLevel(logging.INFO)
        return logger

    def listen_server(self):
        try:
            while not self._is_receiving_file:
                response = self._client_socket.recv(self.BUFFER_SIZE)
                if not response:
                    break
                self.handle_data(response)
        except KeyboardInterrupt:
            self.logger.info("KeyboardInterrupt received. Closing connection.")
        except (socket.error, OSError) as e:
            self.logger.error(f"Connection error: {e}")
        finally:
            self.close_conn()

    def handle_data(self, data) -> None:
        if data.startswith(self.FILE_SENDING_HEADER.encode()):
            self._is_receiving_file = True
            _, file_path, file_size = data.decode().split(self.DELIMITER)
            full_path = os.path.join(self.dir_to_download, file_path)
            self.receive_file(full_path, int(file_size))
        else:
            self.logger.info(f"Server response: {data}")

    def receive_file(self, file_path: str, file_size: int) -> None:
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            with open(file_path, "wb") as file:
                remaining_size = file_size
                while remaining_size > 0:
                    chunk = self._client_socket.recv(min(remaining_size, self.BUFFER_SIZE))
                    if not chunk:
                        break
                    file.write(chunk)
                    remaining_size -= len(chunk)
                if remaining_size > 0:
                    self.logger.error("File transmission incomplete.")
                else:
                    self.logger.info(f"File received: {file_path}")
        except (socket.error, OSError) as e:
            self.logger.error(f"Error receiving file: {e}")
        finally:
            self._is_receiving_file = False

    def send(self, data: str) -> None:
        if data.startswith(self.FILE_SENDING_HEADER):
            self._send_file(data.split(self.DELIMITER)[1])
        else:
            self._send_message(data)

    def _send_message(self, message: str) -> None:
        try:
            self._client_socket.send(message.encode())
        except (socket.error, OSError) as e:
            self.logger.error(f"Connection error: {e}")

    def _send_file(self, file_path: str) -> None:
        try:
            with open(file_path, "rb") as file:
                file_name = os.path.basename(file_path)
                file_size = os.path.getsize(file_path)
                header = f"{self.FILE_SENDING_HEADER}{file_name}{self.DELIMITER}{file_size}"
                self._client_socket.sendall(header.encode())

                # Stream the file rather than loading it into memory
                while True:
                    chunk = file.read(self.BUFFER_SIZE)
                    if not chunk:
                        break
                    self._client_socket.sendall(chunk)

        except FileNotFoundError:
            self.logger.error("File not found.")
        except (socket.error, OSError) as e:
            self.logger.error(f"Error sending file: {e}")

    def start(self):
        try:
            self._client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._client_socket.connect((self.server_address, self.server_port))
            self.logger.info("Connection established. Starting communication.")
            comm_thread = threading.Thread(
                target=self.listen_server, 
                args=(),
                daemon=True
            )
            comm_thread.start()
            self.connected = True
        except (socket.error, OSError) as e:
            self.logger.error(f"Connection failed: {e}")
            self.close_conn()

    def restart_connection(self):
        self.close_conn()
        self.start()

    def close_conn(self) -> None:
        with self._lock:
            if hasattr(self, "_client_socket"):
                self._client_socket.close()
        self.connected = False

if __name__ == "__main__":
    # server_address = 'localhost'
    # server_address = socket.gethostname()
    # server_port = 12345
    server_address = input("SERVER ADDR: ")
    server_port = int(input("SERVER PORT: "))

    import random
    client = Client(
        str(random.random()), 
        server_address, 
        server_port
    )
    client.start()
    
    try:
        while True:
            data = input("Message: ")
            client.send(data)
    except KeyboardInterrupt:
        client.logger.info("KeyboardInterrupt received. Closing connection.")
