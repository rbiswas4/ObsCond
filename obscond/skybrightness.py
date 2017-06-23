from lsst.sims.photUtils import Sed, calcM5, PhotometricParameters
from lsst.sims.photUtils import Bandpass, BandpassDict
import lsst.sims.skybrightness as sb
from .atmosphere import AirmassDependentBandpass
import numpy as np
import pandas as pd

class SkyCalculations(object):
    """
    Class for calculating sky brightnesses and related quantities, as well as
    coordinates. All the heavy lifting is done in `lsst.sims_skybrightness`.
    The main functionality of this wrapper is to fix some of the freedome in
    `sims_skybrightness` to useful choices through defaults to optional
    parameters, thereby simplifiying the usage.

    Among the provisos of the sky model, an important one to recall is that the
    skymagnitudes are only calculated to an airmass of 2.5. For airmasses which
    are beyond that value, the default settings we use will return values for
    an inconsistent airmass of 2.5. This is different from the default setting
    of `sims.skybrightness` model, where this would return `np.nan`
    """
    def __init__(self,
                 observatory='LSST',
                 hwBandpassDict=None,
                 pointings=None,
                 photparams=None,
                 airmass_limit=4.0,
                 mags=False,
                 preciseAltAz=True
                 ):
        """
        Parameters
        ----------
        observatory : 
        mags : 
        preciseAltAz :
        hwBandpassDict :
        photparams :
        pointings :
        airmass_limit :
        """
        self.sm = sb.SkyModel(observatory=observatory,
                              mags=mags,
                              preciseAltAz=preciseAltAz,
                              airmass_limit=airmass_limit)
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


    def fiveSigmaDepth(self, bandName, FWHMeff, ra=None, dec=None,
                       mjd=None, sm=None, provided_airmass=None,
                       use_provided_airmass=True):
        """
        """
        if sm is None:
            sm = self.sm
        if ra is not None:
            sm.setRaDecMjd(lon=ra, lat=dec,
                           filterNames=bandName, mjd=mjd,
                           degrees=False, azAlt=False)
        airmass = sm.airmass
        # SED 
        wave, spec = sm.returnWaveSpec()
        sed = Sed(wavelen=wave, flambda=spec[0])
        amass = airmass
        if use_provided_airmass and provided_airmass is not None:
            amass = provided_airmass
        else:
            amass = airmass
        bp = self.adb.bandpassForAirmass(bandName, amass) 
        fieldmags = calcM5(sed, bp, self.adb.hwbandpassDict[bandName], self.photparams,
                           FWHMeff)
        return fieldmags

    def calculatePointings(self, pointings,
                           raCol='fieldRA', 
                           decCol='fieldDec',
                           bandCol='filter',
                           mjdCol='expMJD',
                           FWHMeffCol='FWHMeff',
                           calcSkyMags=True,
                           calcDepths=True,
                           calcPointingCoords=True,
                           calcMoonSun=True,
                           hwBandPassDict=None,
                           sm=None):
        """
        """
        resultCols = []

        if hwBandPassDict is None:
            hwBandPassDict = self.adb.hwbandpassDict
        if sm is None:
            sm = self.sm

        num = len(pointings)
        idxs = np.zeros(num)
        skymags = np.zeros(num)
        fiveSigmaDepth = np.zeros(num)
        airmass = np.zeros(num)
        altitude = np.zeros(num)
        azimuth = np.zeros(num)
        moonRA = np.zeros(num)
        moonDec = np.zeros(num)
        moonAlt = np.zeros(num)
        moonAZ = np.zeros(num)
        moonPhase = np.zeros(num)
        sunAlt = np.zeros(num)
        sunAz = np.zeros(num)


        count = 0 
        for obsHistID, row in pointings.iterrows():
            ra  =row[raCol]
            dec  =row[decCol]
            bandName = row[bandCol]
            mjd = row[mjdCol]
            FWHMeff = row[FWHMeffCol]
            sm.setRaDecMjd(lon=ra, lat=dec,
                           filterNames=bandName, mjd=mjd,
                           degrees=False, azAlt=False)
            mydict = sm.getComputedVals()
            if calcPointingCoords:
                if count == 0:
                    resultCols += ['airmass', 'altitude' , 'azimuth']
                airmass[count] = mydict['airmass'][0]
                altitude[count] = mydict['alts'][0]
                azimuth[count] = mydict['azs'][0]

            if calcMoonSun:
                if count == 0:
                    resultCols += ['moonRA', 'moonDec' , 'moonAlt', 'moonAZ', 'moonPhase']
                    resultCols += ['sunAlt', 'sunAz']
                moonRA[count] = mydict['moonRA']
                moonDec[count] = mydict['moonDec']
                moonAlt[count] = mydict['moonAlt']
                moonAZ[count] = mydict['moonAz']
                moonPhase[count] = mydict['moonPhase']
                sunAlt[count] = mydict['sunAlt']
                sunAz[count] = mydict['sunAz']

            if calcDepths:
                if count == 0:
                    resultCols += ['fiveSigmaDepth']
                fiveSigmaDepth[count] = self.fiveSigmaDepth(bandName,
                                                            FWHMeff, sm=sm,
                                                            provided_airmass=airmass[count],
                                                            use_provided_airmass=False)
            if calcSkyMags:
                if count == 0:
                    resultCols += ['filtSkyBrightness']
                skymags[count] = self.skymag(bandName, sm=sm,
                                             hwBandPassDict=hwBandPassDict)

            idxs[count] = obsHistID
            count += 1

        df = pd.DataFrame(dict(obsHistID=idxs, filtSkyBrightness=skymags,
                                 fiveSigmaDepth=fiveSigmaDepth,
                                 altitude=altitude,
                                 azimuth=azimuth,
                                 airmass=airmass,
                                 moonRA=moonRA,
                                 moonDec=moonDec,
                                 moonAZ=moonAZ,
                                 moonAlt=moonAlt,
                                 moonPhase=moonPhase,
                                 sunAlt=sunAlt,
                                 sunAz=sunAz)).set_index('obsHistID')
        df.index = df.index.astype(np.int64)
        return df[resultCols]
