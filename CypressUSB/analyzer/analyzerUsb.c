#pragma NOIV               // Do not generate interrupt vectors

/*
 * FILE:
 *   analyzerUsb.c
 *
 * DESCRIPTION:
 *   USB FX2 firmware for Picarro gas analyzer
 *
 * SEE ALSO:
 *   Specify any related information.
 *
 * HISTORY:
 *   07-May-2008  sze  Initial version. Vendor command to read 2-byte version number.
 *   30-Apr-2009  sze  Modification to LED flashing routines for alpha prototype hardware.
 *   22-Apr-2010  sze  Routines for analog interface board using timestamp based approach.
 *
 *  Copyright (c) 2008 Picarro, Inc. All rights reserved
 */

#include "fx2.h"
#include "fx2regs.h"
#include "fx2sdly.h"
#include "intrins.h"
#include "../autogen/usbdefs.h"

// Following defines are for launching transactions by writing into GPIFTRIG

#define GPIFTRIGWR 0
#define GPIFTRIGRD 4

#define GPIF_EP2 0
#define GPIF_EP4 1
#define GPIF_EP6 2
#define GPIF_EP8 3

#define HPI_RDY       GPIFREADYSTAT & bmBIT0 // RDY0
#define LED_ALL       (bmBIT0 | bmBIT1 | bmBIT2 | bmBIT3)
#define bmEP0BSY      0x01

#define bmHPIC        0x00 // HCNTL[1:0] = 00
#define bmHPID_AUTO   0x08 // HCNTL[1:0] = 10
#define bmHPIA        0x04 // HCNTL[1:0] = 01
#define bmHPID_MANUAL 0x0C // HCNTL[1:0] = 11
#define bmHPI_RESETz  0x80 // Port PA7 Low resets HPI
#define bmHPI_HINTz   0x01 // Port PA0 Low issues host interrupt
#define bmHPIHW       0x02 // Port PA1, used to control half-word in single mode

static WORD xdata LED_Count = 0;
static BYTE xdata LED_Status = 0;

extern BOOL   GotSUD;         // Received setup data flag
extern BOOL   Sleep;
extern BOOL   Rwuen;
extern BOOL   Selfpwr;

void LED_Off (BYTE LED_Mask);
void LED_On (BYTE LED_Mask);
void GpifInit( void );
void send_bytes(BYTE *b, BYTE n);

BYTE   Configuration;      // Current configuration
BYTE   AlternateSetting;   // Alternate settings

static short int xdata Tcount = 0;     // transaction count for input from HPI
BOOL enum_high_speed = FALSE;     // flag to let firmware know FX2 enumerated at high speed
static WORD autoinLength = 0;     // Autocommit occurs after these many bytes
static WORD xFIFOBC_IN = 0x0000;  // variable that contains EP6FIFOBCH/L value

//-----------------------------------------------------------------------------
// Variables for DAC resynchronizer
//-----------------------------------------------------------------------------
#define QSIZE   (1600)
#define NCHANNELS (8)
#define MAGIC_CODE 'S'
#define MAKEWORD( h, l ) \ 
  ( ( ( WORD )( h ) << 8 ) | ( BYTE )( l ) )

struct Queue {
    unsigned short int head;
    unsigned short int tail;
    unsigned short int count;
    unsigned char qdata[QSIZE];
} dac_queue;

BYTE buffer[4];
unsigned short int now = 0, divisor;
unsigned short int next_time;
unsigned char errorFlags = 0, data_available = 0;
//-----------------------------------------------------------------------------

void GPIF_SingleWordWrite( WORD gdata ) {
    while ( !( GPIFTRIG & 0x80 ) ); // poll GPIFTRIG.7 Done bit
    // using registers in XDATA space
    XGPIFSGLDATH = gdata >> 8;
    XGPIFSGLDATLX = gdata & 0xFFFF; // trigger GPIF Single Word Write transaction
}

void GPIF_SingleWordRead( WORD *gdata ) {
    static BYTE g_data = 0x00;     // dummy variable
    while ( !( GPIFTRIG & 0x80 ) ); // poll GPIFTRIG.7 Done bit
    // using register in XDATA space
    g_data = XGPIFSGLDATLX;        // dummy read to trigger GPIF
                                   // Single Word Read transaction

    while ( !( GPIFTRIG & 0x80 ) ); // poll GPIFTRIG.7 Done bit
    // using register(s) in XDATA space, retrieve word just read from ext. FIFO
    *gdata = ( ( WORD )XGPIFSGLDATLNOX << 8 ) | ( WORD )XGPIFSGLDATH;
}


//-----------------------------------------------------------------------------
// Queue handling routines
//-----------------------------------------------------------------------------
void qinit()
{
	EA = 0;
    dac_queue.head = dac_queue.tail = dac_queue.count = 0;
	EA = 1;
}

