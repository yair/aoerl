import json
import time
import sys
import os
import requests
from datetime import datetime
sys.path.append(os.path.abspath("/home/yair/w/PGPortfolio/pgportfolio"))
sys.path.append(os.path.abspath("/home/yair/w/PGPortfolio"))
from marketdata.poloniex import Poloniex
import logging
import glob

#PERIOD=360  # 6 minutes, for 30 minute PGP
PERIOD=600  # 10 minutes, for 30 minute PGP
#PERIOD=1440  # 24 minutes, for 2 hour PGP
#PERIOD=2400  # 40 minutes, for 2 hour PGP

class AvgVolume:
    def __init__ (self):
        self.polo = Poloniex ()
        pass

    def getAvgVolume (self, market, fsse, tsse, period):
        assert tsse > fsse
        logging.error("Getting volumes for " + market)
        chart = self.polo.marketChart (market, period=86400, start=fsse, end=tsse)
        v = 0
        for c in chart:
            if 'USDT' in market:
                v = v + float(c['volume']) / float(c['close'])
            else:
                if 'volume' in c:
                    v = v + float(c['volume'])
        r = v * 100000000 * period / (86400. * len(chart))
        logging.error(str(r))
        time.sleep(1)
        return r

    def getAllVols (self, fsse, tsse, period):
#        markets = [os.path.basename(x) for x in glob.glob('../fragments/*')]
        markets = self.getAllMarkets()
        logging.error(str(markets))
        volumes = [self.getAvgVolume(x, fsse, tsse, period) for x in markets]
        result = dict (zip (markets, volumes))
        logging.error(str(result))
        with open ('volumes.poloniex.' + str(period) + 's.' + str(int(round(time.time() * 1000))) + '.json', 'w') as fh:
            json.dump (result, fh, indent=2)

    def getAllMarkets (self):
        ticker = self.polo.marketTicker ()
        return ticker.keys()

if __name__ == '__main__':
#    AvgVolume().getAvgVolume('BTC_ETH', 1528097393, 1532460171, 180)
#    AvgVolume().getAllVols(1528097393, 1536197009775, 180)
#    AvgVolume().getAllVols(1533081600, 1540944000, 720) # Aug. 1st to Oct. 31st, 2018
#    AvgVolume().getAllVols(1533081600, 1550388843, 360) # Aug. 1st to Feb 17th, 2019
#    AvgVolume().getAllVols(1533081600, 1553432311, 360) # Aug. 1st to March 24th, 2019
#    AvgVolume().getAllVols(1533081600, 1556784000, 360) # Aug. 1st to May 2nd, 2019
#    AvgVolume().getAllVols(1543622400, 1562457600, 360) # Dec. 1st to July 7th, 2019
#    AvgVolume().getAllVols(1548979200, 1564272000, 360) # Feb. 1st to July 28th, 2019
#    AvgVolume().getAllVols(1551398400, 1567468800, 360) # Mar. 1st to Sept. 3rd, 2019
#    AvgVolume().getAllVols(1551571200, 1569888000, 360) # Mar. 3rd to Oct. 1st, 2019
#    AvgVolume().getAllVols(1554076800, 1573257600, 360) # Apr. 1st to Nov. 9th, 2019
#    AvgVolume().getAllVols(1556668800, 1574467200, PERIOD) # May 1st to Nov. 23rd, 2019
#    AvgVolume().getAllVols(1556668800, 1576972800, PERIOD) # May 1st to Dec. 22rd, 2019
#    AvgVolume().getAllVols(1559347200, 1576972800, PERIOD) # June 1st to Dec. 22rd, 2019
    AvgVolume().getAllVols(1560643200, 1577664000, PERIOD) # June 16th to Dec. 30th, 2019
