#!/usr/bin/env python

from pynput import mouse
from pynput import keyboard

from pynput.mouse import Button

CLICK: str = 'click'

def onMove(x: float, y: float):

    print(f'Pointer moved to ({round(x)},{round(y)})')

def onClick(floatX: float, floatY: float, button: Button, pressed: bool):

    x: int = round(floatX)
    y: int = round(floatY)
    if pressed is True:
        if button.name == "left":
            print("pyautogui.click(x=%d, y=%d)" % (x, y))
        else:
            print(f"pyautogui.click(x={x}, y={y}, button='right')")


# noinspection PyUnusedLocal
def onScroll(x, y, dx, dy):
    print('Scrolled {0} at {1}'.format('down' if dy < 0 else 'up', (round(x), round(y))))

def onPress(key):
    try:
        print(f'alphanumeric key `{key.char}` pressed')
    except AttributeError:
        print(f'special key `{0}` pressed')

# Collect events until released
# with mouse.Listener(
#         on_move=onMove,
#         on_click=onClick,
#         on_scroll=onScroll) as listener:
#     listener.join()

# ...or, in a non-blocking fashion:


mouseListener = mouse.Listener(on_click=onClick)

mouseListener.start()

keyboardListener = keyboard.Listener(on_press=onPress)
keyboardListener.start()

while True:
    pass
