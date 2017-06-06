from obscond import SkyCalculations
from lsst.sims.photUtils import BandpassDict
import unittest
from numpy.testing import assert_almost_equal

class TestSkyBrightness(unittest.TestCase):
    totalbandpassdict, hwbandpassdict = BandpassDict.loadBandpassesFromFiles()
    skycalc = SkyCalculations(photparams="LSST", hwBandpassDict=hwbandpassdict)

    def test_skymags(self):
        skymag = self.skycalc.skymag('g', 0.925184, -0.4789, 61044.077855)
        assert_almost_equal(skymag, 18.8900, decimal=2) 

    def test_skyDepths(self):
        m5 = self.skycalc.fiveSigmaDepth('g', 1.008652, 1.086662, 0.925184, -0.4789, 61044.077855)
        assert_almost_equal(m5, 23.0601, decimal=2)

