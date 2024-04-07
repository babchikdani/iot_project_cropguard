#include <ESP32Servo.h>
#include <ESP32Time.h>
#include <HardwareSerial.h>
#include <string>

using std::string;

ESP32Time rtc(3600);
int flashlightPin = 14;
Servo servo;
int servoPin = 13;

HardwareSerial lidarSerial(2); 
#define RXD2 27   // green TFmini wire
#define TXD2 26   // white YFmini wire
#define MIN_SIGNAL_STRENGTH 100
#define MAX_READABLE_DISTANCE 1200

#define SERVO_MIN_PWM 544
#define SERVO_MAX_PWM 2400
#define ERROR_DISTANCE 999  
#define BAUD_RATE 115200
#define PACKET_SIZE 5
#define BUFFER_SIZE 2
#define READ_DISTANCE 1
#define FACE_TARGET 2

uint8_t buffer[BUFFER_SIZE] = {0};
uint8_t sys_cmd;
uint8_t sys_angle; 

inline void send_data_to_pc(uint8_t data){
  Serial.write(data);
}

inline void move_servo_to(int angle){
  servo.write(angle);
  delay(10);
}

inline uint16_t read_distance(bool *good_read){
  uint8_t buf[9] = {0};
  uint16_t distance;
  if (lidarSerial.available() > 0) {
    lidarSerial.readBytes(buf, 9);  // Read 9 bytes of data
    if (buf[0] == 0x59 && buf[1] == 0x59) {
      distance = buf[2] + buf[3] * 256;
      uint16_t strength = buf[4] + buf[5] * 256;
      // Flush the serial after reading
      while(lidarSerial.available() > 0) char t = lidarSerial.read();
      if(strength < MIN_SIGNAL_STRENGTH || distance > MAX_READABLE_DISTANCE){ *good_read = false; } 
      else { *good_read = true; }
    } else {  // bad lidar packet header, read again;
      *good_read = false;
    }
    return distance;
  }
}

inline void flashlight(){
  digitalWrite(flashlightPin, HIGH);
  delay(1000);
  digitalWrite(flashlightPin, LOW);
}

inline void wait_for_command(){
  digitalWrite(LED_BUILTIN, HIGH);
  while(Serial.available() == 0) {}
  digitalWrite(LED_BUILTIN, LOW);
}

inline void read_new_command(){
  Serial.readBytes(buffer, BUFFER_SIZE);
  sys_cmd = buffer[0];
  sys_angle = buffer[1];
}

inline void blink_times(int n, int del){
  for(int i=0; i<n; i++){
    digitalWrite(LED_BUILTIN, HIGH);
    delay(del);
    digitalWrite(LED_BUILTIN, LOW);
    delay(del);
  }
}

void setup() {
  // put your setup code here, to run once:
  lidarSerial.begin(115200, SERIAL_8N1, RXD2, TXD2);  // Initializing serial port
  Serial.begin(115200);                               // Initializing serial port
  
  // Servo config
  ESP32PWM::allocateTimer(0);
	ESP32PWM::allocateTimer(1);
	ESP32PWM::allocateTimer(2);
	ESP32PWM::allocateTimer(3);
	servo.setPeriodHertz(50);    // standard 50 hz servo
	servo.attach(servoPin, SERVO_MIN_PWM, SERVO_MAX_PWM); // attaches the servo on pin 18 to the servo object
  pinMode(LED_BUILTIN, OUTPUT);
  pinMode(flashlightPin, OUTPUT);

}

void loop() {
  wait_for_command();
  read_new_command();
  // put your main code here, to run repeatedly:
  if(sys_cmd == FACE_TARGET){
    move_servo_to(sys_angle);
    flashlight();
  }
  if(sys_cmd == READ_DISTANCE){
    move_servo_to(sys_angle);
    bool good_read = false;
    int bad_reads_count = 0;
    uint16_t distance = read_distance(&good_read);
    while (good_read == false){
      bad_reads_count++;
      distance = read_distance(&good_read);
      // edge case: cannot read at a certain angle
      // After X amount of tries, gives up.
      if(bad_reads_count == 500){
        bad_reads_count = 0;
        distance = ERROR_DISTANCE;
        break;
      }
    }
    string str = std::to_string(distance) + "_" + std::to_string(sys_angle) + "_" + std::to_string(rtc.getSecond()) + "_" + std::to_string(rtc.getMillis()) + "\n";
    for(int i=0; i<str.size(); ++i){
      send_data_to_pc(str[i]);
    }
  }
}
