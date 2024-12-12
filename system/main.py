import sys
from PyQt5.QtWidgets import QApplication
from main_window import MainWindow
#from login_window import LoginWindow


def main():
    app = QApplication(sys.argv)
    login_window = MainWindow()
    login_window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
