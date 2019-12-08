"""
  First version of the RTCnoord application to process and use the Powerline logger data

"""

from PyQt5.QtCore import QVariant, QObject, pyqtSignal, pyqtSlot, pyqtProperty, QMetaObject, Qt, QTimer, QByteArray, QAbstractListModel, QModelIndex

# to contain the data for each sensor, apart from that data itself
#   the actual data is the index into the dataObject
class DataSerie(object):

    def __init__(self, name, data, selected=False):
        self._name = name
        self._data = data
        self._selected = selected
    
    def name(self):
        return self._name
    
    def selected(self):
        return self._selected
        
    def data(self):
        return self._data


# dataModel for the listview to select sensors
class DataSensorsModel(QAbstractListModel):

    # Define role enum
    SelectedRole = Qt.UserRole
    NameRole = Qt.UserRole + 1
    DataRole = Qt.UserRole + 2

    _roles = {
        SelectedRole : b"selected",
        NameRole : b"name",
        DataRole : b"data"
    }
    
    # signals
    lengthDataChanged = pyqtSignal()   # nodig?

    
    def __init__(self, data, parent=None):
        QAbstractListModel.__init__(self, parent)
        
        # fill data from sessionInfo, remove first and last column
        self._data_series = []
        for i, name in enumerate(data[1:-1]):
            self._data_series.append(DataSerie(name, i))
        self._length_data = len(data) - 2

    @pyqtProperty(int, notify=lengthDataChanged)
    def lengthData(self):
        return self._length_data
    
    @lengthData.setter
    def lengthData(self, length):
        print('lengthData setter')
        if self._length_data != length:
            self._length_data = length
            self.lengthDataChanged.emit()

    def roleNames(self):
        return self._roles
    
    def rowCount(self, parent=QModelIndex()):
        return len(self._data_series)
        
    def data(self, index, role=Qt.DisplayRole):
        if(index.row() < 0 or index.row() >= len(self._data_series)):
            return QVariant()
        
        series = self._data_series[index.row()]
        
        if role == self.SelectedRole:
            return series.selected()
        elif role == self.NameRole:
            return series.name()
        elif role == self.DataRole:
            return series.data()
        
        return QVariant()
    
    def setData(self, index, value, role=Qt.EditRole):
        print(value)
        if(index.row() < 0 or index.row() >= len(self._data_series)):
            return False
        
        series = self._data_series[index.row()]
        if role == self.SelectedRole:
            series._selected = value
            self.dataChanged.emit(index, index, [role,])
            return True
                
        return False


# dataModel for the makePiecesModel to create pieces
class DataPiecesModel(QAbstractListModel):

    # Define role enum
    SelectedRole = Qt.UserRole
    NameRole = Qt.UserRole + 1
    DataRole = Qt.UserRole + 2

    _roles = {
        SelectedRole : b"selected",
        NameRole : b"name",
        DataRole : b"data"
    }

    # signals
    lengthDataChanged = pyqtSignal()

    def __init__(self, parent=None):
        QAbstractListModel.__init__(self, parent)
        
        self._data_series = []
        self._length_data = 0

    @pyqtProperty(int, notify=lengthDataChanged)
    def lengthData(self):
        return self._length_data
    
    @lengthData.setter
    def lengthData(self, length):
        if self._length_data != length:
            self._length_data = length
            self.lengthDataChanged.emit()

    def roleNames(self):
        return self._roles
    
    def add_piece(self, data):
        print(data)
        self.add_data(data)

    def add_data(self, data_series):
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
        self._data_series.append(data_series)
        self.lengthData = max(self.lengthData, len(data_series.data()))
        self.endInsertRows()
    
    def rowCount(self, parent=QModelIndex()):
        return len(self._data_series)
        
    def data(self, index, role=Qt.DisplayRole):
        if(index.row() < 0 or index.row() >= len(self._data_series)):
            return QVariant()
        
        series = self._data_series[index.row()]
        
        if role == self.SelectedRole:
            return series.selected()
        elif role == self.NameRole:
            return series.name()
        elif role == self.DataRole:
            return series.data()
        
        return QVariant()
    
    def setData(self, index, value, role=Qt.EditRole):
        if(index.row() < 0 or index.row() >= len(self._data_series)):
            return False
        
        series = self._data_series[index.row()]
        if role == self.SelectedRole:
            series._selected = value
            self.dataChanged.emit(index, index, [role,])
            return True
                
        return False



