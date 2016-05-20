#if ARDUINO < 100
#include <WProgram.h>
#else /* ARDUINO < 100 */
#include <Arduino.h>
#endif /* ARDUINO < 100 */

#include "EEPROM.h"

#include "cm_crds_pins.h"


int ledPin =  13;    // LED connected to digital pin 13

const int analogOutPin = 9; // Analog output pin that the htr attached
const int analogPin = 4;
int outputValue = 0;        // value output to the PWM (analog out)
float analogVal = 0;
float error1 = 0.0;
float error2 = 0;
float error_old1, delta_error1;
float error_old2, delta_error2;
float setPoint=10.0;
float temp=0;
float nBuf;
float nExt;
int fanPWM = 15; //pct pwm Duty for interior tube AKA fan
int integrator = 0; //summation reg for our integral term.
int inByte1; //control character for serial comms
int inByte2; //sets command for serial comms
int inByte3; //byte passed from PC to Arduino, e.g. PID coefficient, temperature etc.
int inByte4;
int inByte5;
int T1, T2, T3; //temperature registers for LM35 sensors
int control_out;
int intTmp;
int pwmCount=0;
const long maxPwrLevelNdx=120;
const long maxPwrMinutesNdx=20;
long totalNumPwrLevelsLogged=0;
long totalNumMinutesLogged=0;
byte pwrLevelBuffer[maxPwrLevelNdx];
byte pwrLevelExternal[maxPwrLevelNdx];
int pwrLevelNdx=0;
float pwrLevelBufferMinute[maxPwrMinutesNdx];
float pwrLevelExternalMinute[maxPwrMinutesNdx];
int pwrLevelMinuteNdx=0;

boolean led_state = false;
boolean relay = false;
boolean solenoid_1 = false;
boolean solenoid_2 = false;
boolean solenoid_3 = false;
boolean solenoid_4 = false;//save solenoid states, true is energized
boolean PID_on = true;//false;
boolean sendTemp = false; //send RTD counts (temp) up RS232 or not.
boolean fan_on = true;  //turn on fan
boolean ThirdHeater = true;
boolean valveTest = false;

unsigned long timediff;
unsigned long timeold = 0;

unsigned long timediff1;
unsigned long timeold1= 0;

class PID
{
public:
    PID(){};
    ~PID(){};

    void SetKp(float value);
    void SetTi(float value);
    void SetTd(float value);
    void SetMaxMin(int maxValue, int minValue);
    float CalcPID(float);
    float CalcPID(float, int);
    void ShowValues();

private:
    void CalcP(float);
    void CalcI(float);
    void CalcD(float);
    int delta_T;
    int maxValueOut;
    int minValueOut;
    float ePrevious;
    float pValue;
    float iValue;
    float dValue;
    float kp;
    float ti;
    float td;
};

PID myPID1;        // Creates a PID Object
PID myPID2;        // Creates a PID Object

void serial_table_handler(void);
void get_error(void);
void get_error2(void);
void set_pid(void);
void get_temps(void);
void printFloat(float value, int places);

