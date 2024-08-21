import os
import sys
import cv2
import socket
import pickle
import struct
import threading
from evdev import InputDevice, categorize, ecodes, list_devices
from roboflow import Roboflow
import serial
import time
from picamera2 import Picamera2, Preview
import numpy as np

# Initialize Roboflow with your API key
rf = Roboflow(api_key="DcssodkWPHO4rCwi4q97")
project = rf.workspace().project("trash-3hler")
model = project.version(1).model

# Initialize Arduino serial connection
arduino = serial.Serial('/dev/ttyUSB0', 9600)

camera_enabled = False
frame_width, frame_height = 640, 480

# Lock to synchronize camera mode toggling
toggle_lock = threading.Lock()

# Find the PS5 controller device
def find_ps5_controller():
    while True:
        devices = [InputDevice(path) for path in list_devices()]
        for device in devices:
            if 'Wireless Controller' in device.name:
                print(f"Found controller: {device.name}")
                return device
        print("PS5 Wireless Controller not found. Retrying in 2 seconds...")
        time.sleep(2)

ps5_controller = find_ps5_controller()

# Setup the server socket to stream video
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(('0.0.0.0', 8080))  # Replace '0.0.0.0' with your Raspberry Pi's IP address if necessary
server_socket.listen(5)
print('Server listening on port 8080...')

client_socket, addr = server_socket.accept()
print(f'Connection from: {addr}')

# Function to process a frame and return a direction
def process_frame_and_get_direction(frame):
    frame_resized = cv2.resize(frame, (frame_width, frame_height))
    response = model.predict(frame_resized, confidence=40, overlap=30).json()

    largest_object = None
    largest_area = 0

    if 'predictions' in response and len(response['predictions']) > 0:
        for pred in response['predictions']:
            x_center = int(pred['x'])
            width = int(pred['width'])
            height = int(pred['height'])
            area = width * height
            if area > largest_area:
                largest_area = area
                largest_object = (x_center, width, height)

    direction = "No Object"
    center_x = frame_width // 2

    if largest_object:
        x_center, width, height = largest_object
        if x_center < center_x - 50:
            direction = "Left"
        elif x_center > center_x + 50:
            direction = "Right"
        else:
            direction = "Forward"

    return direction

# Function to process frames in camera mode
def camera_control_loop():
    global camera_enabled
    picam2 = Picamera2()  # Initialize Picamera2
    picam2.configure(picam2.create_still_configuration())  # Configure for still images
    picam2.start()  # Start the camera

    while camera_enabled:
        # Capture a frame as a NumPy array
        frame = picam2.capture_array()
        if frame is None:
            print("Error reading frame.")
            break

        with toggle_lock:
            if not camera_enabled:
                break  # Stop the loop if camera mode is disabled

        direction = process_frame_and_get_direction(frame)
        if direction == "Left":
            arduino.write(b'0')  # Turn left
            print('left motor full speed , turning right')
        elif direction == "Right":
            arduino.write(b'1')  # Turn right
            print('right motor full speed,Turning left')
        elif direction == "Forward":
            arduino.write(b'2')  # Move forward
            print('Moving Forward')

        print(f"Direction of object is: {direction}")

        # Serialize frame
        data = pickle.dumps(frame)
        message_size = struct.pack("Q", len(data))

        # Send message size and frame data
        client_socket.sendall(message_size + data)

        time.sleep(0.1)  # Add a delay for stable processing

    picam2.stop()  # Stop the camera

# Function to toggle camera mode on/off
def toggle_camera_mode():
    global camera_enabled
    with toggle_lock:
        if camera_enabled:
            print("Disabling camera mode...")
            camera_enabled = False
        else:
            print("Enabling camera mode...")
            camera_enabled = True
            threading.Thread(target=camera_control_loop).start()

# Main loop for handling controller inputs
def controller_loop():
    global camera_enabled

    for event in ps5_controller.read_loop():
        if event.type == ecodes.EV_KEY:
            # Toggle between controller and camera mode
            if event.code == ecodes.BTN_START and event.value == 1:  # Square button to toggle mode
                toggle_camera_mode()
            if event.code == ecodes.BTN_SELECT and event.value == 1:  # share button to shutdown RPI mode
                sys.exit(0)
                os.system('sudo shutdown -h now')

            # Handle manual control via the controller if camera mode is not active
            with toggle_lock:
                if not camera_enabled:
                    if event.code == ecodes.BTN_SOUTH and event.value == 1:  # X button to stop motors
                        arduino.write(b'3')
                        print('Motors Off')
                    elif event.code == ecodes.BTN_WEST and event.value == 1:  # Left button
                        arduino.write(b'0')
                        print('Left Motor Full Speed , turning right')
                    elif event.code == ecodes.BTN_EAST and event.value == 1:  # Right button
                        arduino.write(b'1')
                        print('Right Motor Full Speed, turning left')
                    elif event.code == ecodes.BTN_NORTH and event.value == 1:  # Forward button
                        arduino.write(b'2')
                        print('Both Motors Full Speed')

# Function to run the controller loop in a separate thread
def start_controller_loop():
    controller_thread = threading.Thread(target=controller_loop)
    controller_thread.daemon = True
    controller_thread.start()

try:
    start_controller_loop()  # Start controller input loop in a separate thread
    while True:
        # Keep the main thread alive to handle controller and camera operations
        time.sleep(1)

except KeyboardInterrupt:
    print("Program interrupted by the user.")
finally:
    arduino.close()
    client_socket.close()
    server_socket.close()
    print("Resources released.")