unsigned char qput(unsigned char d)
// Places data d onto the queue, returns 1 on success, 0 if queue is full 
{
	EA = 0;
    if (dac_queue.count == QSIZE) {
        errorFlags |= DAC_QUEUE_OVERFLOW;
		EA = 1;
        return 0;
    }
    dac_queue.qdata[dac_queue.tail++] = d;
    if (dac_queue.tail == QSIZE) dac_queue.tail = 0;
    dac_queue.count++;
	EA = 1;
    return 1;
}

unsigned char qget(unsigned char *d)
// Get data *d from the queue, returns 1 on success, 0 if queue is empty 
{
	EA = 0;
    if (dac_queue.count == 0) {
        errorFlags |= DAC_QUEUE_UNDERFLOW;
		EA = 1;
        return 0;
    }
    *d = dac_queue.qdata[dac_queue.head++];
    if (dac_queue.head == QSIZE) dac_queue.head = 0;
    dac_queue.count--;
	EA = 1;
    return 1;
}

void reset()
// Empty queue, reset error flags
{
    errorFlags = 0;
    qinit();
}

void init()
// Resets timestamp, queue and error flags
{
    now = 0;
    reset();
}
//-----------------------------------------------------------------------------
// Write to DAC
//-----------------------------------------------------------------------------
void write_dac(unsigned char channel,unsigned short int value)
{
    ET2 = 0;	// Do not allow timer interrupts when writing to DAC
    buffer[0] = 0x30 | channel;
    buffer[1] = MSB(value);
    buffer[2] = LSB(0xFF);
    EZUSB_WriteI2C(0x10, 3, buffer);
    ET2 = 1;
}
//-----------------------------------------------------------------------------
// Task Dispatcher hooks
//   The following hooks are called by the task dispatcher.
//-----------------------------------------------------------------------------

void TD_Init(void) {           // Called once at startup
    SYNCDELAY;
    // Set the clock speed to 48MHz (default is 12MHz)
    CPUCS = ((CPUCS & ~bmCLKSPD) | bmCLKSPD1);
    SYNCDELAY;

    BREAKPT &= ~bmBPEN;      // to see BKPT LED go out TGE
    Rwuen = TRUE;            // Enable remote-wakeup
    EP1OUTCFG = 0xA0;        // Activate EP1OUT for bulk transfer
    EP1INCFG = 0xA0;         // Activate EP1IN for bulk transfer
    SYNCDELAY;

    EP2CFG = 0xA0;           // Activate EP2 for bulk output, 512 bytes, 4x buffered
    SYNCDELAY;
    EP4CFG = 0x00;           // Activate EP4 for bulk output, 512 bytes, 2x buffered
    SYNCDELAY;
/*
    EP2CFG = 0xA2;           // Activate EP2 for bulk output, 512 bytes, 2x buffered
                             // Note that the endpoint buffer is shared with that for EP4, so
                             //  we cannot use quad buffering
    SYNCDELAY;
    EP4CFG = 0xA0;           // Activate EP4 for bulk output, 512 bytes, 2x buffered
    SYNCDELAY;
*/
	EP6CFG = 0xE0;           // Activate EP6 for bulk input, 512 bytes, 4x buffered
    SYNCDELAY;
    EP8CFG = 0x00;           // Deactivate EP8
    SYNCDELAY;

    FIFORESET = 0x80;        // NAKALL while resetting FIFOs
    SYNCDELAY;
    FIFORESET = 0x02;        // Reset EP2
    SYNCDELAY;
    FIFORESET = 0x04;        // Reset EP4
    SYNCDELAY;
    FIFORESET = 0x06;        // Reset EP6
    SYNCDELAY;
    FIFORESET = 0x0;         // Clear NAKALL
    SYNCDELAY;

    EP2FIFOCFG = 0x01;       // Configure EP2 as word-wide, and do 0->1 transition on AUTOOUT
    SYNCDELAY;
    EP2FIFOCFG = 0x11;
    SYNCDELAY;
    EP6FIFOCFG = 0x09;       // Configure EP6 as word-wide, enable AUTOIN
    SYNCDELAY;
    EP1OUTBC = 0x0;          // Arm EP1OUT

    // Initialize the GPIF registers. Do this before changing PORTCCFG and PORTECFG.
    GpifInit();

    // Set up PORTE as GPIO for slave serial configuration of FPGA
    // PORTECFG = 0;
    // Output enables for PORTE, rest are inputs
    // OEE = FPGA_SS_PROG | FPGA_SS_DIN | FPGA_SS_CCLK;
    // Set PROG and CCLK line high (DIN line low)
    // IO_FPGA_CONF = FPGA_SS_PROG | FPGA_SS_CCLK;

    // Uncomment the next lines if using the synchronous serial interface
    // Set up PORTE.3 as RXD0OUT
    PORTECFG = 0x08;
    // Output enables for PORTE, rest are inputs
    OEE = FPGA_SS_PROG | CYP_LED0 | CYP_LED1 | CYP_LED2;
    // Write initial value to PORTE
    // Set LEDs low and PROG low to reset the FPGA configuration
    IOE = 0x0;

    // Configure the serial interface
    SCON0 = 0x0;

    // Configure PORTA
    PORTACFG = bmBIT0; // PA0 takes on INT0/ alternate function
    OEA  |= 0x9E;      // initialize PA7,c PA4, PA3 PA2 and PA1 port i/o pins as outputs, PA6, PA5, PA0 as inputs
    IOA = bmHPI_RESETz | bmHPI_HINTz;   // Deassert interrupt and reset

    EZUSB_InitI2C();              // Initialize EZ-USB I2C controller
    I2CTL = bm400KHZ;		      // Use 400kHz I2C speed

    // Configure timer 2 with a 4MHz clock in 16 bit timer/counter mode with auto
    // reload. The reload count is set up to give a 100Hz interrupt rate.

    // CKCON.5 T2M = 0 Set CLKOUT/12 = 4MHz
    // T2CON.2 TR2 = 1 Run timer 2
    // T2CON.4 TCLK = 0 
    // T2CON.5 RCLK = 0
    // T2CON.0 CP_RL2 = 0 Enable reload mode

    CKCON &= ~0x20;
    TR2 = 1; TCLK = 0; RCLK = 0; CP_RL2 = 0;
    TF2 = 0;
    // For 100Hz, we need to set RCAP2 to 65536 - 40000 = 0x63C0
    RCAP2H = 0x63;
    RCAP2L = 0xC0;

    init();
    ET2 = 1;                            /* enable timer 2 interrupt    */
	next_time = now + 10;
}

