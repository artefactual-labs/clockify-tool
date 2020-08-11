import os
from setuptools import setup

# Get requirements
with open('requirements.txt') as f:
    requirements = f.read().splitlines()

# Get text of the README file
with open('README.md') as f:
    README = f.read()


setup(
  name='clockifytool',
  packages=['clockifytool'],
  version='0.0.3',
  license='MIT',
  description='Tool to list, create, and delete time entries in Clockify',
  author='Mike Cantelon',
  author_email='mcantelon@gmail.com',

  long_description=README,
  long_description_content_type='text/markdown',

  url='https://github.com/artefactual-labs/clockify-tool',

  keywords=['clockify'],

  install_requires=requirements,

  scripts=['bin/cft'],
)
