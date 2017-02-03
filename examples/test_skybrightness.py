import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
sns.set_style('whitegrid')

from lsst.sims.photUtils import Bandpass, BandpassDict
import lsst.sims.skybrightness as sb
from lsst.sims.photUtils import Sed, calcM5, PhotometricParameters
from lsst.utils import getPackageDir
import os
from brightness import mCalcs, atmTransName
from lsst.sims.skybrightness import SkyModel


tot, hwbpdict = BandpassDict.loadBandpassesFromFiles()
#print(mCalcs(1.464, 'y', 1.676483, -1.082473, 59580.033829, 1.263038, hwbpdict))
#print(mCalcs(1.454958, 'y', 1.69412, -1.033972, 59580.034275, 1.258561, hwbpdict))
print(mCalcs(1.008652, 'g', 0.925184, -0.4789, 61044.077855, 1.086662, hwbpdict=hwbpdict))
print(np.__version__)
