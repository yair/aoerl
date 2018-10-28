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
        with open ('volumes.poloniex.360s.1540623298.json', 'w') as fh:
            json.dump (result, fh, indent=2)

    def getAllMarkets (self):
        ticker = self.polo.marketTicker ()
        return ticker.keys()

if __name__ == '__main__':
#    AvgVolume().getAvgVolume('BTC_ETH', 1528097393, 1532460171, 180)
#    AvgVolume().getAllVols(1528097393, 1536197009775, 180)
    AvgVolume().getAllVols(1538031298, 1540623298, 360)
