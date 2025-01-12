from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QFrame, QDialog
from PyQt5.QtGui import QFont, QColor, QIcon
from PyQt5.QtCore import Qt
from kasperdb import db
from .karyadiscord import connectBot


class DiscordBotGUI(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Discord Bot Manager")
        self.setGeometry(100, 100, 600, 400)
        self.setWindowIcon(QIcon("icon.png"))
        self.setStyleSheet("background-color: #1e1e2f; color: #ffffff;")

        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.title_label = QLabel("⚙️ Discord Bot Manager")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setFont(QFont("Arial", 18, QFont.Bold))
        self.title_label.setStyleSheet("color: #f39c12; margin: 10px 0;")
        self.layout.addWidget(self.title_label)

        self.add_separator()

        # Поле ввода токена
        token_layout = QHBoxLayout()
        self.token_input = QLineEdit()
        self.token_input.setPlaceholderText("Введите токен бота...")
        self.token_input.setFont(QFont("Arial", 12))
        self.token_input.setStyleSheet("""
            QLineEdit {
                background-color: #2c2f38;
                border: 1px solid #444;
                border-radius: 8px;
                padding: 8px;
                color: #ffffff;
            }
            QLineEdit:focus {
                border: 1px solid #f39c12;
            }
        """)
        self.token_input.setText(db.get("database/settings").get("discord_token", ""))
        self.connect_button = QPushButton("Подключить")
        self.connect_button.setFont(QFont("Arial", 12))
        self.connect_button.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: #ffffff;
                border-radius: 10px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #e67e22;
            }
        """)
        self.connect_button.clicked.connect(self.connect_bot)

        token_layout.addWidget(self.token_input)
        token_layout.addWidget(self.connect_button)
        self.layout.addLayout(token_layout)

        self.add_separator()

        # Статус-бар
        self.status_label = QLabel("Статус: Отключен")
        self.status_label.setFont(QFont("Arial", 10))
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #bbbbbb; margin: 10px 0;")
        self.layout.addWidget(self.status_label)

    def add_separator(self):
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("color: #444; margin: 10px 0;")
        self.layout.addWidget(separator)

    def create_styled_button(self, text, handler, enabled=True):
        button = QPushButton(text)
        button.setFont(QFont("Arial", 12))
        button.setStyleSheet("""
            QPushButton {
                background-color: #4caf50;
                color: #ffffff;
                border-radius: 10px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #388e3c;
            }
            QPushButton:disabled {
                background-color: #555;
                color: #888;
            }
        """)
        button.setEnabled(enabled)
        button.clicked.connect(handler)
        return button

    def connect_bot(self):
        token = self.token_input.text()
        if token:
            self.status_label.setText("Статус: Подключение...")
            try:
                connectBot(token)
                self.status_label.setText("Статус: Подключен")
                data = db.get("database/settings")
                data["discord_token"] = token
                db.set("database/settings", data)
            except Exception as e:
                self.status_label.setText(f"Статус: Ошибка: {str(e)}")
        else:
            self.status_label.setText("Статус: Введите токен!")

def startDSui():
    window = DiscordBotGUI()
    window.exec_()