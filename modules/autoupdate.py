import sys
import os
import requests
import time
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel, QProgressBar, QMessageBox
from PyQt5.QtCore import Qt, QThread, pyqtSignal

# Настройки
GITHUB_REPO_URL = "https://github.com/KaSpEr-tv123/Karya-Assistant/releases/download/Karya-Assistant/"
CURRENT_VERSION = "2.0"
EXE_NAME = "KaryaAssistant.exe"


class UpdateThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(bool, str)

    def __init__(self):
        super().__init__()
        self.latest_version = None

    def run(self):
        try:
            # Проверяем версию
            version_url = f"https://raw.githubusercontent.com/KaSpEr-tv123/Karya-Assistant/refs/heads/main/version.txt"
            response = requests.get(version_url)
            response.raise_for_status()
            self.latest_version = response.text.strip()

            if float(self.latest_version) > float(CURRENT_VERSION):
                # Скачиваем новый файл
                exe_url = f"{GITHUB_REPO_URL}{EXE_NAME}"
                response = requests.get(exe_url, stream=True)
                response.raise_for_status()

                total_size = int(response.headers.get('content-length', 0))
                temp_file = EXE_NAME

                if os.path.exists(EXE_NAME):
                    os.rename(EXE_NAME, f".old_{EXE_NAME}")
                with open(temp_file, "wb") as f:
                    downloaded = 0
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            self.progress.emit(int(downloaded / total_size * 100))

                self.finished.emit(True, temp_file)
            elif float(self.latest_version) < float(CURRENT_VERSION):
                self.finished.emit(False, "У вас черезчур актуальная версия.")
            else:
                self.finished.emit(False, "Программа уже актуальна.")
            return
        except Exception as e:
            self.finished.emit(False, str(e))
            return


class UpdateApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Обновление программы")
        self.setGeometry(100, 100, 400, 200)

        # Виджеты
        self.label = QLabel("Текущая версия: " + CURRENT_VERSION, self)
        self.label.setAlignment(Qt.AlignCenter)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)

        self.check_for_updates()

        # Макет
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.progress_bar)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.update_thread = None

    def check_for_updates(self):
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        # Запуск потока
        self.update_thread = UpdateThread()
        self.update_thread.progress.connect(self.progress_bar.setValue)
        self.update_thread.finished.connect(self.on_update_finished)
        self.update_thread.start()

    def on_update_finished(self, success, message):
        self.progress_bar.setVisible(False)

        if success:
            QMessageBox.information(self, "Обновление завершено", "Новая версия загружена. Программа будет перезапущена.")
            self.apply_update(message)
        else:
            self.close()

    def apply_update(self, temp_file):
        os.startfile(temp_file)
        sys.exit()

def main():
    app = QApplication(sys.argv)
    window = UpdateApp()
    window.show()
    app.exec_()
