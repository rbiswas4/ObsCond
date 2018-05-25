from __future__ import print_function, division, absolute_import

__all__ = ['ObservationPotential']
import time
import numpy as np
import pandas as pd

import lsst.sims.skybrightness as sb
from lsst.sims.utils import Site
import ephem
from obscond import SkyCalculations as sm


from lsst.sims.utils import angularSeparation
from scipy.interpolate import interp1d

class ObservationPotential(object):
    def __init__(self, fieldRA, fieldDec,
                 observatory='LSST'):
        self.ra = fieldRA
        self.dec = fieldDec
        self.site = Site('LSST')
        self.sun = ephem.Sun()
        self.moon = ephem.Moon()
        self.obs = ephem.Observer()
        self.obs.lat = np.radians(self.site.latitude)
        self.obs.long = np.radians(self.site.longitude)
        self.obs.elevation = self.site.height
        self.doff = ephem.Date(0) - ephem.Date('1858/11/17')
        self._available_times = None
        self.sec = 1.0 / 24.0 / 60.0/ 60.0 

    def moonCoords_singleTime(self, mjd):
        """
        returns the moon ra, dec, and alt in radians
        
        Parameters
        ----------
        
        """
        self.obs.date = mjd - self.doff
        self.moon.compute(self.obs)
        return self.moon.ra, self.moon.dec, self.moon.alt


    def sunAlt_singleTime(self, tt):
        """return the sun Altitude at a time tt in radians
        
        Parameters
        ----------
        tt : float
            time at which altitude is desired in mjd
            
        Return:
        in radians
        """
        self.obs.date = tt - self.doff
        self.sun.compute(self.obs)
        return self.sun.alt
    
    def sunAlt(self, mjd):
        sunAlt = np.degrees(list(self.sunAlt_singleTime(tt) for tt in mjd))
        return sunAlt
    
    def moonCoords(self, mjd):
        moonRA, moonDec, moonAlt = list(zip(*(self.moonCoords_singleTime(tt) for tt in mjd)))
        return np.degrees(moonRA), np.degrees(moonDec), np.degrees(moonAlt)

    
    def field_coords(self, fieldRA, fieldDec, mjd):
        """
        Return the field Coordinates in degrees.
        
        Parameters
        ----------
        fieldRA : float, or array, radians
            RA of the field
        fiedlDec : float or array, radians
            Dec of the field
        mjd : float or array
        
        """
        ra = np.ravel(fieldRA)
        dec = np.ravel(fieldDec)
        mjd = np.ravel(mjd)
        alt, az = sb.stupidFast_RaDec2AltAz(ra, dec,
                                            self.site.latitude_rad,
                                            self.site.longitude_rad,
                                            mjd=mjd)
        return np.degrees(alt), np.degrees(az)
    
    def potential_obscond(self, t, fieldRA, fieldDec,
                          nightOffset=59579.6):
        """
        Parameters
        ----------
        t : times at which observations are being made
        """
        alt, az = self.field_coords(fieldRA, fieldDec, mjd=t)
        moonra, moondec, moonalt = self.moonCoords(mjd=t)
        sunAlt = self.sunAlt(mjd=t)
        df = pd.DataFrame(dict(mjd=t,
                       alt=alt,
                       az=az, 
                       sunAlt=sunAlt,
                       moonRA=moonra,
                       moonDec=moondec,
                       moonAlt=moonalt,
                       night=np.floor(t-59579.6).astype(np.int)))
        df['moonDist'] = angularSeparation(moonra, moondec,
                                           np.degrees(self.ra),
                                           np.degrees(self.dec))
        #df.sunAlt = df.sunAlt.apply(np.degrees)
        
        return df
    
    def available_times(self, potential_times, constraints):
        
        self._available_times = potential_times.query(constraints)
        return self._available_times
    
    @staticmethod
    def dc2_sequence(start_time, year_block, delta=1):
        sec = 1.0 / 24.0/60./60.
        if year_block == 1:
            fraction = 0.75
        if year_block == 2:
            fraction = 0.5
            delta = 0.
        standard_sequence = np.array(list((20, 10, 20, 26, 20)))
        time  = start_time
        l = []
        visitlist = []
        seq = standard_sequence 
        extravisits = np.array([0, 1, 0, 1, 0]) * delta
        #print(seq)
        bandlist = []
        for band, visits, morevisits in zip(list('rgizy'), seq, extravisits):
            numVisits = np.floor(visits * fraction) + morevisits
            times = np.linspace(time, start_time + (numVisits -1) * 38 *sec, numVisits)
            l.append(times)
            visitlist.append(numVisits)
            time = times[-1] + 150.0 * sec
            bandlist.append(np.repeat(band, numVisits))
        df = pd.DataFrame(dict(expMJD=np.concatenate(l),
                          filter=np.concatenate(bandlist)))
        return df, visitlist
    
    @staticmethod
    def dc2_visits(start_times, year_block, delta=1, pointings=None):
        
        vs = []
        for st in start_times.values:
            df, vl = ObservationPotential.dc2_sequence(st, year_block, delta=1)
            vs.append(df)
        df = pd.concat(vs)
        df['night'] = np.floor(df.expMJD - 59579.6)
        if pointings is not None:
            rawSeeing = interp1d(pointings.expMJD.values, 
                                 pointings.rawSeeing.values,
                                 kind='nearest')
            df['rawSeeing'] = interp1d(df.expMJD.values)
            
        return df
        
    
    @staticmethod
    def nightStats(availabletimes):
        df = availabletimes.groupby('night').agg(dict(mjd=(min, max))).reset_index()
        df = pd.DataFrame(df.values, columns=('night', 'minmjd', 'maxmjd'))
        df['availTime'] = (df.maxmjd - df.minmjd) * 24.0
        return df.set_index('night')
        
    @staticmethod
    def start_times(nightStats, chosen_nights, rng):
        zz = nightStats
        df = zz.loc[chosen_nights]#.tolist())
        df['maxtime'] = df.maxmjd - 1.25 / 24.
        random = rng.uniform(size=len(chosen_nights))
        start_time = df.minmjd + (df.maxtime - df.minmjd) * random
        return start_time
    
    @staticmethod
    def timerange(series):
        return (max(series) - min(series))*24.0
