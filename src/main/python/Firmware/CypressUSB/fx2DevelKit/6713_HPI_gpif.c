// This program configures the General Programmable Interface (GPIF) for FX2.
// Please do not modify sections of text which are marked as "DO NOT EDIT ...".
//
// DO NOT EDIT ...
// GPIF Initialization
// Interface Timing      Sync
// Internal Ready Init   IntRdy=1
// CTL Out Tristate-able Binary
// SingleWrite WF Select     1
// SingleRead WF Select      0
// FifoWrite WF Select       3
// FifoRead WF Select        2
// Data Bus Idle Drive   Tristate
// END DO NOT EDIT

// DO NOT EDIT ...
// GPIF Wave Names
// Wave 0   = SingleRe
// Wave 1   = SingleWr
// Wave 2   = FIFO Rea
// Wave 3   = FIFO Wri

// GPIF Ctrl Outputs   Level
// CTL 0    = HRWz     CMOS
// CTL 1    = HDS1z    CMOS
// CTL 2    = HHWIL    CMOS
// CTL 3    = CTL3     CMOS
// CTL 4    = CTL4     CMOS
// CTL 5    = CTL5     CMOS

// GPIF Rdy Inputs
// RDY0     = HRDYz
// RDY1     = HWSEL
// RDY2     = RDY2
// RDY3     = RDY3
// RDY4     = RDY4
// RDY5     = TCXpire
// FIFOFlag = FIFOFlag
// IntReady = IntReady
// END DO NOT EDIT
// DO NOT EDIT ...
//
// GPIF Waveform 0: SingleRe
//
// Interval     0         1         2         3         4         5         6     Idle (7)
//          _________ _________ _________ _________ _________ _________ _________ _________
//
// AddrMode Same Val  Same Val  Same Val  Same Val  Same Val  Same Val  Same Val
// DataMode NO Data   NO Data   NO Data   Activate  NO Data   NO Data   Activate
// NextData SameData  SameData  SameData  SameData  SameData  SameData  SameData
// Int Trig No Int    No Int    No Int    No Int    No Int    No Int    No Int
// IF/Wait  IF        Wait 1    Wait 1    IF        Wait 1    Wait 1    IF
//   Term A HWSEL                         HRDYz                         HRDYz
//   LFunc  AND                           AND                           AND
//   Term B HWSEL                         HRDYz                         HRDYz
// Branch1  Then 4                        ThenIdle                      ThenIdle
// Branch0  Else 1                        ElseIdle                      ElseIdle
// Re-Exec  No                            No                            No
// Sngl/CRC Default   Default   Default   Default   Default   Default   Default
// HRWz         1         1         1         1         1         1         1         1
// HDS1z        1         1         0         1         1         0         1         1
// HHWIL        1         0         0         0         1         1         1         1
// CTL3         0         0         0         0         0         0         0         0
// CTL4         0         0         0         0         0         0         0         0
// CTL5         0         0         0         0         0         0         0         0
//
// END DO NOT EDIT
// DO NOT EDIT ...
//
// GPIF Waveform 1: SingleWr
//
// Interval     0         1         2         3         4         5         6     Idle (7)
//          _________ _________ _________ _________ _________ _________ _________ _________
//
// AddrMode Same Val  Same Val  Same Val  Same Val  Same Val  Same Val  Same Val
// DataMode NO Data   NO Data   Activate  NO Data   NO Data   Activate  NO Data
// NextData SameData  SameData  SameData  SameData  SameData  SameData  SameData
// Int Trig No Int    No Int    No Int    No Int    No Int    No Int    No Int
// IF/Wait  IF        Wait 1    Wait 1    IF        Wait 1    Wait 1    IF
//   Term A HWSEL                         HRDYz                         HRDYz
//   LFunc  AND                           AND                           AND
//   Term B HWSEL                         HRDYz                         HRDYz
// Branch1  Then 4                        ThenIdle                      ThenIdle
// Branch0  Else 1                        ElseIdle                      ElseIdle
// Re-Exec  No                            No                            No
// Sngl/CRC Default   Default   Default   Default   Default   Default   Default
// HRWz         1         0         0         0         0         0         0         1
// HDS1z        1         1         0         1         1         0         1         1
// HHWIL        1         0         0         0         1         1         1         1
// CTL3         0         0         0         0         0         0         0         0
// CTL4         0         0         0         0         0         0         0         0
// CTL5         0         0         0         0         0         0         0         0
//
// END DO NOT EDIT
// DO NOT EDIT ...
//
// GPIF Waveform 2: FIFO Rea
//
// Interval     0         1         2         3         4         5         6     Idle (7)
//          _________ _________ _________ _________ _________ _________ _________ _________
//
// AddrMode Same Val  Same Val  Same Val  Same Val  Same Val  Same Val  Same Val
// DataMode NO Data   NO Data   NO Data   Activate  NO Data   NO Data   Activate
// NextData SameData  SameData  SameData  SameData  SameData  SameData  SameData
// Int Trig No Int    No Int    No Int    No Int    No Int    No Int    No Int
// IF/Wait  Wait 2    Wait 2    IF        Wait 2    Wait 2    IF        IF
//   Term A                     HRDYz                         HRDYz     TCXpire
//   LFunc                      AND                           AND       AND
//   Term B                     HRDYz                         HRDYz     TCXpire
// Branch1                      Then 2                        Then 5    ThenIdle
// Branch0                      Else 3                        Else 6    Else 0
// Re-Exec                      No                            No        Yes
// Sngl/CRC Default   Default   Default   Default   Default   Default   Default
// HRWz         1         1         1         1         1         1         1         1
// HDS1z        1         0         0         1         0         0         1         1
// HHWIL        0         0         0         1         1         1         1         1
// CTL3         0         0         0         0         0         0         0         0
// CTL4         0         0         0         0         0         0         0         0
// CTL5         0         0         0         0         0         0         0         0
//
// END DO NOT EDIT
// DO NOT EDIT ...
//
// GPIF Waveform 3: FIFO Wri
//
// Interval     0         1         2         3         4         5         6     Idle (7)
//          _________ _________ _________ _________ _________ _________ _________ _________
//
// AddrMode Same Val  Same Val  Same Val  Same Val  Same Val  Same Val  Same Val
// DataMode NO Data   Activate  Activate  NO Data   Activate  Activate  NO Data
// NextData SameData  SameData  SameData  NextData  SameData  SameData  NextData
// Int Trig No Int    No Int    No Int    No Int    No Int    No Int    No Int
// IF/Wait  Wait 2    Wait 2    IF        Wait 2    Wait 2    IF        IF
//   Term A                     HRDYz                         HRDYz     TCXpire
//   LFunc                      AND                           AND       AND
//   Term B                     HRDYz                         HRDYz     TCXpire
// Branch1                      Then 2                        Then 5    ThenIdle
// Branch0                      Else 3                        Else 6    Else 0
// Re-Exec                      No                            No        No
// Sngl/CRC Default   Default   Default   Default   Default   Default   Default
// HRWz         0         0         0         0         0         0         1         1
// HDS1z        1         0         0         1         0         0         1         1
// HHWIL        0         0         0         1         1         1         1         1
// CTL3         0         0         0         0         0         0         0         0
// CTL4         0         0         0         0         0         0         0         0
// CTL5         0         0         0         0         0         0         0         0
//
// END DO NOT EDIT

