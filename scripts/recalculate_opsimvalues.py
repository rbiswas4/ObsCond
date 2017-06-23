"""
This script can be used to re-calculate skybrightnesses `filtSkyBrightness` and the 5 sigma depth
 `m5` that are in the OpSim output columns using the `sims_skybrightness` model in `lsst.sims`. 

Prerequisites:
    - the `lsst.sims` package must be installed and setup correctly.
    - `OpSimSummary` must be installed
    - joblib is required for parallelization on a multi-processor machine
    - pandas with hdf5 capabilities

Usage:
    - Setup the lsst sims stack
    - `nohup python recalculate_m5.py > recalculate_m5.log 2>&1 &`

Output:
    - A set of hdf5 files and log files  

"""
# This script is run when the LSST Sims  package is installed and setup
import logging
import os
import time
import numpy as np
import healpy as hp
import pandas as pd
from joblib import Parallel, delayed
from lsst.sims.photUtils import Sed, calcM5, PhotometricParameters
from lsst.sims.photUtils import Bandpass, BandpassDict
import lsst.sims.skybrightness as sb
from opsimsummary import OpSimOutput
from lsst.utils import getPackageDir
import sys
import obscond
sys.stdout.flush()


# Read the opsim data base and start logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
tstart = time.time()
logger.info('Start Program at time {}'.format(tstart))
print('Healpy version: ', hp.__version__)
print('numpy version: ', np.__version__)
print('healpy dir', getPackageDir('healpy'))
print('sims_skybrightness_dir', getPackageDir('sims_skybrightness'))
print('sims_skybrightness_data_dir', getPackageDir('sims_skybrightness_data'))
print('obscond version', obscond.__version__)

logger.info('Start reading opsim database')
minion_out = '/local/lsst/rbiswas/data/LSST/OpSimData/minion_1016_sqlite.db'
#minion_out = '/Users/rbiswas/data/LSST/OpSimData/minion_1016_sqlite.db'
opsout = OpSimOutput.fromOpSimDB(minion_out, zeroDDFDithers=True, subset="unique_all")
# opsout = OpSimOutput.fromOpSimDB(minion_out, zeroDDFDithers=True, subset="ddf")
print('reading done\n')
df = opsout.summary.copy()
logger.info('Finished reading database at {}'.format(time.time()))

totalbpdict, hwbpdict = BandpassDict.loadBandpassesFromFiles()
photparams = PhotometricParameters()


# Split the entries in the opsim database for parallelization
splits = 1000
dfs = np.array_split(df, splits)
print('splitting dataframe of size {0} into {1} splits each of size {2}\n'.format(len(df), splits, len(dfs[0])))

calcdfs = []
def recalcmags(j):
    logfname = 'newres_{}.log'.format(j)
    tsplitstart = time.time()
    with open(logfname, 'w') as f:
        f.write('starting split {0} at time {1}\n'.format(j, tsplitstart))
    df = dfs[j]
    sm = sb.SkyModel(observatory='LSST', mags=False, preciseAltAz=True)
    skycalc = obscond.SkyCalculations(photparams="LSST", hwBandpassDict=hwbpdict)

    fname = 'newres{}.hdf'.format(j)
    df_res = skycalc.calculatePointings(df)
    with open(logfname, mode='a+') as f:
        f.write('dataframe calculated\n')
    df_res.to_hdf(fname, key='0')
    tsplitend = time.time()
    with open(logfname, mode='a+') as f:
        f.write('dataframe written at time {} \n'.format(tsplitend))
        f.write('For dataframe of size {0} time taken is {1}\n'.format(len(df_res), tsplitend - tsplitstart))
    return df_res

ndf = Parallel(n_jobs=-1)(delayed(recalcmags)(j=j) for j in range(splits)) 
print('After loops are over, this is the number of dataframes\n', len(ndf))
newdf = pd.concat(ndf)
print('number of lines {}\n'.format(len(newdf)))
newdf.to_hdf('newOpSim.hdf', key='0')
tend = time.time() 
logger.info('End Program at time {} sec'.format(tend))
logger.info('Time taken is {} sec'.format(tend - tstart))
print('DONE')
