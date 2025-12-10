
from typing import Dict
from typing import List
from typing import cast

from logging import Logger
from logging import getLogger

from os import linesep as osLineSep

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
from wx.lib.sized_controls import SizedStaticBox

from pynput.mouse import Button
from pynput.mouse import Listener as MouseListener

from pynput.keyboard import Key
from pynput.keyboard import KeyCode
from pynput.keyboard import Listener as KeyboardListener

from uitranscriber.resources.stop import embeddedImage as stopImage
from uitranscriber.resources.save import embeddedImage as saveImage
from uitranscriber.resources.record import embeddedImage as recordImage

CLICK: str = 'click'
WRITE: str = 'write'
PRESS: str = 'press'

PRESSES_ARGUMENT: str = 'presses'

SCRIPT_PREAMBLE: List[str] = [
    f'#!/usr/bin/env python{osLineSep}',
    f'# /// script{osLineSep}'
    f'# dependencies = ["pyautogui"]{osLineSep}'
    f'# ///{osLineSep}'
    f'{osLineSep}'
    f'import pyautogui{osLineSep}'
    f'from pyautogui import press{osLineSep}',
    f'from pyautogui import click{osLineSep}',
    f'{osLineSep}'
    f'{osLineSep}'
    f'pyautogui.PAUSE = 0.5{osLineSep}'
    f'{osLineSep}'
]

