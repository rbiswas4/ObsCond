import obscond as oc
import unittest
import numpy as np
import pandas as pd
from pandas.util.testing import assert_frame_equal
import os


class weatherInterfaceTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.wFromTxt = oc.WeatherData.fromTxtFiles()
        cls.seeingHistoryFile = os.path.join(oc.example_data_dir,
                                             'SeeingPachon.txt')
        cls.seeingHistory = pd.DataFrame(np.genfromtxt(cls.seeingHistoryFile,
                                                       names=True))
        cls.seeingHistory['days'] = cls.seeingHistory['s_date']/oc.DAY_IN_SEC


        cls.cloudHistoryFile = os.path.join(oc.example_data_dir,
                                            'CloudTololo.txt')
        cls.cloudHistory = pd.DataFrame(np.genfromtxt(cls.cloudHistoryFile,
                                        names=True))
        cls.cloudHistory['days'] = cls.cloudHistory['c_date']/oc.DAY_IN_SEC

        cls.seeing_df = cls.seeingHistory[['days', 'seeing']]
        cloud_df = cls.cloudHistory[['days', 'cloud']]
        cloud_df.rename(columns= {'cloud': 'cloudFraction'}, inplace=True)
        cls.cloud_df = cloud_df


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


# def test_weather_interface():
#    w = oc.WeatherData.fromTxtFiles()
#    assert len(w.seeingHistory) > 0
#    assert len(w.cloudHistory) > 0
