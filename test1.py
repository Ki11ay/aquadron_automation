import cv2
from picamera import PiCamera
from time import sleep

camera = PiCamera()

# Start preview
camera.start_preview()
sleep(5)  # Preview for 5 seconds

# Capture an image
camera.capture('/home/pi/image.jpg')

# Stop preview
camera.stop_preview()

# Load the captured image using OpenCV
img = cv2.imread('/home/pi/image.jpg')

# Display the image in a window
cv2.imshow('Camera Output', img)

# Wait for a key press to close the window
cv2.waitKey(0)
cv2.destroyAllWindows()
