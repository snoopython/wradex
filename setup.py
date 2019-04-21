from setuptools import setup

setup(name = 'wradex',
      description = 'RADEX wrapper written in Python 3',
      version = '0.1',
      author = 'astropenguin',
      author_email = 'taniguchi@a.phys.nagoya-u.ac.jp',
      url = 'https://github.com/astropenguin/wradex',
      keywords = 'astronomy radex wrapper',
      packages = ['wradex'],
      package_data = {'wradex': ['data/*.yaml']},
      install_requires = ['astropy', 'numpy', 'pyyaml'])
