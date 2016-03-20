from distutils.core import setup

setup(name='ObsCond',
      version='0.0.1dev',
      description='Interpolating Observing Conditions from historic data',
      packages=['obscond'],
      package_dir={'obscond': 'obscond'},
      package_data={'obscond': ['obscond/example_data/*.txt', 'obscond/example_data/*.md']},
      include_package_data=True
     )
