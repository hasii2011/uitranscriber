#!/usr/bin/env python

from logging import Logger
from logging import getLogger

import logging.config

from json import load as jsonLoad

from os import sep as osSep
from typing import cast

from wx import App

from codeallybasic.ResourceManager import ResourceManager

from uitranscriber.UITranscriberFrame import UITranscriberFrame


class UITranscriber(App):
    JSON_LOGGING_CONFIG_FILENAME: str = "loggingConfiguration.json"

    # noinspection SpellCheckingInspection
    PROJECT_NAME:           str = 'uitranscriber'
    RESOURCES_PACKAGE_NAME: str = f'{PROJECT_NAME}.resources'
    RESOURCES_PATH:         str = f'{PROJECT_NAME}{osSep}resources'

    RESOURCE_ENV_VAR:       str = 'RESOURCEPATH'

    def __init__(self):
        self._setupApplicationLogging()

        self.logger: Logger = getLogger(__name__)
        self._wxFrame:         UITranscriberFrame = cast(UITranscriberFrame, None)

        super().__init__(redirect=False)    # This calls OnInit()

    def _setupApplicationLogging(self):

        configFilePath: str = ResourceManager.retrieveResourcePath(bareFileName=UITranscriber.JSON_LOGGING_CONFIG_FILENAME,
                                                                   resourcePath=UITranscriber.RESOURCES_PATH,
                                                                   packageName=UITranscriber.RESOURCES_PACKAGE_NAME)

        with open(configFilePath, 'r') as loggingConfigurationFile:
            configurationDictionary = jsonLoad(loggingConfigurationFile)

        logging.config.dictConfig(configurationDictionary)
        logging.logProcesses = False
        logging.logThreads   = False

    def OnInit(self):

        self._wxFrame = UITranscriberFrame()

        self.SetTopWindow(self._wxFrame)

        return True


if __name__ == '__main__':

    testApp: UITranscriber = UITranscriber()

    testApp.MainLoop()
