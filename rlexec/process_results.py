from os.path import isfile, join
import glob
import os
import logging
import json
import numpy as np

from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt

#market = 'BTC_ETH'
#market = 'USDT_BTC'
#market = 'BTC_DOGE'
market = 'BTC_STR'
#market = 'ICNBTC'
#market = 'BTCUSDT' # 40kBTCpd
#market = 'ETHBTC' # 6kBTCpd
#market = 'IOTABTC' # 1kBTCpd -- doesn't descend below a=4 on avgvol/10. Now sticks to 0 too much. :/
#market = 'ENJBTC' # 100BTCpd -- Now gets to 0 avgvol/10 :/
#market = 'GRSBTC' # 10BTCpd
#outputs = glob.glob('../binance_rlexec_output/*')
outputs = glob.glob('../rlexec_output/*')
latestdir = max(outputs, key=os.path.getctime)
logging.error('Latest dir: ' + latestdir)
#latestdir = join ('../rlexec_output/1532499592.pruned/', 'policy.json')
#latestdir = '../binance_rlexec_output/1533609646/'
with open (join (join (latestdir, market), 'q.json')) as fh:
    q = np.array (json.load (fh))
    q_buy = q[0]
    q_sell = q[1]
with open (join (join (latestdir, market), 'policy.json')) as fh:                       # default is latest run
    pi = np.array (json.load (fh))
    pi_buy = pi[0]
    pi_sell = pi[1]

# Shape of q - (2, time_rez, vol_rez, ACTIONS) (((2, 8, 8, 8)))
# Shape of pi - (2, time_rez, vol_rez) (((2, 8, 8)))

print ('q[0][0][0] = ' + str(q[0][0][0]))
print ('argmax (q[0][0][0]) = ' + str(np.argmax (q[0][0][0])))

def plot_policy (pi):
    fig = plt.figure()
    ax1 = fig.add_subplot(111, projection='3d')

    xpos = [0, 1, 2, 3, 4, 5, 6, 7, 0, 1, 2, 3, 4, 5, 6, 7, 0, 1, 2, 3, 4, 5, 6, 7, 0, 1, 2, 3, 4, 5, 6, 7, 0, 1, 2, 3, 4, 5, 6, 7, 0, 1, 2, 3, 4, 5, 6, 7, 0, 1, 2, 3, 4, 5, 6, 7, 0, 1, 2, 3, 4, 5, 6, 7]
    ypos = [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3, 3, 3, 3, 4, 4, 4, 4, 4, 4, 4, 4, 5, 5, 5, 5, 5, 5, 5, 5, 6, 6, 6, 6, 6, 6, 6, 6, 7, 7, 7, 7, 7, 7, 7, 7]
    zpos = np.zeros(64)
    dx = np.ones(64) * 0.8
    dy = np.ones(64) * 0.8
    if True:
        dz = pi.flatten()
        ax1.set_xlabel ('i')
        ax1.set_ylabel ('t')
        ax1.set_zlabel ('argmax(a)')
    else:
        dz = q_sell[1].flatten()
        ax1.set_xlabel ('a')
        ax1.set_ylabel ('i')
        ax1.set_zlabel ('q')

    ax1.bar3d(xpos, ypos, zpos, dx, dy, dz, color='#00ceaa')
    ax1.xlabel = 'blah'

plot_policy (pi_buy)
plot_policy (pi_sell)
plt.show()

