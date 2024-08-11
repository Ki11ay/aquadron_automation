import serial
from evdev import InputDevice, categorize, ecodes

# Connect to Arduino via serial
arduino = serial.Serial('/dev/ttyUSB0', 9600)

# Open the PS5 controller device
ps5_controller = InputDevice('/dev/input/event0')

is_rpi = True

for event in ps5_controller.read_loop():
    if event.type == ecodes.EV_KEY:
        if event.code == ecodes.BTN_SOUTH and event.value == 1:  # X button
            # Send PWM signal to start thrusters at 20% power
            arduino.write(b'3')  # Assuming '3' triggers 20% power in Arduino code

        elif event.code == ecodes.BTN_WEST and event.value == 1:  # Left button
            arduino.write(b'0')

        elif event.code == ecodes.BTN_EAST and event.value == 1:  # Right button
            arduino.write(b'1')

        elif event.code == ecodes.BTN_NORTH and event.value == 1:  # Forward button
            arduino.write(b'2')

        elif event.code == ecodes.BTN_SELECT and event.value == 1:  # Options button
            is_rpi = not is_rpi
            arduino.write(b'4')  # Assuming '4' toggles isRPI in Arduino code