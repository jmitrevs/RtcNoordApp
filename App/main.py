"""First version of the RTCnoord application

Used to process and use the Powerline logger data.
Input is the csv_data that can be extracted from the Powerline software.

This program is a Qt program with a custom backend for use with QtQuick.
Matplotlib is used for the graphs.

"""

import sys, os, math, time, csv, yaml, shlex

import numpy as np

from PyQt5.QtGui import QGuiApplication
from PyQt5.QtQml import QQmlApplicationEngine, qmlRegisterType

# import matplotlib
# matplotlib.use('Agg')
import matplotlib.pyplot as plt

sys.path.append('../QtQuickBackend')
from backend_qtquick5 import FigureCanvasQTAggToolbar, MatplotlibIconProvider

import globalData as gd

from gui import *
from utils import *
from profil import *

def interactive(session=None):
    """For interactive use in python.

    This function creates the global variables associated with the currently selected session.
    To use this software from the python prompt do the following:

    import globaldata as gd
    import main
    main.interactive()

    Now the global data can be used for experiments and development.

    gd.sessionInfo
    import matplotlib.pyplot as plt

    plt.plot(gd.dataObject[:, 2]

"""

    gd.config = startup()
    gd.globals = readGlobals()
    gd.sessionInfo = selectSession()

    if session is not None:
        gd.config['Session'] = session

    # if data cached, use that.
    file = os.path.expanduser('~') + '/' + gd.config['BaseDir'] + '/caches/' + gd.config['Session'] + '.npy'
    try:
        fd = open(file, 'r')
        fd.close()
        gd.dataObject = np.load(file)
    except IOError:
        # first time, when there is no cache yet
        makecache(file)

    # print(gd.sessionInfo)
    

def cleanup_mpv():
    gd.submpv.kill()
    del(gd.submpv)
    
def main():
    """The main entry point when used as regular app

    It assumes a session is selected. When not, a dummy session None is used.
    A real session can be selected from the menu.
    Either an existing session or  new one using a csv-file.

    """

    # mainly for mpv program
    sys.exitfunc = cleanup_mpv

    gd.config = startup()
    # always start without secondary session
    gd.config['Session2'] = None
    gd.globals = readGlobals()

    # sys_argv = sys.argv
    # sys_argv += ['--style', 'material']
    app = QGuiApplication(sys.argv)
    
    # needed by filedialog
    app.setOrganizationName("RTC noord")
    app.setOrganizationDomain("RTC")
    app.setApplicationName("RtcNoordApp")

    qmlRegisterType(FigureCanvasQTAggToolbar, "Backend", 1, 0, "FigureToolbar")
    imgProvider = MatplotlibIconProvider()

    engine = QQmlApplicationEngine(parent=app)
    engine.addImageProvider("mplIcons", imgProvider)
    context = engine.rootContext()

    # Setup pieces
    gd.data_model = DataSensorsModel()
    context.setContextProperty("sensorModel", gd.data_model)
    gd.mainPieces = FormPieces(data=gd.data_model)
    context.setContextProperty("draw_mpl", gd.mainPieces)
    # model to create pieces
    gd.data_model2 = DataPiecesModel()
    context.setContextProperty("makePiecesModel", gd.data_model2)
        
    # View piece
    gd.data_model3 = DataSensorsModel()
    context.setContextProperty("sensorModel3", gd.data_model3)
    # model for secondary session
    gd.data_model4 = DataSensorsModel()
    context.setContextProperty("sensorModel4", gd.data_model4)
    gd.mainView = FormView(data=gd.data_model3, data2=gd.data_model4)
    context.setContextProperty("piece_mpl", gd.mainView)
    gd.data_model5 = DataPiecesModel()
    context.setContextProperty("viewPiecesModel", gd.data_model5)
        
    # Boat
    gd.boattablemodel = BoatTableModel()
    context.setContextProperty("boatTableModel", gd.boattablemodel)
    gd.boatPlots = BoatForm()
    context.setContextProperty("boat_mpl", gd.boatPlots)

    # Crew
    gd.crewPlots = CrewForm()
    context.setContextProperty("crew_mpl", gd.crewPlots)


    engine.load("qml/main.qml")

    win = engine.rootObjects()[0]
    gd.mainPieces.figure = win.findChild(QObject, "pieces").getFigure()
    gd.mainView.figure = win.findChild(QObject, "viewpiece").getFigure()
    gd.boatPlots.figure = win.findChild(QObject, "viewboat").getFigure()
    gd.crewPlots.figure = win.findChild(QObject, "viewcrew").getFigure()

    engine.quit.connect(app.quit)
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
