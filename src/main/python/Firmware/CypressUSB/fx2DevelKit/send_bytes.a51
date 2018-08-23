;
; FILE:  
;   send_bytes.a51
;
; DESCRIPTION:                                                
;   Cypress 8051 assembler code to send bytes via bit-banging to GPIO port C
;                                                             
; SEE ALSO:                                             
;   Specify any related information.                   
;                                                             
; HISTORY:
;   15-May-2008  sze  Initial version
;    7-Jun-2008  sze  Modified to use Port E for FPGA configuration
;
;  Copyright (c) 2008 Picarro, Inc. All rights reserved 
;                                                            
$NOMOD51
$nolist
$include (fx2regs.inc)          ; EZ-USB register assignments
$list

$include (..\autogen\usbdefs.inc)

NAME    SEND_BYTES

CLK0DAT0    EQU     FPGA_SS_PROG
CLK1DAT0    EQU     FPGA_SS_PROG + FPGA_SS_CCLK
CLK0DAT1    EQU     FPGA_SS_PROG + FPGA_SS_DIN
CLK1DAT1    EQU     FPGA_SS_PROG + FPGA_SS_CCLK + FPGA_SS_DIN 

?PR?_send_bytes?SEND_BYTES               SEGMENT CODE 
    EXTRN   CODE (?C?CLDPTR)  
    PUBLIC  _send_bytes

; void send_bytes(BYTE *b, BYTE n)
; Sends n (1<=n<=64) bytes from address b to pins on GPIO port C

    RSEG  ?PR?_send_bytes?SEND_BYTES
_send_bytes:
    USING   0
; Registers R2:R1 contain pointer to data
; Register  R5 contains number of bytes
    MOV     DPS,#0
    MOV     DPL,R1
    MOV     DPH,R2

LOOP:
    MOVX    A,@DPTR
; Rotate the bits one at a time through the carry flag
;  and produce a positive edge on the clock while the data
;  line is kept constant. Unrolled for performance.
    RRC     A
    JNC     LBL0A
    MOV     IO_FPGA_CONF,#CLK0DAT1
    MOV     IO_FPGA_CONF,#CLK1DAT1
    SJMP    LBL0B
LBL0A:
    MOV     IO_FPGA_CONF,#CLK0DAT0
    MOV     IO_FPGA_CONF,#CLK1DAT0
LBL0B:
    RRC     A
    JNC     LBL1A
    MOV     IO_FPGA_CONF,#CLK0DAT1
    MOV     IO_FPGA_CONF,#CLK1DAT1
    SJMP    LBL1B
LBL1A:
    MOV     IO_FPGA_CONF,#CLK0DAT0
    MOV     IO_FPGA_CONF,#CLK1DAT0
LBL1B:
    RRC     A
    JNC     LBL2A
    MOV     IO_FPGA_CONF,#CLK0DAT1
    MOV     IO_FPGA_CONF,#CLK1DAT1
    SJMP    LBL2B
LBL2A:
    MOV     IO_FPGA_CONF,#CLK0DAT0
    MOV     IO_FPGA_CONF,#CLK1DAT0
LBL2B:
    RRC     A
    JNC     LBL3A
    MOV     IO_FPGA_CONF,#CLK0DAT1
    MOV     IO_FPGA_CONF,#CLK1DAT1
    SJMP    LBL3B
LBL3A:
    MOV     IO_FPGA_CONF,#CLK0DAT0
    MOV     IO_FPGA_CONF,#CLK1DAT0
LBL3B:
    RRC     A
    JNC     LBL4A
    MOV     IO_FPGA_CONF,#CLK0DAT1
    MOV     IO_FPGA_CONF,#CLK1DAT1
    SJMP    LBL4B
LBL4A:
    MOV     IO_FPGA_CONF,#CLK0DAT0
    MOV     IO_FPGA_CONF,#CLK1DAT0
LBL4B:
    RRC     A
    JNC     LBL5A
    MOV     IO_FPGA_CONF,#CLK0DAT1
    MOV     IO_FPGA_CONF,#CLK1DAT1
    SJMP    LBL5B
LBL5A:
    MOV     IO_FPGA_CONF,#CLK0DAT0
    MOV     IO_FPGA_CONF,#CLK1DAT0
LBL5B:
    RRC     A
    JNC     LBL6A
    MOV     IO_FPGA_CONF,#CLK0DAT1
    MOV     IO_FPGA_CONF,#CLK1DAT1
    SJMP    LBL6B
LBL6A:
    MOV     IO_FPGA_CONF,#CLK0DAT0
    MOV     IO_FPGA_CONF,#CLK1DAT0
LBL6B:
    RRC     A
    JNC     LBL7A
    MOV     IO_FPGA_CONF,#CLK0DAT1
    MOV     IO_FPGA_CONF,#CLK1DAT1
    SJMP    LBL7B
LBL7A:
    MOV     IO_FPGA_CONF,#CLK0DAT0
    MOV     IO_FPGA_CONF,#CLK1DAT0
LBL7B:
; Increment data pointer and loop back for next byte

    INC     DPTR
LBL8:
    DJNZ     R5,LOOP1
    RET
; Too long for a relative jump
LOOP1:
    LJMP    LOOP
; END OF _send_bytes
    END
