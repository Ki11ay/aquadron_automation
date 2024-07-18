import cv2
import numpy as np
import time

# Define the color range for object detection (HSV)
color_ranges = [
    {'name': 'red', 'lower': np.array([0, 120, 70]), 'upper': np.array([10, 255, 255])},
    {'name': 'red', 'lower': np.array([170, 120, 70]), 'upper': np.array([180, 255, 255])},
    {'name': 'green', 'lower': np.array([36, 25, 25]), 'upper': np.array([70, 255, 255])},
    {'name': 'blue', 'lower': np.array([94, 80, 2]), 'upper': np.array([126, 255, 255])},
    {'name': 'yellow', 'lower': np.array([22, 93, 0]), 'upper': np.array([45, 255, 255])},
    {'name': 'orange', 'lower': np.array([10, 100, 20]), 'upper': np.array([25, 255, 255])},
    {'name': 'purple', 'lower': np.array([129, 50, 70]), 'upper': np.array([158, 255, 255])}
]

# Open a video capture
cap = cv2.VideoCapture(0)  # Change to 0 to use webcam

# Function to calculate the distance from the middle line
def distance_from_middle(x, frame_width):
    middle = frame_width // 2
    return x - middle

# Minimum area to consider an object
min_area = 1000

# Variable to keep track of the last time the position was printed
last_print_time = time.time()

# Variables to store the current largest object
current_largest_contour = None
current_largest_color_name = ""

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame_height, frame_width = frame.shape[:2]

    # Convert the frame to HSV color space
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    largest_contour = None
    largest_area = 0
    largest_color_name = ""

    if current_largest_contour is None:
        # Find the largest object if we are not tracking any object
        for color in color_ranges:
            # Create a mask for the specified color
            mask = cv2.inRange(hsv, color['lower'], color['upper'])
            
            # Special case for red: merge the two red masks
            if color['name'] == 'red':
                lower_red_mask = cv2.inRange(hsv, color_ranges[0]['lower'], color_ranges[0]['upper'])
                upper_red_mask = cv2.inRange(hsv, color_ranges[1]['lower'], color_ranges[1]['upper'])
                mask = cv2.bitwise_or(lower_red_mask, upper_red_mask)

            # Find contours in the mask
            contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area >= min_area and area > largest_area:
                    largest_area = area
                    largest_contour = cnt
                    largest_color_name = color['name']

        if largest_contour is not None:
            current_largest_contour = largest_contour
            current_largest_color_name = largest_color_name
    else:
        # Track the current largest object
        mask = cv2.inRange(hsv, color_ranges[[color['name'] for color in color_ranges].index(current_largest_color_name)]['lower'],
                                 color_ranges[[color['name'] for color in color_ranges].index(current_largest_color_name)]['upper'])
        
        # Special case for red: merge the two red masks
        if current_largest_color_name == 'red':
            lower_red_mask = cv2.inRange(hsv, color_ranges[0]['lower'], color_ranges[0]['upper'])
            upper_red_mask = cv2.inRange(hsv, color_ranges[1]['lower'], color_ranges[1]['upper'])
            mask = cv2.bitwise_or(lower_red_mask, upper_red_mask)

        contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        found = False
        for cnt in contours:
            if cv2.contourArea(cnt) >= min_area:
                current_largest_contour = cnt
                found = True
                break

        if not found:
            current_largest_contour = None

    if current_largest_contour is not None:
        # Calculate the centroid of the largest contour
        M = cv2.moments(current_largest_contour)
        if M['m00'] != 0:
            cx = int(M['m10'] / M['m00'])
            cy = int(M['m01'] / M['m00'])

            # Calculate distance from the middle
            distance = distance_from_middle(cx, frame_width)

            # Determine the position
            if distance > 80:
                position = "right"
            elif distance < -80:
                position = "left"
            else:
                position = "forward"

            # Print the position to the terminal every second
            current_time = time.time()
            if current_time - last_print_time >= 1:
                print(position)
                last_print_time = current_time

            # Draw the contour and centroid on the frame
            cv2.drawContours(frame, [current_largest_contour], -1, (0, 255, 0), 2)
            cv2.circle(frame, (cx, cy), 5, (255, 0, 0), -1)
            cv2.putText(frame, current_largest_color_name, (cx - 20, cy - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    # Draw the middle line
    cv2.line(frame, (frame_width // 2, 0), (frame_width // 2, frame_height), (0, 255, 255), 2)

    # Display the frame
    cv2.imshow('Frame', frame)

    # Break the loop if 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the video capture and close all OpenCV windows
cap.release()
cv2.destroyAllWindows()
