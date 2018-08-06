import glob
from os import listdir
from os.path import isfile, join
import os
import logging
import json

outputs = glob.glob('../rlexec_output/*')
#basedir = max(outputs, key=os.path.getctime)
#basedir = '../rlexec_output/1532960450'
basedir = '../rlexec_output/1533058191.1x72.xrp'
coindirs = glob.glob(basedir + '/*')
coindirs = [x for x in coindirs if os.path.isdir(x)]
logging.error('coindirs: ' + str(coindirs))
chash = {}

# Shape of q - (2, time_rez, vol_rez, ACTIONS) (((2, 8, 8, 8)))

for d in coindirs:
    with open (d + '/q.json', 'r') as fh:
        q = json.load(fh)
    c = (q[0][7][7][7] + q[1][7][7][7]) / 2
    logging.error('consumption for ' + d + ': ' + str(c))
    with open (d + '/consumption.json', 'w') as fh:
        json.dump(c, fh)
    market = os.path.basename(d)
    chash[market] = c

logging.error(str(chash))
with open (basedir + '/consumptions.json', 'w') as fh:
    json.dump (chash, fh)
logging.error('Calced consumption for ' + str(len(coindirs)) + ' markets')