// GPIF Program Code

// DO NOT EDIT ...
#include "fx2.h"
#include "fx2regs.h"
#include "fx2sdly.h"     // SYNCDELAY macro
// END DO NOT EDIT

// DO NOT EDIT ...
const char xdata WaveData[128] =
{
// Wave 0
/* LenBr */ 0x21,     0x01,     0x01,     0x3F,     0x01,     0x01,     0x3F,     0x07,
/* Opcode*/ 0x01,     0x00,     0x00,     0x03,     0x00,     0x00,     0x03,     0x00,
/* Output*/ 0x07,     0x03,     0x01,     0x03,     0x07,     0x05,     0x07,     0x07,
/* LFun  */ 0x09,     0x00,     0x00,     0x00,     0x00,     0x00,     0x00,     0x3F,
// Wave 1
/* LenBr */ 0x21,     0x01,     0x01,     0x3F,     0x01,     0x01,     0x3F,     0x07,
/* Opcode*/ 0x01,     0x00,     0x02,     0x01,     0x00,     0x02,     0x01,     0x00,
/* Output*/ 0x07,     0x02,     0x00,     0x02,     0x06,     0x04,     0x06,     0x07,
/* LFun  */ 0x09,     0x00,     0x00,     0x00,     0x00,     0x00,     0x00,     0x3F,
// Wave 2
/* LenBr */ 0x02,     0x02,     0x13,     0x02,     0x02,     0x2E,     0xB8,     0x07,
/* Opcode*/ 0x00,     0x00,     0x01,     0x02,     0x00,     0x01,     0x03,     0x00,
/* Output*/ 0x03,     0x01,     0x01,     0x07,     0x05,     0x05,     0x07,     0x07,
/* LFun  */ 0x00,     0x00,     0x00,     0x00,     0x00,     0x00,     0x2D,     0x3F,
// Wave 3
/* LenBr */ 0x02,     0x02,     0x13,     0x02,     0x02,     0x2E,     0x38,     0x07,
/* Opcode*/ 0x00,     0x02,     0x03,     0x04,     0x02,     0x03,     0x05,     0x00,
/* Output*/ 0x02,     0x00,     0x00,     0x06,     0x04,     0x04,     0x07,     0x07,
/* LFun  */ 0x00,     0x00,     0x00,     0x00,     0x00,     0x00,     0x2D,     0x3F,
};
// END DO NOT EDIT

