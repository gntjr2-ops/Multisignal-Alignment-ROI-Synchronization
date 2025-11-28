# app.py
import sys
from PySide6.QtWidgets import QApplication
from main_window import ROISyncApp

def main():
    app = QApplication(sys.argv)
    gui = ROISyncApp()
    gui.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