void setup() {
    //int prescalerVal = 0x07; //create a variable called prescalerVal and set it equal to the binary number "00000111"
    //TCCR1B &= ~prescalerVal; //AND the value in TCCR0B with binary number "11111000"
    //prescalerVal = 1; //set prescalerVal equal to binary number "00000001" 16KHz
    //prescalerVal = 2; //set prescalerVal equal to binary number "00000010" 8KHz
    //TCCR1B |= prescalerVal; //OR the value in TCCR0B with binary number "00000001"
    //prescalerVal = 0x07;
    //TCCR2B &= ~prescalerVal; //AND the value in TCCR0B with binary number "11111000"
    //prescalerVal = 1; //set prescalerVal equal to binary number "00000001" 64KHz
    //prescalerVal = 2; //set prescalerVal equal to binary number "00000010" 8Khz
    //TCCR2B |= prescalerVal; //OR the value in TCCR0B with binary number "00000001"

    //continue with main loop - pid, etc.
    setPoint = 100*EEPROM.read(8) +10*EEPROM.read(9) + EEPROM.read(10);
    fanPWM = 100*EEPROM.read(11) +10*EEPROM.read(12) + EEPROM.read(13);
    if(setPoint>200 || setPoint<0)
      setPoint=140.0;
    if(fanPWM>25 || fanPWM<0)
      fanPWM=15;

    pinMode(ledPin, OUTPUT);
    pinMode(12, OUTPUT);   //valve1
    pinMode(7, OUTPUT);    //valve2
    pinMode(6, OUTPUT);    //valve3
    pinMode(5, OUTPUT);    //valve4
    pinMode(4, OUTPUT);    //fan control
    // initialize serial communications at 9600 bps:
    Serial.begin(9600);
    digitalWrite(4, LOW);   //Turn off the Fan
    myPID1.SetMaxMin(500,-500);  //was 500,-500
    myPID1.SetKp(995.0); // Insert Kp-value as argument
    myPID1.SetTi(990.0); // Insert Ti-value as argument
    myPID1.SetTd(990.0); // Insert Td-value as argument

    myPID2.SetMaxMin(500,-500);  //was 500,-500
    myPID2.SetKp(995.0); // Insert Kp-value as argument
    myPID2.SetTi(990.0); // Insert Ti-value as argument
    myPID2.SetTd(990.0); // Insert Td-value as argument

    analogWrite(HEATER3_PWM_EXTERNAL_LINE, 0);
    analogWrite(HEATER2_PWM_BUFFER_VOL, 0);
    analogWrite(HEATER1_PWM_BUFFER_VOL, 0);

    digitalWrite(12, HIGH);  //clear solenoid
    digitalWrite(7, HIGH); //set solenoid
    solenoid_2 = true;
}

float PID::CalcPID(float eCurrent)
{
    delta_T = 500;

    CalcP(eCurrent);
    CalcI(eCurrent);
    CalcD(eCurrent);

    return (pValue + iValue + dValue);
}

void PID::CalcP(float eCurrent)
{
    pValue = (kp * eCurrent);
}

void PID::CalcI(float eCurrent)
{
    float tempI=0.0;
    if((ti == 0))
    {
        iValue = 0;
    }
    else
    {
        if(minValueOut < maxValueOut)
        {
            tempI=((delta_T * kp * eCurrent) / ti) + iValue;
            if((tempI >= minValueOut) && (tempI <= maxValueOut))
            {
              iValue = tempI;
            }
        }
        else
        {
            Serial.println("Wrong minValueOut and/or maxValueOut");
        }
    }
}

void PID::CalcD(float eCurrent)
{
    dValue = ((td / delta_T) * (ePrevious - eCurrent));
    ePrevious = eCurrent;
}

void PID::SetKp(float value)
{
    kp = value;
}

void PID::SetTi(float value)
{
    ti = value;
}

void PID::SetTd(float value)
{
    td = value;
}

void PID::SetMaxMin(int maxValue, int minValue)
{
    maxValueOut = maxValue;
    minValueOut = minValue;
}

void PID::ShowValues()
{
    Serial.print("Kp=");
    Serial.print(kp);

    Serial.print("  Ti=");
    Serial.print(ti);

    Serial.print("  Td=");
    Serial.print(td);

    Serial.print("  p=");
    Serial.print(pValue);

    Serial.print("  i=");
    Serial.print(iValue);

    Serial.print("  d=");
    Serial.println(dValue);
}

