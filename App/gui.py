"""The Gui related classes for the RTCnoord app."""

import os, re, yaml, time
from shutil import copyfile, move
import numpy as np

from PyQt5.QtCore import QVariant, QObject, pyqtSignal, pyqtSlot, pyqtProperty, QMetaObject, Qt, QTimer, QByteArray, QAbstractListModel, QModelIndex
from PyQt5.QtGui import QColor

import globalData as gd

from utils import *

from models import *

import matplotlib.pyplot as plt

# matplotlib plot in Pieces
class FormPieces(QObject):

    legendChanged = pyqtSignal()
    statusTextChanged = pyqtSignal()
    stateChanged = pyqtSignal()

    def __init__(self, parent=None, data=None, tempi=[]):
        QObject.__init__(self, parent)

        s = gd.config['Session']
        if s == 'None':
            self._status_text = 'No session loaded, please create or load a session via the menu.'
        else:
            self._status_text = s            

        self._figure = None
        self.ax1 = None
        self.ax2 = None

        self.traceCentre = 0  # halverwege de x-as
        self.scale = 1
        self.scale_r = 1
        
        # with legends it becomes slow
        self._legend = True

        self._data = data
        # tempi en traces komen nu later
        self._tempi = tempi
        self._traces = None
        self.pieceWidth = 30
        self.times = []
        
        # markers
        self.tempoline = None
        self.markers_ax1 = None
        self.markers_ax2 = None
        
        # the pieces are put in data_model2
        # markers to be set
        self.mbegin = 0
        self.mend = 0

        # mode:   0:uit, 1:begin, 2:end,  3: creer gui entry en -> 1  (via qui -> 0)
        self.pmode = 0

    def onclick_d(self, event):
        try:
            """
            print('%s click: button=%d, x=%d, y=%d, xdata=%f, ydata=%f' %
                  ('double' if event.dblclick else 'single', event.button,
                   event.x, event.y, event.xdata, event.ydata))
            """
            if event.inaxes == self.ax1:
                # ax1 processing
                #   zetten pieces (button 1)
                if self.pmode == 1:
                    b = int(event.xdata*Hz)
                    # we start a piece 2/5 second before the catch, better for displaying
                    self.mbegin = n_catches(1, b)[0]-20
                    self.pmode = 2
                elif self.pmode == 2:
                    self.mend = int(event.xdata*Hz)
                    self.pmode = 3
                elif self.pmode == 3:
                    # will not occurr when the piece is accepted
                    print('set point in traces 3, remove markers')
                    self.pmode = 1

            elif event.inaxes == self.ax2:
                # ax2 processing
                # pos = selfelf.ax1.get_position()
                # print(pos)
                # draw new line
                self.tempoline.remove()
                self.tempoline = self.ax2.vlines(event.xdata, 0, 20,
                                                 transform=self.ax2.get_xaxis_transform(), colors='r')
                self.traceCentre = event.xdata
                self.update_figure()
            else:
                #  ook hier verschillende buttons verwerken
                pass
            
        except TypeError:
            # clicked outside the plot, ignore
            pass


    # cid = fig.canvas.mpl_connect('button_press_event', onclick)
    # fig.canvas.mpl_disconnect(cid)

    def onclick_u(self, event):
        try:
            print('%s click: button=%d, x=%d, y=%d, xdata=%f, ydata=%f' %
                  ('double' if event.dblclick else 'single', event.button,
                   event.x, event.y, event.xdata, event.ydata))
            print('Up')
        except TypeError:
            pass

    def onscroll(self, event):
        try:
            if event.inaxes == self.ax1:
                self.scale += event.step*0.05
                if self.scale < 0.05:
                    self.scale = 0.05
                self.update_figure()
            elif event.inaxes == self.ax2:
                pass
            else:
                pass

        except TypeError:
            pass



    @property
    def figure(self):
        return self._figure
    
    @figure.setter
    def figure(self, fig):
        self._figure = fig
        self._figure.set_facecolor('white')
        fig.subplots_adjust(hspace=0.7)
        gs = self._figure.add_gridspec(3, 3)
        self.ax1 = self._figure.add_subplot(gs[0:2, :])
        self.ax2 = self._figure.add_subplot(gs[-1, :])

        self.ax1.set_title('Traces')
        self.ax2.set_title('Rating')

        self.tempoline = self.ax2.vlines(7, -10, 10, transform=self.ax2.get_xaxis_transform(), colors='r')

        # to set positions
        # pos1 = ax.get_position() # get the original position 
        # pos2 = [pos1.x0 + 0.3, pos1.y0 + 0.3,  pos1.width / 2.0, pos1.height / 2.0] 
        # ax.set_position(pos2) # set a new position

        # set limits
        # ax.get_xlim()
        # ax.set_xlim(a, b)
        
        cid1 = fig.canvas.mpl_connect('button_press_event', self.onclick_d)
        # cid2 = fig.canvas.mpl_connect('button_release_event', self.onclick_u)
        cid3 = fig.canvas.mpl_connect('scroll_event', self.onscroll)

        # Signal connection
        self.stateChanged.connect(self._figure.canvas.draw_idle)
        self.legendChanged.connect(self._figure.canvas.draw_idle)

        self.update_tempo_figure()
        
    @pyqtProperty('QString', notify=statusTextChanged)
    def statusText(self):
        return self._status_text
    
    @statusText.setter
    def statusText(self, text):
        if self._status_text != text:
            self._status_text = text
            self.statusTextChanged.emit()

    @pyqtProperty(bool, notify=legendChanged)
    def legend(self):
        return self._legend
    
    @legend.setter
    def legend(self, legend):
        if self.figure is None:
            return
            
        if self._legend != legend:
            self._legend = legend
            if self._legend:
                self.axes.legend()
            else:
                leg = self.axes.get_legend()
                if leg is not None:
                    leg.remove()
            self.legendChanged.emit()
            print('lengend')

    # twee functies voor de twee subplots?
    @pyqtSlot()
    def update_tempo_figure(self):
        if self.figure is None:
            return
    
        self.ax2.clear()
        self.ax2.grid(True)
        self.ax2.set_title('Rating')
        
        q = [list(t) for t in zip(*self._tempi)]
        if len(q) is not 0:
            t = [i/Hz for i in q[0]]            
            self.ax2.plot(t, q[1], linewidth=0.6)
            self.ax2.set_xlim((0, len(self._traces)/Hz))
        
        # set all prepared ax2 markers here
        #     marker tempoline is done in onclick
        for d in gd.data_model2.alldata():
            b, e = d.data()
            self.ax2.plot([b/Hz], [0], marker='>', color='g')
            self.ax2.plot([e/Hz], [0], marker='<', color='r')

        self.stateChanged.emit()
        

    @pyqtSlot()
    def update_figure(self):
        if self.figure is None:
            return
    
        self.ax1.clear()
        self.ax1.grid(True)
        self.ax1.set_title('Traces')

        has_series = False

        for row in range(self._data.rowCount()):
            model_index = self._data.index(row, 0)
            checked = self._data.data(model_index, DataSensorsModel.SelectedRole)
            
            if checked:
                has_series = True
                name = self._data.data(model_index, DataSensorsModel.NameRole)                
                i = self._data.data(model_index, DataSensorsModel.DataRole) + 1
                values = self._traces[1: -1, i]
                self.ax1.plot(self.times, values, linewidth=0.6,  label=name)

        # set all prepared ax1 markers here
        for d in gd.data_model2.alldata():
            b, e = d.data()
            self.ax1.plot([b/Hz], [0], marker='>', color='g')
            self.ax1.plot([e/Hz], [0], marker='<', color='r')

        # self.ax1.set_xlim((self.xFrom, self.xTo))
        self.ax1.set_xlim((self.traceCentre - self.pieceWidth*self.scale, self.traceCentre + self.pieceWidth*self.scale))

        if has_series and self.legend:
            self.ax1.legend()

        self.stateChanged.emit()
        
    def update_figures(self):
        self.update_figure()
        self.update_tempo_figure()

    @pyqtSlot(str)
    def new_piece(self, name):
        #  Button "New Piece" processing
        
        if self.pmode == 0:
            self.pmode = 1
        if self.pmode == 3:
            # create new piece
            # the profile pieces (start, t20, t24, t28, t32, max) should be contiguous
            #   we could test for this, and signal is using the delete button for the piece.
            gd.data_model2.add_piece(name, (self.mbegin, self.mend))
            self.update_figures()
            self.pmode = 0

    @pyqtSlot(str)
    def remove_piece(self, index):
        gd.data_model2.del_piece(index)
        self.update_figures()
        
    @pyqtSlot()
    def savepieces(self):
        gd.sessionInfo['Pieces'] = [(i.name(), i.data()) for i in gd.data_model2.alldata()]
        saveSessionInfo(gd.sessionInfo)
        gd.boattablemodel.make_profile()

    @pyqtProperty(list, notify=stateChanged)
    def the_pieces(self):
        return [i.name() for i in gd.data_model2.alldata()]

    @pyqtProperty(str, notify=stateChanged)
    def csvDir(self):
        return '/home/sietse/' + gd.config['BaseDir'] + '/csv_data'

    @pyqtProperty(int, notify=stateChanged)
    def nmbrRowers(self):
        if gd.sessionInfo == {}:
            return 1
        else:
            return gd.sessionInfo['RowerCnt']

    @pyqtProperty(str, notify=stateChanged)
    def sessionDir(self):
        return '/home/sietse/' + gd.config['BaseDir'] + '/session_data'

    @pyqtProperty(str, notify=stateChanged)
    def sessionName(self):
        return gd.config['Session']

    def cleanup_global_data(self):
        gd.sessionInfo = {}
        gd.dataObject = []
        gd.data_model.del_all()
        gd.data_model2.del_all()
        gd.data_model3.del_all()
        gd.data_model4.del_all()
        gd.data_model5.del_all()
        gd.boattablemodel.del_all()
        gd.boatPlots.del_all()

    def update_the_models(self, session):
        self._data.load_sessionInfo(gd.sessionInfo['uniqHeader'])
        self.statusText = "Current session:  " + session

        self._traces = gd.dataObject
        self._tempi = gd.sessionInfo['Tempi']
        self.times = list(map( lambda x: x/Hz, list(range(len(self._traces) - 2))))

        gd.mainView.set_data_traces()
        self.update_figures()

    @pyqtSlot(str)
    def createSessionCsv(self, f):
        """Used from the menu when (re)creating a new session."""
        csv_file = re.sub('\Afile://', '', f)
        # in BaseDir ?? afdwingen?
        b = os.path.basename(csv_file)
        session = re.sub('.csv', '', b)
        csv_dir = re.sub(b, '', csv_file)
        session_dir = re.sub('csv_data', 'session_data', csv_dir)
        cache_dir = re.sub('csv_data', 'caches', csv_dir)
        configs_dir = re.sub('csv_data', 'configs', csv_dir)        
        session_file = session_dir + session + '.yaml'
        cache_file = cache_dir + session + '.npy'

        # move session in old subdir and remove cache file if they exist
        try:
            fd = open(session_file, 'r')
            fd.close()
            try:
                os.mkdir(session_dir + "/old")
            except FileExistsError:
                pass
            move(session_file, session_dir + 'old')
        except IOError:
            # assume no session_file
            pass
        try:
            fd = open(cache_file, 'r')
            fd.close()
            os.remove(cache_file)
        except IOError:
            pass

        self.cleanup_global_data()

        gd.config['Session'] = session
        saveConfig(gd.config)

        # create sessionfile
        copyfile(configs_dir + 'session_template.yaml', session_file)
        gd.sessionInfo = selectSession()
        gd.cal_value = gd.sessionInfo['Calibration']

        # read numpy data
        makecache(cache_file)

        calibrate()
        self.update_the_models(session)

    @pyqtSlot()
    def selectCurrent(self):
        """Used when starting the program."""
        session = gd.config['Session']
        session_file = sessionFile(session)
        basename = '/' + session + '.yaml'
        session_dir = re.sub(basename, '', session_file)

        if session != 'None':
            self.selectIt(session_dir, session)

    @pyqtSlot(str)
    def selectSessionFile(self, f):
        """ used from the menu to select an existing session."""
        session_file = re.sub('\Afile://', '', f)
        s = os.path.basename(session_file)
        session = re.sub('.yaml', '', s)

        # beetje dubbelop
        session_file = sessionFile(session)
        basename = '/' + session + '.yaml'
        session_dir = re.sub(basename, '', session_file)

        gd.config['Session'] = session
        saveConfig(gd.config)
        
        self.selectIt(session_dir, session)

    def selectIt(self, session_dir, session):
        session_file = session_dir + '/' + session + '.yaml'
        cache_dir = re.sub('session_data', 'caches/', session_dir)
        cache_file = cache_dir + session + '.npy'

        self.cleanup_global_data()

        # update sessionInfo
        try:
            fd = open(session_file, 'r')
            inhoud = fd.read()
        except IOError:
            print(f'selectIt: cannot read Sessions file, should not happen  {session_file}')
            gd.config['Session'] = 'None'
            saveConfig(gd.config)
            exit()
        gd.sessionInfo = yaml.load(inhoud)
        gd.cal_value = gd.sessionInfo['Calibration']

        # update dataObject (should be there)
        try:
            fd = open(cache_file, 'r')
            fd.close()
            gd.dataObject = np.load(cache_file)
        except IOError:
            print(f'Cannot read cachefile, should not happen  {cache_file}')
            print("Repairing cache file,")
            makecache(cache_file)

        calibrate()
        self.update_the_models(session)
        gd.boattablemodel.make_profile()

