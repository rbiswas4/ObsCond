import obscond as oc
import unittest
import numpy as np
import pandas as pd
from pandas.util.testing import assert_frame_equal
import os


class weatherInterfaceTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """
        Sets up required quantities to check that obscond.WeatherData
        set up using the fromTxtFiles() methods and setup directly
        test as equal as they should

        cls.seeingHistoryFile :  seeing txt file used in this test
        cls.cloudHistoryFile : cloud fraction txt file used in this test
        cls.wFromTxt : WeatherData class constructed from TxtFiles
        """
        cls.seeingHistoryFile = os.path.join(oc.example_data_dir,
                                             'SeeingPachon.txt')
        cls.cloudHistoryFile = os.path.join(oc.example_data_dir,
                                            'CloudTololo.txt')
        # Simplest, probably most frequently used method of building the
        # weather data

        cls.wFromTxt = oc.WeatherData.fromTxtFiles()

        # Read the seeing history file and create the required input
        # creation of WeatherData instance

        _seeingHistory = pd.DataFrame(np.genfromtxt(cls.seeingHistoryFile,
                                                    names=True))
        _seeingHistory['days'] = _seeingHistory['s_date']/oc.DAY_IN_SEC
        cls.seeing_df = _seeingHistory[['days', 'seeing']]

        # Read the cloud History file and create the required input for
        # creation of WeatherData instance
        _cloudHistory = pd.DataFrame(np.genfromtxt(cls.cloudHistoryFile,
                                     names=True))
        _cloudHistory['days'] = _cloudHistory['c_date']/oc.DAY_IN_SEC
        _cloud_df = _cloudHistory[['days', 'cloud']]
        _cloud_df.rename(columns={'cloud': 'cloudFraction'}, inplace=True)
        cls.cloud_df = _cloud_df

        return cls

    def test_seeingHistory_match(self):
        assert_frame_equal(self.wFromTxt.seeingHistory, self.seeing_df)

    def test_cloudHistory_match(self):
        assert_frame_equal(self.wFromTxt.cloudHistory, self.cloud_df)

    def test_directCreation(self):
        w = oc.WeatherData(seeingHistory=self.seeing_df,
                           cloudHistory=self.cloud_df,
                           startDate=0)

        assert_frame_equal(w.seeingHistory, self.wFromTxt.seeingHistory)
        assert_frame_equal(w.cloudHistory, self.wFromTxt.cloudHistory)

    def test_seeing(self):

        times = np.arange(0., 1000. / oc.DAY_IN_SEC, 1. / oc.DAY_IN_SEC/100.)
        x = self.wFromTxt.seeing(times=times, startDate=0.)
        assert len(x) == len(times)
        assert isinstance(x, np.ndarray)



if __name__=="__main__":

    unittest.main()
