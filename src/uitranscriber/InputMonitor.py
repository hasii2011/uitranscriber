
from typing import Dict
from typing import List
from typing import cast
from typing import Callable

from logging import Logger
from logging import getLogger

from os import linesep as osLineSep

from pynput.mouse import Button
from pynput.mouse import Listener as MouseListener

from pynput.keyboard import Key
from pynput.keyboard import KeyCode
from pynput.keyboard import Listener as KeyboardListener


CLICK: str = 'click'
WRITE: str = 'write'
PRESS: str = 'press'

PRESSES_ARGUMENT: str = 'presses'

"""
From the command line and if you have `uv` installed  
you can execute this script as follow:

uv run transcribed.py
"""

SCRIPT_PREAMBLE: List[str] = [
    f'#!/usr/bin/env python{osLineSep}',
    f'# /// script{osLineSep}'
    f'# dependencies = ["pyautogui"]{osLineSep}'
    f'# ///{osLineSep}'
    f'"""{osLineSep}'
    f'From the command line and if you have `uv` installed{osLineSep}'
    f'you can execute this script as follow:{osLineSep}'
    f'{osLineSep}'
    f'uv run transcribed.py{osLineSep}'
    f'"""{osLineSep}'
    f'{osLineSep}'
    f'import pyautogui{osLineSep}'
    f'from pyautogui import write{osLineSep}'
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

ReportCallback = Callable[[str], None]

class InputMonitor:
    """
    Isolate the monitor code
    """
    def __init__(self, reportCB: ReportCallback):

        self.logger: Logger = getLogger(__name__)

        self._reportCB: ReportCallback = reportCB

        self._mouseListener:    MouseListener    = MouseListener(on_click=self._onClickListener)
        self._keyboardListener: KeyboardListener = KeyboardListener(on_press=self._onKeyPressListener)

        self._mouseListener.start()
        self._keyboardListener.start()

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
        self._recording:             bool = False
        self._lastInsertionPosition: int  = 0
        self._loadPreamble()

    @property
    def recording(self) -> bool:
        return self._recording

    @recording.setter
    def recording(self, recording: bool):
        self._recording = recording

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
                self._reportCB(f'{writeCmd}{osLineSep}')
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
                self._reportCB(f'{clickCmd}{osLineSep}')

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
                    self._reportCB(f'{pressCmd}{osLineSep}')

    def _loadPreamble(self):

        for line in SCRIPT_PREAMBLE:
            self._reportCB(line)

    def _unBufferKeyCode(self):
        pressCmd: str = f"{PRESS}('{self._repeatedKeyCode}', {PRESSES_ARGUMENT}={self._repeatKeyCodeCount})"
        self._resetKeyCodeMode()
        self._reportCB(f'{pressCmd}{osLineSep}')

    def _resetKeyCodeMode(self):

        self._repeatKeyCodeCount = 0
        self._repeatedKeyCode    = ''
        self._keyCodeMode        = False

    def _handleKeyCode(self, pressedKey: KeyCode):

        self.logger.debug(f'{pressedKey=}')

        keyStr: str = SPECIAL_KEY_MAP[pressedKey]
        self.logger.info(f'Special Key {keyStr}')

        if pressedKey == Key.backspace:
            self._keyCodeMode = True
            self._repeatedKeyCode = keyStr
            self._repeatKeyCodeCount += 1