# matplotlib plot in Pieces
class FormView(QObject):

    legendChanged = pyqtSignal()
    statusTextChanged = pyqtSignal()
    stateChanged = pyqtSignal()

    def __init__(self, parent=None, data=None, data2=None):
        QObject.__init__(self, parent)

        self._status_text = ""
        self._figure = None
        self.ax1 = None

        # in seconds
        self.xFrom = 0
        self.xTo = 1
        # in index
        self.xFrom2 = 0
        self.xTo2 = 1

        self.scale = 1

        self.dd = None
        self.ee = None

        # with legends it becomes slow
        self._legend = True

        self._data = data
        self._traces = None

        # length of segment shown in the plots
        self._length = None
        self._starttime = 0
        self.videoStart = 0
        
        # the part we show
        self._window_tr = None
        self._window_tr2 = None
        # second session
        self.secondary = False
        self._data2 = data2
        self._traces2 = None
        self.times = []
        
        self.update_figure()

    def onclick_d(self, event):
        try:
            """
            print('%s click: button=%d, x=%d, y=%d, xdata=%f, ydata=%f' %
                  ('double' if event.dblclick else 'single', event.button,
                   event.x, event.y, event.xdata, event.ydata))
            """
            if event.inaxes == self.ax1:
                self.videoStart = event.xdata
                self.update_figure()
            else:
                pass
            
        except TypeError:
            # clicked outside the plot, ignore
            pass


    def onscroll(self, event):
        try:
            self.scale += event.step*0.05
            if self.scale < 0.05:
                self.scale = 0.05
            self.update_figure()

        except TypeError:
            pass

    @property
    def figure(self):
        return self._figure
    
    @figure.setter
    def figure(self, fig):
        self._figure = fig
        self._figure.set_facecolor('white')
        self.ax1 = self.figure.add_subplot(111)    
        self.ax1.set_title('Traces')

        # Signal connection
        self.stateChanged.connect(self._figure.canvas.draw_idle)
        self.legendChanged.connect(self._figure.canvas.draw_idle)

        cid1 = fig.canvas.mpl_connect('button_press_event', self.onclick_d)
        cid3 = fig.canvas.mpl_connect('scroll_event', self.onscroll)
        
    @pyqtProperty(bool, notify=legendChanged)
    def legend(self):
        return self._legend
    
    @legend.setter
    def legend(self, legend):
        if self.figure is None:
            return
            
        if self._legend != legend:
            self._legend = legend
            if self._legend:
                self.axes.legend()
            else:
                leg = self.axes.get_legend()
                if leg is not None:
                    leg.remove()
            self.legendChanged.emit()

    @pyqtSlot()
    def update_figure(self):
        if self.figure is None:
            return
    
        self.ax1.clear()
        self.ax1.grid(True)
        self.ax1.set_title('Traces')

        has_series = False

        # always use 120 seconds of data, 30 seconds before the start of the piece and 90 after
        #    this to (almost) always be able to have a secondary session to show
        #  when no piece selected use the first 120 seconds
        #  the secondary session is mapped onto this
        #  evt. mapping aanpassen: strokes voor en achteruit via de gui

        self.dd = self.ax1.scatter([self.xFrom], [0], marker='>', color='green')
        self.ee = self.ax1.scatter([self.xTo], [0], marker='<', color='red')
       
        for row in range(self._data.rowCount()):
            model_index = self._data.index(row, 0)
            checked = self._data.data(model_index, DataSensorsModel.SelectedRole)
            
            if checked:
                has_series = True
                name = self._data.data(model_index, DataSensorsModel.NameRole)                
                i = self._data.data(model_index, DataSensorsModel.DataRole) + 1
                values = self._window_tr[:, i]
                self.ax1.plot(self.times, values, linewidth=0.6,  label=name)

        # secondary plots
        for row in range(self._data2.rowCount()):
            model_index = self._data2.index(row, 0)
            checked = self._data2.data(model_index, DataSensorsModel.SelectedRole)
            
            if checked:
                has_series = True
                name = self._data2.data(model_index, DataSensorsModel.NameRole)                
                i = self._data2.data(model_index, DataSensorsModel.DataRole) + 1
                values = self._window_tr2[:, i]
                self.ax1.plot(self.times, values, linewidth=0.7,  label=name, linestyle='--')

        self.tempoline = self.ax1.vlines(self.videoStart, 0, 20,
                                                 transform=self.ax1.get_xaxis_transform(), colors='r')

        vidToPos(self.videoStart)

        if has_series and self.legend:
            self.ax1.legend()

        #
        distance = (self.xTo - self.xFrom) * self.scale

        self.ax1.set_xlim((self.xFrom, self.xFrom+distance))
        # start at correct beginvalue
        locs = self.ax1.get_xticks()
        ticks = [item+self._starttime for item in locs]
        self.ax1.set_xticklabels(ticks)

        self.stateChanged.emit()

    def set_windows(self, piece=False, x=0, y=0):
        """Set windows for primary and secondary datasets.
           Limit view to 120 seconds max"""
        if piece:
            xFrom = x
            self._starttime = int(x/Hz)
            xTo = x + len(self._traces[x: y, 1])
            self._length = xTo - xFrom
            self._window_tr = self._traces[xFrom: xTo, :]
            self.times = list(map( lambda x: x/Hz, list(range(xTo-xFrom))))
            self.xFrom = 0
            self.xTo =  int((self._length)/Hz)

            if self.secondary:
                if len(self._window_tr2) > self._length:
                    window2 = np.copy(self._window_tr2[0: self._length, :])
                    self._window_tr2 = window2
                else:
                    a, _ = self._window_tr.shape
                    s, b = self._window_tr2.shape
                    window2 = np.copy(self._window_tr2)
                    window2.resize((a, b))
                    window2[s:, :] = np.nan
                    self._window_tr2 = window2

        else:
            self._starttime = 0
            xFrom = 0
            xTo = len(self._traces[1: -1, 1])
            self._length = xTo - xFrom
            self._window_tr = self._traces[xFrom: xTo, :]
            self.times = list(map( lambda x: x/Hz, list(range(xTo-xFrom))))
            self.xFrom = int(xFrom/Hz)
            self.xTo = int(xTo/Hz)

        return xFrom, xTo

    @pyqtSlot(str)
    def set_piece(self, name):
        for i in gd.data_model2.alldata():        
            if i.name() == name:
                xFrom, xTo = i.data()
                strt, end = self.set_windows(piece=True, x=xFrom, y=xTo)

        self.update_figure()

    # aangeroepen vanuit FromPieces (dan 2de sessie eruit) en lokaal bij nieuwe secondary
    def set_data_traces(self, local=False):
        self._data.load_sessionInfo(gd.sessionInfo['uniqHeader'])
        self._traces = gd.dataObject
        gd.data_model2.set_all(gd.sessionInfo['Pieces'])

        if not local:
            # always start without a secondary session
            self.secondary = False
            gd.config['Session2'] = ''
            saveConfig(gd.config)
            gd.data_model5.del_all()
            self._starttime = 0
            
        if self.secondary:
            gd.data_model4.del_all()
            gd.data_model4.load_sessionInfo(gd.sessionInfo2['uniqHeader'])
            gd.data_model5.del_all()
            gd.data_model5.set_all(gd.sessionInfo2['Pieces'])

        strt, end = self.set_windows()
        if self.secondary:
            window2 = self._traces2[strt: end, :]
            size = window2.shape[0]
            if size < self._length:
                a, _ = self._window_tr.shape
                _, b = window2.shape
                self._window_tr2 = np.copy(window2)
                self._window_tr2.resize((a, b))
                self._window_tr2[size:, :] = np.nan
            else:
                #
                end = strt + self._length
                self._window_tr2 = np.copy(self._traces2[strt: end, :])
            # normalise to compare better (alleen als we met pieces bezig zijn)
        self.update_figure()


    @pyqtSlot()
    def videoOpen(self):
        print('Start video use')
        sendToMpv('set_property window-scale 0.5')
        sendToMpv('set_property pause yes')
        # uit sesionInfo halen
        v = gd.sessionInfo['Video']
        file = videoFile(v[0])
        sendToMpv('loadfile ' + file)
        # print('loadfile ' + file + ' ' + str(v[1]))
        time.sleep(0.2)
        vidToPos(v[1])

    @pyqtSlot()
    def frame_step(self):
        # sendToMpv('frame-step')
        self.videoStart += 0.04
        self.update_figure()

    @pyqtSlot()
    def frame_back_step(self):
        # sendToMpv('frame-back-step')
        self.videoStart -= 0.04
        self.update_figure()

    # handling of second session

    # een andere sessie kan een aander aantal sensoren hebben, hoe de mappen?

    @pyqtProperty(str, notify=stateChanged)
    def sessionName(self):
        return gd.config['Session2']

    @pyqtSlot(str)
    def selectSecondFile(self, f):
        """ used from the menu to select a secondary session."""
        session_file = re.sub('\Afile://', '', f)
        s = os.path.basename(session_file)
        session = re.sub('.yaml', '', s)

        # beetje dubbelop
        session_file = sessionFile(session)
        basename = '/' + session + '.yaml'
        session_dir = re.sub(basename, '', session_file)

        gd.config['Session2'] = session
        saveConfig(gd.config)
        
        self.selectSecond(session_dir, session)

    def selectSecond(self, session_dir, session):
        session_file = session_dir + '/' + session + '.yaml'
        cache_dir = re.sub('session_data', 'caches/', session_dir)
        cache_file = cache_dir + session + '.npy'

        # wat nodig?
        # self.cleanup_global_data()
        gd.data_model3.del_all()
        gd.data_model5.del_all()

        # update sessionInfo2
        try:
            fd = open(session_file, 'r')
            inhoud = fd.read()
        except IOError:
            print(f'selectIt: cannot read secondary Sessions file, should not happen  {session_file}')
            gd.config['Session2'] = 'None'
            saveConfig(gd.config)
            exit()
        gd.sessionInfo2 = yaml.load(inhoud)
        gd.cal_value2 = gd.sessionInfo2['Calibration']

        # update dataObject (should be there)
        try:
            fd = open(cache_file, 'r')
            fd.close()
            gd.dataObject2 = np.load(cache_file)
        except IOError:
            print(f'Cannot read secondary cachefile, should not happen  {cache_file}')
            gd.config['Session2'] = 'None'
            saveConfig(gd.config)
            exit()
            
        calibrate(True)
        self.update_the_models(session)

    def update_the_models(self, session):
        self.statusText = "Secondary session:  " + session

        self._traces2 = gd.dataObject2
        self._tempi = gd.sessionInfo2['Tempi']
        self.secondary = True

        self.set_data_traces(local=True)
        self.update_figure()


        
    @pyqtSlot(str)
    def set_2nd_piece(self, name):
        for i in gd.data_model5.alldata():        
            if i.name() == name:
                xFrom2, xTo2 = i.data()
                # zet xFrom2 op eerste catch
                self.xFrom2, self.xTo2 = xFrom2/Hz, xTo2/Hz
                self._window_tr2 = np.copy(self._traces2[xFrom2: xFrom2+self._length, :])
                size = self._window_tr2.shape[0]
                if size < self._length:
                    a, _ = self._window_tr.shape
                    _, b = self._window_tr2.shape
                    self._window_tr2.resize((a, b))
                    self._window_tr2[size:, :] = np.nan
                else:
                    end = xFrom2 + self._length
                    self._window_tr2 = np.copy(self._traces2[xFrom2: end, :])
                    
                # normalise to compare better

        self.update_figure()

    @pyqtProperty(list, notify=stateChanged)
    def the_2nd_pieces(self):
        return [i.name() for i in gd.data_model5.alldata()]