# matplotlib plot in Pieces
class FormPieces(QObject):

    legendChanged = pyqtSignal()
    statusTextChanged = pyqtSignal()
    stateChanged = pyqtSignal()

    def __init__(self, parent=None, data=None, tempi=None, traces=None):
        QObject.__init__(self, parent)

        self._status_text = "Please load a data file"
        self._figure = None
        self.ax1 = None
        self.ax2 = None

        self.tempoline = None
        self.traceCentre = 0  # halverwege de x-as
        
        # with legends it becomes slow
        self._legend = False

        self._data = data
        self._tempi = tempi
        self._traces = traces
        self.traceLenght = len(traces)/50   # in seconds
        self.pieceWidth = 30
        self.times = list(map( lambda x: x/50, list(range(len(traces) - 2))))
        
        # the pieces
        #   name, begin, end
        self.pieces = {}
        self.begin = 0
        self.end = 0

        # mode:   0:uit, 1:begin, 2:end,  3: creer gui entry en -> 1  (via qui -> 0)
        self.pmode = 0

    def onclick(self, event):
        try:
            if event.inaxes == self.ax1:
                # ax1 processing
                #   zetten pieces (button 1)
                if self.pmode == 1:
                    print('set point in traces 1')
                    self.begin = int(event.xdata*50)
                    # set and remember a green marker (later also in rating plot)
                    self.pmode = 2
                elif self.pmode == 2:
                    print('set point in traces 2')                    
                    self.end = int(event.xdata*50)
                    # set and remember a green marker (later also in rating plot)
                    # change color of "New Piece" button"
                    self.pmode = 3
                elif self.pmode == 3:
                    # will not occurr when the piece is accepted
                    print('set point in traces 3, remove markers')
                    self.pmode = 1


            else:
                # ax2 processing
                # pos = selfelf.ax1.get_position()
                # print(pos)
                # draw new line
                self.tempoline.remove()
                self.tempoline = self.ax2.vlines(event.xdata, 0, 50,
                                                 transform=self.ax2.get_xaxis_transform(), colors='r')
                self.traceCentre = event.xdata
                self.update_figure()
        except TypeError:
            # click outside the plot, ignore
            pass

        # bovenstaand alleen met button 1, en button 2 en 3 ook gebruiken voor pan en zoom!

        
    # cid = fig.canvas.mpl_connect('button_press_event', onclick)
    # fig.canvas.mpl_disconnect(cid)


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

        #self.tempoline = self.ax2.scatter([0], [0], marker=11, color='red')
        self.tempoline = self.ax2.vlines(7, -10, 10, transform=self.ax2.get_xaxis_transform(), colors='r')



        # to set positions
        # pos1 = ax.get_position() # get the original position 
        # pos2 = [pos1.x0 + 0.3, pos1.y0 + 0.3,  pos1.width / 2.0, pos1.height / 2.0] 
        # ax.set_position(pos2) # set a new position

        # set limits
        # ax.get_xlim()
        # ax.set_xlim(a, b)
        
        cid = fig.canvas.mpl_connect('button_press_event', self.onclick)

        # Signal connection
        self.stateChanged.connect(self._figure.canvas.draw_idle)
        self.legendChanged.connect(self._figure.canvas.draw_idle)

        self.update_tempo_figure()
        
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
            print('lengent')

    # twee functies voor de twee subplots?
    @pyqtSlot()
    def update_tempo_figure(self):
        if self.figure is None:
            return
    
        self.ax2.clear()
        self.ax2.grid(True)
        self.ax2.set_title('Rating')
        
        q = [list(t) for t in zip(*self._tempi)]
        self.ax2.plot(q[0], q[1], linewidth=0.5)
        #self.ax2.set_xlim((self.xFrom, self.xTo))
        
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
                self.ax1.plot(self.times, values, linewidth=0.5,  label=name)

        # self.ax1.set_xlim((self.xFrom, self.xTo))
        self.ax1.set_xlim((self.traceCentre - self.pieceWidth, self.traceCentre + self.pieceWidth))

        if has_series and self.legend:
            self.ax1.legend()

        self.stateChanged.emit()
        
    @pyqtSlot()
    def new_piece(self):
        global data_model3
        print('New piece')
        #   genoteerde pieces zijn ook button waarmee piece een naam gegeven kunen worden of verwijderd worden
        #   savebutton om op te slaan (alleen zichtbaar als er pieces zijn)
        #      en ook meteen beschikbaar in andere tab
        if self.pmode == 0:
            self.pmode = 1
        if self.pmode == 3:
            # create new piece
            data_model3.add_piece((self.begin, self.end))
            self.pmode = 0

# matplotlib plot in Pieces
class FormView(QObject):

    legendChanged = pyqtSignal()
    statusTextChanged = pyqtSignal()
    stateChanged = pyqtSignal()

    def __init__(self, parent=None, data=None, traces=None):
        QObject.__init__(self, parent)

        self._status_text = "Please load a data file"
        self._figure = None
        self.ax1 = None

        self.dd = None
        self.xdata = None
        self.ydata = None
        
        # with legends it becomes slow
        self._legend = False

        self._data = data
        self._traces = traces
        self.times = list(map( lambda x: x/50, list(range(len(traces) - 2))))
        
        self.update_figure()



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
            print('lengent')

    @pyqtSlot()
    def update_figure(self):
        if self.figure is None:
            return
    
        self.ax1.clear()
        self.ax1.grid(True)
        self.ax1.set_title('Traces')

        self.dd=self.ax1.scatter([self.xdata], [self.ydata], marker=11, color='red')
       
        has_series = False

        for row in range(self._data.rowCount()):
            model_index = self._data.index(row, 0)
            checked = self._data.data(model_index, DataSensorsModel.SelectedRole)
            
            if checked:
                has_series = True
                name = self._data.data(model_index, DataSensorsModel.NameRole)                
                i = self._data.data(model_index, DataSensorsModel.DataRole) + 1
                values = self._traces[1: -1, i]
                self.ax1.plot(self.times, values, linewidth=0.5,  label=name)

        # self.ax1.set_xlim((self.xFrom, self.xTo))
        if has_series and self.legend:
            self.ax1.legend()

        
        self.stateChanged.emit()
