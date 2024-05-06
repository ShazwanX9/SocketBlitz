import cv2
import pickle
from typing import Callable

if __name__ == "__main__":
    from frame import FrameSubject
else:
    from .frame import FrameSubject

def count_connected_cameras() -> int:
    num_cameras = 0
    index = 0
    while True:
        cap = cv2.VideoCapture(index)
        if not cap.isOpened():
            break
        num_cameras += 1
        cap.release()
        index += 1
    return num_cameras

class Streamer(FrameSubject):
    def __init__(self, frame_callback: Callable[[bytes], None] = None) -> None:
        self.frame_callback = frame_callback
        self.frame_value = None
        self.cap = None
        self.camera = 0
        self.isrunning = True

    def start(self) -> None:
        while self.isrunning:
            if self.cap is not None:
                self.cap.release()
            self.cap = cv2.VideoCapture(self.camera)

            curcamera=self.camera
            while self.cap.isOpened():
                ret, frame = self.cap.read()
                if not ret or self.camera != curcamera:
                    break
                self.frame_value = pickle.dumps(frame)
                if self.frame_callback:
                    self.frame_callback(self.frame_value)

    def stop(self):
        self.isrunning = False

    def change_camera(self, new_camera):
        self.camera = new_camera

    def get_frame_value(self):
        return self.frame_value