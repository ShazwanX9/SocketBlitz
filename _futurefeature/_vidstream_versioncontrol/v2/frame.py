import pickle

class FrameObserver:
    def update(self, frame_value: bytes) -> None:
        pass

class FrameSubject:
    def __init__(self) -> None:
        self.observers: list[FrameObserver] = []

    def add_observer(self, observer: FrameObserver) -> None:
        self.observers.append(observer)

    def remove_observer(self, observer: FrameObserver) -> None:
        self.observers.remove(observer)

    def notify_observers(self, frame_value: bytes) -> None:
        for observer in self.observers:
            observer.update(frame_value)

class FrameHandler:
    def __init__(self, client):
        self.client = client

    def handle_frame(self, frame_data):
        frame = pickle.loads(frame_data)
        self.client.set_recent_frame(frame)
