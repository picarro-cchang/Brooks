#include <Wire.h>   // include Wire library for I2C
#include "EEPROM.h"
int inByte1 = 0;         // incoming serial byte
int inByte2 = 0;         // incoming serial byte
float volt = 0.0;
float m=1.0;
float b=0.0;
char buf[16];
#define U2 0x27  // The LTC2485 in this circuit, with CA0 floating and CA1 high (U2)
#define U3 0x26  // The LTC2485 in this circuit, with both address lines high (U3)
#define U6 0x17  // The LTC2485 in this circuit, with CA0 High and CA1 address line floating (U6)
#define U7 0x24  // The LTC2485 in this circuit, with both address lines floating. (U7)

//#define IM 1   //Temp Conversion
#define IM 0   //ADC Conversion
#define FA 0   //50&60 Hz Freq Rejection
#define FB 0   //50&60 Hz Freq Rejection
#define SPD 0  //Autocalibration
int config = IM*16 + FA*32 + FB*64 + SPD*128;
int ledPin =  3;    // LED connected to digital pin 13

typedef union _data {
  float f;
  char  s[4];
} floatData;

floatData q;

void setup() {
  Serial.begin(9600);   // start serial port at 9600 bps:
  Wire.begin();         // start Wire library as I2C-Bus Master   
  pinMode(ledPin, OUTPUT);    //FreqOutputEnable
  analogWrite(ledPin, 108);
  m=EEPROMReadFloat(11);
  b=EEPROMReadFloat(15);
  loop(); 
}

void loop() {
  if (Serial.available() >= 2) {
    inByte1 = Serial.read();   // get incoming bytes:
    if(inByte1 == 'u') {
      inByte2 = Serial.read();
      if(inByte2 == 's') {
        Serial.print("ok from Arduino board");
        TerminateLine();
      } else if(inByte2 == '2') {
        readLTCADC(U2,false);
      } else if(inByte2 == '3') {
        readLTCADC(U3,false);
      } else if(inByte2 == '6') {
        readLTCADC(U6,false);
      } else if(inByte2 == '7') {
        readLTCADC(U7,false);
      } else if(inByte2 == '8') {
        readLTCADC(U7,true);
      } else if(inByte2 == 'B') {
        b=readFloat();
        EEPROMWriteFloat(15,b);
        Serial.println(b,6);
      } else if(inByte2 == 'M') {
        m=readFloat();
        EEPROMWriteFloat(11,m);
        Serial.println(m,6);
      } else if(inByte2 == 'b') {
        Serial.println(b,6);
      } else if(inByte2 == 'm') {
        Serial.println(m,6);
      } else if(inByte2 == 'f') {
        Serial.println("1.04");
        TerminateLine();
      } else if(inByte2 == 'l') {
        Serial.println("LED Off");
        analogWrite(ledPin, 0);
      } else if(inByte2 == 'L') {
        Serial.println("LED On");
        analogWrite(ledPin, 108);
      } else if(inByte2 == '?') {
        Serial.print("u?: help, us: getArduinoStatus, uf: getFirmwareVersion, u2: getVoltageOnU2ADC,  u3: getVoltageOnU3ADC,  u6: getVoltageOnU6ADC,  u7: getVoltageOnU7ADC");
        TerminateLine();
      }
    } else if(inByte1 == 'f') {
      inByte2 = Serial.read();
      if(inByte2 == '0') {
        readADC0();
      }
    } 
  }
}

void TerminateLine(){
  Serial.print("\r");
  Serial.print("\n");
}

void readLTCADC(char addr, boolean tf)
{
  long x;     // Integer result from LTC2481
  float voltage; // Variable for floating point math
  if((x = read_LTC2485(addr, config)) != 0) {
    x ^= 0x80000000; // Invert MSB, result is 2’s complement
    voltage = (float) x; // convert to float
    voltage = voltage * 3.0 / 2147483648.0;// Multiply by Vref, divide by 2^31
    if(tf)
      voltage = m*voltage + b;
    Serial.print(voltage,6);
    //Serial.print(" from LTC ADC on addr: ");
    //Serial.print(addr, BIN);
    TerminateLine();
  }
} 

void readADC0()
{
  long x;     // Integer result from LTC2481
  float voltage; // Variable for floating point math
  x = analogRead(0);
  voltage = (float) x; // convert to float
  voltage = voltage * 5.0 / 1024.0;// Multiply by Vref, divide by 2^10
  Serial.print(voltage,6);
  TerminateLine();
} 

long read_LTC2485(char addr, char config)
{
  struct fourbytes { // Define structure of four consecutive bytes To allow byte access to a 32 bit int or float.
    byte te0; 
    byte te1; 
    byte te2; 
    byte te3; 
  };
  union                  // adc_code.bits32 all 32 bits
  {                      // adc_code.by.te0 byte 0
    long bits32;         // adc_code.by.te1 byte 1
    struct fourbytes by; // adc_code.by.te2 byte 2
  } adc_code;            // adc_code.by.te3 byte 3
  int timeout=0;
  int avail = 0;
  while(1) {
    Wire.requestFrom(addr,4);
    avail = Wire.available();
    if(avail != 4) { 
      timeout++;
      if(timeout>=300) {
        Serial.print("-99 Timeout Error in I2C Read of addr ");
        Serial.print(addr);
        Serial.print(",");
        Serial.print(avail);
        Serial.print(" bytes are available, must be exactly 4 bytes");
        TerminateLine();
        return 0L;
      }
      delay(1);
    } else {
      adc_code.by.te3 = Wire.receive();
      adc_code.by.te2 = Wire.receive(); 
      adc_code.by.te1 = Wire.receive();
      adc_code.by.te0 = Wire.receive();
      adc_code.by.te0 &= 0xC0;
      return adc_code.bits32;
    }
  }
  return 0L;
}

float readFloat(){
  delay(13);
  int n=0;
  while (Serial.available() >=1) {
    buf[n++]= Serial.read();
  }
  buf[n]=0;
  return atof(buf);
}

void writeFloat( float fv, int n)
{
  q.f=fv;
  Serial.println(q.s[0],DEC);
  Serial.println(q.s[1],DEC);
  Serial.println(q.s[2],DEC);
  Serial.println(q.s[3],DEC);
}

float readFloat( int n)
{
  Serial.println(q.s[0],DEC);
  Serial.println(q.s[1],DEC);
  Serial.println(q.s[2],DEC);
  Serial.println(q.s[3],DEC);
  return 0.0;  
}

//This function will write a 4 byte float to the eeprom at the specified address and address + 1,2,3
void EEPROMWriteFloat(int p_address, float val){
  q.f= val;
  EEPROM.write(p_address, q.s[0]);
  EEPROM.write(p_address+1, q.s[1]);
  EEPROM.write(p_address+2, q.s[2]);
  EEPROM.write(p_address+3, q.s[3]);
}

//This function will read a 4 byte float from the eeprom at the specified address and address + 1,2,3
float EEPROMReadFloat(int p_address){
  float rtnVal=0.0;
  q.s[0] = EEPROM.read(p_address);
  q.s[1] = EEPROM.read(p_address+1);
  q.s[2] = EEPROM.read(p_address+2);
  q.s[3] = EEPROM.read(p_address+3);
  return q.f;
}

