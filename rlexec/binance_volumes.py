import json
import time
import sys
import os
import requests
from datetime import datetime
sys.path.append(os.path.abspath("/home/yair/w/PGPortfolio/pgportfolio"))
#from marketdata.poloniex import Poloniex
from binance.client import Client
import logging
import glob

class AvgVolume:
    def __init__ (self):
#        self.polo = Poloniex ()
        self.client = Client('09UxIZ56EDIk3qDAhPYNmHvBiApnZaWhNu55H77xc3sZiY1g2S7BT5z35zFaXUyg', 'pDYr7ro4DMcFiH9fASjnYgna2jR3hIyVYqw8ePZed9Ulatoz5mq2JE9UrI3mSm7h')
        pass

    def getAvgVolume (self, market, fsse, tsse, period):
        assert tsse > fsse
        logging.error("Getting volumes for " + market)
#        chart = self.polo.marketChart (market, period=86400, start=fsse, end=tsse)
        klines = self.client.get_historical_klines(market, Client.KLINE_INTERVAL_1DAY, '30 days ago utc')
        if len(klines) == 0:
            return 0;
#        logging.error('klines: ' + str(klines))
        v = 0.
        for c in klines:
#            if market == 'BTCUSDT':
#                v = v + float(c[5]) # BTC in BTC, which here is the asset volume
#            else:
                v = v + float(c[7]) # All the rest in BTC, which here is the base asset volume
        r = v * 100000000 * period / (86400. * len(klines))
        logging.error(market + 'volume: ' + str(r))
        time.sleep(1)
        return r

    def getAllVols (self, fsse, tsse, period):
        markets = [os.path.basename(x) for x in glob.glob('../binance_fragments/*')]
#        list(filter(lambda x: x < 0, number_list))
        markets = list(filter(lambda x: 'BTC' in x, markets))
        volumes = [self.getAvgVolume(x, fsse, tsse, period) for x in markets]
        result = dict (zip (markets, volumes))
        logging.error(str(result))
        with open ('binance_volumes.json', 'w') as fh:
            json.dump (result, fh, indent=2)

if __name__ == '__main__':
#    AvgVolume().getAvgVolume('BTC_ETH', 1528097393, 1532460171, 180)
#    AvgVolume().getAllVols(1528097393, 1532460171, 180)
#    AvgVolume().getAllVols(1543622400, 1551100727, 360) # 1.12.18 - 25.2.19, 6 minute interval
    AvgVolume().getAllVols(1552521600, 1558656000, 360) # 14.3.19 - 24.5.19, 6 minute interval
