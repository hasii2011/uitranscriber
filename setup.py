
from setuptools import setup
from setuptools import find_packages

import pathlib

from uitranscriber import __version__

# TODO:  Currently requires that PYTHONPATH point to the src directory
# Perhaps, I should move the code out of the src directory
#
#
# The directory containing this file
HERE = pathlib.Path(__file__).parent

APP = ['src/uitranscriber/UITranscriber.py']
DATA_FILES = [('uitranscriber/resources', ['src/uitranscriber/resources/loggingConfiguration.json']),
              # ('umldiagrammer/resources/img', ['pyut/resources/img/pyut.ico']),
              ]
OPTIONS = {}

# The text of the README file
README = (HERE / "README.md").read_text()
LICENSE = (HERE / 'LICENSE').read_text()

setup(
    name='uitranscriber',
    version=__version__,
    app=APP,
    data_files=DATA_FILES,
    packages=find_packages(include=['umldiagrammer.*']),
    include_package_data=True,
    zip_safe=False,

    url='https://github.com/hasii2011/umldiagrammer',
    author='Humberto A. Sanchez II',
    author_email='Humberto.A.Sanchez.II@gmail.com',
    maintainer='Humberto A. Sanchez II',
    maintainer_email='humberto.a.sanchez.ii@gmail.com',
    description='Records PyAutoGUI Scripts',
    long_description='Conveniently record UI Testing Scripts.',
    options=dict(
        py2app=dict(
            plist=dict(
                NSRequiresAquaSystemAppearance='False',
                CFBundleGetInfoString='Records PyAutoGUI Scripts',
                CFBundleIdentifier='uitranscriber',
                CFBundleShortVersionString=__version__,
                CFBundleDocumentTypes=[
                    {'CFBundleTypeName': 'uitranscriber'},
                    {'CFBundleTypeRole': 'Generator'},
                    {'CFBundleTypeExtensions':  ['py']}
                ],
                LSMinimumSystemVersion='12',
                LSEnvironment=dict(
                    APP_MODE='True',
                    PYTHONOPTIMIZE='1',
                ),
                LSMultipleInstancesProhibited='True',
            )
        ),
    )
)
