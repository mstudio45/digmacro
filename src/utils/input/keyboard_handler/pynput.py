import pynput

_pynput_keyboard_controller = pynput.keyboard.Controller()

# press/release #
def press(key):   _pynput_keyboard_controller.press(key)
def release(key): _pynput_keyboard_controller.release(key)