import socket
import struct
import logging
import threading

if __name__ == "__main__":
    from streamer import Streamer
    from frame import FrameObserver
else:
    from .streamer import Streamer
    from .frame import FrameObserver

class Server(FrameObserver):
    BUFFER_SIZE = 4096

    def __init__(self, host: str, port: int, maxconn: int, logger: logging.Logger) -> None:
        self.host = host
        self.port = port
        self.maxconn = maxconn
        self.logger = logger
        self._conns = []
        self._server_socket = None
        self.frame_value = None
        self._ishost = False

    # def frame_callback(self, frame_value: bytes) -> None:
    #     self.frame_value = frame_value

    def update(self, frame_value: bytes) -> None:
        self.frame_value = frame_value
        return super().update(frame_value)

    def setup_server_socket(self) -> None:
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind((self.host, self.port))
        self._server_socket.listen(self.maxconn)
        self._server_socket.settimeout(3)
        self.logger.info(f"Server listening on {self._server_socket.getsockname()}")
        self._ishost = True

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
            self.setup_server_socket()
            self.streamer = Streamer(self.update)
            stream_thread = threading.Thread(
                target=self.streamer.start,
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
        if self._server_socket:
            self._ishost = False
            self._server_socket.close()

    def get_logger(self) -> logging.Logger:
        return self.logger

    def get_frame_value(self) -> bytes:
        return self.frame_value

    def ishost(self) -> bool:
        return self._ishost

    def change_camera_option(self, option: int) -> None:
        self.streamer.change_camera(option)

if __name__ == "__main__":
    from logger import setup_logger
    hostname = socket.gethostname()
    host = socket.gethostbyname(hostname)
    port = 0
    maxconn = 5
    logger = setup_logger(f"{__name__}.Server")

    # server = Server(host, port, maxconn, logger)
    server = Server(hostname, 12345, maxconn, logger)
    # server.start()
    comm_thread = threading.Thread(
        target=server.start,
        args=(),
        daemon=True
    )
    comm_thread.start()

    import cv2
    import pickle
    try:
        while True:
            if server.get_frame_value() is not None:
                flipped_frame = cv2.flip(pickle.loads(server.get_frame_value()), 1)
                cv2.imshow("Display window From Server", flipped_frame)
                if cv2.waitKey(1) & 0xFF == ord('q'): 
                    break
        cv2.destroyAllWindows()
    except KeyboardInterrupt:
        server.logger.info("KeyboardInterrupt received. Closing connection.")