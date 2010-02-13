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
xdata volatile unsigned char force_mode _at_ 0xE6FB;
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
//    EP2CFG = 0xAA;         // Activate EP2 for bulk output, 1024 bytes, 2x buffered
    SYNCDELAY;
    EP4CFG = 0x00;           // Deactivate EP4
    SYNCDELAY;
    EP6CFG = 0xE0;           // Activate EP6 for bulk input, 512 bytes, 4x buffered
    SYNCDELAY;
    EP8CFG = 0x00;           // Deactivate EP8
    SYNCDELAY;

    FIFORESET = 0x80;        // NAKALL while resetting FIFOs
    SYNCDELAY;
    FIFORESET = 0x02;        // Reset EP2
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
    force_mode = 0x0; 
}

void TD_Poll(void) {           // Called repeatedly while the device is idle
    WORD nTransfers;
    if ( GPIFTRIG & 0x80 ) {           // if GPIF interface IDLE
        if ( ! ( EP24FIFOFLGS & 0x02 ) ) { // if there's a packet in the peripheral domain for EP2
            // TODO: Uncomment this line when the hardware arrives
            while(!HPI_RDY);             // wait for HPI to complete internal portion of previous transfer
            // Divide the number of bytes in FIFO by two to get number of GPIF transfers
            // N.B. The (WORD) cast is essential so that the expression is not evaluated as a byte
            nTransfers = ((WORD)(EP2FIFOBCH<<8) | EP2FIFOBCL);
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
    }

    if (Tcount) {                           // if Tcount is not zero
        if ( GPIFTRIG & 0x80 ) {            // if GPIF interface IDLE
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

                xFIFOBC_IN = ( (WORD)( EP6FIFOBCH << 8 ) | EP6FIFOBCL ); // get EP6FIFOBCH/L value
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

    // blink LED0 to indicate firmware is running

    if (++LED_Count == 10000) {
        if (LED_Status) {
            LED_Off (bmBIT0);
            LED_Status = 0;
        } else {
            LED_On (bmBIT0);
            LED_Status = 1;
        }
        LED_Count = 0;
    }
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
    BYTE b;
    int i;
    int i1, i2, sum = 0;
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
            _nop_();
            _nop_();
            _nop_();
            _nop_();
            _nop_();
            _nop_();
            _nop_();
            _nop_();
            // Pulses PROG line low momentarily (>0.5us) to start programming
            // TODO: Check length of pulse
            IOE &= ~FPGA_SS_PROG;
            _nop_();
            _nop_();
            _nop_();
            _nop_();
            _nop_();
            _nop_();
            _nop_();
            _nop_();
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
            EP0BCH = 0;
            EP0BCL = 1;
            // Acknowledge handshake phase of device request
            EP0CS |= bmHSNAK;
            break;
        case USB_STATUS_GPIFTRIG:
            EP0BUF[0] = GPIFTRIG;
            // Specify length (in bytes) to return
            EP0BCH = 0;
            EP0BCL = 1;
            // Acknowledge handshake phase of device request
            EP0CS |= bmHSNAK;
            break;
        case USB_STATUS_GPIFTC:
            EP0BUF[0] = GPIFTCB0;
            EP0BUF[1] = GPIFTCB1;
            EP0BUF[2] = GPIFTCB2;
            EP0BUF[3] = GPIFTCB3;
            // Specify length (in bytes) to return
            EP0BCH = 0;
            EP0BCL = 4;
            // Acknowledge handshake phase of device request
            EP0CS |= bmHSNAK;
            break;
        default:
            return TRUE; // Indicates failure
        }
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
    case VENDOR_RECONNECT:
        USBCS |= 0x08;
        // Delay for stabilization
        for (i1=0; i1<2000; i1++)
        {
            for (i2=0; i2<100; i2++)
            {
                sum += i1 + i2;
            }
        }
        force_mode = 0x0;           
        SYNCDELAY;
        USBCS &= 0xF7;
        // Return value to host
        EP0BUF[0] = 0;
        EP0BCH = 0;
        EP0BCL = 1;
        // Acknowledge handshake phase of device request
        EP0CS |= bmHSNAK;
        break;
    default:
        return TRUE; // Indicates failure
    }
    return FALSE; // Indicates success
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

BYTE xdata portA = 0;
BYTE xdata portE = 0;

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
