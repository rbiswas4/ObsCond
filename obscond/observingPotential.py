from __future__ import print_function, division, absolute_import

__all__ = ['ObservationPotential']
import time
import numpy as np
import pandas as pd


import lsst.sims.skybrightness as sb
from lsst.sims.utils import (Site, approx_RaDec2AltAz)
import ephem
from obscond import SkyCalculations as sm


from lsst.sims.utils import angularSeparation
from scipy.interpolate import interp1d

class ObservationPotential(object):
    """
    Class to define the potential for observations


    Parameters
    ----------
    fieldRA : float, in radians
        RA of the field
    fieldDec : float, in radians
        Dec of the field
    observatory : string, defaults to `LSST`
        string specifying observatory to `ephem`
    """
    def __init__(self, fieldRA, fieldDec,
                 observatory='LSST'):
        self.ra = np.degrees(fieldRA)
        self.dec = np.degrees(fieldDec)
        self.site = Site(observatory)
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
        mjd : `np.float`, unit day
            time of observation

        Returns
        -------
        moon ra: radians
        moon dec: radians
        moon alt: radians
        """
        self.obs.date = mjd - self.doff
        self.moon.compute(self.obs)
        return self.moon.ra, self.moon.dec, self.moon.alt


    def sunAlt_singleTime(self, tt):
        """return the sun Altitude at a time tt in radians
        
        Parameters
        ----------
        tt : `np.float`, unit day
            time at which altitude is desired in mjd
            
        Returns
        -------
        sun alt: radians
        """
        self.obs.date = tt - self.doff
        self.sun.compute(self.obs)

        return self.sun.alt
    
    def sunAlt(self, mjd):
        """return the sun Altitude at an array of times in degrees

        Parameters
        ----------
        mjd : array-like, MJD
            sequence of times of observation in MJD
        """
        sunAlt = np.degrees(list(self.sunAlt_singleTime(tt) for tt in mjd))
        return sunAlt
    
    def moonCoords(self, mjd):
        """return the moon coordinates (ra, dec, Alt) at an array of times in
        degrees


        Parameters
        ----------
        mjd : sequence of floats
            Times in Modified Julian Date

        Returns
        -------
        moon ra: degrees
        moon dec: degrees
        moon alt: degrees
        """
        moonRA, moonDec, moonAlt = list(zip(*(self.moonCoords_singleTime(tt) for tt in mjd)))
        return np.degrees(moonRA), np.degrees(moonDec), np.degrees(moonAlt)

    
    def field_coords(self, fieldRA, fieldDec, mjd):
        """Return the field Coordinates in degrees.
        
        Parameters
        ----------
        fieldRA : float, or array, degrees
            RA of the field
        fiedlDec : float or array, degrees
            Dec of the field
        mjd : float or array
        Returns
        -------
        alt : degrees
        az : degrees 
        """
        ra = np.ravel(fieldRA)
        dec = np.ravel(fieldDec)
        mjd = np.ravel(mjd)

        # note that all angle arguments are in degrees
        alt, az = approx_RaDec2AltAz(ra=ra, dec=dec,
                                     lat=self.site.latitude,
                                     lon=self.site.longitude,
                                     mjd=mjd,
                                     lmst=None)
        return alt, az
    
    def potential_obscond(self, t, fieldRA, fieldDec,
                          nightOffset=59579.6):
        """
        Calculate the observing Conditions at a sequence of mjd values
         `t` for a location with ra and dec `fieldRA` and `fieldDec` in
         `degrees`.
        Parameters
        ----------
        t : times at which observations are being made

        fieldRA : RA, degree

        fieldDec : Dec, degree

        nightOffset : mjd value, defaults to 59579.6
            mjd value for night = 0 of the survey.
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
        
        return df
    
    def available_times(self, potential_times, constraints):
        """returns available times 
        """
        self._available_times = potential_times.query(constraints)
        return self._available_times
    
    @staticmethod
    def dc2_sequence(start_time, year_block, delta=1):
        """

        Parameters
        ----------
        start_time :

        year_block :

        delta : , defaults to 1.
        """
        sec = 1.0 / 24.0/60./60.

        if year_block == 1:
            fraction = 0.75

        if year_block == 2:
            fraction = 0.5
            delta = 0.

        standard_sequence = np.array(list((20, 10, 20, 26, 20)))
        time = start_time
        l = []
        visitlist = []
        seq = standard_sequence 
        extravisits = np.array([0, 1, 0, 1, 0]) * delta
        #print(seq)
        bandlist = []

        # Iterate through the standard list of band, standard visit sequences
        # For on and off years
        for band, visits, morevisits in zip(list('rgizy'), seq, extravisits):
            numVisits = np.floor(visits * fraction) + morevisits
            times = np.linspace(time, time + (numVisits - 1) * 38 * sec,
                                numVisits)
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
            df, vl = ObservationPotential.dc2_sequence(st, year_block, delta)
            vs.append(df)
        df = pd.concat(vs)
        df['night'] = np.floor(df.expMJD - 59579.6)

        if pointings is not None:
            rawSeeing = interp1d(pointings.expMJD.values,
                                 pointings.rawSeeing.values,
                                 kind='nearest')

            df['rawSeeing'] = rawSeeing(df.expMJD.values)
            alt, az = approx_RaDec2AltAz(ra=ra, dec=dec,
                                         lat=self.site.latitude,
                                         lon=self.site.longitude,
                                         mjd=df.expMJD.values,
                                         lmst=None)
            df['alt'] = alt
            df['az'] = az
   
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