///////////////////start main - this block will loop and check all services///////////////////////////////////
void loop() {
  unsigned long time = millis();
  if (Serial.available() >=2)//call the table handler if there is serial activity
  {
    serial_table_handler();
  }

  ///////////////////////////////////////////////////////////////////////////////////////////for the timer "interrupt"
   timediff = time - timeold;         //to periodically get the error signal every 500mS
   timediff1 = time - timeold1;         //to periodically get the error signal every 500mS
   if (timediff1 >= 25) {
     pwmCount++;
     timeold1 = time;
     if(pwmCount>=100)
       pwmCount=0;
     if(pwmCount>fanPWM)
       digitalWrite(4, LOW);   //Turn off the Fan
     else
       digitalWrite(4, HIGH);   //Turn on the Fan
   }

   if (timediff >= 500)
   {
     analogWrite(HEATER3_PWM_EXTERNAL_LINE, 0);
     analogWrite(HEATER2_PWM_BUFFER_VOL, 0);
     analogWrite(HEATER1_PWM_BUFFER_VOL, 0);
     delay(11);
     get_error();  //get input for the PID loop
     get_error2();  //get input for the PID loop
     timeold = time;
     set_pid();    //write the control current on PID
   }
   if (timediff <= 0) //rollover happened
   {
     timeold = time; //skip this cycle and do nothing.  This will happen every 50 days.  There will be a hiccup at 50 days but that's it.
                     //the get_error will not run and we'll have the old value of the error for 500mS
   }//////////////////////////////////////////////////////////////////////////////////////////end timer "interrupt"

}
//////////////////////////////////////////////////////////////////////////////////////////////////////////////
void serial_table_handler()  //read in serial commands from PC
{
  inByte1 = Serial.read();
  if (inByte1 == 's')
  {
    inByte2 = Serial.read();
    switch (inByte2)
    {
      case 'a':
        Serial.println("CM-CRDS Version 1.07");
        break;
      case 'e'://get three temperatures, return S3, S2, S1, (AN1, AN2, AN3)
        get_temps();
        break;
      case 'f'://set fan heater setpoint.  enter data in format "sf000" or "sf002" for 100 or 2.
        ///need to figure out a delay here for the 9600 baud data to get in.  I would like to put polling
        ///here, but the potential exists to get locked in an infinite loop and we don't have a WDT.  For
        ///now I'll put a tiny delay.  We need about 0.1mS/char.
        delay(10);//kill 10mS
        if (Serial.available() >= 3)  //you need three bytes ready BEFORE reading
        {
          //read out 100's 10's and 1's places
          inByte3 = Serial.read() - 48;
          delay(10);//kill 10mS
          inByte4 = Serial.read() - 48;
          delay(10);//kill 10mS
          inByte5 = Serial.read() - 48; //convert to dec
          delay(10);//kill 10mS
          inByte3 = 100*inByte3 + 10*inByte4 + inByte5;
          fanPWM = inByte3; //now your set point is reset
          if(fanPWM>25 || fanPWM<0) {
            fanPWM=15;
          } else {
            EEPROM.write(11, inByte3);
            EEPROM.write(12, inByte4);
            EEPROM.write(13, inByte5);
          }
          Serial.print("Fan PWM % setpoint at ");
          Serial.println(fanPWM);
        }

        Serial.flush();
        break;
      case 'p':
        nBuf=nExt=0.0;
        for(long i=0; i<maxPwrMinutesNdx; i++){
          //Serial.print(pwrLevelBufferMinute[i]);
          //Serial.print(", ");
          //Serial.println(pwrLevelExternalMinute[i]);
          nBuf+=pwrLevelBufferMinute[i];
          nExt+=pwrLevelExternalMinute[i];
        }
        //Serial.print(nBuf,6);
        //Serial.print(", ");
        //Serial.println(nExt,6);
        if(totalNumMinutesLogged<maxPwrMinutesNdx) {
          nBuf/=totalNumMinutesLogged;
          nExt/=totalNumMinutesLogged;
        } else {
          nBuf/=maxPwrMinutesNdx;
          nExt/=maxPwrMinutesNdx;
          totalNumMinutesLogged=maxPwrMinutesNdx+1;
        }
        Serial.print(nBuf,6);
        Serial.print(", ");
        Serial.println(nExt,6);
        break;
      case 'o'://set heater 1 temp (PID)  enter data in format "so255" or "so002" for 255 or 2.
        ///need to figure out a delay here for the 9600 baud data to get in.  I would like to put polling
        ///here, but the potential exists to get locked in an infinite loop and we don't have a WDT.  For
        ///now I'll put a tiny delay.  We need about 0.1mS/char.
        delay(10);//kill 10mS
        if (Serial.available() >= 3)  //you need three bytes ready BEFORE reading
        {
          //read out 100's 10's and 1's places
          inByte3 = Serial.read() - 48;
          delay(10);//kill 10mS
          EEPROM.write(8, inByte3);
          inByte4 = Serial.read() - 48;
          delay(10);//kill 10mS
          EEPROM.write(9, inByte4);
          inByte5 = Serial.read() - 48; //convert to dec
          delay(10);//kill 10mS
          EEPROM.write(10, inByte5);
          inByte3 = 100*inByte3 + 10*inByte4 + inByte5;
          setPoint = inByte3; //now your PID set point is reset
          Serial.print("Ext Heater Line Temp setpoint at ");
          Serial.println(setPoint);
        }

        Serial.flush();
        break;
      case 't': //check pid status
        //check the error
        if ((error1 <= 4.0) && (error2 <= 4.0))
        {
          Serial.print("PID locked ");
        }
        else
        {
          Serial.print("PID not locked ");
        }
        printFloat(setPoint,4);
        Serial.println(" ");
        break;
      case 'u'://toggle the sending up of RTD counts to RS232
        sendTemp = !sendTemp;
        break;
      default:
        break;
    }//end serial table handler
  }
}

