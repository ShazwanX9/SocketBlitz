import socket
import logging
import threading

if __name__ == "__main__":
    from plugin import Plugin, CV2VideoPlugin
else:
    from .plugin import Plugin, CV2VideoPlugin

class Server:
    BUFFER_SIZE = 4096

    def __init__(self, host: str, port: int, maxconn: int, plugins: list[Plugin] = [], logger: logging.Logger = None) -> None:
        self.host = host
        self.port = port
        self.maxconn = maxconn
        self.logger = logger
        self._plugins = plugins
        self._conns = []
        self._server_socket = None
        self._is_server_listening = False

    def is_server_listening(self) -> bool:
        return self._is_server_listening

    def setup_server_socket(self) -> None:
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind((self.host, self.port))
        self._server_socket.listen(self.maxconn)
        # self._server_socket.settimeout(3)
        self._is_server_listening = True
        if self.logger: self.logger.info(f"Server listening on {self._server_socket.getsockname()}")

    def _setup_plugin(self, plugin: Plugin) -> None:
        try:
            plugin.setup(self)
        except Exception as e:
            if self.logger: self.logger.error(f"Plugin error: {e}")

    def _start_plugin(self, plugin: Plugin, client_socket, addr) -> None:
        try:
            plugin.send(self, client_socket, addr)
        except Exception as e:
            if self.logger: self.logger.error(f"Plugin error: {e}")

    def start(self) -> None:
        try:
            self.setup_server_socket()
            for plugin in self._plugins:
                plugin_thread = threading.Thread(
                    target=self._setup_plugin,
                    args=(plugin, ),
                    daemon=True
                )
                plugin_thread.start()

            while True:
                try:
                    client_socket, addr = self._server_socket.accept()
                except socket.timeout:
                    continue  # Timeout occurred, try again

                for plugin in self._plugins:
                    plugin_thread = threading.Thread(
                        target=self._start_plugin,
                        args=(plugin, client_socket, addr),
                        daemon=True
                    )
                    plugin_thread.start()

                if self.logger: self.logger.info(f'Connected to {addr}')
                self._conns.append(client_socket)

        except KeyboardInterrupt:
            if self.logger: self.logger.info("KeyboardInterrupt received. Shutting down server.")
        except Exception as e:
            if self.logger: self.logger.error(f"Error in server loop: {e}")
        finally:
            self.shutdown()

    def close_conn(self, client_socket: socket.socket, addr: int = -1) -> None:
        # Close the connection
        if self.logger: self.logger.info(f"Connection closed with ({addr})")
        client_socket.close()
        self._conns.remove(client_socket)

    def shutdown(self) -> None:
        for client_socket in self._conns:
            self.close_conn(client_socket)
        if self._server_socket:
            self._is_server_listening = False
            self._server_socket.close()

if __name__ == "__main__":
    from logger import setup_logger
    hostname = socket.gethostname()
    host = socket.gethostbyname(hostname)
    host = ""
    port = 0
    maxconn = 5
    logger = setup_logger(f"{__name__}.Server")

    video_plugin = CV2VideoPlugin()

    server = Server(host, port, maxconn, plugins=[video_plugin], logger=logger)
    # server.start()
    comm_thread = threading.Thread(
        target=server.start,
        args=(),
        daemon=True
    )
    comm_thread.start()

    import cv2
    try:
        while True:
            if video_plugin.get_frame_value() is not None:
                flipped_frame = cv2.flip(video_plugin.get_frame_value(), 1)
                cv2.imshow("Display window From Server", flipped_frame)
                if cv2.waitKey(1) & 0xFF == ord('q'): 
                    break
        cv2.destroyAllWindows()
    except KeyboardInterrupt:
        if server.logger: server.logger.info("KeyboardInterrupt received. Closing connection.")