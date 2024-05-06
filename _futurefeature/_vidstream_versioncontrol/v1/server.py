import socket
import cv2
import pickle
import struct
import logging
import threading

class Server:
    BUFFER_SIZE = 1024

    def __init__(self, host="", port=8000, maxconn=socket.SOMAXCONN) -> None:
        self._conns: list[socket.socket] = []
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.logger = self.setup_logger()

        self._server_socket.bind((host, port))
        self._server_socket.listen(maxconn)
        self._server_socket.settimeout(3)
        self.logger.info(f"Server listening on {self._server_socket.getsockname()}")
        self.frame_value = None

    def setup_logger(self) -> logging.Logger:
        logger = logging.getLogger(f"{__name__}.Server")
        formatter = logging.Formatter('[%(levelname)s] %(message)s')
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        logger.setLevel(logging.INFO)
        return logger

    def stream(self) -> None:
        cap = cv2.VideoCapture(0)
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            self.frame_value = pickle.dumps(frame)

    def handle_client(self, client_socket, addr):
        self.logger.info(f'Listening to {addr}')
        try:
            while True:
                if self.frame_value is not None:
                    client_socket.sendall(struct.pack("L", len(self.frame_value)))
                    client_socket.sendall(self.frame_value)

        except Exception as e:
            self.logger.error(f"Error receiving data from client {addr}: {e}")
        finally:
            self.close_conn(client_socket, addr)

    def start(self) -> None:
        try:
            stream_thread = threading.Thread(
                target=self.stream, 
                args=(),
                daemon=True
            )
            stream_thread.start()

            while True:
                try:
                    client_socket, addr = self._server_socket.accept()
                except socket.timeout:
                    continue  # Timeout occurred, try again

                self.logger.info(f'Connected to {addr}')
                client_thread = threading.Thread(
                    target=self.handle_client, 
                    args=(client_socket, addr),
                    daemon=True
                )
                client_thread.start()
                self._conns.append(client_socket)

        except KeyboardInterrupt:
            self.logger.info("KeyboardInterrupt received. Shutting down server.")
        except Exception as e:
            self.logger.error(f"Error in server loop: {e}")
        finally:
            self.shutdown()

    def close_conn(self, client_socket: socket.socket, addr: int = -1) -> None:
        # Close the connection
        self.logger.info(f"Connection closed with ({addr})")
        client_socket.close()
        self._conns.remove(client_socket)

    def shutdown(self) -> None:
        for client_socket in self._conns:
            self.close_conn(client_socket)
        self._server_socket.close()

    def get_logger(self) -> logging.Logger:
        return self.logger

if __name__ == "__main__":
    hostname = socket.gethostname()
    host = socket.gethostbyname(hostname)
    port = 0
    maxconn = 5
    # server = Server(host, port, maxconn)
    server = Server(hostname, 12345, maxconn)
    server.start()