from obscond import AirmassDependentBandpass
from lsst.sims.photUtils import BandpassDict
from numpy.testing import assert_allclose

def test_airmassdep_bandpass_shape():
    adb  = AirmassDependentBandpass.fromThroughputs()
    bp = adb.bandpassForAirmass(bandname='r', airmass=1.2)
    num = len(bp.wavelen)
    assert num == len(bp.sb) 


def test_airmassdep_bandpass_fid():
    adb  = AirmassDependentBandpass.fromThroughputs()
    tot = BandpassDict.loadTotalBandpassesFromFiles()
    bp = adb.bandpassForAirmass(bandname='r', airmass=1.200)
    assert_allclose(bp.wavelen, tot['r'].wavelen, rtol=1.0e-3, atol=1.0e-8)
    assert_allclose(bp.sb, tot['r'].sb, rtol=1.0e-1, atol=1.0e-8)
