
/* Picarro Mobile Kit Arduino code
 * Copyright Picarro 2014
 *
 * Possible commands / responses are:
 *   Backup battery voltage B / <floating-point number of volts>
 *   Car battery voltage    C / <floating-point number of volts>
 *   Identify device        D / <text string identifying the Mobile Kit with serial number in EEPROM>
 *   Fan 1 speed            F / <fan status frequency, floating point>
 *   Fan 2 speed            G / <fan status frequency, floating point>
 *   Help                   H or ? / <query and command summary>
 *   Ignition status        I / 1 | 0
 *   Ignition status by s/w J / 1 | 0
 *   Flowmeter speed        L / <flowmeter speed>
 *   Temperature            M / <temperature>
 *   Pump 1 speed           P / <pump speed, floating point>
 *   Pump 2 speed           Q / <pump speed, floating point>
 *   Soft reset             R
 *   Set serial number      Snn...n<space>: stores alphanumerical s/n into EEPROM
 *   Time since last reset  T / <integer number of milliseconds>
 *   UPS status             U / <integer: fail (4), discharged (2), okay (1), or ORed combination>
 *   Firmware revision      W / <revision string>
 *   Chassis voltage        Z / <floating-point number of volts>
 */

#include <EEPROM.h>
#include <Wire.h>

#define REVISION_STRING "0.5"

/* Revision history
 * 
 * Revision 0:   W command not implemented
 * Revision 0.1: first implementation of W command
 * Revision 0.5: J command added, software method of ignition detection
 */

#define PIN_CAR_BATT    0  // Analog input
#define PIN_BACKUP_BATT 1  // Analog input
#define PIN_CHASSIS     2  // Analog input
#define PIN_FAN_1       8  // Digital input
#define PIN_FAN_2      10  // Digital input
#define PIN_PUMP_1      3  // Digital input
#define PIN_PUMP_2      2  // Digital input
#define PIN_IGNITION    9  // Digital input
#define PIN_UPS_FAIL    5  // Digital input
#define PIN_UPS_DISCH   6  // Digital input
#define PIN_UPS_OK      7  // Digital input

#define FLOWMETER_I2C_ADDR   0x49
#define FLOWMETER_SERIAL_NO  1
#define FLOWMETER_PWRON_RST  2
#define FLOWMETER_CHECKSUM   3
#define FLOWMETER_FULL_SCALE 10.0

#define TEMPSENSOR_I2C_ADDR  0x4f

#define MAX_SER_NO_CHAR 32

void setup()
{
  pinMode(PIN_FAN_1, INPUT);
  pinMode(PIN_FAN_2, INPUT);
  pinMode(PIN_PUMP_1, INPUT);
  pinMode(PIN_PUMP_2, INPUT);
  pinMode(PIN_IGNITION, INPUT);
  pinMode(PIN_UPS_FAIL, INPUT);
  pinMode(PIN_UPS_DISCH, INPUT);
  pinMode(PIN_UPS_OK, INPUT);
  analogReference(EXTERNAL);  // External 3V reference

  if (EEPROM.read(MAX_SER_NO_CHAR))
    EEPROM.write(MAX_SER_NO_CHAR, '\0');  // Preemptively truncate the serial number
  delay(4);

  Wire.begin();
  Serial.begin(115200);
  while (Serial.available() > 0)  // Flush serial receiver
    Serial.read();
  resetFlowmeter();
}