#
# Maps pynput keys to PyAutoGUI keys
# noinspection PyTypeChecker
# noinspection SpellCheckingInspection
SPECIAL_KEY_MAP: Dict[KeyCode, str] = {
    Key.backspace: 'backspace',
    Key.delete:    'delete',
    Key.down:   'down',
    Key.end:    'end',
    Key.enter:  'enter',
    Key.esc: '   esc',
    Key.f1:  'f1',  Key.f2:  'f2',  Key.f3:  'f3',  Key.f4:  'f4',  Key.f5:  'f5',
    Key.f6:  'f6',  Key.f7:  'f7',  Key.f8:  'f8',  Key.f9:  'f9',  Key.f10: 'f10',
    Key.f11: 'f11', Key.f12: 'f12', Key.f13: 'f13', Key.f14: 'f14', Key.f15: 'f15',

    Key.home: 'home', Key.left: 'left',
    Key.page_down: 'pagedown', Key.page_up: 'pageup',
    Key.right: 'right',
    Key.space: 'space',
    Key.tab:   'tab',
    Key.up:    'up',
}
class UITranscriberFrame(SizedFrame):
    """
    Contains the simplified UI and all the UI handlers;  Also, contains
    the pynput listeners
    """

    def __init__(self):
        """
        Start the pynput listeners here
        """
        self.logger: Logger = getLogger(__name__)

        super().__init__(parent=None, title='UI Transcriber', size=Size(width=450, height=300), style=self._getFrameStyle())

        self.SetPosition(pt=Point(x=20, y=40))
        sizedPanel: SizedPanel = self.GetContentsPane()
        sizedPanel.SetSizerProps(expand=True, proportion=1)
        sizedPanel.SetSizerType('vertical')

        self.CreateStatusBar(style=STB_DEFAULT_STYLE)  # should always do this when there's a resize border

        self._recordButton: BitmapButton = cast(BitmapButton, None)
        self._stopButton:   BitmapButton = cast(BitmapButton, None)
        self._saveButton:   BitmapButton = cast(BitmapButton, None)

        self._recordText: TextCtrl = self._layoutRecordTextControl(sizedPanel)
        self._layoutRecorderButtons(sizedPanel)

        self._mouseListener:    MouseListener    = MouseListener(on_click=self._onClickListener)
        self._keyboardListener: KeyboardListener = KeyboardListener(on_press=self._onKeyPressListener)

        self._mouseListener.start()
        self._keyboardListener.start()

        self._recording:      bool = False

        self._keyCodeMode:        bool = False
        self._repeatKeyCodeCount: int = 0
        self._repeatedKeyCode:    str = ''
        """
        We really never stop the listeners.  We just stop handling anything
        when the recording flag is False
        """
        self._keyboardBuffer: str  = ''
        """
        The single character presses are buffered to generate a single PyAutoGUI press command
        """
        self._lastInsertionPosition: int = 0
        self._loadPreamble()

        self.SetAutoLayout(True)
        self.Show(True)
        self.Bind(EVT_BUTTON, self._onRecord, self._recordButton)
        self.Bind(EVT_BUTTON, self._onStop,   self._stopButton)
        self.Bind(EVT_BUTTON, self._onSave,    self._saveButton)

        self.Bind(EVT_CLOSE, self.Close)

    def Close(self, force: bool = False) -> bool:
        """
        Closing handler overload. Save files and ask for confirmation.
        """
        self.Destroy()
        return True

    # noinspection PyUnusedLocal
    def _onRecord(self, event: CommandEvent):

        self._recording = True
        self.logger.warning(f'Start recording')

    # noinspection PyUnusedLocal
    def _onStop(self, event: CommandEvent):
        """
        Do not really stop;  Just tell the listeners to not record
        Args:
            event:
        """
        self._recording = False

    # noinspection PyUnusedLocal
    def _onSave(self, event: CommandEvent):
        wildCard: str = f'Executable Script (*.py) |*.py'

        fileName: str = FileSelector("Choose output script name",
                                     default_filename='transcribed.py',
                                     wildcard=wildCard,
                                     flags=FD_SAVE | FD_OVERWRITE_PROMPT | FD_CHANGE_DIR
                                     )

        self._recordText.SaveFile(fileName)

    def _onClickListener(self, floatX: float, floatY: float, button: Button, pressed: bool):
        """
        Check the keyboard buffer.  If it is non-empty generate the press command

        Calls to this method come from a thread running outside the UI event loop.  Use the
        wxPython CallAfter method to ensure updates to the UI occur within the UI event loop

        Args:
            floatX:
            floatY:
            button:
            pressed:
        """
        if self._recording is True:
            if len(self._keyboardBuffer) > 0:
                writeCmd: str = f"{WRITE}('{self._keyboardBuffer}')"
                wxCallAfter(self._recordCommand, f'{writeCmd}{osLineSep}')
                self._keyboardBuffer = ''
            if self._keyCodeMode is True:
                self._unBufferKeyCode()

            x: int = round(floatX)
            y: int = round(floatY)
            if pressed is True:
                if button.name == "left":
                    clickCmd: str = f"{CLICK}(x={x}, y={y})"
                else:
                    clickCmd = f'{CLICK}(x={x}, y={y}, button="right")'

                self.logger.debug(clickCmd)
                wxCallAfter(self._recordText.AppendText, f'{clickCmd}{osLineSep}')

    def _onKeyPressListener(self, pressedKey: KeyCode):
        """
        We will buffer normal characters so as not to generate a bunch of single character
        press commands

        Will count repeated key code so as not to generate spurious 'press' commands

        Whenever, the click listener activates it checks the keyboard buffer.  If non-empty,
        it generates the press command

        Calls to this method come from a thread running outside the UI event loop.  Use the
        wxPython CallAfter method to ensure updates to the UI occur within the UI event loop

        Args:
            pressedKey:
        """
        if self._recording is True:

            if isinstance(pressedKey, KeyCode):

                keyCode: KeyCode = cast(KeyCode, pressedKey)
                keyStr:  str     = f'{keyCode.char}'
                self._keyboardBuffer = f'{self._keyboardBuffer}{keyStr}'
                self.logger.debug(f'keyboard buffer: {self._keyboardBuffer}')
            else:
                try:
                    self._handleKeyCode(pressedKey=pressedKey)
                except KeyError as ke:
                    self.logger.warning(f'unhandled KeyCode: {ke=}')

                    keyStr   = 'unhandled'
                    pressCmd = f"{WRITE}('{keyStr}')"
                    self.logger.debug(f'{pressCmd}')
                    wxCallAfter(self._recordCommand, f'{pressCmd}{osLineSep}')

    def _loadPreamble(self):

        for line in SCRIPT_PREAMBLE:
            self._recordText.AppendText(line)

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
        textControl.SetSizerProps(expand=True, proportion=2)

        #
        # The code I generate does not work with smart quotes
        #
        textControl.OSXDisableAllSmartSubstitutions()
        textControl.SetEditable(False)
        return textControl

    def _layoutRecorderButtons(self, sizedPanel: SizedPanel):
        buttonPanel: SizedStaticBox = SizedStaticBox(sizedPanel, label='', style=BORDER_THEME)
        buttonPanel.SetSizerProps(expand=True, proportion=1)
        buttonPanel.SetSizerType('horizontal')

        self._recordButton = BitmapButton(parent=buttonPanel, id=ID_ANY, bitmap=recordImage.GetBitmap())
        self._stopButton   = BitmapButton(parent=buttonPanel, id=ID_ANY, bitmap=stopImage.GetBitmap())
        self._saveButton   = BitmapButton(parent=buttonPanel, id=ID_ANY, bitmap=saveImage.GetBitmap())

    def _unBufferKeyCode(self):
        pressCmd: str = f"{PRESS}('{self._repeatedKeyCode}', {PRESSES_ARGUMENT}={self._repeatKeyCodeCount})"
        self._resetKeyCodeMode()
        wxCallAfter(self._recordText.AppendText, f'{pressCmd}{osLineSep}')

    def _handleKeyCode(self, pressedKey: KeyCode):

        self.logger.debug(f'{pressedKey=}')

        keyStr: str = SPECIAL_KEY_MAP[pressedKey]
        self.logger.info(f'Special Key {keyStr}')

        if pressedKey == Key.backspace:
            self._keyCodeMode = True
            self._repeatedKeyCode = keyStr
            self._repeatKeyCodeCount += 1

    def _resetKeyCodeMode(self):

        self._repeatKeyCodeCount = 0
        self._repeatedKeyCode    = ''
        self._keyCodeMode        = False

    def _recordCommand(self, recordedCommand: str):

        self._lastInsertionPosition = self._recordText.GetLastPosition()

        self.logger.debug(f'{self._lastInsertionPosition=}')
        self._recordText.AppendText(recordedCommand)
