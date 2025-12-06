#!/usr/bin/env python
# /// script
# dependencies = ['wxPython', 'pynput']
# ///
from wx import ART_CROSS_MARK
from wx import ART_FILE_SAVE
from wx import ART_PLUS
from wx import ART_TOOLBAR
from wx import App

from typing import cast

from wx import ArtProvider
from wx import Bitmap

from wx import ID_ANY
from wx import EVT_BUTTON
from wx import EVT_CLOSE
from wx import BORDER_THEME
from wx import Point
from wx import TE_MULTILINE
from wx import DEFAULT_FRAME_STYLE
from wx import FRAME_FLOAT_ON_PARENT
from wx import STB_DEFAULT_STYLE

from wx import Size
from wx import BitmapButton
from wx import TextCtrl
from wx import CommandEvent

from wx.lib.sized_controls import SizedFrame
from wx.lib.sized_controls import SizedPanel
from wx.lib.sized_controls import SizedStaticBox

from pynput.mouse import Button
from pynput.mouse import Listener as MouseListener
from pynput.keyboard import Listener as KeyboardListener

CLICK: str = 'pyautogui.click'


class TranscriberFrame(SizedFrame):

    def __init__(self):

        super().__init__(parent=None, title='UI Transcriber', size=Size(width=350, height=300), style=self._getFrameStyle())

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

        self._recording: bool = False

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
        print(f'Start recording')

    # noinspection PyUnusedLocal
    def _onStop(self, event: CommandEvent):
        """
        Do not really stop;  Just tell the listeners to not record
        Args:
            event:
        """
        print(f'Stop recording')
        self._recording = False

    def _onSave(self, event: CommandEvent):
        print(f'{event}')

    def _onClickListener(self, floatX: float, floatY: float, button: Button, pressed: bool):

        if self._recording is True:
            x: int = round(floatX)
            y: int = round(floatY)
            if pressed is True:
                if button.name == "left":
                    print("pyautogui.click(x=%d, y=%d)" % (x, y))
                else:
                    print(f"pyautogui.click(x={x}, y={y}, button='right')")
                # listbox.insert(tkinter.END, "time.sleep(%f)" % clock.elapsed(True))

    def _onKeyPressListener(self, key):
        if self._recording is True:
            try:
                print(f"pyautogui.keyDown('{key.name}')")

            except AttributeError:
                print(f'special key `{0}` pressed')

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

        return textControl

    def _layoutRecorderButtons(self, sizedPanel: SizedPanel):
        buttonPanel: SizedStaticBox = SizedStaticBox(sizedPanel, label='', style=BORDER_THEME)
        buttonPanel.SetSizerProps(expand=True, proportion=1)
        buttonPanel.SetSizerType('horizontal')

        saveImage:   Bitmap = ArtProvider.GetBitmap(ART_FILE_SAVE,  client=ART_TOOLBAR, size=Size(width=32, height=32))
        stopImage:   Bitmap = ArtProvider.GetBitmap(ART_CROSS_MARK, client=ART_TOOLBAR, size=Size(width=32, height=32))
        recordImage: Bitmap = ArtProvider.GetBitmap(ART_PLUS,       client=ART_TOOLBAR, size=Size(width=32, height=32))

        self._recordButton = BitmapButton(parent=buttonPanel, id=ID_ANY, bitmap=recordImage)    # noqa
        self._stopButton   = BitmapButton(parent=buttonPanel, id=ID_ANY, bitmap=stopImage)      # noqa
        self._saveButton   = BitmapButton(parent=buttonPanel, id=ID_ANY, bitmap=saveImage)      # noqa

        self._recordButton.SetToolTip('Start Recording')
        self._stopButton.SetToolTip('Stop Recording')
        self._saveButton.SetToolTip('Save Recording')


if __name__ == '__main__':
    pass

    app:  App                 = App(False)
    frame: TranscriberFrame = TranscriberFrame()
    frame.Show()
    app.MainLoop()
