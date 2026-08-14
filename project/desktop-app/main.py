"""
GameMaster - PUBG Controller
Entry point. Run with: python main.py
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

from src.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("GameMaster")
    app.setOrganizationName("GameMaster")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