void loop()
{
  char commandByte;

  if (Serial.available() > 0)
    commandByte = Serial.read();
  if (commandByte) {  // Test for nonzero character, since nulls seem to accumulate in receiver buffer
    switch (commandByte) {
      case 'b':
      case 'B':
        // Backup battery voltage
        Serial.println(analogRead(PIN_BACKUP_BATT) * 0.017151, 3);
        break;
      case 'c':
      case 'C':
        // Car battery voltage
        Serial.println(analogRead(PIN_CAR_BATT) * 0.017151, 3);
        break;
      case 'd':
      case 'D':
        // Identify device
        identify();
        break;
      case 'f':
      case 'F':
        // Fan speed
        fanSpeed(PIN_FAN_1);
        break;
      case 'g':
      case 'G':
        // Fan speed
        fanSpeed(PIN_FAN_2);
        break;
      case 'h':
      case 'H':
      case '?':
        // Help
        sendMenu();
        break;
      case 'i':
      case 'I':
        // Ignition status
        Serial.println(!digitalRead(PIN_IGNITION));
        break;
      case 'j':
      case 'J':
        // Ignition status (software method)
        Serial.println(!digitalRead(PIN_IGNITION));
        break;
      case 'l':
      case 'L':
        // Flowmeter speed
        Serial.println(flowmeterReading(), 3);
        break;
      case 'm':
      case 'M':
        // Temperature
        Serial.println(readTemp(), 1);
        break;
      case 'p':
      case 'P':
        // Pump 1 speed
        pumpSpeed(PIN_PUMP_1);
        break;
      case 'q':
      case 'Q':
        // Pump 2 speed
        pumpSpeed(PIN_PUMP_2);
        break;
      case 'r':
      case 'R':
        // Soft reset
        asm volatile ("  jmp 0");
        break;
      case 's':
      case 'S':
        // Set serial number
        setSerialNumber();
        break;
      case 't':
      case 'T':
        // Time since last reset
        Serial.println(millis(), DEC);
        break;
      case 'u':
      case 'U':
        // UPS status
        upsStatus();
        break;
      case 'w':
      case 'W':
        // Firmware revision
        Serial.println(REVISION_STRING);
        break;
      case 'z':
      case 'Z':
        // Chassis voltage
        Serial.println(((float)analogRead(PIN_CHASSIS) - 109.71) * 0.0037287, 3);
        break;
      default:
        Serial.println("Bad command, do H for help");
    }
  }
}

void fanSpeed(int pin) {
  unsigned long pulseWidthHigh, pulseWidthLow; // High or low fan motor driver pulse duration in microseconds

  pulseWidthHigh = pulseIn(pin, HIGH, 10000);  // 10 ms timeout (amounts to 1500 RPM, monimal fan speed 7500RPM)
  pulseWidthLow = pulseIn(pin, LOW, 10000);    // 10 ms timeout
  if (pulseWidthHigh == 0 || pulseWidthLow == 0) {
    // Timeout, fan locked
    Serial.println("0.000");
  }
  else
    // Convert microsecond period to RPM (two pulses per rotation)
    Serial.println(30e6 / ((float)pulseWidthHigh + (float)pulseWidthLow), 3);
}

float flowmeterReading(void) {
  int flow = 0;
  float slope = 1.0;
  float offset = 0.0;

  Wire.requestFrom(FLOWMETER_I2C_ADDR, 2, true);
  if (I2CTimeout())
    resetFlowmeter();
  else {
    flow = (Wire.read() << 8) & 0xff00;
    flow |= Wire.read() & 0x00ff;
    // Serial.println(flow, HEX);
  }
  if (flow == 0 || (flow & 0xc000) != 0)
    return -999.999;

  return slope * FLOWMETER_FULL_SCALE * (((float)flow / 16384.0) - 0.1) / 0.8 + offset;
}

bool I2CTimeout(void) {
  unsigned long int time = millis() + 1001;
  while (Wire.available() < 1) {
    if (millis() > time) {
      // Serial.println("I2C timeout!");
      return true;
    }
  }
  return false;
}

void identify(void) {
  char eepromByte;
  int characterCount = 0;

  Serial.print("Picarro Mobile Kit serial #");
  while (eepromByte = EEPROM.read(characterCount)) {  // Single equal sign to test read value is nonzero
    Serial.print(eepromByte);
    characterCount++;
  }
  Serial.print("\n");
}

void pumpSpeed(int pin) {
  unsigned long pulseWidthHigh, pulseWidthLow;     // High or low pump PWM pulse duration in microseconds

  pulseWidthHigh = pulseIn(pin, HIGH, 20000);  // 20 ms timeout
  pulseWidthLow = pulseIn(pin, LOW, 20000);    // 20 ms timeout
  if (pulseWidthHigh == 0 || pulseWidthLow == 0) {
    // Timeout, pump stopped
    Serial.println("0.000");
  }
  else
    Serial.println(60e6 / ((float)pulseWidthHigh + (float)pulseWidthLow), 3);  // Convert microsecond period to RPM
}