# matplotlib plot in BoatProfile
class BoatForm(QObject):

    legendChanged = pyqtSignal()
    statusTextChanged = pyqtSignal()
    stateChanged = pyqtSignal()

    def __init__(self, parent=None, data=None, traces=None):
        QObject.__init__(self, parent)

        self._status_text = ""
        self._figure = None
        self.ax1 = None
        self.ax2 = None
        self.ax3 = None
        self.ax4 = None

        self.een = None
        self.twee = None
        self.drie = None
        
        self._legend = False

        self._data = data

    @property
    def figure(self):
        return self._figure
    
    @figure.setter
    def figure(self, fig):
        self._figure = fig
        self._figure.set_facecolor('white')
        gs = self._figure.add_gridspec(2, 2)
        self.ax1 = self._figure.add_subplot(gs[0, 0])
        self.ax2 = self._figure.add_subplot(gs[0, 1])
        self.ax3 = self._figure.add_subplot(gs[1, 0])
        self.ax4 = self._figure.add_subplot(gs[1, 1])

        # Signal connection
        self.stateChanged.connect(self._figure.canvas.draw_idle)
        self.legendChanged.connect(self._figure.canvas.draw_idle)
        
        self.update_figure()
        
    @pyqtProperty(bool, notify=legendChanged)
    def legend(self):
        return self._legend
    
    @legend.setter
    def legend(self, legend):
        if self.figure is None:
            return
            
        if self._legend != legend:
            self._legend = legend
            if self._legend:
                self.axes.legend()
            else:
                leg = self.axes.get_legend()
                if leg is not None:
                    leg.remove()
            self.legendChanged.emit()

    @pyqtSlot()
    def update_figure(self):
        if self.figure is None:
            return
    
        self.ax1.clear()
        self.ax1.grid(True)
        self.ax1.set_title('Snelheid')
        self.ax2.clear()
        self.ax2.grid(True)
        self.ax2.set_title('Versnelling')
        self.ax3.clear()
        self.ax3.grid(True)
        self.ax3.set_title('Pitch')
        self.ax4.clear()
        self.ax4.grid(True)
        self.ax4.set_title('Versnelling/Tempo')

        # do the plotting
        # bootsnelheid, accel, pitch
        if gd.profile_available:
            sensors = gd.sessionInfo['Header']
            self.een = self.ax1.plot(gd.norm_arrays[:, sensors.index('Speed')], linewidth=0.6)
            self.twee = self.ax2.plot(gd.norm_arrays[:, sensors.index('Accel')], linewidth=0.6)
            self.drie = self.ax3.plot(gd.norm_arrays[:, sensors.index('Pitch Angle')], linewidth=0.6)

        if self.legend:
            self.ax1.legend()

        self.stateChanged.emit()

    def del_all(self):
        if gd.profile_available:
            for l in self.een:
                l.remove()
            gd.profile_available = False
            self.update_figure()
            """ deze kennelijk niet nodig
            self.twee.remove()
            self.drie.remove()
            """