void TD_Poll(void) {           // Called repeatedly while the device is idle
    unsigned char b, c, i, channel;
    short int delta;
    unsigned short int value;
    WORD nTransfers;
    if ( GPIFTRIG & 0x80 ) {           // if GPIF interface IDLE
        if ( ! ( EP24FIFOFLGS & 0x02 ) ) { // if there's a packet in the peripheral domain for EP2
            // TODO: Uncomment this line when the hardware arrives
            while(!HPI_RDY);             // wait for HPI to complete internal portion of previous transfer
            // Divide the number of bytes in FIFO by two to get number of GPIF transfers
            // N.B. The (WORD) cast is essential so that the expression is not evaluated as a byte
            nTransfers = MAKEWORD( EP2FIFOBCH, EP2FIFOBCL );
            nTransfers >>= 1;
            // According to 6713 errata SPRZ191G, last 32-bit transfer should be done without autoincrement
            //  At this point, nTransfers are measured in 16-bit words
            nTransfers-=2;
            if (nTransfers>0) {
                IOA = bmHPI_RESETz | bmHPI_HINTz | bmHPID_AUTO; // select HPID register with address auto-increment
            GPIFTCB1 = nTransfers>>8;      // setup transaction count with number of bytes in the EP2 FIFO
            SYNCDELAY;
            GPIFTCB0 = nTransfers & 0xFF;
            SYNCDELAY;
            GPIFTRIG = GPIFTRIGWR | GPIF_EP2; // launch GPIF FIFO WRITE Transaction from EP2 FIFO
            SYNCDELAY;
                while ( !( GPIFTRIG & 0x80 ) ); // poll GPIFTRIG.7 GPIF Done bit
                SYNCDELAY;
            }
            while(!HPI_RDY);             // wait for HPI to complete internal portion of previous transfer
            IOA = bmHPI_RESETz | bmHPI_HINTz | bmHPID_MANUAL; // select HPID register without address auto-increment
            GPIFTCB1 = 0;      // setup transaction count with number of bytes in the EP2 FIFO
            SYNCDELAY;
            GPIFTCB0 = 2;
            SYNCDELAY;
            GPIFTRIG = GPIFTRIGWR | GPIF_EP2; // launch GPIF FIFO WRITE Transaction from EP2 FIFO
            SYNCDELAY;
            while ( !( GPIFTRIG & 0x80 ) ); // poll GPIFTRIG.7 GPIF Done bit
            SYNCDELAY;
            while(!HPI_RDY);             // wait for HPI to complete internal portion of previous transfer
            SYNCDELAY;
        }

        if (Tcount) {                           // if Tcount is not zero
            if ( !( EP68FIFOFLGS & 0x01 ) ) { // if EP6 FIFO is not full

                // TODO: Uncomment next line when hardware is present
                while(!HPI_RDY);         // wait for HPI to complete internal portion of previous transfer

                // According to 6713 errata SPRZ191G, last 32-bit transfer should be done without autoincrement
                //  At this point, Tcount is measured in 16-bit words
                Tcount -=2;
                if (Tcount > 0) {
                    IOA = bmHPI_RESETz | bmHPI_HINTz | bmHPID_AUTO;          // select HPID register with address auto-increment
                    GPIFTCB3 = 0;
                    SYNCDELAY;
                    GPIFTCB2 = 0;
                    SYNCDELAY;
                    GPIFTCB1 = MSB(Tcount);           // setup transaction count with Tcount value
                    SYNCDELAY;
                    GPIFTCB0 = LSB(Tcount);
                    SYNCDELAY;

                    GPIFTRIG = GPIFTRIGRD | GPIF_EP6; // launch GPIF FIFO READ Transaction to EP6IN
                    SYNCDELAY;

                    while ( !( GPIFTRIG & 0x80 ) );   // poll GPIFTRIG.7 GPIF Done bit
                    SYNCDELAY;
                }
                IOA = bmHPI_RESETz | bmHPI_HINTz | bmHPID_MANUAL;          // select HPID register with address auto-increment
                GPIFTCB3 = 0;
                SYNCDELAY;
                GPIFTCB2 = 0;
                SYNCDELAY;
                GPIFTCB1 = 0;           // setup transaction count with Tcount value
                SYNCDELAY;
                GPIFTCB0 = 2;
                SYNCDELAY;

                GPIFTRIG = GPIFTRIGRD | GPIF_EP6; // launch GPIF FIFO READ Transaction to EP6IN
                SYNCDELAY;

                while ( !( GPIFTRIG & 0x80 ) );   // poll GPIFTRIG.7 GPIF Done bit
                SYNCDELAY;

                xFIFOBC_IN = MAKEWORD(EP6FIFOBCH, EP6FIFOBCL ); // get EP6FIFOBCH/L value
                if ( xFIFOBC_IN < autoinLength ) { // if pkt is short,
                    INPKTEND = 0x06;              // force a commit to the host
                }

                Tcount = 0;                       // set Tcount to zero to cease reading from DSP HPI RAM
                IOA = bmHPI_RESETz | bmHPI_HINTz | bmHPID_MANUAL; // Turn off address auto-increment
                while(!HPI_RDY);             // wait for HPI to complete internal portion of previous transfer
                SYNCDELAY;
            }
        }
    }

/*	
	if (now == next_time) {
		channel = 0;
		value = now << 8;
    	write_dac(channel,value);
		channel = 1;
		value = (65535-now) << 8;
        write_dac(channel,value);
		next_time++;
	}
*/    

	if (data_available) {
        delta = next_time - now;
        if (delta > 0) goto cont;	// Next time has not yet come
		data_available = 0;
		// Check for magic code for resynchronization
    	do {
	    	if (!qget(&c)) goto cont;
		} while ( c != MAGIC_CODE );
        // Send out data at front of queue
        if (!qget(&c)) goto cont;   // get channel mask
        channel = 0;
        for (i=0; (i<8)&&c; i++) {
            if (c & 1) {
                if (!qget(&b)) goto cont;	// get data
                value = b;
                if (!qget(&b)) goto cont;
                value |= ((WORD)(b) << 8); 
                write_dac(channel,value);
            }
            channel++;
            c >>= 1;
        }
		if (dac_queue.count > 0) {
	        if (!qget(&b)) goto cont;	// pop off timestamp
			next_time = b;
    	    if (!qget(&b)) goto cont;
			next_time |= ((WORD)(b) << 8);
			data_available = 1;			// more data are still on queue
		}
    }
cont:

	// blink LED0 to indicate firmware is running
    if (!LED_Count) {
        if (LED_Status) {
            LED_Off (bmBIT0);
            LED_Status = 0;
        } else {
            LED_On (bmBIT0);
            LED_Status = 1;
        }
    }
    LED_Count++;
}

