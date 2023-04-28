"""A setuptools based setup module.

See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
from codecs import open
from os import path
from kiharalab import __version__, _logo

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

# Arguments marked as "Required" below must be included for upload to PyPI.
# Fields marked as "Optional" may be commented out.

setup(
    name='scipion-em-kiharalab',  # Required
    version=__version__,  # Required
    description='Scipion plugin in order to use ther kiharalab software',  # Required
    long_description=long_description,  # Optional
    url='https://github.com/scipion-em/scipion-em-kiharalab',  # Optional
    author='Daniel Del Hoyo',  # Optional
    author_email='ddelhoyo@cnb.csic.es',  # Optional
    keywords='scipion kiharalab scipion-3.0 EM',  # Optional
    packages=find_packages(),
    install_requires=[requirements],
    entry_points={'pyworkflow.plugin': 'kiharalab = kiharalab'},
    package_data={  # Optional
       'kiharalab': [_logo, 'protocols.conf'],
    }
)
