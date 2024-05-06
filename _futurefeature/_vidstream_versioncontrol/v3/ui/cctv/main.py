import cv2
import threading

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen

from kivy.utils import platform
from kivy.uix.image import Image
from kivy.uix.camera import Camera
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.properties import (
    NumericProperty, StringProperty,
    BooleanProperty, ObjectProperty
)

from module import Server
from module import VideoPlugin
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

# def getIP():
#     from jnius import autoclass
#     PythonActivity = autoclass('org.renpy.android.PythonActivity')
#     SystemProperties = autoclass('android.os.SystemProperties')
#     Context = autoclass('android.content.Context')
#     wifi_manager = PythonActivity.mActivity.getSystemService(Context.WIFI_SERVICE)
#     int_to_ip4 = lambda x: '.'.join(str(int((x + 2 ** 32) / (256 ** i) % 256)) for i in range(4))
#     ip = wifi_manager.getConnectionInfo()
#     ip = ip.getIpAddress()
#     ip = int_to_ip4(int(ip))
#     return ip

class GetSocketVar:
    HOST = '0.0.0.0'
    PORT = 0
    MAX_CONN = 5
    LOGGER = setup_logger(f"{__name__}.Server")

class GetScreenName:
    CONNECT_SERVER_SCREEN = "connect_server_screen"
    VIDEO_HOSTING_SCREEN = "video_hosting_screen"

import numpy as np
class KivyVideoPlugin(Camera, VideoPlugin):
    def update_frame(self):
        frame_data = self.texture.pixels
        width = self.texture.width
        height = self.texture.height
        frame_np = np.frombuffer(frame_data, dtype=np.uint8).reshape((height, width, 4))
        if platform == "android":
            frame_np = np.transpose(frame_np, (1, 0, 2))
            frame_np = np.flip(frame_np, axis=1)
        self.set_frame_value(frame_np)

    def on_texture(self, instance, value):
        value = value.flip_horizontal()
        return super().on_texture(instance, value)

video_plugin = KivyVideoPlugin(play=True)
server = Server(
    GetSocketVar.HOST, 
    GetSocketVar.PORT,
    GetSocketVar.MAX_CONN,
    plugins=[video_plugin],
    logger=GetSocketVar.LOGGER
)

class VideoHostingScreen(MDScreen):
    FPS = NumericProperty(1/60)
    # FPS = NumericProperty(2)
    # count_connected_cameras()
    total_camera = NumericProperty(0)
    camera_layout = ObjectProperty()

    hostname = StringProperty("")
    portnum = NumericProperty()

    def update_image(self, dt=-1) -> None:
        video_plugin.update_frame()
        frame_value = video_plugin.get_frame_value()
        if frame_value is not None:
            frame = frame_value
            frame_flipped = cv2.flip(frame, -1)
            frame_rgb = cv2.cvtColor(frame_flipped, cv2.COLOR_RGB2RGBA)
            buf = frame_rgb.tobytes()
            texture = Texture.create(size=(frame_flipped.shape[1], frame_flipped.shape[0]), colorfmt='rgba')
            texture.blit_buffer(buf, colorfmt='rgba', bufferfmt='ubyte')
            self.ids.image.texture = texture
            self.ids.image.reload()
        if self.manager.current==self.name: Clock.schedule_once(self.update_image, self.FPS)

    def on_enter(self, *args):
        self.hostname, self.portnum = server._server_socket.getsockname()
        # if platform=="android":
        #     self.hostname += f" | {getIP()}"
        video_plugin.play = True
        if not video_plugin.parent: self.camera_layout.add_widget(video_plugin)
        Clock.schedule_once(self.update_image, self.FPS)
        return super().on_enter(*args)

    def on_leave(self, *args):
        video_plugin.play = False
        Clock.schedule_once(self.update_image, self.FPS)
        return super().on_leave(*args)

    def disconnect(self) -> None:
        server.shutdown()

class MainApp(MDApp):
    iswaiting = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Clock.schedule_interval(self.check_connection, 5)

    def check_connection(self, dt=-1) -> None:
        if self.root and server.is_server_listening():
            self.root.current = GetScreenName.VIDEO_HOSTING_SCREEN
        elif self.root:
            self.root.current = GetScreenName.CONNECT_SERVER_SCREEN
            self.iswaiting = False

    def host_server(self) -> None:
        self.iswaiting = True
        comm_thread = threading.Thread(
            target=server.start,
            daemon=True
        )
        comm_thread.start()

    def build(self):
        self.theme_cls.primary_palette = "Orange"
        self.theme_cls.theme_style = "Light"  # "Dark"
        if platform == 'android':
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