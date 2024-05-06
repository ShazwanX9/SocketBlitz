class Plugin:
    def setup(self, server) -> None:
        pass

    def send(self, server, client_socket, addr) -> None:
        pass

    def receive(self, server, client_socket, addr) -> None:
        pass

import pickle

class VideoPlugin(Plugin):
    BUFFER_SIZE = 4096

    def __init__(self) -> None:
        super().__init__()
        self.frame_value = None
        self.cap = None
        self.camera = 0
        self.isrunning = True

    def start(self):
        self.isrunning = True

    def stop(self):
        self.isrunning = False

    def change_camera(self, new_camera):
        self.camera = new_camera

    def get_frame_value(self):
        return self.frame_value

    def set_frame_value(self, frame):
        self.frame_value = frame

    def send(self, server, client_socket, addr) -> None:
        # For server to send data to client
        # run in the server thread
        while True:
            while self.isrunning:
                if self.frame_value is not None:
                    serialized_data = pickle.dumps(self.frame_value)
                    # client_socket.sendall(struct.pack("L", len(serialized_data)))
                    # client_socket.sendall(serialized_data)
                    # message = struct.pack("!Q", len(serialized_data)) + serialized_data
                    # client_socket.sendall(message)
                    data_length = len(serialized_data)
                    # Fixed-size header of length 8
                    header = b"%08d" % data_length
                    message = header + serialized_data
                    client_socket.sendall(message)

    def receive(self, client_socket) -> None:
        # For client to receive data from server
        # run in the client thread
        while True:
            while self.isrunning:
                # Receive fixed-size header of length 8
                header = client_socket.recv(8)
                if len(header) < 8:
                    raise RuntimeError("Failed to receive header")
                data_length = int(header)
                received_data = b""
                while len(received_data) < data_length:
                    packet = client_socket.recv(min(data_length - len(received_data), self.BUFFER_SIZE))
                    if not packet:
                        raise RuntimeError("Incomplete data received")
                    received_data += packet
                self.set_frame_value(pickle.loads(received_data))

import cv2
class CV2VideoPlugin(VideoPlugin):
    def setup(self, server) -> None:
        # A function that will be run in the server thread
        # Using cv2
        while True:
            while self.isrunning:
                if self.cap is not None:
                    self.cap.release()
                self.cap = cv2.VideoCapture(self.camera)

                curcamera=self.camera
                while self.cap.isOpened():
                    ret, frame = self.cap.read()
                    if not ret or self.camera != curcamera:
                        break
                    self.set_frame_value(frame)
        return super().setup(server)