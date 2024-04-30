import os
from kivy.clock import Clock
from kivy.properties import StringProperty, BooleanProperty, ObjectProperty

from kivymd.app import MDApp
from kivymd.uix.widget import Widget
from kivymd.uix.screen import MDScreen
from kivymd.uix.filemanager import MDFileManager
from kivymd.uix.screenmanager import MDScreenManager 

from kivy.core.window import Window
Window.size = (375, 667)

from client import Client

class ClientManager:
    def __init__(self) -> None:
        self.client = Client()

    def get_connection(self) -> bool:
        return self.client.get_connection()

    def update_id(self, new_id: str) -> None:
        self.client_id = new_id
        self.client.change_name(new_id)

    def connect(self, server_address: str, server_port: int) -> None:
        self.server_address = server_address
        self.server_port = server_port
        self.client.change_server(self.server_address, self.server_port)
        self.client.start()

    def save_to(self, filepath: str) -> None:
        self.client.change_download_dir(filepath)

    def upload_file(self, filepath: str) -> None:
        fileformat = self.client.get_sendfile_format(filepath=filepath)
        self.client.send(fileformat)

    def disconnect(self) -> None:
        self.client.close_conn()

clientmanager = ClientManager()

class FileManager(Widget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        Window.bind(on_keyboard=self.events)
        self.manager_open = False
        self.directory_manager = MDFileManager(
            exit_manager=self.exit_directory_manager, select_path=self.select_directory
        )
        self.single_file_manager = MDFileManager(
            exit_manager=self.exit_single_file_manager, select_path=self.select_single_file
        )
        self.multi_file_manager = MDFileManager(
            exit_manager=self.exit_multi_file_manager, select_path=self.select_multi_file, selector="multi"
        )

    def callback(self, path: str) -> None:
        pass

    def show_directory_manager(self, callback=None):
        self.directory_manager.search = "dirs"
        self.directory_manager.selector = "folder"
        self.directory_manager.show(os.path.expanduser("~"))
        self.manager_open = True
        if callback: self.callback = callback

    def show_single_file_manager(self, callback=None):
        self.single_file_manager.selector = "file"
        self.single_file_manager.show(os.path.expanduser("~"))
        self.manager_open = True
        if callback: self.callback = callback

    def show_multi_file_manager(self, callback=None):
        self.multi_file_manager.selector = "file"
        self.multi_file_manager.show(os.path.expanduser("~"))
        self.manager_open = True
        if callback: self.callback = callback

    def select_directory(self, path):
        self.exit_directory_manager()
        self.callback(self.directory_manager.current_path)

    def select_single_file(self, path):
        self.exit_single_file_manager()
        self.callback(path)

    def select_multi_file(self, paths):
        self.exit_multi_file_manager()
        self.callback(", ".join(paths))

    def exit_directory_manager(self, *args):
        self.manager_open = False
        self.directory_manager.close()

    def exit_single_file_manager(self, *args):
        self.manager_open = False
        self.single_file_manager.close()

    def exit_multi_file_manager(self, *args):
        self.manager_open = False
        self.multi_file_manager.close()

    def switch_to_directory_manager(self):
        self.root.ids.screen_manager.current = "directory_manager"
        self.root.ids.directory_textfield.focus = True

    def switch_to_file_manager(self):
        self.root.ids.screen_manager.current = "file_manager"
        self.root.ids.files_textfield.focus = True

    def events(self, instance, keyboard, keycode, text, modifiers):
        if keyboard in (1001, 27):
            if self.manager_open:
                if self.directory_manager.manager:
                    self.exit_directory_manager()
                elif self.single_file_manager.manager:
                    self.exit_single_file_manager()
                elif self.multi_file_manager.manager:
                    self.exit_multi_file_manager()
        return True

class GetScreenName:
    SERVER_SCREEN = "connect_server_screen"
    FILE_TRANSFER_SCREEN = "file_transfer_screen"

class ConnectServerScreen(MDScreen):
    iswaiting = BooleanProperty(False)
    phone_num = StringProperty("")
    server_id = StringProperty("")
    server_port = StringProperty("")
    error_response = StringProperty("")

    def create_connection(self, dt=-1) -> None:
        clientmanager.update_id(self.phone_num)
        clientmanager.connect(self.server_id, int(self.server_port))
        if clientmanager.get_connection():
            self.error_response = ""
            self.manager.transition.direction = "left"
            self.manager.current = GetScreenName.FILE_TRANSFER_SCREEN
        else:
            self.error_response = "Failed to connect to server"
        self.iswaiting = False

    def connect(self) -> None:
        Clock.schedule_once(self.create_connection, 1)
        self.iswaiting = True

class FileTransferScreen(MDScreen):
    file_manager = ObjectProperty()
    savedir = StringProperty("./")
    filepath = StringProperty("")

    def update_savedir(self, filepath: str) -> None:
        self.savedir = filepath
        clientmanager.save_to(self.savedir)

    def update_filepath(self, filepath: str) -> None:
        self.filepath = filepath
        clientmanager.upload_file(self.filepath)

    def check_connection(self, dt=-1) -> None:
        if not clientmanager.get_connection():
            server_screen: ConnectServerScreen = self.manager.get_screen(GetScreenName.SERVER_SCREEN)
            server_screen.error_response = "Server Connection Lost"
            self.manager.transition.direction = "right"
            self.manager.current = GetScreenName.SERVER_SCREEN
        else:
            Clock.schedule_once(self.check_connection, 5)

    def on_enter(self):
        Clock.schedule_once(self.check_connection, 5)

    def quit(self) -> None:
        clientmanager.disconnect()
        self.check_connection()

class AppManager(MDScreenManager):
    file_manager = ObjectProperty()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.file_manager = FileManager()

class MainApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Orange"
        self.theme_cls.theme_style = "Light"  # "Dark"
        return AppManager()

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