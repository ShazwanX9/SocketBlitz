import socket
import threading
import logging

class Server:
    BUFFER_SIZE = 1024
    DELIMITER = "://"
    FILE_SENDING_HEADER = "FILE"+DELIMITER

    def __init__(self, host="", port=8000, maxconn=socket.SOMAXCONN) -> None:
        self._conns: list[socket.socket] = []
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.logger = self.setup_logger()

        self._server_socket.bind((host, port))
        self._server_socket.listen(maxconn)
        self._server_socket.settimeout(3)
        self.logger.info(f"Server listening on {self._server_socket.getsockname()}")

    def setup_logger(self) -> logging.Logger:
        logger = logging.getLogger(f"{__name__}.Server")
        formatter = logging.Formatter('[%(levelname)s] %(message)s')
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        logger.setLevel(logging.INFO)
        return logger

    def broadcast(self, data, client=None):
        for client_socket in self._conns:
            if client_socket != client:
                try:
                    client_socket.sendall(data)
                except Exception as e:
                    self.logger.error(f"Error broadcasting data to a client: {e}")
                    self.close_conn(client_socket)

    def handle_client(self, client_socket, addr):
        self.logger.info(f'Listening to {addr}')
        try:
            while True:
                client_data = client_socket.recv(self.BUFFER_SIZE)
                if not client_data:
                    break
                
                if client_data.startswith(self.FILE_SENDING_HEADER.encode()):
                    self.receive_file(client_socket, client_data)
                else:
                    self.logger.info(f"Received from client ({addr}): {client_data.decode()}")
                    self.broadcast(client_data, client_socket)
        except Exception as e:
            self.logger.error(f"Error receiving data from client {addr}: {e}")
        finally:
            self.close_conn(client_socket, addr)

    def stream_file(self, file_path, client_socket):
        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(self.BUFFER_SIZE)
                if not chunk:
                    break  # End of file
                self.broadcast(chunk, client_socket)

    def receive_file(self, client_socket, header_data: str, save=False) -> None:
        try:
            _, file_name, file_size = header_data.decode().split(self.DELIMITER)
            file_size = int(file_size)

            self.broadcast(header_data, client_socket)

            remaining_size = file_size
            while remaining_size > 0:
                chunk = client_socket.recv(min(remaining_size, self.BUFFER_SIZE))
                if not chunk:
                    break
                self.broadcast(chunk, client_socket)
                remaining_size -= len(chunk)
            if remaining_size > 0:
                self.logger.error("File transmission incomplete.")
            else:
                self.logger.info(f"File transmission complete.")

        except Exception as e:
            self.logger.error(f"Error receiving file from client: {e}")

    def start(self) -> None:
        try:
            while True:
                try:
                    client_socket, addr = self._server_socket.accept()
                except socket.timeout:
                    continue  # Timeout occurred, try again

                self.logger.info(f'Connected to {addr}')
                self._conns.append(client_socket)
                client_thread = threading.Thread(
                    target=self.handle_client, 
                    args=(client_socket, addr),
                    daemon=True
                )
                client_thread.start()

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
    server = Server(host, port, maxconn)
    server.start()
