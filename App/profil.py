"""The profile module

Contains the functions to create and visualise the profiles

This file contains the following functions:

   * profile - creates the basic profile and returns a data structure
   * visualise - makes a visualisation of the data structure

"""
import sys, os, math, time, csv, yaml
import numpy as np
from scipy import signal
from scipy.interpolate import interp1d

import globalData as gd
from utils import *

def profile(pindex, n):
    """Create a profile with averaging over n strokes

    Globals
    ----
    Uses the following global data from globalData
      config, sessionInfo, dataObject


    Parameters
    ----------
    pindex: list of indices of the profile pieces in correct order
    n: int
       The number of strokes to average over
    """
    # offset: later beginnen met het te gebruiken stuk

    # get correct pieces to use
    pieces = gd.sessionInfo['Pieces']
    # convert pieces to dict
    pd = { pieces[i][0]: pieces[i][1] for i in pindex}

    # Calculate the size for the averaging array for profiling
    #  also number of strokes and average rating of the pieces
    tempi = gd.sessionInfo['Tempi']
    # maximum length of the pieces (normally that of the t20 piece)
    mx = 0
    # positions used for averaging
    pos = []
    nlist = []
    # use correct order
    for nm in prof_pcs:
        b, e = pd[nm]
        # assume tempi long enough
        # list with startpoints in this piece
        tlist = []
        scnt = 0
        mode = 0
        rating = 0
        for (t, r) in tempi:
            if mode == 0:
                if t > b:
                    strt = t
                    tlist.append(t)
                    scnt += 1
                    rating += r
                    mode = n+2     # a little more
            elif mode > 0:


                mode -= 1
                tlist.append(t)
                scnt += 1
                rating += r
                if mode == 0:
                    pn = t-strt
                    mode = -1
            else:
                if t < e:
                    scnt += 1
                    rating += r
                else:
                    break

        if mode == -1:
            if pn > mx:
                mx = pn
        pos.append(tlist)
        # scnt and rating for entire piece
        rating = rating/scnt
        nlist.append((scnt, rating))
    gd.sessionInfo['PieceCntRating'] = nlist

    sensors = gd.sessionInfo['Header']
    # allocate array for the average arrays, we need at least one cycle
    length = int(mx/n)
    av_arrays = np.zeros((len(pd), length, len(sensors)))
    #  made to match structure of dataObject, efficient enough?

    # average the data
    for i, st in enumerate(pos):
        for j in range(n):
            r = st[j] + length
            av_arrays[i, :, :] += gd.dataObject[st[j]:r, :]
    av_arrays = av_arrays/n

    # scull: gate angle and force:  average and add
    # Use port
    if gd.sessionInfo['BoatType'] == 'scull':
        for i, s in enumerate(sensors):
            if s.find('P GateAngle') >= 0:
                av_arrays[:, :, i] = (av_arrays[:, :, i] + av_arrays[:, :, i+1])/2
            if s.find('P GateForce') >= 0:
                av_arrays[:, :, i] =  av_arrays[:, :, i] + av_arrays[:, :, i+1]
        # note: assume S site is at next position!

    # nu de echte berekeningen
    outcome = []
    for i, sp in enumerate(pos):
        nm = prof_pcs[i]
        outcome.append(pieceCalculations(nm, sp, av_arrays[i, :, :]))
        
    saveSessionInfo(gd.sessionInfo)
    return outcome


