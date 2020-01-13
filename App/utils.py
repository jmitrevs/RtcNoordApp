"""Utility functions for the RTCnoord app"""

import sys, os, subprocess, socket, mpv, math, time, csv, yaml, copy, shlex
from pathlib import Path

import numpy as np
from scipy import signal
import mpv

import globalData as gd

# sampling rate of the logger
Hz = 50
# pieces needed for the profile, in THAT order
prof_pcs = ['start', 't20', 't24', 't28', 't32', 'max']

def startup():
    """Determine platform we are on.
Load the config file to find the data and session to use.

    Create a config file in the appropriate location, if it does not exist.
    """
    
    rtcnoordconfig = """# Initial .noordrtc file
# Where all user data is to be found wrt the users homedir
BaseDir: RtcNoord

# Name of last session, None if none
Session: None

"""

    # determine OS
    gd.os = sys.platform
    try:
        os.environ['ANDROID_ARGUMENT']
        gd.os = 'android'
    except KeyError:
        pass
    
    if gd.os == 'linux' or gd.os == 'android':
        gd.configfile = Path.home() / '.config' / 'rtcnoord'
    elif gd.os == 'win32':
        gd.configfile = Path.home() / 'Application Data' / 'Local Settings' / 'AppAuthor' / 'rtcnoord'
    elif gd.os == 'darwin':
        gd.configfile = Path.home() / 'Library' / 'Application Support' / 'rtcnoord'
    
    try:
        fd = Path.open(gd.configfile, 'r')
        rtcnoordconfig = fd.read()
    except IOError:
        if gd.os == 'win32':
            # appauthor dir?
            pass
        fd = Path.open(gd.configfile, 'w')
        fd.write(rtcnoordconfig)

    # we now have a configfile
    config = yaml.load(rtcnoordconfig)

    return config

def saveConfig(config):
    """Save config data to the yaml file."""
    fd = Path.open(gd.configfile, 'w')
    yaml.dump(config, fd)

def readGlobals():
    """Return the GlobalSettings from the config."""
    try:
        fd = Path.open(configsDir() / 'GlobalSettings.yaml')
        inhoud = fd.read()
    except IOError:
        print(f'Cannot read GlobalSettings file.')
        exit()

    globals = yaml.load(inhoud)
    return globals

def configsDir():
    """Return the path to the configs dir."""
    path = Path.home() / gd.config['BaseDir'] / 'configs'
    return path

def csvsDir():
    """Return the path to the csv_data dir."""
    path = Path.home() / gd.config['BaseDir'] / 'csv_data'
    return path

def sessionsDir():
    """Return the path to the session_data dir."""
    path = Path.home() / gd.config['BaseDir'] / 'session_data'
    return path

def cachesDir():
    """Return the path to the caches dir."""
    path = Path.home() / gd.config['BaseDir'] / 'caches'
    return path

# select and read session info
def selectSession():
    """Load the selected session.

    Use session None if the selected one does not exist
    """
    
    if not gd.config['Session']:
        print('No session set, should not happen')

    session = gd.config['Session']
    file = sessionsDir() / (session + '.yaml')

    inhoud = ''
    try:
        fd = Path.open(file, 'r')
        inhoud = fd.read()
    except IOError:
        print(f'SelectSession: cannot read Sessions file, should not happen   {file}')
        gd.config['Session'] = 'None'
        saveConfig(gd.config)
        # nog netter oplossen
        exit()

    # new config set
    return yaml.load(inhoud)


def saveSessionInfo(sessionInfo):
    """Save session data to the yaml file."""
    file = sessionsDir() / (gd.config['Session'] + '.yaml')
    fd = Path.open(file, 'w')
    yaml.dump(sessionInfo, fd)



def calibrate(secondary=False):
    """Calibrate speed and distance data"""
    if not secondary:
        i = gd.sessionInfo['Header'].index('Speed')
        gd.dataObject[:, i] = gd.dataObject[:, i] * gd.cal_value
        i = gd.sessionInfo['Header'].index('Distance')
        gd.dataObject[:, i] = gd.dataObject[:, i] * gd.cal_value
    else:
        i = gd.sessionInfo2['Header'].index('Speed')
        gd.dataObject2[:, i] = gd.dataObject2[:, i] * gd.cal_value2
        i = gd.sessionInfo2['Header'].index('Distance')
        gd.dataObject2[:, i] = gd.dataObject2[:, i] * gd.cal_value2
        

# csv and session file have same name
def readCsvData(config, csvdata):
    """Read data for a session from the csv-file.

    Csv data can use comma or tab as delimiter
    """
    
    path = csvsDir() / (config['Session'] + '.csv')
    fd = Path.open(path, newline='')
    dialect = csv.Sniffer().sniff(fd.read(20000))
    fd.seek(0)
    reader = csv.reader(fd, dialect)    

    # als we de logger direct kunnen gebruiken!
    # preheader:  rtcnoord, logger, filename, from, to

    header = next(reader)
    lenheader = len(header)
    header2 = next(reader)
    # print(header)
    # welke sensors zijn er?
    # print(header2)
    # boottype uit eerste 2 rijen halen
    #  backwings!

    for line, row in enumerate(reader):
        row[0] = float(row[0])  # we don't use it anyway
        for i in range(lenheader):
            if row[i] is '':
                row[i] = float('NaN')
            else:
                row[i] = float(row[i])
        csvdata.append(row)
    return header, header2