void get_error()//get error signal
{
  error_old1 = error1;  //save old error for derivative

  analogVal=analogRead(TEMP_SENSE2_BUFFER_VOL);
  for(int i=0; i<299; i++)
    analogVal+=analogRead(TEMP_SENSE2_BUFFER_VOL);
  analogVal/=300.0;
  temp = 5.0 * (analogVal/1024.0);
  if (sendTemp == true) {
    printFloat(100.0*temp,4);
    Serial.print("\t");
  }

  error1 = (float)(setPoint) - 100.0*temp;
  delta_error1 = error1 - error_old1;
}

void get_error2()//get error signal
{
  error_old2 = error2;  //save old error for derivative

  analogVal=analogRead(TEMP_SENSE1_EXTERNAL_LINE);
  for(int i=0; i<299; i++)
    analogVal+=analogRead(TEMP_SENSE1_EXTERNAL_LINE);
  analogVal/=300.0;
  temp = 5.0 * (analogVal/1024.0);
  if (sendTemp == true) {
    printFloat(100.0*temp,4);
    Serial.print("\t");
  }

  error2 = (float)(setPoint) - 100.0*temp;
  delta_error2 = error2 - error_old2;
}

void get_temps()  //sample the LM35 sensors
{
  //try {
    analogWrite(HEATER3_PWM_EXTERNAL_LINE, 0);
    analogWrite(HEATER2_PWM_BUFFER_VOL, 0);
    analogWrite(HEATER1_PWM_BUFFER_VOL, 0);
    delay(10);
    analogVal=(float)analogRead(TEMP_SENSE1_EXTERNAL_LINE);
    for(int i=0; i<299; i++)
      analogVal+=(float)analogRead(TEMP_SENSE1_EXTERNAL_LINE);
    analogVal/=300.0;
    temp = 5.0 * (analogVal/1024.0);
    printFloat(100.0*temp,4);
    Serial.print("\t");

    analogVal=(float)analogRead(TEMP_SENSE2_BUFFER_VOL);
    for(int i=0; i<299; i++)
      analogVal+=(float)analogRead(TEMP_SENSE2_BUFFER_VOL);
    analogVal/=300.0;
    temp = 5.0 * (analogVal/1024.0);
    printFloat(100.0*temp,4);
    Serial.print("\r\n");
  //} catch(...) {
  //  Serial.print("Exception Seen in get_temps()\r\n");
  //}
}

