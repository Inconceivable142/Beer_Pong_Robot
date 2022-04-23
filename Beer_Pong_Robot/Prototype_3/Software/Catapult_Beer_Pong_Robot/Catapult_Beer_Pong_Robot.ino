#include <Servo.h>
#include <AccelStepper.h>

//create servo object to control the latc servo
Servo latchservo;
//create servo object to control the agitator servo
Servo agitatorservo;
//create servo object to control the load servo
Servo loadservo;

//define fan motor pin
#define fanPin 3

//define the potentiometer pin for tracking the rotating base
#define basePot A0
//define the potentiometer pin for tracking the tensioner
#define catPot A1

#define dirPin 10
#define stepPin 11
#define motorInterfaceType 1
#define centerPin 7

//define pins used for H bridge to control tension motor
#define  motorpin1 2
#define  motorpin2 4

//set up accelstepper object
AccelStepper stepper = AccelStepper(motorInterfaceType, stepPin, dirPin);

//declare variable for stepper speed
int stepperSpeed = 300;

//declare string and char variables for parsing serial data
String rx_str = "";
char rx_char[20];
char *rx_values;
int rx_int = 0;


void setup() {
  //set the baud rate for serial data transmission
  Serial.begin(9600);

  //attach the latch servo to pin 9
  latchservo.attach(9);
  //attach the agitator servo to pin 8
  agitatorservo.attach(8);
  //attach the load servo to pin 5
  loadservo.attach(5);
  
  //Set fan speed to zero
  analogWrite(fanPin, 0);

  //set tension motor to off
  digitalWrite(motorpin1, LOW);
  digitalWrite(motorpin2, LOW);

  //set up pin connected to phototransistor
  pinMode(centerPin, INPUT);

  //set stepper speed and acceleratiom for base
  stepper.setMaxSpeed(10000);
  stepper.setAcceleration(3000);

  //align the base using the base pot to 390 < base position < 410
  if (analogRead(basePot) > 390){
    while (analogRead(basePot) != 400){
      stepper.setSpeed(stepperSpeed);
      stepper.runSpeed();
    }
  }
  
  delay(1000);

  if (analogRead(basePot) < 410){
    while (analogRead(basePot) != 400){
      stepper.setSpeed(-stepperSpeed);
      stepper.runSpeed();
    }
  }
  
  delay(1000);
  
  //set the current postion of the base as 0
  stepper.setCurrentPosition(0);
}


void loop() {
  
  while(Serial.available()){
      rx_str = Serial.readString();
  }
  
  if (rx_str != "") {
    
    //Convert string received by serial to character array
    rx_str.toCharArray(rx_char, 20);
    //split character array using "," as a seperator
    rx_values = strtok (rx_char,",");
    
    //Get analog value for base pot
    if (rx_str == "basePot"){
      //Will be between 0 and 1023
      Serial.println(analogRead(basePot)); 
    }

   //Get analog value for catapult pot
    if (rx_str == "catPot"){
      //Will be between 0 and 1023
      Serial.println(analogRead(catPot)); 
    }

    //if str received is equal to "latch" then call latch function
    if (rx_str == "latch"){
      latch();
    }

    //if str received is equal to "unlatch" then call unlatch function
    if (rx_str == "ulatch"){
      unlatch();
    }

    //if str received is equal to "agitate" then call agitate function
    if (rx_str == "ag"){
      agitate();
    }

    //if str received is equal to "load" then call load function
    if (rx_str == "load"){
      load();
    }

    //if first item in rx_values array is equal to "tension" use the second item to set the tension position
    if (strcmp(rx_values ,"tension ") == 0){
      rx_int = atoi(strtok (NULL,","));
      tension(rx_int);
    }

    //if first item in rx_values array is equal to "untension" use the second item to set the untension position
    if (strcmp(rx_values ,"untension") == 0){
      rx_int = atoi(strtok (NULL,","));
      untension(rx_int);
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
    
    //if first item in rx_values array is equal to "fire" use the second item to set the tension position and the third item to set the base position, then load and release ball
    if (strcmp(rx_values ,"fire") == 0){
      rx_int = atoi(strtok (NULL,","));
      goTo(rx_int);
      delay(1000);
      untension(237);
      delay(1000);
      latch();
      agitate();
      fanSpeed(255);
      load();
      delay(3000);
      rx_int = atoi(strtok (NULL,","));
      tension(rx_int);
      delay(100);
      unlatch();
    }
    
    rx_str = "";
  }
}

boolean isValidNumber(String str){
  for(byte i=0;i<str.length();i++){
    if(isDigit(str.charAt(i))) return true;
  }
  return false;
}

//function for latching the latch servo
void latch(){
  latchservo.write(90);
}

//function for unlatching the latch servo
void unlatch(){
  latchservo.write(160);
}

//function for agitating the ball reservoir
void agitate(){
  agitatorservo.write(125);
  delay(1000);
  agitatorservo.write(55);
  delay(1000);
  agitatorservo.write(125);
  delay(1000);
  agitatorservo.write(55);
  delay(1000);
  agitatorservo.write(90);
  delay(1000);
}

//function for loading ball from ball reservoir
void load(){
  loadservo.write(30);
  delay(500);
  loadservo.write(150);
  delay(500);
}

//function for tensioning the tensioning mechanism
void tension(int rx_int){
  while (analogRead(catPot) > rx_int){
    digitalWrite(motorpin1, HIGH);
    digitalWrite(motorpin2, LOW);
  }
  digitalWrite(motorpin1, LOW);
  digitalWrite(motorpin2, LOW);
}

//function for untensioning the tensioning mechanism
void untension(int rx_int){
  while (analogRead(catPot) > rx_int){
    digitalWrite(motorpin1, LOW);
    digitalWrite(motorpin2, HIGH);
  }
  digitalWrite(motorpin1, LOW);
  digitalWrite(motorpin2, LOW);
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
