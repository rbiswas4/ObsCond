from lsst.sims.photUtils import Sed, calcM5, PhotometricParameters
from lsst.sims.photUtils import Bandpass, BandpassDict
import lsst.sims.skybrightness as sb
from .atmosphere import AirmassDependentBandpass

sm = sb.SkyModel(observatory='LSST', mags=False, preciseAltAz=True)



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

        def skymag(self, ra, dec, bandName, mjd, sm=None):
            """
            ra : radians
            dec : radians
            """
            if sm is None:
                sm = self.sm
            sm.setRaDecMjd(lon=ra, lat=dec,
                           filterNames=bandName, mjd=mjd,
                           degrees=False, azAlt=False)
            skymag = sm.returnMags(bandpasses=self.adb.hwbandpassDict)['bandName'][0]
            return skymag


        def fiveSigmaDepth(self, ra, dec, bandName, mjd, airmass, FWHMeff,
                           sm=None):
            """
            """
            if sm is None:
                sm = self.sm
            sm.setRaDecMjd(lon=ra, lat=dec,
                           filterNames=bandName, mjd=mjd,
                           degrees=False, azAlt=False)
            # SED 
            wave, spec = sm.returnWaveSpec()
            sed = Sed(wavelen=wave, flambda=spec[0])
            bp = self.adb.bandpassForAirmass(bandName, airmass) 
            fieldmags = calcM5(sed, bp, self.adb.hwbandpassDict, self.photparams,
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
                               sm=skyModel):
            """
            """
            num = len(pointings)
            idxs = np.zeros(num)
            skymag = np.zeros(num)
            fiveSigmaDepth = np.zeros(num)

            count = 0 
            for obsHistID, row in pointings.iterrows():
                ra  =row['raCol']
                dec  =row['decCol']
                bandname = row[bandCol]
                airmass = row[airmassCol]
                mjd = row[mjdCol]
                FWHMeff = row[FWHMeffCol]
                sm.setRaDecMjd(lon=ra, lat=dec,
                               filterNames=bandName, mjd=mjd,
                               degrees=False, azAlt=False)
                if calcDepths:
                    fiveSigmaDepths[i] = fiveSigmaDepth(self, ra, dec,
                                                        bandName, mjd, airmass,
                                                        FWHMeff, sm=sm)
                if calcSkyMags:
                    skymag[i] = skymag(self, ra, dec, bandName, mjd, sm=None)

                idxs[count] = obsHistID
