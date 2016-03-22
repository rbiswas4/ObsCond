import os
import pandas as pd
import sys
import numpy as np
from .constants import *
from .io import *

__all__ = ['WeatherData']

SeeingFile = os.path.join(example_data_dir, 'SeeingPachon.txt')
CloudFile = os.path.join(example_data_dir, 'CloudTololo.txt')

class WeatherData(object):
    """
    Class to provide Seeing and Cloud fraction as a function of time. 
    """
    def __init__(self,
                 seeingHistory,
                 cloudHistory,
                 startDate=None,
                 endDate=None):
        """
        Parameters
        ----------
        SeeingHistory : `pandas.DataFrame` with the following columns
            'days', 
        CloudHistory:
        """

        self.cloudHistory = None
        self.seeingHistory = seeingHistory 
        self.startDate = startDate

    @classmethod
    def fromTxtFiles(cls,
                     SeeingTxtFile=SeeingFile,
                     CloudTxtFile=CloudFile):
        """
        build the class from txt files that are being used in OpSim

        Parameters
        ----------

        Returns
        -------
        """
        seeingHistory = pd.read_csv(SeeingTxtFile, delim_whitespace=True)
        stripLeadingPoundFromHeaders(seeingHistory)

        # seeingHistory.rename(columns={seeingHistory.columns[0]:
        #                              seeingHistory.columns[0][1:]},
        #                              inplace=True)

        seeingHistory['days'] = seeingHistory['s_date'] / DAY_IN_SEC
        seeingColNames = ['days', 'seeing']

        cloudHistory = pd.read_csv(CloudTxtFile, delim_whitespace=True)
        stripLeadingPoundFromHeaders(cloudHistory)

        cloudHistory['days'] = cloudHistory['c_date'] / DAY_IN_SEC
        cloudHistory.rename(columns={'cloud', 'cloudFraction'}, inplace=True)
        cloudColNames = ['days', 'cloud']

        return cls(seeingHistory=seeingHistory[seeingColNames],
                   cloudHistory=cloudHistory)

    def seeing(self, times, startDate=None, method='linearInterp'):
        """
        """
        if startDate is None:
            startDate = self.startDate
            if startDate is None:
                raise ValueError('startDate must be provided as an attribute or\
                                 as a parameter to the method\n')

        native_times = self.seeingHistory.days.values - startDate
        native_seeing = self.seeingHistory.seeing.values 

        if method == 'linearInterp':
            return np.interp(times, native_times, native_seeing, period=max(native_times))
        else:
            raise ValueError('method not implemented \n')

