import serial
import time
from evdev import InputDevice, categorize, ecodes

# Connect to Arduino via serial
arduino = serial.Serial('/dev/ttyUSB0', 9600)

# Open the PS5 controller device
ps5_controller = InputDevice('/dev/input/event0')

is_rpi = True
direction_state = {'left': False, 'right': False, 'up': False}

def send_signal(signal):
    arduino.write(signal)
    time.sleep(5)

while True:
    for event in ps5_controller.read_loop():
        if event.type == ecodes.EV_KEY:
            if event.code == ecodes.BTN_DPAD_LEFT:
                direction_state['left'] = event.value == 1
            elif event.code == ecodes.BTN_DPAD_RIGHT:
                direction_state['right'] = event.value == 1
            elif event.code == ecodes.BTN_DPAD_UP:
                direction_state['up'] = event.value == 1
            elif event.code == ecodes.BTN_SELECT and event.value == 1:  # Options button
                is_rpi = not is_rpi
                arduino.write(b'4')  # Assuming '4' toggles isRPI in Arduino code

    if direction_state['left']:
        send_signal(b'0')
    elif direction_state['right']:
        send_signal(b'1')
    elif direction_state['up']:
        send_signal(b'2')

    time.sleep(0.1)  # Small delay to avoid overwhelming the CPU