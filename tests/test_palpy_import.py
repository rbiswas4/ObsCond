from obscond import pal
import numpy as np

def test_airmass_values():
    pa = pal.airmas(1.2354)
    np.testing.assert_allclose(pa, 3.015698990074724, 11)

