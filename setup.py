import os
from setuptools import setup, find_packages

import librarian_core


def read(fname):
    """ Return content of specified file """
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


VERSION = librarian_core.__version__

setup(
    name='librarian-core',
    version=VERSION,
    license='BSD',
    packages=find_packages(),
    long_description=read('README.rst'),
    install_requires=[
        'bottle',
        'bottle-utils-common',
        'bottle-utils-ajax',
        'bottle-utils-csrf',
        'bottle-utils-form',
        'bottle-utils-html',
        'bottle-utils-i18n',
        'bottle-utils-lazy',
        'webassets',
        'Mako',
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Topic :: Applicaton',
        'Framework :: Bottle',
        'Environment :: Web Environment',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],
)
