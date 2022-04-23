#include <Servo.h>
#include <AccelStepper.h>

// create servo object to control the hopper servo
Servo hopperservo;
// create servo object to control the barrel servo
Servo barrelservo;

//define fan motor pin
#define fanPin 3

//define the potentiometer pin for tracking the rotating base
#define potPin A0

//define pins used for controlling the A4988 stepper motor driver
#define dirPin 10
#define stepPin 11

//define motor interface type as bering controlled by a dedicated driver board
#define motorInterfaceType 1

//set up accelstepper object
AccelStepper stepper = AccelStepper(motorInterfaceType, stepPin, dirPin);

//declare variable for stepper speed
int stepperSpeed = 300;

//declare string and char variables for parsing serial data
String rx_str = "";
char rx_char[20];
char *rx_values;
int rx_int = 0;

//declare variable for starting position (set when wanting to block ball) for the hopper servo
int hopperStart = 160;
//declare variable for ending position (set when wanting to release ball) for the hopper servo
int hopperEnd = 110;

//declare variable for starting position (set when wanting to block ball) for the barrel servo
int barrelStart = 160;
//declare variable for ending position (set when wanting to release ball) for the barrel servo
int barrelEnd = 100;

void setup() {
  //set the baud rate for serial data transmission
  Serial.begin(9600);
  
  //Set motor speed to zero
  analogWrite(fanPin, 0);
  
  //attach the hopper servo object to pin 9
  hopperservo.attach(9);
  hopperservo.write(hopperStart);

  //attach the barrel servo object to pin 8
  barrelservo.attach(8);
  barrelservo.write(barrelStart);

  //set max speed and acceleration for stepper motor in base
  stepper.setMaxSpeed(10000);
  stepper.setAcceleration(3000);



  //align the base using the base pot to 390 < base position < 410
  if (analogRead(potPin) > 390){
    while (analogRead(potPin) != 400){
      stepper.setSpeed(stepperSpeed);
      stepper.runSpeed();
    }
  }
  
  delay(1000);

  if (analogRead(potPin) < 410){
    while (analogRead(potPin) != 400){
      stepper.setSpeed(-stepperSpeed);
      stepper.runSpeed();
    }
  }
  
  delay(1000);

  //set the current postion of the base as 0
  stepper.setCurrentPosition(0);
}


void loop() {

  //when serial data is availible set it equal to the rx_str variable
  while(Serial.available()){
      rx_str = Serial.readString();
  }
  
  if (rx_str != "") {
    
    //Convert string received by serial to character array
    rx_str.toCharArray(rx_char, 20);
    //split character array using , as a seperator
    rx_values = strtok (rx_char,",");

    //if str received is equal to analog then print the base pot value
    if (rx_str == "analog"){
      //Will be between 0 and 1023
      Serial.println(analogRead(potPin)); 
    }
    
    //if str received is equal to "load" then call loadBall function
    if (rx_str == "load"){
      //call function to load ball
      loadBall();
    }

    //if str received is equal to "release" then call loadBall function
    if (rx_str == "release"){
      //call functon to release ball
      releaseBall();
    }

    //if first item in rx_values array is equal to "fanspeed" use the second item to set the fan speed
    if (strcmp(rx_values ,"fanspeed") == 0){
      rx_int = atoi(strtok (NULL,","));
      fanSpeed(rx_int);
    }
    
    //if first item in rx_values array is equal to "goto" use the second item to set the base position
    if (strcmp(rx_values ,"goto") == 0){
      rx_int = atoi(strtok (NULL,","));
      goTo(rx_int);
    }

    //if first item in rx_values array is equal to "fire" use the second item to set the fan speed and the third item to set the base position, then load and release ball
    if (strcmp(rx_values ,"fire") == 0){
      rx_int = atoi(strtok (NULL,","));
      goTo(rx_int);
      delay(1000); 
      rx_int = atoi(strtok (NULL,","));
      fanSpeed(rx_int);
      delay(1000);
      loadBall();
      delay(1000);
      releaseBall();
    }
    rx_str = "";
  }
}

//function for checking if a str contains an int
boolean isValidNumber(String str){
  for(byte i=0;i<str.length();i++){
    if(isDigit(str.charAt(i))){
      return true;
    }
  }
  return false;
}

//function for loading ball
void loadBall(){
  //tell hopper servo to go to end position
  hopperservo.write(hopperEnd);
  //delay for the ball to drop
  delay(155);
  //tell hopper servo to go to starting position
  hopperservo.write(hopperStart);           
  delay(15);   
}

//function for releasing ball
void releaseBall(){
  //tell barrel servo to go to end position
  barrelservo.write(barrelEnd);
  //delay for the ball to drop
  delay(1000);
  barrelservo.write(barrelStart);
  delay(15); 
}

//function for setting fan speed
void fanSpeed(int rx_int){
  analogWrite(fanPin, rx_int);
}

//function for moving base to specific position
void goTo(int rx_int){
  stepper.moveTo(rx_int);
  stepper.runToPosition();
}
