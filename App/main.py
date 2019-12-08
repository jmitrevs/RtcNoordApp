"""
  First version of the RTCnoord application to process and use the Powerline logger data

"""

import sys, os, math, time, csv, yaml

import numpy as np

from PyQt5.QtGui import QGuiApplication
from PyQt5.QtQml import QQmlApplicationEngine, qmlRegisterType
from PyQt5.QtCore import QVariant, QObject, pyqtSignal, pyqtSlot, pyqtProperty, QMetaObject, Qt, QTimer, QByteArray, QAbstractListModel, QModelIndex

# import matplotlib
# matplotlib.use('Agg')
import matplotlib.pyplot as plt

sys.path.append('../QtQuickBackend')
from backend_qtquick5 import FigureCanvasQTAggToolbar, MatplotlibIconProvider

# globals
data_model3 = None
#  voor interactief werk
sessionInfo = None
dataObject = None

from gui import *
from utils import *

# To use this software from the python prompt
#   import main
#   main.interactive()
#   main.sessionInfo
#   main.dataObject[2,3]
def interactive():
    global sessionInfo, dataObject

    config = startup()
    globals = readGlobals(config)

    # dit later starten via de gui?
    sessionInfo = selectSession(config)
    t = time.time()

    # if data cached, use that. Much faster load
    file = os.path.expanduser('~') + '/' + config['BaseDir'] + '/caches/' + config['Session'] + '.npy'
    try:
        fd = open(file, 'r')
        fd.close()
        dataObject = np.load(file)
        h1 = sessionInfo['Header']
        h2 = sessionInfo['Header2']
    except IOError:
        # first time, when there is no cache yet
        csvdata = []
        h1, h2 = readCsvData(config, csvdata)
        dataObject = np.asarray(csvdata)
        np.save(file, dataObject)

        # add 2 header rows and tempo list to sessionInfo
        #   header lijst maken met positie van de sensor in de boot erbij?
        sessionInfo['Header'] = h1
        sessionInfo['Header2'] = h2
        try:
            i = h1.index('P GateAngle')
        except ValueError:
            i = h1.index('GateAngle')
        sessionInfo['Tempi'] = tempi(dataObject[:, i])            

        saveSessionInfo(sessionInfo, config)

    print(sessionInfo)
    
# When used as the regular app
def main():
    global data_model3, sessionInfo, dataObject
    
    config = startup()
    globals = readGlobals(config)

    # dit later starten via de gui?
    sessionInfo = selectSession(config)
    t = time.time()

    # if data cached, use that. Much faster load
    file = os.path.expanduser('~') + '/' + config['BaseDir'] + '/caches/' + config['Session'] + '.npy'
    try:
        fd = open(file, 'r')
        fd.close()
        dataObject = np.load(file)
        h1 = sessionInfo['Header']
        h2 = sessionInfo['Header2']
    except IOError:
        # first time, when there is no cache yet
        csvdata = []
        h1, h2 = readCsvData(config, csvdata)
        dataObject = np.asarray(csvdata)
        np.save(file, dataObject)

        # add 2 header rows and tempo list to sessionInfo
        #   header lijst maken met positie van de sensor in de boot erbij?
        sessionInfo['Header'] = h1
        sessionInfo['Header2'] = h2
        try:
            i = h1.index('P GateAngle')
        except ValueError:
            i = h1.index('GateAngle')
        sessionInfo['Tempi'] = tempi(dataObject[:, i])            

        saveSessionInfo(sessionInfo, config)

    app = QGuiApplication(sys.argv)
    qmlRegisterType(FigureCanvasQTAggToolbar, "Backend", 1, 0, "FigureToolbar")
    imgProvider = MatplotlibIconProvider()

    engine = QQmlApplicationEngine(parent=app)
    engine.addImageProvider("mplIcons", imgProvider)
    context = engine.rootContext()
    
    # Setup pieces
    data_model = DataSensorsModel(sessionInfo['Header'])
    context.setContextProperty("sensorModel", data_model)
    mainPieces = FormPieces(data=data_model, tempi=sessionInfo['Tempi'], traces=dataObject)
    context.setContextProperty("draw_mpl", mainPieces)

    # View piece
    data_model2 = DataSensorsModel(sessionInfo['Header'])
    context.setContextProperty("sensorModel2", data_model2)    
    mainView = FormView(data=data_model2, traces=dataObject)
    context.setContextProperty("piece_mpl", mainView)

    # model to create Pieces
    data_model3 = DataPiecesModel()
    context.setContextProperty("makePiecesModel", data_model3)
        
    engine.load("qml/main.qml")

    win = engine.rootObjects()[0]
    mainPieces.figure = win.findChild(QObject, "pieces").getFigure()
    mainView.figure = win.findChild(QObject, "viewpiece").getFigure()

    engine.quit.connect(app.quit)
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
