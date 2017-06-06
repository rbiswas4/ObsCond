from __future__ import absolute_import
import numpy as np
import pandas as pd
from lsst.sims.photUtils import Bandpass, BandpassDict
import lsst.sims.skybrightness as sb
from lsst.sims.skybrightness import SkyModel
from lsst.sims.photUtils import Sed, calcM5, PhotometricParameters
from lsst.utils import getPackageDir
import os

__all__ = ['atmTransName', 'mCalcs']

def atmTransName(airmass):
    """
    return filename for atmospheric transmission with aerosols for airmass
    closest to input
        
    Parameters
    ----------
    airmass : airmass
    """
    l = np.arange(1.0, 2.51, 0.1)
    idx = np.abs(l - airmass).argmin()
    a = np.int(10*l[idx])
    baseline = getPackageDir('THROUGHPUTS')
    fname = os.path.join(baseline, 'atmos', 'atmos_{}_aerosol.dat'.format(a))
    return fname

def mCalcs(airmass, bandName, ra, dec, expMJD,  FWHMeff, hwbpdict, photparams=None, sm=None):
    """
    sm : 
    """
    if photparams is None:
        photparams = PhotometricParameters()
    if sm is None:
        sm = SkyModel(observatory='LSST', mags=False, preciseAltAz=True)
    # Obtain full sky transmission at airmass
    # Note that this method is not interpolating but choosing the atmospheric transmission from
    # Modtran simulations of the closest airmass in a sequence of np.arange(1., 2.51, 0.1)
    fname = atmTransName(airmass)
    print(fname)
    atmTrans = np.loadtxt(fname)
    wave, trans = hwbpdict[bandName].multiplyThroughputs(atmTrans[:, 0], atmTrans[:, 1])
    bp = Bandpass(wavelen=wave, sb=trans)
    # Set the observing condition
    sm.setRaDecMjd(lon=[ra], lat=[dec], filterNames=[bandName],
                   mjd=expMJD, degrees=False, azAlt=False)
    # Get the sky sed
    wave, spec = sm.returnWaveSpec()
    sed = Sed(wavelen=wave, flambda=spec[0])
    sed.writeSED('skySED_laptop.csv')
    m5 = calcM5(sed, bp, hwbpdict[bandName], photparams, FWHMeff)
    # Get the sky magnitude only in the band concerned
    m = sm.returnMags(bandpasses=hwbpdict)[bandName][0]
    return m5, m
