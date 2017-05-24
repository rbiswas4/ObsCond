"""
A module to describe the atmospheric transmission
"""
__all__ = ['AirmassDependentBandpass']

import os
import numpy as np
from lsst.utils import getPackageDir 
from lsst.sims.photUtils import Bandpass, BandpassDict


class AirmassDependentBandpass(object):
    """
    Class to describe airmass dependent bandpasses. The method that provides
    a `lsst.sims.photUtils.bandpass` object for the appropriate bandpassname 
    and airmass is the method `bandpassForAirmass`
    """
    def __init__(self, hwBandpassDict):
        """
        Parameters
        ----------
        hwBandpassDict: `lsst.sims.photUtils.BandpassDict` object 
            Hardware BandpassDict for the system bandpass (no atmosphere) only.
            This is a dictionary with keys given by each of the bandpass filter
            names 'ugrizy' with values equal to the corresponding
            `lsst.sims.Bandpass` object`
	"""
        self.hwbandpassDict = hwBandpassDict

    @classmethod
    def fromThroughputs(cls):
        """
        instantiate class from the LSST throughputs in the throughputs
        directory
	"""
        totalbpdict, hwbpdict = BandpassDict.loadBandpassesFromFiles()	
        return cls(hwBandpassDict=hwbpdict)

    @staticmethod
    def atmTransName(airmass):
        """
        return the filename holding the atmospheric transmission with airmass
        closest to the provided airmass
    
        Parammeters
        -----------
        airmass : `np.float`
    	value of airmass for which we would like to get the atmospheric
            transmission filename
        """
    
        l = np.arange(1.0, 2.51, 0.1)
        idx = np.abs(l - airmass).argmin()
        a = np.int(10 * l[idx])
        baseline = getPackageDir('THROUGHPUTS')
        fname = os.path.join(baseline, 'atmos', 'atmos_{}_aerosol.dat'.format(a))
    
        return fname

    def bandpassForAirmass(self, bandname, airmass=1.2):
        """
        return the `lsst.sims.photUtils.Bandpass` object corresponding to the
	bandname and airmass

        Parameters
        ----------
        bandname : mandatory, string
            name of the band, which must match the dictionary keys on the
            `lsst.sims.photUtils.BandpassDict`
        airmass : float, defaults to 1.2
            value of airmass for which we want to obtain the bandpass
        """
        fname = self.atmTransName(airmass)
        atmTrans = np.loadtxt(fname)
        wave, trans = self.hwbandpassDict[bandname].multiplyThroughputs(atmTrans[:, 0],
								  atmTrans[:, 1])

        return Bandpass(wavelen=wave, sb=trans)