BOOL TD_Suspend(void) {        // Called before the device goes into suspend mode
    return(TRUE);
}

BOOL TD_Resume(void) {        // Called after the device resumes
    return(TRUE);
}

//-----------------------------------------------------------------------------
// Device Request hooks
//   The following hooks are called by the end point 0 device request parser.
//-----------------------------------------------------------------------------

BOOL DR_GetDescriptor(void) {
    return(TRUE);
}

BOOL DR_SetConfiguration(void) { // Called when a Set Configuration command is received
    if ( EZUSB_HIGHSPEED( ) ) { // FX2 enumerated at high speed
        SYNCDELAY;
        EP6AUTOINLENH = 0x02;       // set AUTOIN commit length to 512 bytes
        SYNCDELAY;
        EP6AUTOINLENL = 0x00;
        SYNCDELAY;
        enum_high_speed = TRUE;
        autoinLength = 0x400;
    } else { // FX2 enumerated at full speed
        SYNCDELAY;
        EP6AUTOINLENH = 0x00;       // set AUTOIN commit length to 64 bytes
        SYNCDELAY;
        EP6AUTOINLENL = 0x40;
        SYNCDELAY;
        enum_high_speed = FALSE;
        autoinLength = 0x40;
    }
    Configuration = SETUPDAT[2];
    return(TRUE);            // Handled by user code
}

