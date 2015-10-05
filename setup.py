import os
from setuptools import setup, find_packages

import librarian_core as pkg


def read(fname):
    """ Return content of specified file """
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


VERSION = pkg.__version__

setup(
    name='librarian-core',
    version=VERSION,
    license='BSD',
    packages=[pkg.__name__],
    include_package_data=True,
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
        'python-dateutil',
        'sqlize',
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
