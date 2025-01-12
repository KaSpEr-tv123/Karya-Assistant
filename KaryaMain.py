from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QLineEdit,
    QTextEdit,
    QHBoxLayout,
    QDialog
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor, QIcon

from modules.chat import karya_request
from modules.command_compiler import CommandCompiler
from modules.autoupdate import main
from modules.discordUI import startDSui
import modules.karyadiscord
import modules.types

from kasperdb import db

import asyncio

def get_username():
    return db.get("database/username")["username"] if db.get("database/username") else None

def set_username(username):
    db.set("database/username", {"username": username})

class MainMenu(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Главное меню")
        self.setGeometry(200, 200, 400, 300)
        self.setStyleSheet("background-color: #2c2f38;")

        font = QFont("Arial", 12)
        font.setBold(True)

        layout = QVBoxLayout()

        # Кнопка для запуска Discord UI
        discord_ui_button = QPushButton("Настроить Discord бота", self)
        discord_ui_button.setFont(font)
        discord_ui_button.setStyleSheet(self.get_button_style())
        discord_ui_button.clicked.connect(self.start_discord_ui)
        layout.addWidget(discord_ui_button)

        clear = QPushButton("Очистить чат", self)
        clear.setFont(font)
        clear.setStyleSheet(self.get_button_style())
        clear.clicked.connect(parent.clear_chat)
        layout.addWidget(clear)

        self.setLayout(layout)

    def start_discord_ui(self):
        startDSui()

    def get_button_style(self):
        return """
            QPushButton {
                background-color: #0078d4;
                color: white;
                border-radius: 10px;
                padding: 10px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #005fa3;
            }
        """

class KaryaGUI(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Karya Assistant")
        self.setWindowIcon(QIcon("karya.ico"))
        self.setGeometry(100, 100, 600, 500)
        self.setStyleSheet("background-color: #2c2f38;")

        self.font = QFont("Arial", 12)
        self.font.setBold(True)

        self.username = get_username()
        self.dark_mode = True

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.initUI()

    def initUI(self):
        for i in reversed(range(self.layout.count())):
            widget = self.layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()

        if self.username is None:
            self.show_username_input()
        else:
            self.show_chat_ui()

    def show_username_input(self):
        label = QLabel("Введите ваше имя пользователя:", self)
        label.setFont(self.font)
        label.setStyleSheet("color: white;")
        label.setAlignment(Qt.AlignCenter)

        username_input = QLineEdit(self)
        username_input.setFont(self.font)
        username_input.setStyleSheet("background-color: #444; color: white; padding: 5px;")
        username_input.setPlaceholderText("Ваше имя")

        submit_button = QPushButton("Подтвердить", self)
        submit_button.setFont(self.font)
        submit_button.setStyleSheet(self.get_button_style())
        submit_button.clicked.connect(lambda: self.on_submit_click(username_input.text()))

        self.layout.addWidget(label)
        self.layout.addWidget(username_input)
        self.layout.addWidget(submit_button)

    def show_chat_ui(self):
        self.chat_area = QTextEdit(self)
        self.chat_area.setFont(self.font)
        self.chat_area.setStyleSheet("background-color: #2c2f38; color: white; border: 1px solid #444;")
        self.chat_area.setReadOnly(True)
        self.layout.addWidget(self.chat_area)

        input_layout = QHBoxLayout()

        self.input_area = QLineEdit(self)
        self.input_area.setFont(self.font)
        self.input_area.setStyleSheet("background-color: #444; color: white; padding: 5px;")
        self.input_area.setPlaceholderText("Введите сообщение...")
        input_layout.addWidget(self.input_area)

        send_button = QPushButton("Отправить", self)
        send_button.setFont(self.font)
        send_button.setStyleSheet(self.get_button_style())
        send_button.clicked.connect(self.on_send_click)
        input_layout.addWidget(send_button)

        self.layout.addLayout(input_layout)

        control_layout = QHBoxLayout()

        main_menu_button = QPushButton("Главное меню", self)
        main_menu_button.setFont(self.font)
        main_menu_button.setStyleSheet(self.get_button_style())
        main_menu_button.clicked.connect(self.open_main_menu)
        control_layout.addWidget(main_menu_button)

        self.layout.addLayout(control_layout)

    def on_submit_click(self, username):
        if username:
            set_username(username)
            self.username = username
            self.initUI()

    def on_send_click(self):
        user_message = self.input_area.text()
        if user_message.strip():
            self.chat_area.setTextColor(QColor("white"))
            self.chat_area.append(f"{self.username}: {user_message}")
            response = karya_request(self.username, user_message, CommandCompiler.commands)
            self.chat_area.setTextColor(QColor(238, 130, 238))
            self.chat_area.append(f"Каря: {response}")
            self.input_area.clear()
            asyncio.run(CommandCompiler.compile(response, self))

    def clear_chat(self):
        self.chat_area.clear()

    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        if self.dark_mode:
            self.setStyleSheet("background-color: #2c2f38;")
            self.chat_area.setStyleSheet("background-color: #2c2f38; color: white; border: 1px solid #444;")
            self.input_area.setStyleSheet("background-color: #444; color: white; padding: 5px;")
        else:
            self.setStyleSheet("background-color: #f0f0f0;")
            self.chat_area.setStyleSheet("background-color: #ffffff; color: black; border: 1px solid #ccc;")
            self.input_area.setStyleSheet("background-color: #ffffff; color: black; padding: 5px;")

    def open_main_menu(self):
        main_menu = MainMenu(self)
        main_menu.exec_()

    def get_button_style(self):
        return """
            QPushButton {
                background-color: #0078d4;
                color: white;
                border-radius: 10px;
                padding: 10px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #005fa3;
            }
        """

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.on_send_click()

def get_app():
    return QApplication([])

def start():
    app = get_app()
    window = KaryaGUI()
    window.show()
    app.exec_()

if __name__ == "__main__":
    main()
    start()