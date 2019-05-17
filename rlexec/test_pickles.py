from os import listdir
import os
import sys
import pickle
sys.path.append(os.path.abspath(".."))
sys.path.append(os.path.abspath("../market_emulator"))
#sys.path.append(os.path.abspath("/home/yair/w/PGPortfolio/pgportfolio"))
#from market_emulator.fragment import *
#from market_emulator.fragment import Fragment as Fragment
from fragment import *


marts = listdir('.')
for mart in marts:
    pickles = listdir('./' + mart)
    for p in pickles:
        fn = './' + mart + '/' + p
#        print('loading ' + fn)
        try:
            with open(fn, 'rb') as pickle_file:
                pickle.load(pickle_file)
        except Exception as e:
            print('Failed to load ' + fn + ': ' + str (e))