def makecache(file):
    """Create and cache the data read from the csv-file in a .npy file """
    csvdata = []
    h1, h2 = readCsvData(gd.config, csvdata)
    gd.dataObject = np.asarray(csvdata)
    np.save(file, gd.dataObject)

    gd.sessionInfo['Header']   = h1
    gd.sessionInfo['Header2']  = h2

    # correction for backwing rigging: no seat position 1 means backwing.
    #    laat voorlopig maar ....

    # use stroke rower to determine start of stroke and rating
    try:
        h1.index('P GateAngle')
        gd.sessionInfo['BoatType'] = 'scull'
        indexes = [i for i, x in enumerate(h1) if x == "P GateAngle"]
        i = indexes[-1]
    except ValueError:
        h1.index('GateAngle')
        gd.sessionInfo['BoatType'] = 'sweep'
        indexes = [i for i, x in enumerate(h1) if x == "GateAngle"]
        i = indexes[-1]

    gd.sessionInfo['Tempi'] = tempi(gd.dataObject[:, i])    
    
    # add position number to sensor name
    n = []
    h1 = copy.copy(h1)
    for i in range(len(h1)):
        if not (h2[i] == 'Boat' or h2[i] == ''):
            n.append(h2[i])
            h1[i] = h1[i] + ' ' + h2[i]
            h2[i] = int(h2[i])
    # number of rowers
    #  moeten de junctionboxes wel goed zitten!
    gd.sessionInfo['RowerCnt'] = int(max(n)) - int(min(n)) + 1
    gd.sessionInfo['uniqHeader']   = h1
    
    saveSessionInfo(gd.sessionInfo)


def tempi(gateData):
    """Creates a list with strokes from the session

    Returns:
       [(strokestart in seconds/Hz steps, rating)]
    """

    # negatieve flanken van een gateangle is het begin van een cyclus
    #     in de recover, riemen loodrecht op de boot
    # tempo alleen tussen 10 en 60 proberen te herkennen
    tempoList = []
    i = 0
    end = len(gateData)
    state = 1
    while i < end:
        if math.isnan(gateData[i]):
            i += 1
            state = 1
            continue
        if state == 1:
            # voor een nuldoorgang naar beneden
            if gateData[i] > 10:
                state = 2
        elif state == 2:
            # herken nuldoorgang
            if gateData[i] < 0:
                strokestart = i
                i += 2
                state = 3
        elif state == 3:
            #
            if gateData[i] < -20:
                state = 4
        elif state == 4:
            # volgende nuldoorgang
            if gateData[i] > 0:
                i += 2
                state = 5
        elif state == 5:
            if gateData[i] > 15:
                state = 6
        elif state == 6:
            # einde haal cyclus
            stroketime = (i - strokestart)
            rating = 60*Hz/stroketime
            if gateData[i] < 0:
                if rating < 10 or rating > 60:
                    # tempo < 10 or > 60,  restart
                    state = 1
                # record stroke
                tempoList.append((strokestart, rating))
                # print(strokestart, rating)
                strokestart = i
                i += 2
                state = 3
        i += 1

    # we use the turning point in the gate angle at the catch as the starting point in a stroke

    # filter the signal a bit
    [B, A] = signal.butter(4, 2*5/Hz)
    # filtfilt cannot cope with Nans.
    for j in range(len(gateData)):
        if math.isnan(gateData[j]):
            gateData[j] = 0.0
    gate_d = signal.filtfilt(B, A, gateData)

    # use first and second catch of stroke rower
    catchList = []
    end = len(tempoList) - 2
    t, r = tempoList[0]
    for i, st in enumerate(tempoList):
        if i < 1:
            continue
        # search in first halve of the previous strokes
        next = int(t+(st[0]-t)/2)
        catch = t+np.argmin(gate_d[t: next])
        catchList.append((catch, r))
        t, r = st
        if i == end:
            break

    return catchList
    # return tempoList

def n_catches(n, x):
    """Return n catches starting at x"""
    ll = []
    for i, (j, _) in enumerate(gd.sessionInfo['Tempi']):
        if j < x:
            continue
        ll.append(j)
        if len(ll) == n:
            break
    return ll

#
def prof_pieces(pieces):
    """Returns profile piece indices in correct order or [] if not complete"""
    r = []
    for i, (s, p) in enumerate(pieces):
        if s == 'start':
            r.append(i)
    for i, (s, p) in enumerate(pieces):
        if s == 't20':
            r.append(i)
    for i, (s, p) in enumerate(pieces):
        if s == 't24':
            r.append(i)
    for i, (s, p) in enumerate(pieces):
        if s == 't28':
            r.append(i)
    for i, (s, p) in enumerate(pieces):
        if s == 't32':
            r.append(i)
    for i, (s, p) in enumerate(pieces):
        if s == 'max':
            r.append(i)
    if len(r) == 6:
        return r
    else:
        return []


# Video processing
def videoFile(mp4file):
    """Return the path to the session."""
    path = Path.home() / gd.config['BaseDir'] / 'videos' / mp4file
    return path


#    test mpv availability!
def startVideo():
    gd.player = mpv.MPV()
    gd.player.pause = True
    gd.player.window_scale = 0.5
    gd.video = True

def stopVideo():
    gd.player.terminate()
    del(gd.player)
    gd.video = False
