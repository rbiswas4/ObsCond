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
sys.stdout.flush()


# Read the opsim data base and start logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
print('Healpy version: ', hp.__version__)
print('numpy version: ', np.__version__)
print('healpy dir', getPackageDir('healpy'))
print('sims_skybrightness_dir', getPackageDir('sims_skybrightness'))
print('sims_skybrightness_data_dir', getPackageDir('sims_skybrightness_data'))

logger.info('Start reading opsim database')
minion_out = '/local/lsst/rbiswas/data/LSST/OpSimData/minion_1016_sqlite.db'
opsout = OpSimOutput.fromOpSimDB(minion_out, zeroDDFDithers=True, subset="unique_all")
print('reading done')
df = opsout.summary.copy()
logger.info('Finished reading database at {}'.format(time.time()))

# Bandpasses and LSST related stuff
def atmTransName(airmass):
    """
    obtain the filename with the transmissions for files for an airmass value closest to the requested value
    """
    l = np.arange(1.0, 2.51, 0.1)
    idx = np.abs(l - airmass).argmin()
    a = np.int(10*l[idx])
    baseline = getPackageDir('THROUGHPUTS')
    fname = os.path.join(baseline, 'atmos', 'atmos_{}_aerosol.dat'.format(a))
    return fname

logger.info('Get Bandpasses')
totalbpdict, hwbpdict = BandpassDict.loadBandpassesFromFiles()
photparams = PhotometricParameters()


# Split the entries in the opsim database for parallelization
splits = 40
dfs = np.array_split(df, splits)
print('splitting dataframe of size {0} into {1} splits each of size {2}'.format(len(df), splits, len(dfs[0])))

calcdfs = []
def recalcmags(j, lst=calcdfs):
    logfname = 'newres_{}.log'.format(j)
    with open(logfname, 'w') as f:
        f.write('starting split {} \n'.format(j))
    # print('starting split ', j)
    df = dfs[j]
    sm = sb.SkyModel(observatory='LSST', mags=False, preciseAltAz=True)
    i = 0
    fieldmags = np.zeros(len(df), dtype=np.float)
    skymags = np.zeros(len(df), dtype=np.float)

    # ditheredmags = np.zeros(len(df), dtype=np.float)    
    for obsHistID, row in df.iterrows():
        bandname = row['filter']
        airmass = row['airmass']
        # The Skybrightness Model only has support for airmass <=2.5
        if airmass > 2.5:
            skymags[i] = np.nan
            fieldmags[i] = np.nan
            continue

        # Get atmospheric transmission for airmass of pointing
        fname = atmTransName(airmass)
        atmTrans = np.loadtxt(fname)
        wave, trans = hwbpdict[bandname].multiplyThroughputs(atmTrans[:, 0], atmTrans[:, 1]) 
        bp = Bandpass(wavelen=wave, sb=trans)
        sm.setRaDecMjd(lon=[row['fieldRA']], lat=[row['fieldDec']], filterNames=[row['filter']],
                       mjd=row['expMJD'], degrees=False, azAlt=False)
        
        wave, spec = sm.returnWaveSpec()
        sed = Sed(wavelen=wave, flambda=spec[0])
        skymags[i] = sm.returnMags(bandpasses=hwbpdict)[row['filter']][0]
        fieldmags[i] = calcM5(sed, bp, hwbpdict[bandname], photparams, 
                              row['FWHMeff'])
        #sm.setRaDecMjd(lon=row['ditheredRA'], lat=row['ditheredDec'], filterNames=row['filter'],
        #               mjd=row['expMJD'], degrees=False, azAlt=False)
        
        # sed = Sed(wavelen=wave, flambda=spec[1])
        # ditheredmags[i] = calcM5(sed, bp, hwbpdict[bandname], photparams, 
        #                         row['FWHMeff'])
    
        i += 1
        if (i%1000) == 0:
            with open(logfname, mode='a+') as f:
                f.write('calculation done for {} th record\n'.format(i))

    df['fieldm5'] = fieldmags
    df['skymags'] = skymags
    #df['ditheredm5'] = ditheredmags
    lst.append(df)
    # print('done')

    fname = 'newres{}.hdf'.format(j)
    df = df[['fiveSigmaDepth', 'fieldm5','skymags', 'airmass', 'filter']]
    with open(logfname, mode='a+') as f:
        f.write('dataframe calculated')
    df.to_hdf(fname, key='0')
    # print('finished writing ', fname)
    # print('num of lines is ', len(df))
    with open(logfname, mode='a+') as f:
        f.write('dataframe written')
    return df

# ndf = Parallel(n_jobs=-1)(delayed(recalcmags)(j=j, lst=calcdfs) for j in range(2)) 
ndf = Parallel(n_jobs=-1)(delayed(recalcmags)(j=j, lst=calcdfs) for j in range(splits)) 
print('After loops are over, this is the number of dataframes', len(ndf))
newdf = pd.concat(ndf)
print('number of lines {}'.format(len(newdf)))
newdf.to_hdf('newOpSim.hdf', key='0')
print('DONE')
