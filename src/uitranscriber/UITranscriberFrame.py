
from typing import cast

from logging import Logger
from logging import getLogger

from wx import FD_CHANGE_DIR
from wx import FD_OVERWRITE_PROMPT
from wx import FD_SAVE
from wx import FileSelector
from wx import ID_ANY
from wx import EVT_BUTTON
from wx import EVT_CLOSE
from wx import BORDER_THEME
from wx import TE_MULTILINE
from wx import DEFAULT_FRAME_STYLE
from wx import FRAME_FLOAT_ON_PARENT
from wx import STB_DEFAULT_STYLE

from wx import Size
from wx import Point
from wx import BitmapButton
from wx import TextCtrl
from wx import CommandEvent

from wx import CallAfter as wxCallAfter

from wx.lib.sized_controls import SizedFrame
from wx.lib.sized_controls import SizedPanel

from uitranscriber.InputMonitor import InputMonitor
from uitranscriber.resources.stop import embeddedImage as stopImage
from uitranscriber.resources.save import embeddedImage as saveImage
from uitranscriber.resources.record import embeddedImage as recordImage
from uitranscriber.resources.clear import embeddedImage as clearImage


class UITranscriberFrame(SizedFrame):
    """
    Contains the simplified UI and all the UI handlers;
    """
    def __init__(self):
        """
        Start the Input Monitor here
        """
        self.logger: Logger = getLogger(__name__)

        super().__init__(parent=None, title='UI Transcriber', size=Size(width=450, height=500), style=self._getFrameStyle())

        self.SetPosition(pt=Point(x=20, y=40))
        sizedPanel: SizedPanel = self.GetContentsPane()
        sizedPanel.SetSizerProps(expand=True, proportion=1)
        sizedPanel.SetSizerType('vertical')

        self.CreateStatusBar(style=STB_DEFAULT_STYLE)  # should always do this when there's a resize border

        self._recordButton: BitmapButton = cast(BitmapButton, None)
        self._stopButton:   BitmapButton = cast(BitmapButton, None)
        self._saveButton:   BitmapButton = cast(BitmapButton, None)
        self._clearButton:  BitmapButton = cast(BitmapButton, None)

        self._recordText: TextCtrl = self._layoutRecordTextControl(sizedPanel)
        self._layoutRecorderButtons(sizedPanel)

        self._inputMonitor: InputMonitor = InputMonitor(reportCB=self._listenReporting)
        self._inputMonitor.recording = False
        self._setButtonState()

        self.SetAutoLayout(True)
        self.Show(True)
        self.Bind(EVT_BUTTON, self._onRecord, self._recordButton)
        self.Bind(EVT_BUTTON, self._onStop,   self._stopButton)
        self.Bind(EVT_BUTTON, self._onSave,   self._saveButton)
        self.Bind(EVT_BUTTON, self._onClear,  self._clearButton)

        self.Bind(EVT_CLOSE, self.Close)

    def Close(self, force: bool = False) -> bool:
        """
        Closing handler overload. Save files and ask for confirmation.
        """
        self.Destroy()
        return True

    # noinspection PyUnusedLocal
    def _onRecord(self, event: CommandEvent):
        """
        Do not really start;  Just tell the listeners to record
        Args:
            event:
        """
        self._inputMonitor.recording = True
        self.logger.warning(f'Start recording')
        self._setButtonState()

    # noinspection PyUnusedLocal
    def _onStop(self, event: CommandEvent):
        """
        Do not really stop;  Just tell the listeners to not record
        Args:
            event:
        """
        self._inputMonitor.recording = False
        self._setButtonState()

    # noinspection PyUnusedLocal
    def _onSave(self, event: CommandEvent):
        wildCard: str = f'Executable Script (*.py) |*.py'

        fileName: str = FileSelector("Choose output script name",
                                     default_filename='transcribed.py',
                                     wildcard=wildCard,
                                     flags=FD_SAVE | FD_OVERWRITE_PROMPT | FD_CHANGE_DIR
                                     )

        self._recordText.SaveFile(fileName)

    # noinspection PyUnusedLocal
    def _onClear(self, event: CommandEvent):
        self._recordText.Clear()
        self._inputMonitor.loadPreamble()

    def _getFrameStyle(self) -> int:
        """
        wxPython 4.2.4 update:  using FRAME_TOOL_WINDOW causes the title to be above the toolbar
        in production mode use FRAME_TOOL_WINDOW

        Note:  Getting the environment variable from the plist dictionary (LSEnvironment) only works
        by double-clicking on the built application;  We simulate that with a PyCharm custom Run/Debug
        configuration

        Returns:  An appropriate frame style
        """
        # appModeStr: Optional[str] = osGetEnv(DiagrammerTypes.APP_MODE)

        # if appModeStr is None:
        #     appMode: bool = False
        # else:
        #     appMode = SecureConversions.secureBoolean(appModeStr)
        frameStyle: int  = DEFAULT_FRAME_STYLE | FRAME_FLOAT_ON_PARENT
        # if appMode is True:
        #     frameStyle = frameStyle | FRAME_TOOL_WINDOW

        return frameStyle

    def _layoutRecordTextControl(self, sizedPanel: SizedPanel):

        textControl: TextCtrl = TextCtrl(sizedPanel, ID_ANY, size=Size(-1, -1), style=TE_MULTILINE)
        textControl.SetSizerProps(expand=True, proportion=5)

        #
        # The code I generate does not work with smart quotes
        #
        textControl.OSXDisableAllSmartSubstitutions()
        textControl.SetEditable(False)
        return textControl

    def _layoutRecorderButtons(self, sizedPanel: SizedPanel):
        buttonPanel: SizedPanel = SizedPanel(sizedPanel, style=BORDER_THEME)
        buttonPanel.SetSizerType('horizontal')
        buttonPanel.SetSizerProps(expand=False, proportion=1, halign='right')       # expand False allows aligning right

        self._recordButton = BitmapButton(parent=buttonPanel, id=ID_ANY, bitmap=recordImage.GetBitmap())
        self._stopButton   = BitmapButton(parent=buttonPanel, id=ID_ANY, bitmap=stopImage.GetBitmap())
        self._saveButton   = BitmapButton(parent=buttonPanel, id=ID_ANY, bitmap=saveImage.GetBitmap())
        self._clearButton  = BitmapButton(parent=buttonPanel, id=ID_ANY, bitmap=clearImage.GetBitmap())

    def _listenReporting(self, cmd: str):
        wxCallAfter(self._recordCommand, cmd)

    def _recordCommand(self, recordedCommand: str):

        self._lastInsertionPosition = self._recordText.GetLastPosition()

        self.logger.debug(f'{self._lastInsertionPosition=}')
        self._recordText.AppendText(recordedCommand)

    def _setButtonState(self):
        """
        if recording we can only `Stop` the recording
        if not recording we can `Save` the script o `Start` the recording
        """

        if self._inputMonitor.recording is True:

            self._recordButton.Enable(enable=False)
            self._stopButton.Enable(enable=True)
            self._saveButton.Enable(enable=False)
            self._clearButton.Enable(enable=False)
        else:
            self._recordButton.Enable(enable=True)
            self._stopButton.Enable(enable=False)
            self._saveButton.Enable(enable=True)
            self._clearButton.Enable(enable=True)
