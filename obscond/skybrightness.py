from lsst.sims.photUtils import Sed, calcM5, PhotometricParameters
from lsst.sims.photUtils import Bandpass, BandpassDict
import lsst.sims.skybrightness as sb
from .atmosphere import AirmassDependentBandpass
import numpy as np
import pandas as pd

class SkyCalculations(object):
    def __init__(self,
                 observatory='LSST',
                 mags=False,
                 preciseAltAz=True,
                 hwBandpassDict=None,
                 photparams = None,
                 pointings=None):
        """
        """
        self.sm = sb.SkyModel(observatory=observatory,
                              mags=mags,
                              preciseAltAz=preciseAltAz)
        self.adb = AirmassDependentBandpass(hwBandpassDict) 
    
        self.photparams = photparams
        if self.photparams == 'LSST':
            self.photparams = PhotometricParameters()

    def skymag(self, bandName, ra=None, dec=None, mjd=None,
               hwBandPassDict=None,
               sm=None):
        """
        ra : radians
        dec : radians
        """
        if hwBandPassDict is None:
            hwBandPassDict = self.adb.hwbandpassDict
        if sm is None:
            sm = self.sm
        if ra is not None:
            sm.setRaDecMjd(lon=ra, lat=dec,
                           filterNames=bandName, mjd=mjd,
                           degrees=False, azAlt=False)
        skymag = sm.returnMags(bandpasses=hwBandPassDict)[bandName][0]
        return skymag


    def fiveSigmaDepth(self, bandName, airmass, FWHMeff, ra=None, dec=None,
                       mjd=None, sm=None):
        """
        """
        if sm is None:
            sm = self.sm
        if ra is not None:
            sm.setRaDecMjd(lon=ra, lat=dec,
                           filterNames=bandName, mjd=mjd,
                           degrees=False, azAlt=False)
        # SED 
        wave, spec = sm.returnWaveSpec()
        sed = Sed(wavelen=wave, flambda=spec[0])
        bp = self.adb.bandpassForAirmass(bandName, airmass) 
        fieldmags = calcM5(sed, bp, self.adb.hwbandpassDict[bandName], self.photparams,
                           FWHMeff)
        return fieldmags

    def calculatePointings(self, pointings,
                           raCol='fieldRA', 
                           decCol='fieldDec',
                           bandCol='filter',
                           mjdCol='expMJD',
                           airmassCol='airmass',
                           FWHMeffCol='FWHMeff',
                           calcSkyMags=True,
                           calcDepths=True,
                           hwBandPassDict=None,
                           sm=None):
        """
        """
        if hwBandPassDict is None:
            hwBandPassDict = self.adb.hwbandpassDict
        if sm is None:
            sm = self.sm

        num = len(pointings)
        idxs = np.zeros(num)
        skymags = np.zeros(num)
        fiveSigmaDepth = np.zeros(num)


        count = 0 
        for obsHistID, row in pointings.iterrows():
            ra  =row[raCol]
            dec  =row[decCol]
            bandName = row[bandCol]
            airmass = row[airmassCol]
            mjd = row[mjdCol]
            FWHMeff = row[FWHMeffCol]
            sm.setRaDecMjd(lon=ra, lat=dec,
                           filterNames=bandName, mjd=mjd,
                           degrees=False, azAlt=False)
            if calcDepths:
                fiveSigmaDepth[count] = self.fiveSigmaDepth(bandName, airmass,
                                                         FWHMeff, sm=sm)
            if calcSkyMags:
                skymags[count] = self.skymag(bandName, sm=sm, hwBandPassDict=hwBandPassDict)

            idxs[count] = obsHistID
            count += 1

        return pd.DataFrame(dict(obsHistID=idxs, filtSkyBrightness=skymags,
                                 fiveSigmaDepth=fiveSigmaDepth)).set_index('obsHistID')