BOOL DR_GetConfiguration(void) { // Called when a Get Configuration command is received
    EP0BUF[0] = Configuration;
    EP0BCH = 0;
    EP0BCL = 1;
    return(TRUE);            // Handled by user code
}

BOOL DR_SetInterface(void) {     // Called when a Set Interface command is received
    AlternateSetting = SETUPDAT[2];
    return(TRUE);            // Handled by user code
}

BOOL DR_GetInterface(void) {     // Called when a Get Interface command is received
    EP0BUF[0] = AlternateSetting;
    EP0BCH = 0;
    EP0BCL = 1;
    return(TRUE);            // Handled by user code
}

BOOL DR_GetStatus(void) {
    return(TRUE);
}

BOOL DR_ClearFeature(void) {
    return(TRUE);
}

BOOL DR_SetFeature(void) {
    return(TRUE);
}

#define BIT0_TOGGLE (FPGA_SS_CCLK)
#define BIT1_TOGGLE (FPGA_SS_CCLK|FPGA_SS_DIN)

BOOL DR_VendorCmnd(void) {
    WORD value = (SETUPDAT[3]<<8)|SETUPDAT[2];
    WORD length = (SETUPDAT[7]<<8)|SETUPDAT[6];
    WORD *Destination;
    unsigned char b;
    unsigned short int i;
    switch (SETUPDAT[1]) {
    case VENDOR_GET_VERSION:
        EP0BUF[0] = USB_VERSION & 0xFF;
        EP0BUF[1] = (USB_VERSION>>8) & 0xFF;
        // Specify length (in bytes) to return
        EP0BCH = 0;
        EP0BCL = 2;
        // Acknowledge handshake phase of device request
        EP0CS |= bmHSNAK;
        break;
    case VENDOR_FPGA_CONFIGURE:
        switch (value) {
        case FPGA_START_PROGRAM:
            OEE = FPGA_SS_PROG | CYP_LED0 | CYP_LED1 | CYP_LED2;
            IOE = FPGA_SS_PROG;
            _nop_(); _nop_(); _nop_(); _nop_(); _nop_(); _nop_(); _nop_(); _nop_();
            // Pulses PROG line low momentarily (>0.5us) to start programming
            // TODO: Check length of pulse
            IOE &= ~FPGA_SS_PROG;
            _nop_(); _nop_(); _nop_(); _nop_(); _nop_(); _nop_(); _nop_(); _nop_();
            IOE |= FPGA_SS_PROG;
            OEE = CYP_LED0 | CYP_LED1 | CYP_LED2;
            // Return 1 to host
            EP0BUF[0] = 1;
            EP0BCH = 0;
            EP0BCL = 1;
            // Acknowledge handshake phase of device request
            EP0CS |= bmHSNAK;
            break;
        case FPGA_SEND_DATA:
            EP0BCL = 0;
            // Make sure that EP0 is not busy before trying get from the FIFO
            while (EP01STAT & bmEP0BSY);
            // send_bytes(EP0BUF,(BYTE)length);
            // Uncomment the following for synchronous serial port
            // Send bytes via synchronous serial port
            for (i=0;i<length;i++) {
                SBUF0 = EP0BUF[i];
                while (SCON0 & 0x2 == 0);
                SCON0 &= ~0x2;
            }
            // Acknowledge handshake phase of device request
            //EP0CS |= bmHSNAK;
            break;
        case FPGA_GET_STATUS:
            // Returns one byte with INIT in b0 and DONE in b1
            b = IOE;
            EP0BUF[0] = ((b & FPGA_SS_INIT) ? 1:0) | ((b & FPGA_SS_DONE) ? 2:0);
            // Specify length (in bytes) to return
            EP0BCH = 0;
            EP0BCL = 1;
            // Acknowledge handshake phase of device request
            EP0CS |= bmHSNAK;
            break;
        default:
            return TRUE; // Indicates failure
        }
        break;
    case VENDOR_GET_STATUS:
        switch (value) {
        case USB_STATUS_SPEED:
            EP0BUF[0] = enum_high_speed;
            // Specify length (in bytes) to return
            EP0BCL = 1;
            break;
        case USB_STATUS_GPIFTRIG:
            EP0BUF[0] = GPIFTRIG;
            // Specify length (in bytes) to return
            EP0BCL = 1;
            break;
        case USB_STATUS_GPIFTC:
            EP0BUF[0] = GPIFTCB0;
            EP0BUF[1] = GPIFTCB1;
            EP0BUF[2] = GPIFTCB2;
            EP0BUF[3] = GPIFTCB3;
            // Specify length (in bytes) to return
            EP0BCL = 4;
            break;
        default:
            return TRUE; // Indicates failure
        }
        EP0BCH = 0;
        // Acknowledge handshake phase of device request
        EP0CS |= bmHSNAK;
        break;
    case VENDOR_READ_HPIC:
        // TODO: Enable this when h/w becomes available
        while(!HPI_RDY);

        Destination = (WORD *)(&EP0BUF);
        IOA = bmHPI_RESETz | bmHPI_HINTz | bmHPIC;       // Select HPIC register with HHWIL low
        SYNCDELAY;
        GPIF_SingleWordRead(Destination);
        while ( 0 == (GPIFTRIG & 0x80) );
        Destination++;
        IOA = bmHPI_RESETz | bmHPI_HINTz | bmHPIC | bmHPIHW;     // Set HHWIL high
        SYNCDELAY;
        GPIF_SingleWordRead(Destination);
        while ( 0 == (GPIFTRIG & 0x80) );
        EP0BCH = 0;
        EP0BCL = 4;
        // Acknowledge handshake phase of device request
        EP0CS |= bmHSNAK;
        break;
    case VENDOR_WRITE_HPIC:
        EP0BCL = 0;
        while (EP01STAT & bmEP0BSY);
        // TODO: Enable this when h/w becomes available
        while(!HPI_RDY);

        IOA = bmHPI_RESETz | bmHPI_HINTz | bmHPIC;       // Select HPIC register with HHWIL low
        SYNCDELAY;
        GPIF_SingleWordWrite(((WORD)EP0BUF[1]<<8) | EP0BUF[0]);
        while ( 0 == (GPIFTRIG & 0x80) );
        IOA = bmHPI_RESETz | bmHPI_HINTz | bmHPIC | bmHPIHW;     // Set HHWIL high
        SYNCDELAY;
        GPIF_SingleWordWrite(((WORD)EP0BUF[3]<<8) | EP0BUF[2]);
        while ( 0 == (GPIFTRIG & 0x80) );
        // Acknowledge handshake phase of device request
        // EP0CS |= bmHSNAK;
        break;
    case VENDOR_READ_HPIA:
        // TODO: Enable this when h/w becomes available
        while(!HPI_RDY);

        Destination = (WORD *)(&EP0BUF);
        IOA = bmHPI_RESETz | bmHPI_HINTz | bmHPIA;       // Select HPIC register with HHWIL low
        SYNCDELAY;
        GPIF_SingleWordRead(Destination);
        while ( 0 == (GPIFTRIG & 0x80) );
        Destination++;
        IOA = bmHPI_RESETz | bmHPI_HINTz | bmHPIA | bmHPIHW;     // Set HHWIL high
        SYNCDELAY;
        GPIF_SingleWordRead(Destination);
        while ( 0 == (GPIFTRIG & 0x80) );
        EP0BCH = 0;
        EP0BCL = 4;
        // Acknowledge handshake phase of device request
        EP0CS |= bmHSNAK;
        break;
    case VENDOR_WRITE_HPIA:
        EP0BCL = 0;
        while (EP01STAT & bmEP0BSY);
        // TODO: Enable this when h/w becomes available
        while(!HPI_RDY);

        IOA = bmHPI_RESETz | bmHPI_HINTz | bmHPIA;       // Select HPIA register with HHWIL low
        SYNCDELAY;
        GPIF_SingleWordWrite(((WORD)EP0BUF[1]<<8) | EP0BUF[0]);
        while ( 0 == (GPIFTRIG & 0x80) );
        IOA = bmHPI_RESETz | bmHPI_HINTz | bmHPIA | bmHPIHW;     // Set HHWIL high
        SYNCDELAY;
        GPIF_SingleWordWrite(((WORD)EP0BUF[3]<<8) | EP0BUF[2]);
        while ( 0 == (GPIFTRIG & 0x80) );
        // Acknowledge handshake phase of device request
        // EP0CS |= bmHSNAK;
        break;
    case VENDOR_SET_HPID_IN_BYTES:
        EP0BCL = 0;
        while (EP01STAT & bmEP0BSY);
        Tcount = ((WORD)EP0BUF[1] << 8) | EP0BUF[0];
        Tcount = Tcount >> 1;
        // Acknowledge handshake phase of device request
        // EP0CS |= bmHSNAK;
        break;
    case VENDOR_RESET_HPID_IN_FIFO:
        FIFORESET = 0x80; // set NAKALL bit to NAK all transfers from host
        SYNCDELAY;
        FIFORESET = 0x06; // reset EP6 FIFO
        SYNCDELAY;
        FIFORESET = 0x00; // clear NAKALL bit to resume normal operation
        SYNCDELAY;
        // Return 1 to host
        EP0BUF[0] = 1;
        EP0BCH = 0;
        EP0BCL = 1;
        // Acknowledge handshake phase of device request
        // EP0CS |= bmHSNAK;
        break;
    case VENDOR_DSP_CONTROL:
        if (0 != (value & VENDOR_DSP_CONTROL_RESET)) IOA &= ~bmHPI_RESETz;
        else IOA |= bmHPI_RESETz;
        if (0 != (value & VENDOR_DSP_CONTROL_HINT)) IOA &= ~bmHPI_HINTz;
        else IOA |= bmHPI_HINTz;
        // Return value to host
        EP0BUF[0] = value;
        EP0BCH = 0;
        EP0BCL = 1;
        // Acknowledge handshake phase of device request
        EP0CS |= bmHSNAK;
        break;
    case VENDOR_SET_DAC:
        // value specifies the DAC
        EP0BCL = 0;
        // Make sure that EP0 is not busy before trying get from the FIFO
        while (EP01STAT & bmEP0BSY);
        // send_bytes(EP0BUF,(BYTE)length);
        buffer[0] = 0x30 | (SETUPDAT[2] & 0x7);
        buffer[1] = EP0BUF[0];
        buffer[2] = EP0BUF[1];
        EZUSB_WriteI2C(0x10, 3, buffer);
        // Acknowledge handshake phase of device request
        //EP0CS |= bmHSNAK;
        break;
    case VENDOR_DAC_QUEUE_CONTROL:
        EP0BCL = 0;
        // Make sure that EP0 is not busy before trying get from the FIFO
        while (EP01STAT & bmEP0BSY);

        switch (value) {
        case DAC_QUEUE_RESET:
            reset();
            break;
        case DAC_SET_TIMESTAMP:
            now     = ((WORD)EP0BUF[1]<<8) | EP0BUF[0];
			next_time = now + 10;
            break;
        case DAC_SET_RELOAD_COUNT:
            ET2 = 0;
            RCAP2L  = EP0BUF[0];
            RCAP2H  = EP0BUF[1];
            ET2 = 1;
            break;
        }
        break;
    case VENDOR_DAC_QUEUE_STATUS:
        switch (value) {
        case DAC_GET_TIMESTAMP:
            EP0BUF[0] = LSB(now);
            EP0BUF[1] = MSB(now);
            ET2 = 1;
            EP0BCL = 2;
            break;
        case DAC_GET_RELOAD_COUNT:
            EP0BUF[0] = RCAP2L;
            EP0BUF[1] = RCAP2H;
            EP0BCL = 2;
            break;
        case DAC_QUEUE_GET_FREE:
            i = QSIZE - dac_queue.count;
            EP0BUF[0] = LSB(i);
            EP0BUF[1] = MSB(i);
            EP0BCL = 2;
            break;
        case DAC_QUEUE_GET_ERRORS:
            EP0BUF[0] = errorFlags;
            EP0BCL = 1;
            break;
        }
        EP0BCH = 0;
        // Acknowledge handshake phase of device request
        EP0CS |= bmHSNAK;
        break;
    case VENDOR_DAC_ENQUEUE_DATA:
        EP0BCL = 0;
        // Make sure that EP0 is not busy before trying get from the FIFO
        while (EP01STAT & bmEP0BSY);
		i = 0;
		while (i<length) {
	        unsigned char c;
			qput(EP0BUF[i++]);		// Enqueue timestamp
			qput(EP0BUF[i++]);		
			qput(MAGIC_CODE);		// Write magic code (for synchronization)
			qput(c = EP0BUF[i++]);	// Enqueue channel bitmask
            while (c) {
                if (c & 1) {		// Enqueue DAC data
                    qput(EP0BUF[i++]);
                    qput(EP0BUF[i++]);
                }
                c >>= 1;
            }
        }
		if (!data_available) {
	        if (qget(&b)) {	// pop off timestamp
				next_time = b;
		    	if (qget(&b)) {
					next_time |= ((WORD)(b) << 8);
					data_available = 1;
				}
			}
		}
		break;
    default:
        return TRUE; // Indicates failure
    }
    return FALSE; // Indicates success
}
//-----------------------------------------------------------------------------
// Timer interrupt for serving DAC queues
//-----------------------------------------------------------------------------
void timer2_isr (void) interrupt TMR2_VECT {
    /* Service the queues on timer interrupt */
    // unsigned char i;
	now++;
	TF2 = 0;
}
//-----------------------------------------------------------------------------
// USB Interrupt Handlers
//   The following functions are called by the USB interrupt jump table.
//-----------------------------------------------------------------------------
// Setup Data Available Interrupt Handler
void ISR_Sudav(void) interrupt 0 {
    GotSUD = TRUE;            // Set flag
    EZUSB_IRQ_CLEAR();
    USBIRQ = bmSUDAV;         // Clear SUDAV IRQ
}

