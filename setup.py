#!/usr/bin/env python
import sys

from setuptools import setup, find_packages

import youtube2srt


requires = []


if sys.version_info[:2] == (2, 6):
    # For python2.6 we have to require argparse since it
    # was not in stdlib until 2.7.
    requires.append('argparse>=1.1')


setup_options = dict(
    name='youtube2srt',
    version=youtube2srt.__version__,
    description='Command-line utility to download closed captions from YouTube as a SRT file.',
    long_description=open('README.rst').read(),
    author='Ozan Sener, Paulo Miguel Almeida',
    author_email='ozan@ozansener.com, paulo.miguel.almeida.rodenas@gmail.com',
    url='https://github.com/PauloMigAlmeida/youtube2srt/',
    scripts=['bin/youtube2srt', 'bin/youtube2srt.cmd'],
    packages=find_packages(exclude=['tests*']),
    install_requires=requires,
    extras_require={
        ':python_version=="2.6"': [
            'argparse>=1.1',
        ]
    },
    license="",
    classifiers=(
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
    ),
)

if 'py2exe' in sys.argv:
    # This will actually give us a py2exe command.
    import py2exe
    # And we have some py2exe specific options.
    setup_options['options'] = {
        'py2exe': {
            'optimize': 0,
            'skip_archive': True,
            'dll_excludes': ['crypt32.dll'],
            'packages': ['youtube2srt'],
        }
    }
    setup_options['console'] = ['bin/youtube2srt']


setup(**setup_options)
