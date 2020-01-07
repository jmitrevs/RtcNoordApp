"""Global data for the app."""

#
config = None

# data from the GlobalSettings yaml file
globals     = {}

# the primary data
# data from the session yaml file
sessionInfo = {}
# ESSENTIAL: sensors are in same order as in dataObject
dataObject  = []

# the secondary data
sessionInfo2 = {}
dataObject2  = []

# the models for:
# the sensors in setup pieces
data_model = []

# the pieces in setup pieces and view piece
data_model2 = []

# the sensors in view pieces
data_model3 = []

# the secondary sensors in view pieces
data_model4 = []

# the secondary pieces in view pieces
data_model5 = []

#
mainPieces = None
mainView = None

# calibration value for speed and distance
cal_value = None
cal_value2 = None

# profile available?
profile_available = False
# number of strokes to average over for the profile
averaging = 1
#
boattablemodel = []

#
boatPlots = None

# the averaged data and normalized data
norm_arrays = None

# mpv and video socket
video = False
submpv = None
vsocket = None