// Setup Token Interrupt Handler
void ISR_Sutok(void) interrupt 0 {
    EZUSB_IRQ_CLEAR();
    USBIRQ = bmSUTOK;         // Clear SUTOK IRQ
}

void ISR_Sof(void) interrupt 0 {
    EZUSB_IRQ_CLEAR();
    USBIRQ = bmSOF;            // Clear SOF IRQ
}

void ISR_Ures(void) interrupt 0 {
    // whenever we get a USB reset, we should revert to full speed mode
    pConfigDscr = pFullSpeedConfigDscr;
    ((CONFIGDSCR xdata *) pConfigDscr)->type = CONFIG_DSCR;
    pOtherConfigDscr = pHighSpeedConfigDscr;
    ((CONFIGDSCR xdata *) pOtherConfigDscr)->type = OTHERSPEED_DSCR;

    EZUSB_IRQ_CLEAR();
    USBIRQ = bmURES;         // Clear URES IRQ
}

void ISR_Susp(void) interrupt 0 {
    Sleep = TRUE;
    EZUSB_IRQ_CLEAR();
    USBIRQ = bmSUSP;
}

void ISR_Highspeed(void) interrupt 0 {
    if (EZUSB_HIGHSPEED()) {
        pConfigDscr = pHighSpeedConfigDscr;
        ((CONFIGDSCR xdata *) pConfigDscr)->type = CONFIG_DSCR;
        pOtherConfigDscr = pFullSpeedConfigDscr;
        ((CONFIGDSCR xdata *) pOtherConfigDscr)->type = OTHERSPEED_DSCR;
    }
    EZUSB_IRQ_CLEAR();
    USBIRQ = bmHSGRANT;
}

