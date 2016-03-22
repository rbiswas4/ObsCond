import os
__all__ = ['example_data_dir', 'DAY_IN_SEC']
dirname = os.path.dirname(os.path.abspath(__file__))
example_data_dir =  os.path.join(dirname, 'example_data')
DAY_IN_SEC = 24.0 * 60. * 60