# matplotlib plot in BoatProfile
class CrewForm(QObject):

    legendChanged = pyqtSignal()
    statusTextChanged = pyqtSignal()
    stateChanged = pyqtSignal()

    def __init__(self, parent=None, data=None, traces=None):
        QObject.__init__(self, parent)

        self._status_text = ""
        self._figure = None
        self.ax1 = None
        self.ax2 = None
        self.ax3 = None
        self.ax4 = None

        self.een = None
        self.twee = None
        self.drie = None
        
        self._legend = False

        self._data = data

    @property
    def figure(self):
        return self._figure
    
    @figure.setter
    def figure(self, fig):
        self._figure = fig
        self._figure.set_facecolor('white')
        gs = self._figure.add_gridspec(2, 2)
        self.ax1 = self._figure.add_subplot(gs[0, 0])
        self.ax2 = self._figure.add_subplot(gs[0, 1])
        self.ax3 = self._figure.add_subplot(gs[1, 0])
        self.ax4 = self._figure.add_subplot(gs[1, 1])

        # Signal connection
        self.stateChanged.connect(self._figure.canvas.draw_idle)
        self.legendChanged.connect(self._figure.canvas.draw_idle)
        
        self.update_figure()
        
    @pyqtProperty(bool, notify=legendChanged)
    def legend(self):
        return self._legend
    
    @legend.setter
    def legend(self, legend):
        if self.figure is None:
            return
            
        if self._legend != legend:
            self._legend = legend
            if self._legend:
                self.axes.legend()
            else:
                leg = self.axes.get_legend()
                if leg is not None:
                    leg.remove()
            self.legendChanged.emit()

    @pyqtSlot()
    def update_figure(self):
        if self.figure is None:
            return
    
        self.ax1.clear()
        self.ax1.grid(True)
        self.ax1.set_title('Snelheid')
        self.ax2.clear()
        self.ax2.grid(True)
        self.ax2.set_title('Versnelling')
        self.ax3.clear()
        self.ax3.grid(True)
        self.ax3.set_title('Pitch')
        self.ax4.clear()
        self.ax4.grid(True)
        self.ax4.set_title('Versnelling/Tempo')

        # do the plotting
        # bootsnelheid, accel, pitch
        if gd.profile_available:
            sensors = gd.sessionInfo['Header']
            self.een = self.ax1.plot(gd.norm_arrays[:, sensors.index('Speed')], linewidth=0.6)
            self.twee = self.ax2.plot(gd.norm_arrays[:, sensors.index('Accel')], linewidth=0.6)
            self.drie = self.ax3.plot(gd.norm_arrays[:, sensors.index('Pitch Angle')], linewidth=0.6)

        if self.legend:
            self.ax1.legend()

        self.stateChanged.emit()

    def del_all(self):
        if gd.profile_available:
            for l in self.een:
                l.remove()
            gd.profile_available = False
            self.update_figure()
            """ deze kennelijk niet nodig
            self.twee.remove()
            self.drie.remove()
            """

            """
min/max in sessionInfo voor ieder sensor
voor display is de eenheid niet van belang, dus alles goed schalen adhv min/max
evt. meerdere schaken ivm verschilende nulpunten, bijv. bij alleen positieve waarden


"""
