import sys
from PyQt5.QtGui import QGuiApplication
from PyQt5.QtQml import QQmlApplicationEngine

def main():

    app = QGuiApplication(sys.argv)

    app.setOrganizationName("RTC noord")
    app.setOrganizationDomain("RTC")
    app.setApplicationName("RtcNoordApp")

    engine = QQmlApplicationEngine(parent=app)

    engine.load("qml/test-main.qml")

    engine.quit.connect(app.quit)
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