void ISR_Ep0ack(void) interrupt 0 {
}
void ISR_Stub(void) interrupt 0 {
}
void ISR_Ep0in(void) interrupt 0 {
}
void ISR_Ep0out(void) interrupt 0 {
}
void ISR_Ep1in(void) interrupt 0 {
}
void ISR_Ep1out(void) interrupt 0 {
}
void ISR_Ep2inout(void) interrupt 0 {
}
void ISR_Ep4inout(void) interrupt 0 {
}
void ISR_Ep6inout(void) interrupt 0 {
}
void ISR_Ep8inout(void) interrupt 0 {
}
void ISR_Ibn(void) interrupt 0 {
}
void ISR_Ep0pingnak(void) interrupt 0 {
}
void ISR_Ep1pingnak(void) interrupt 0 {
}
void ISR_Ep2pingnak(void) interrupt 0 {
}
void ISR_Ep4pingnak(void) interrupt 0 {
}
void ISR_Ep6pingnak(void) interrupt 0 {
}
void ISR_Ep8pingnak(void) interrupt 0 {
}
void ISR_Errorlimit(void) interrupt 0 {
}
void ISR_Ep2piderror(void) interrupt 0 {
}
void ISR_Ep4piderror(void) interrupt 0 {
}
void ISR_Ep6piderror(void) interrupt 0 {
}
void ISR_Ep8piderror(void) interrupt 0 {
}
void ISR_Ep2pflag(void) interrupt 0 {
}
void ISR_Ep4pflag(void) interrupt 0 {
}
void ISR_Ep6pflag(void) interrupt 0 {
}
void ISR_Ep8pflag(void) interrupt 0 {
}
void ISR_Ep2eflag(void) interrupt 0 {
}
void ISR_Ep4eflag(void) interrupt 0 {
}
void ISR_Ep6eflag(void) interrupt 0 {
}
void ISR_Ep8eflag(void) interrupt 0 {
}
void ISR_Ep2fflag(void) interrupt 0 {
}
void ISR_Ep4fflag(void) interrupt 0 {
}
void ISR_Ep6fflag(void) interrupt 0 {
}
void ISR_Ep8fflag(void) interrupt 0 {
}
void ISR_GpifComplete(void) interrupt 0 {
}
void ISR_GpifWaveform(void) interrupt 0 {
}
// ...debug LEDs
// use this global variable when (de)asserting debug LEDs...

void LED_Off (BYTE LED_Mask) {
    if (LED_Mask & bmBIT0) IOE &= ~CYP_LED0;
    if (LED_Mask & bmBIT1) IOE &= ~CYP_LED1;
    if (LED_Mask & bmBIT2) IOE &= ~CYP_LED2;
    if (LED_Mask & bmBIT3) IOA &= ~CYP_LED3;
}

void LED_On (BYTE LED_Mask) {
    if (LED_Mask & bmBIT0) IOE |= CYP_LED0;
    if (LED_Mask & bmBIT1) IOE |= CYP_LED1;
    if (LED_Mask & bmBIT2) IOE |= CYP_LED2;
    if (LED_Mask & bmBIT3) IOA |= CYP_LED3;
}

