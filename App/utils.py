"""
  First version of the RTCnoord application to process and use the Powerline logger data

"""

import sys, os, math, time, csv, yaml


def startup():
    homedir = os.path.expanduser('~')
    configfile = homedir + '/.noordrtc'
    # print(f'Config file: {configfile}')
    try:
        fd = open(configfile, 'r')
        inhoud = fd.read()
    except IOError:
        inhoud = '# Initial .noordrtc file\n# Where all data is to be found wrt the users homedir\nBaseDir: Roeien/Meten/RtcNoordApp\n\n# Name of last session\nSession:  No\n'
        fd = open(configfile, 'w')
        fd.write(inhoud)

    # we now have a configfile
    config = yaml.load(inhoud)
    return config


def readGlobals(config):
    file = os.path.expanduser('~') + '/' + config['BaseDir'] + '/session_data/GlobalSettings.yaml'
    print(file)
    try:
        fd = open(file, 'r')
        inhoud = fd.read()
    except IOError:
        print(f'Cannot read GlobalSettings file.')
        exit()

    globals = yaml.load(inhoud)
    # print(globals)
    return globals


# select and read session info
def selectSession(config):
    if not config['Session']:
        # ask for a session to use, or csv-file to create one, using the template
        # set for this 'session'
        config['Session'] = 'test'

    file = os.path.expanduser('~') + '/' + config['BaseDir'] + '/session_data/' + config['Session'] + '.yaml'
    try:
        fd = open(file, 'r')
        inhoud = fd.read()
    except IOError:
        print(f'Cannot read Sessions file.')
        exit()
    # new config set
    return yaml.load(inhoud)

def saveSessionInfo(sessionInfo, config):
    file = os.path.expanduser('~') + '/' + config['BaseDir'] + '/session_data/' + config['Session'] + '.yaml'    
    fd = open(file, 'w')
    yaml.dump(sessionInfo, fd)


# csv and session file have same name
def readCsvData(config, csvdata):
    
    filename = os.path.expanduser('~') + '/' + config['BaseDir'] + '/csv_data/' + config["Session"] + '.csv'
    print(f'Read session from {filename}')
    file = open(filename, newline='')
    reader = csv.reader(file, delimiter=',')
    header = next(reader)
    if len(header) < 3:
        # we now assume tabs as delimiter
        file.close()
        file = open(filename, newline='')
        reader = csv.reader(file, delimiter='\t')
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

def tempi(sensorData):
    # creeer lijst met (time, tempo) waarden

    # negatieve flanken van een gateangle is het begin van een cyclus
    #     in de recover, riemen loodrecht op de boot
    # tempo alleen tussen 10 en 60 proberen te herkennen
    tempoList = []
    i = 0
    end = len(sensorData)
    state = 1
    while i < end:
        if math.isnan(sensorData[i]):
            i += 1
            state = 1
            continue
        if state == 1:
            # voor een nuldoorgang naar beneden
            if sensorData[i] > 10:
                state = 2
        elif state == 2:
            # herken nuldoorgang
            if sensorData[i] < 0:
                strokestart = i
                i += 2
                state = 3
        elif state == 3:
            #
            if sensorData[i] < -20:
                state = 4
        elif state == 4:
            # volgende nuldoorgang
            if sensorData[i] > 0:
                i += 2
                state = 5
        elif state == 5:
            if sensorData[i] > 15:
                state = 6
        elif state == 6:
            # einde haal cyclus
            stroketime = (i - strokestart)/50
            rating = 60/stroketime
            if sensorData[i] < 0:
                if rating < 10 or rating > 60:
                    # tempo < 10 or > 60,  restart
                    state = 1
                # record stroke
                tempoList.append((strokestart/50, rating))
                # print(strokestart/50, rating)
                strokestart = i
                i += 2
                state = 3
        i += 1

    return tempoList


def saveSession(sessionInfo, tempList):
    # save to yaml.file
    print('Session saved')
