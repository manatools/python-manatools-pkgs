#!/usr/bin/env python3

from setuptools import setup
exec(open('manatools/pkgs/version.py').read())

setup(
  name=__project_name__,
  version=__project_version__,
  author='Angelo Naselli',
  author_email='anaselli@linux.it',
  packages=['manatools', 'test'],
  #scripts=['scripts/'],
  license='LICENSE',
  description='Python ManaTools pkgs',
  long_description=open('README.md').read(),
  #data_files=[('conf/manatools', ['XXX.yy',]), ],
  zip_safe=False,
  install_requires=[
    #"argparse",
    "distribute",
  ],
)