void printFloat(float value, int places) {
  int digit;
  float tens = 0.1;
  int tenscount = 0;
  int i;
  float tempfloat = value;
  float d = 0.5;
  if (value < 0)
    d *= -1.0;
  for (i = 0; i < places; i++)
    d/= 10.0;
  tempfloat +=  d;
  if (value < 0)
    tempfloat *= -1.0;
  while ((tens * 10.0) <= tempfloat) {
    tens *= 10.0;
    tenscount += 1;
  }
  if (value < 0)
    Serial.print('-');
  if (tenscount == 0)
    Serial.print(0, DEC);
  for (i=0; i< tenscount; i++) {
    digit = (int) (tempfloat/tens);
    Serial.print(digit, DEC);
    tempfloat = tempfloat - ((float)digit * tens);
    tens /= 10.0;
  }
  if (places <= 0)
    return;
  Serial.print('.');
  for (i = 0; i < places; i++) {
    tempfloat *= 10.0;
    digit = (int) tempfloat;
    Serial.print(digit,DEC);
    tempfloat = tempfloat - (float) digit;
  }
}

//////////////////////////////////////////////////////////////////////////////////////////////////////////////
void set_pid()
{
  long int yOut = myPID1.CalcPID((float)error1); // Calculates P, I and D Values
  if(yOut < 0)      // This just makes sure yOut stays in range so...
    yOut = 0;
  if(yOut > 1023)
    yOut = 1023;
  yOut = map(yOut, 0, 1023, 0, 190);
  analogWrite(HEATER1_PWM_BUFFER_VOL, yOut); //this is heater 1
  analogWrite(HEATER2_PWM_BUFFER_VOL, yOut); //this is heater 2
  if(pwrLevelNdx==maxPwrLevelNdx) {
    nBuf=nExt=0.0;
    for(long i=0; i<maxPwrLevelNdx; i++){
      //Serial.print(pwrLevelBuffer[i]);
      //Serial.print(", ");
      //Serial.println(pwrLevelExternal[i]);
      nBuf+=pwrLevelBuffer[i];
      nExt+=pwrLevelExternal[i];
    }
    //Serial.print(nBuf,6);
    //Serial.print(", ");
    //Serial.println(nExt,6);
    if(totalNumPwrLevelsLogged<maxPwrLevelNdx) {
      nBuf/=totalNumPwrLevelsLogged;
      nExt/=totalNumPwrLevelsLogged;
    } else {
      nBuf/=maxPwrLevelNdx;
      nExt/=maxPwrLevelNdx;
      totalNumPwrLevelsLogged=maxPwrLevelNdx+1;
    }
    pwrLevelBufferMinute[pwrLevelMinuteNdx]=nBuf;
    pwrLevelExternalMinute[pwrLevelMinuteNdx]=nExt;
    //Serial.print(nBuf,6);
    //Serial.print(", ");
    //Serial.println(nExt,6);
    pwrLevelNdx=0;
    pwrLevelMinuteNdx++;
    totalNumMinutesLogged++;
  }
  if(pwrLevelMinuteNdx>=maxPwrMinutesNdx)
    pwrLevelMinuteNdx=0;
  pwrLevelBuffer[pwrLevelNdx]=yOut;
  if (sendTemp == true) {
    Serial.print("  ");
    Serial.print(yOut);
  }

  long int yOut2 = myPID2.CalcPID((float)error2); // Calculates P, I and D Values
  if(yOut2 < 0)      // This just makes sure yOut stays in range so...
    yOut2 = 0;
  if(yOut2 > 1023)
    yOut2 = 1023;
  yOut2 = map(yOut2, 0, 1023, 0, 255);
  analogWrite(HEATER3_PWM_EXTERNAL_LINE, yOut2);
  pwrLevelExternal[pwrLevelNdx]=yOut2;
  pwrLevelNdx++;
  totalNumPwrLevelsLogged++;
  if (sendTemp == true) {
    Serial.print("  ");
    Serial.print(yOut2);
    Serial.println("  ");
  }
}