def pieceCalculations(nm, sp, a):
    """Calculate all parameters needed for the protocol

    Parameters
    ----------
    nm: str
    Name of piece

    sp: list
    startpoints of the strokes

    a: numpy.array (sensors, length)
    Array containing the sensor data for the stroke

    Returns
    -------
    outcome: dict with calculated values
    e: extra arrays: power, ...
    sizes depend on boattype and number of rowers
    """

    # will need filtering for some signals
    [B, A] = signal.butter(4, 2*5/Hz)
    #  We assume that there are NO NaN's in the pieces

    sensors = gd.sessionInfo['Header']

    out = {}
    out['PieceName'] = nm

    """ What we need:
    Boatreport:
      - table boat parameters
      - normalized graphs
          - speed and accelleration
          - pitch, roll, yaw
          - accell/powerloss agains tempi of different pieces ?

    Crewreport:
      - graphs to compare rowers
        - gate angles  (+accel as support)
        - seatposition (+accel as support)
        - gate force   (+accel as support)
        - gate force agains gate angle
        - stretcher force
        - stretcher force agains gate angle
        - propulsive force?

    Rower report, one for each rower
      - table met targets erbij
      - graphs
        - gate angle
        - gate force X/Y
        - power, handlevel, handlevdsseat
        - stretcher forces

    """

    # number of strokes and average rating: in sessionInfo

    # 500 meter split in seconds
    i = sensors.index('Speed')
    speed = np.mean(a[:, i])
    out['Speed'] = speed
    out['Split'] = 500/speed
    # print(f'Split {out["Split"]} in {nm}')

    # distance per stroke: 60*speed/rating
    # staat in goede volgorde
    l = prof_pcs
    scnt, r = gd.sessionInfo['PieceCntRating'][l.index(nm)]
    out['DistancePerStroke'] = 60 * speed / r

    out['Starting points'] = sp

    # TODO
    # maximum speed at %cycle
    # positive acceleration at %cycle
    # speed fluctuation
    # speed fluctuation power loss
    # pitch yaw roll average


    # Crewreport, all data already available. Only normalising needed


    # Rowerreport
    rwcnt = gd.sessionInfo['RowerCnt']
    boattype = gd.sessionInfo['BoatType']
    
    if boattype == 'sweep':
        ind_ga = [i for i, x in enumerate(sensors) if x == "GateAngle"]
        ind_fx = [i for i, x in enumerate(sensors) if x == "GateForceX"]
        ind_fy = [i for i, x in enumerate(sensors) if x == "GateForceY"]

        inboard  = gd.globals['Parameters']['inboardSweep']
        outboard = gd.globals['Parameters']['outboardSweep']
        IOratio  = inboard+outboard/(inboard+outboard)

        # allocate data for profile data: power, handleVel, handleVDSSeat (3)
        nmbr_oars = len(ind_ga)
        length = a.shape[0]
        # use only power for now
        profile_data = np.zeros((3*nmbr_oars, length))

        # TODO: HandleVel, HandleVDSSeat

        # power
        for i, r in enumerate(ind_ga):
            # power for a rower
            gate_a       = signal.filtfilt(B, A, a[:, ind_ga[i]])
            tmp          = math.pi * a[:, ind_ga[i]] / 180
            pinForceTS   = 9.81 * (np.multiply(a[:, ind_fx[i]], np.cos(tmp)) -
                                   np.multiply(a[:, ind_fy[i]], np.sin(tmp)))
            moment       = IOratio * pinForceTS
            # waarom niet de sensordata gebruiken?
            gateAngleVel = np.gradient(math.pi*gate_a/180, 1/Hz)
            profile_data[i+0]        = moment * gateAngleVel

            # TODO: PowerLegs, PowerTruncArms
    else:
        inboard = gd.globals['Parameters']['inboardScull']
        outboard = gd.globals['Parameters']['outboardScull']
        IOratio = inboard+outboard/(inboard+outboard)


        ind_gap = [i for i, x in enumerate(sensors) if x == "P GateAngle"]
        ind_gas = [i for i, x in enumerate(sensors) if x == "S GateAngle"]
        ind_fxp = [i for i, x in enumerate(sensors) if x == "P GateForceX"]
        ind_fxs = [i for i, x in enumerate(sensors) if x == "S GateForceX"]
        ind_fyp = [i for i, x in enumerate(sensors) if x == "P GateForceY"]
        ind_fys = [i for i, x in enumerate(sensors) if x == "S GateForceY"]

        inboard = gd.globals['Parameters']['inboardScull']
        outboard = gd.globals['Parameters']['outboardScull']

        # allocate data for profile data: power, handleVel, handleVDSSeat (3)
        nmbr_oars = len(ind_gap)
        length = a.shape[0]

        # use only power for now
        profile_data = np.zeros((3*nmbr_oars, length))

        # TODO: HandleVel, HandleVDSSeat

        # power (both oars merged)
        # NOG duidelijk fout!
        for i in range(len(ind_gap)):
            # power for a sculler
            gate_a       = signal.filtfilt(B, A, (a[:, ind_gap[i]]+a[:, ind_gas[i]])/2)
            tmp          = math.pi * (a[:, ind_gap[i]]+a[:, ind_gas[i]]) / 180
            pinForceTS   = 9.81 * (np.multiply(a[:, ind_fxp[i]]+a[:, ind_fxs[i]], np.cos(tmp)) -
                                   np.multiply(a[:, ind_fyp[i]]+a[:, ind_fys[i]], np.sin(tmp)))
            moment       = IOratio * pinForceTS
            # waarom niet de sensordata gebruiken?
            gateAngleVel = np.gradient(math.pi*gate_a/180, 1/Hz)
            profile_data[i+0]        = moment * gateAngleVel

            # TODO: PowerLegs, PowerTruncArms

    # TODO

    # centreer yaw, pitch en angle ( averages in boat table)
    # slip


    # normalize data
    #   from  catch1 to catch2
    gd.norm_arrays = np.empty((100, a.shape[1]))
    for i in range(a.shape[1]):
        l = sp[1]-sp[0]
        x = np.arange(l)
        # print(f'x {x}')
        g = interp1d(x, a[0:l, i], kind='cubic')
        xnew = np.arange(100)*((l-1)/(100-1))
        # print(len(x), len(xnew), len(a[0:l, i]))
        # print(f'xnew {xnew}')
        # print(a[0:l, i])
        gd.norm_arrays[:, i] = g(xnew)

    # normalize profile_data

    return out, profile_data


def visualize(data):
    print('Profile data pictures or pdf')