float readTemp(void) {
  int readData;
  char configByte = 1; // One-shot, 9-bit resolution

  // First, stop any ongoing conversion
  Wire.beginTransmission(TEMPSENSOR_I2C_ADDR);
  Wire.write(0x22);   // Command to stop conversion
  Wire.endTransmission();

  // Verify configuration register
  Wire.beginTransmission(TEMPSENSOR_I2C_ADDR);
  Wire.write(0xac);   // Access configuration register
  Wire.endTransmission();
  Wire.requestFrom(TEMPSENSOR_I2C_ADDR, 1);
  if(!I2CTimeout()) {
    readData = Wire.read();
    readData &= 0x0f;
  }
  else
    return 999.999;
  if (readData != configByte) {
    // Write EEPROM configuration only if necessary
    Wire.beginTransmission(TEMPSENSOR_I2C_ADDR);
    Wire.write(0xac); // Access configuration register
    Wire.write(configByte);
    Wire.endTransmission();
  }

  // Start a conversion
  Wire.beginTransmission(TEMPSENSOR_I2C_ADDR);
  Wire.write(0x51);   // Start conversion
  Wire.endTransmission();

  // Wait 94 ms for 9-bit resolution, 188 ms for 10 bits,
  // 376 ms for 11 bits, and 751 ms for 12 bits
  delay(94);

  // Read result
  Wire.beginTransmission(TEMPSENSOR_I2C_ADDR);
  Wire.write(0xaa);   // Request temperature
  Wire.endTransmission();
  Wire.requestFrom(TEMPSENSOR_I2C_ADDR, 2);
  if(!I2CTimeout()) {
    readData = Wire.read();
    readData <<= 8;
    readData |= (Wire.read() & 0x00ff );
  }
  else
    return 999.999;
  return 0.00390625 * (float)readData;
}

void resetFlowmeter(void) {
  Wire.beginTransmission(FLOWMETER_I2C_ADDR);
  Wire.write(FLOWMETER_PWRON_RST);
  Wire.endTransmission();
  delay(21);
  // Flush serial-number readings
  Wire.requestFrom(FLOWMETER_I2C_ADDR, 2);
  if (!I2CTimeout()) {
    // Serial.print("Flowmeter serial number: 0x");
    Wire.read(); // Serial.print(Wire.read(), HEX);
    Wire.read(); // Serial.print(Wire.read(), HEX);
  }
  delay(11);
  Wire.requestFrom(FLOWMETER_I2C_ADDR, 2);
  if (!I2CTimeout()) {
    Wire.read(); // Serial.print(Wire.read(), HEX);
    Wire.read(); // Serial.println(Wire.read(), HEX);
  }
  delay(11);
}

void setSerialNumber(void) {
  char serialNumberChar;
  int eepromAddress = 0;

  if (EEPROM.read(MAX_SER_NO_CHAR)) {
    EEPROM.write(MAX_SER_NO_CHAR, '\0');  // Preemptively truncate the serial number
    delay(4);
  }

  while (eepromAddress < MAX_SER_NO_CHAR) {
    if (Serial.available() > 0) {
      serialNumberChar = Serial.read();
      if (serialNumberChar == ' ') {
        EEPROM.write(eepromAddress, '\0');
        delay(4);
        Serial.print("\n");
        return;
      }
      else {
        EEPROM.write(eepromAddress, serialNumberChar);
        eepromAddress++;
        delay(4);
      }
    }
  }
}

void upsStatus(void) {
  int statusByte = 7;  // Bits 2, 1 and 0 high

    if (digitalRead(PIN_UPS_FAIL) == LOW)
      statusByte = 3;  // Bit 2 low
    if (digitalRead(PIN_UPS_DISCH) == LOW)
      statusByte &= 5; // Bit 1 low
    if (digitalRead(PIN_UPS_OK) == LOW)
      statusByte &= 6; // Bit 0 low
  Serial.println(statusByte, DEC);
}

// This function is declared last because the line continuations cause a problem with the parser
void sendMenu(void) {
  Serial.println("\n\
    Backup battery voltage        B\n\
    Car battery voltage           C\n\
    Identify device               D\n\
    Fan 1 speed                   F\n\
    Fan 2 speed                   G\n\
    Help                          H or ?\n\
    Ignition status               I\n\
    Ignition status (s/w method)  J\n\
    Flowmeter speed               L\n\
    Temperature                   M\n\
    Pump 1 speed                  P\n\
    Pump 2 speed                  Q\n\
    Soft reset                    R\n\
    Set serial number             Snn...n<space>\n\
    Time since last reset         T\n\
    UPS status                    U / response: fail (4), discharged (2), or okay (1)\n\
    Firmware revision             W\n\
    Chassis voltage               Z\n\
    ");
}

