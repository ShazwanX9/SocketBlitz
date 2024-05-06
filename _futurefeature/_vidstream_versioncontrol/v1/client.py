import os
import cv2
import struct
import pickle
import socket
import threading
import logging

class Client:
    BUFFER_SIZE = 1024

    def __init__(self, client_name="", server_address="", server_port=8000) -> None:
        self.client_name = client_name
        self.server_address = server_address
        self.server_port = server_port
        self._client_socket = None
        self.logger = self.setup_logger()
        self._lock = threading.Lock()
        self.connected = False
        self.frame = None

    def change_name(self, client_name: str) -> None:
        self.client_name = client_name

    def change_server(self, server_address: str, server_port: int) -> None:
        self.server_address = server_address
        self.server_port = server_port

    def get_sendfile_format(self, filepath: str) -> str:
        return self.FILE_SENDING_HEADER+filepath

    def get_connection(self) -> bool:
        return self.connected

    def get_recent_frame(self):
        return self.frame

    def setup_logger(self) -> logging.Logger:
        logger = logging.getLogger(f"{__name__}.Client")
        formatter = logging.Formatter('[%(levelname)s] %(message)s')
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        logger.setLevel(logging.INFO)
        return logger

    def listen_server(self):
        data = b""
        payload_size = struct.calcsize("L")

        try:
            while True:
                # Receive frame size
                while len(data) < payload_size:
                    data += self._client_socket.recv(4096)

                # Extract frame size
                packed_msg_size = data[:payload_size]
                data = data[payload_size:]
                msg_size = struct.unpack("L", packed_msg_size)[0]

                # Receive frame data
                while len(data) < msg_size:
                    data += self._client_socket.recv(4096)

                # Extract frame data
                frame_data = data[:msg_size]
                data = data[msg_size:]

                # Deserialize frame
                self.frame = pickle.loads(frame_data)
                # self.handle_data(self.frame)

        except (socket.error, OSError, KeyboardInterrupt) as e:
            self.logger.error(f"Error: {e}")
        finally:
            self.close_conn()

    def handle_data(self, data=None) -> None:
        while True:
            if self.frame is not None:
                # print("Displaying frame...")
                flipped_frame = cv2.flip(self.frame, 1)
                cv2.imshow("Display window", flipped_frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):  # Press 'q' to exit
                    break
        cv2.destroyAllWindows()

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
            # ui_thread = threading.Thread(
            #     target=self.handle_data,
            #     args=(),
            #     daemon=True
            # )
            # ui_thread.start()
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
    server_address = socket.gethostname()
    server_port = 12345
    # server_address = input("SERVER ADDR: ")
    # server_port = int(input("SERVER PORT: "))

    import random
    client = Client(
        str(random.random()), 
        server_address, 
        server_port
    )
    client.start()
    
    try:
        while True:
            if client.get_recent_frame() is not None:
                # print("Displaying frame...")
                flipped_frame = cv2.flip(client.get_recent_frame(), 1)
                cv2.imshow("Display window", flipped_frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):  # Press 'q' to exit
                    break
        cv2.destroyAllWindows()
    #         data = input("Message: ")
    #         client.send(data)
    except KeyboardInterrupt:
        client.logger.info("KeyboardInterrupt received. Closing connection.")