// DO NOT EDIT ...
const char xdata FlowStates[36] =
{
/* Wave 0 FlowStates */ 0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
/* Wave 1 FlowStates */ 0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
/* Wave 2 FlowStates */ 0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
/* Wave 3 FlowStates */ 0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
};
// END DO NOT EDIT

// DO NOT EDIT ...
const char xdata InitData[7] =
{
/* Regs  */ 0xE0,0x00,0x00,0x07,0xEA,0x4E,0x00
};
// END DO NOT EDIT

// TO DO: You may add additional code below.

void GpifInit( void )
{
  BYTE i;

  // Registers which require a synchronization delay, see section 15.14
  // FIFORESET        FIFOPINPOLAR
  // INPKTEND         OUTPKTEND
  // EPxBCH:L         REVCTL
  // GPIFTCB3         GPIFTCB2
  // GPIFTCB1         GPIFTCB0
  // EPxFIFOPFH:L     EPxAUTOINLENH:L
  // EPxFIFOCFG       EPxGPIFFLGSEL
  // PINFLAGSxx       EPxFIFOIRQ
  // EPxFIFOIE        GPIFIRQ
  // GPIFIE           GPIFADRH:L
  // UDMACRCH:L       EPxGPIFTRIG
  // GPIFTRIG

  // Note: The pre-REVE EPxGPIFTCH/L register are affected, as well...
  //      ...these have been replaced by GPIFTC[B3:B0] registers

  // 8051 doesn't have access to waveform memories 'til
  // the part is in GPIF mode.

  IFCONFIG = 0xEA;
  // IFCLKSRC=1   , FIFOs executes on internal clk source
  // xMHz=1       , 48MHz internal clk rate
  // IFCLKOE=0    , Don't drive IFCLK pin signal at 48MHz
  // IFCLKPOL=0   , Don't invert IFCLK pin signal from internal clk
  // ASYNC=1      , master samples asynchronous
  // GSTATE=1     , Drive GPIF states out on PORTE[2:0], debug WF
  // IFCFG[1:0]=10, FX2 in GPIF master mode

  GPIFABORT = 0xFF;  // abort any waveforms pending

  GPIFREADYCFG = InitData[ 0 ];
  GPIFCTLCFG = InitData[ 1 ];
  GPIFIDLECS = InitData[ 2 ];
  GPIFIDLECTL = InitData[ 3 ];
  GPIFWFSELECT = InitData[ 5 ];
  GPIFREADYSTAT = InitData[ 6 ];

  // use dual autopointer feature...
  AUTOPTRSETUP = 0x07;          // inc both pointers,
                                // ...warning: this introduces pdata hole(s)
                                // ...at E67B (XAUTODAT1) and E67C (XAUTODAT2)

  // source
  AUTOPTRH1 = MSB( &WaveData );
  AUTOPTRL1 = LSB( &WaveData );

  // destination
  AUTOPTRH2 = 0xE4;
  AUTOPTRL2 = 0x00;

  // transfer
  for ( i = 0x00; i < 128; i++ )
  {
    EXTAUTODAT2 = EXTAUTODAT1;
  }

// Configure GPIF Address pins, output initial value,
//  PORTCCFG = 0xFF;    // [7:0] as alt. func. GPIFADR[7:0]
//  OEC = 0xFF;         // and as outputs
//  PORTECFG |= 0x80;   // [8] as alt. func. GPIFADR[8]
//  OEE |= 0x80;        // and as output

// ...OR... tri-state GPIFADR[8:0] pins
  PORTCCFG = 0x00;  // [7:0] as port I/O
  OEC = 0x00;       // and as inputs
  PORTECFG &= 0x7F; // [8] as port I/O
  OEE &= 0x7F;      // and as input

// GPIF address pins update when GPIFADRH/L written
  SYNCDELAY;                    //
  GPIFADRH = 0x00;    // bits[7:1] always 0
  SYNCDELAY;                    //
  GPIFADRL = 0x00;    // point to PERIPHERAL address 0x0000

// Configure GPIF FlowStates registers for Wave 0 of WaveData
  FLOWSTATE = FlowStates[ 0 ];
  FLOWLOGIC = FlowStates[ 1 ];
  FLOWEQ0CTL = FlowStates[ 2 ];
  FLOWEQ1CTL = FlowStates[ 3 ];
  FLOWHOLDOFF = FlowStates[ 4 ];
  FLOWSTB = FlowStates[ 5 ];
  FLOWSTBEDGE = FlowStates[ 6 ];
  FLOWSTBHPERIOD = FlowStates[ 7 ];
}

