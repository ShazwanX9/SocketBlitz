import cv2
import threading

from kivymd.app import MDApp
# from kivy.uix.screenmanager import Screen
from kivymd.uix.screen import MDScreen

from kivy.utils import platform
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.properties import (
    StringProperty, BooleanProperty, 
    NumericProperty, ObjectProperty,
)

from module import Client, DataHandler
from module import setup_logger

# Define the callback function to handle the permission request result
def on_permission_granted(permissions, results):
    for permission, result in zip(permissions, results):
        if result:
            print(f"Permission {permission} granted")
        else:
            print(f"Permission {permission} denied")

# Request permissions
def request_android_permissions():
    try:
        from android.permissions import request_permissions, Permission
        from android import activity

        request_permissions([
            Permission.INTERNET,
            Permission.CAMERA,
            Permission.WRITE_EXTERNAL_STORAGE,
            Permission.READ_EXTERNAL_STORAGE,
            Permission.ACCESS_NETWORK_STATE,
            Permission.CHANGE_NETWORK_STATE
        ], on_permission_granted)
    except Exception as e:
        print(f"Error requesting permissions: {e}")


class GetScreenName:
    SERVER_SCREEN = "connect_server_screen"
    VIDEO_HOSTING_SCREEN = "video_hosting_screen"

LOGGER = setup_logger(f"{__name__}.Server")
class ClientManager:
    def __init__(self) -> None:
        self.client = Client(logger=LOGGER)
        self.data_handler = DataHandler(self.client)

    def isconnected(self) -> bool:
        return self.client.get_connection()

    def update_id(self, new_id: str) -> None:
        self.client_id = new_id
        self.client.change_name(new_id)

    def connect(self, server_address: str, server_port: int) -> None:
        self.server_address = server_address
        self.server_port = server_port
        self.client.change_server(self.server_address, self.server_port)
        self.client.start()

        comm_thread = threading.Thread(
            target=self.data_handler.listen_server,
            args=(),
            daemon=True
        )
        comm_thread.start()

    def disconnect(self) -> None:
        self.client.close_conn()

    def get_recent_frame(self) -> bytes:
        return self.data_handler.get_recent_frame()

clientmanager = ClientManager()

class ConnectServerScreen(MDScreen):
    iswaiting = BooleanProperty(False)
    phone_num = StringProperty("")
    server_id = StringProperty("")
    server_port = StringProperty("")
    error_response = StringProperty("")

    def create_connection(self, dt=-1) -> None:
        clientmanager.update_id(self.phone_num)
        clientmanager.connect(self.server_id, int(self.server_port))
        if clientmanager.isconnected():
            self.error_response = ""
            self.manager.transition.direction = "left"
            self.manager.current = GetScreenName.VIDEO_HOSTING_SCREEN
        else:
            self.error_response = "Failed to connect to server"
        self.iswaiting = False

    def connect(self) -> None:
        Clock.schedule_once(self.create_connection, 1)
        self.iswaiting = True

class GetScreenName:
    CONNECT_SERVER_SCREEN = "connect_server_screen"
    VIDEO_HOSTING_SCREEN = "video_hosting_screen"

class VideoHostingScreen(MDScreen):
    FPS = NumericProperty(1/60)

    def update_image(self, image: Image) -> None:
        frame_value = clientmanager.get_recent_frame()
        if frame_value is not None:
            frame = frame_value
            frame_flipped = cv2.flip(frame, -1)
            frame_rgb = cv2.cvtColor(frame_flipped, cv2.COLOR_RGB2RGBA)
            buf = frame_rgb.tobytes()
            texture = Texture.create(size=(frame_flipped.shape[1], frame_flipped.shape[0]), colorfmt='rgba')
            texture.blit_buffer(buf, colorfmt='rgba', bufferfmt='ubyte')
            image.texture = texture
            image.reload()
        Clock.schedule_once(lambda dt: self.update_image(self.ids.image), self.FPS)

    def on_leave(self, *args):
        self.disconnect()
        return super().on_leave(*args)

    def on_enter(self, *args):
        Clock.schedule_once(lambda dt: self.update_image(self.ids.image), self.FPS)
        return super().on_enter(*args)

    def disconnect(self) -> None:
        clientmanager.disconnect()

class MainApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Clock.schedule_interval(self.check_connection, 5)

    def check_connection(self, dt=-1) -> None:
        if self.root and clientmanager.isconnected():
            self.root.current = GetScreenName.VIDEO_HOSTING_SCREEN
        elif self.root:
            self.root.current = GetScreenName.CONNECT_SERVER_SCREEN

    def build(self):
        self.theme_cls.primary_palette = "Orange"
        self.theme_cls.theme_style = "Light"  # "Dark"
        if platform == "android":
            request_android_permissions()
        return

    def switch_theme_style(self, btn):
        self.theme_cls.primary_palette = (
            "Orange" if self.theme_cls.primary_palette == "Red" else "Red"
        )
        self.theme_cls.theme_style = (
            "Dark" if self.theme_cls.theme_style == "Light" else "Light"
        )

    def on_start(self):
        self.root.md_bg_color = self.theme_cls.backgroundColor

if __name__ == "__main__":
    MainApp().run()