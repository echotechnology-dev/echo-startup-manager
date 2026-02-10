import sys
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow
from utils.admin import is_admin, relaunch_as_admin

def main():
    if not is_admin():
        relaunch_as_admin()
        return

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
