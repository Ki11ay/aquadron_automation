#include <Servo.h>

Servo left;  // left
Servo right;  // right
void rampThrust(Servo &escPrimary, Servo &escSecondary, int primaryMax, int secondaryMax);

const int leftPin = 9;  // PWM pin for left thruster
const int rightPin = 10; // PWM pin for right thruster
const long rampTime = 5000;  // Time to go from zero to full power in milliseconds (15 seconds)
const int minspeed = 1000;  // Minimum pulse width (adjust if necessary)
const int maxspeed = 2000;
int control = -1;

void setup() {
  left.attach(leftPin);  
  right.attach(rightPin);  
  Serial.begin(9600);
  // Initialize ESCs
  left.writeMicroseconds(1000);  
  right.writeMicroseconds(1000);  
  delay(2000);  
}
void loop() {
    if (Serial.available() > 0){
     control = Serial.readString().toInt();
    }else {
      rampThrust(left, right, maxspeed/2, minspeed);
    }
    switch(control){
      case 1:  // Left motor full speed
        rampThrust(left, right, maxspeed, minspeed);
        control = -1;  // Reset command
        break;
      case 0:  // Right motor full speed
        rampThrust(right, left, maxspeed, minspeed);
        control = -1;  // Reset command
        break;  
      case 2:  // Both motors full speed
        rampThrust(left, right, maxspeed, maxspeed);
        control = -1;  // Reset command
        break;
      case 3:
        left.writeMicroseconds(minspeed);
        right.writeMicroseconds(minspeed);
        control = -1;  // Reset command
        break;
      default:
        // Do nothing, waiting for new command
        break;
    }
  delay(50);  
}
void rampThrust(Servo &escPrimary, Servo &escSecondary, int primaryMax, int secondaryMax) {
  for (long t = 0; t < rampTime; t += 100) {
    int primaryPulse = map(t, 0, rampTime, minspeed, primaryMax);
    int secondaryPulse = map(t, 0, rampTime, minspeed, secondaryMax);
    escPrimary.writeMicroseconds(primaryPulse);
    escSecondary.writeMicroseconds(secondaryPulse);
    delay(100);
  }
}