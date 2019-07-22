# Boxer -- Manifold Box Controller #

Boxer code will run on two incarnations of the system board: Out of
Form Factor (OFF) and In Form Factor (IFF).  OFF hardware will use the
[Arduino Mega](https://www.sparkfun.com/products/11061), while IFF
hardware will be a custom PCB.

<!-- markdown-toc start - Don't edit this section. Run M-x markdown-toc-refresh-toc -->
**Table of Contents**

- [Boxer -- Manifold Box Controller](#boxer----manifold-box-controller)
    - [Serial connection details](#serial-connection-details)
        - [OFF hardware](#off-hardware)
            - [Command interface](#command-interface)
            - [Debug interface](#debug-interface)
    - [Uploading new firmware](#uploading-new-firmware)
        - [OFF hardware](#off-hardware-1)
    - [Command reference](#command-reference)
        - [IEEE-488 common commands](#ieee-488-common-commands)
            - [\*IDN?](#idn)
                - [Parameter](#parameter)
                - [Typical Return](#typical-return)
            - [\*RST](#rst)
                - [Parameter](#parameter-1)
                - [Typical Return](#typical-return-1)
        - [System-level commands](#system-level-commands)
            - [SERNUM n](#sernum-n)
                - [Parameter (n)](#parameter-n)
                - [Typical Return](#typical-return-2)
            - [SLOTID n](#slotid-n)
                - [Parameter (n)](#parameter-n-1)
                - [Typical Return](#typical-return-3)
            - [SLOTID?](#slotid)
                - [Typical Return](#typical-return-4)
            - [OPSTATE?](#opstate)
            - [Typical Return](#typical-return-5)
            - [TZA.SN n](#tzasn-n)
                - [Parameter (n)](#parameter-n-2)
                - [Typical Return](#typical-return-6)
            - [TZA.SN?](#tzasn)
                - [Typical Return](#typical-return-7)
        - [Channel commands](#channel-commands)
            - [CHANENA n](#chanena-n)
                - [Parameter (n)](#parameter-n-3)
                - [Typical Return](#typical-return-8)
            - [CHANENA? n](#chanena-n)
                - [Parameter (n)](#parameter-n-4)
                - [Typical Return](#typical-return-9)
            - [CHANOFF n](#chanoff-n)
                - [Parameter (n)](#parameter-n-5)
                - [Typical Return](#typical-return-10)
            - [CHANSET n](#chanset-n)
                - [Parameter (n)](#parameter-n-6)
                - [Typical Return](#typical-return-11)
            - [CHANSET?](#chanset)
                - [Typical Return](#typical-return-12)
    - [Release history](#release-history)
        - [Version 1.0.0](#version-100)
        - [Version 1.0.1](#version-101)
        - [Version 1.0.2](#version-102)
        - [Version 1.0.3](#version-103)
        - [Version 1.0.4](#version-104)
        - [Version 1.0.5](#version-105)
        - [Version 1.0.6](#version-106)

<!-- markdown-toc end -->



## Serial connection details ##

### OFF hardware ###

#### Command interface ####

The command interface is via USB, but the hardware will enumerate as a
virtual serial port.  The port will need to be configured with these
settings:

| Baud  | Data bits | Stop bits | Parity checking |
|-------|-----------|-----------|-----------------|
| 38400 | 8         | 1         | None            |

#### Debug interface ####

The debug interface is via USB, but the hardware will enumerate as a
virtual serial port.  The port will need to be configured with these
settings:

| Baud  | Data bits | Stop bits | Parity checking |
|-------|-----------|-----------|-----------------|
| 38400 | 8         | 1         | None            |

## Uploading new firmware ##

Both the OFF and IFF hardware versions will use the
[Optiboot](https://github.com/Optiboot/optiboot) bootloader to burn
new firmware into memory.  Optiboot is supported by
[AVRDUDE](https://www.nongnu.org/avrdude/), which can coordinate
sending new hex files over a Virtual Comm Port (VCP).  The relevant
command is:

```makefile
$(avrdude) -v -p m2560 -P $(VCP) -c arduino -b $(avrdude_baud) -F -u -U flash:w:$(hex_file)
```

where `$(avrdude)` is the AVRDUDE executable, `$(VCP)` is the Virtual
Comm Port, `$(avrdude_baud)` is the baud rate used by the bootloader,
and `$(hex_file)` is the new firmware in Intel HEX format.

For Windows, VCP examples are `com5`, `com23`, etc.  For Linux, VCP
examples are `/dev/ttyUSB0`, `/dev/ttyUSB1`, etc.

### OFF hardware ###

OFF hardware uses 38400 baud.  IFF hardware may use something
different.





## Command reference ##

Commands are not case-sensitive -- the command `*IDN?` is the same as
`*idn?`.

Commands always return something.  If the command doesn't have an
explicit return value or string, it will return 0 (ACK).  Unrecognized
commands or commands causing other problems will return -1 (NACK).

A naked carriage return is not considered a command, and as such may
be used to clear the instrument's receive queue.  The first carriage
return may send garbage to the command handler and return a NACK, so
the host will need to clear it's own receive queue before sending new
commands.

The controller can only handle one command at a time, and commands
take a variable length of time to execute.  Waiting for 500ms after
sending a command is enough for all commands to produce their returns.

### IEEE-488 common commands ###

#### \*IDN? ####

Returns the instrument's identification string containing four
comma-separated fields:

1. Manufacturer name
2. Model number
3. Serial number
4. Revision code

##### Parameter #####

None

##### Typical Return #####

`Picarro,Boxer,SN0,1.0.0`

#### \*RST ####

Initiates a system reset.

##### Parameter #####

None

##### Typical Return #####

None

### System-level commands ###

#### SERNUM n ####

Set the instrument's serial number to n.  Query the serial number with
[\*IDN?](#idn).

##### Parameter (n) #####

16-bit integer (0-65535) formatted as a decimal.

##### Typical Return #####

`0`

#### SLOTID n ####

Set the manifold box's slot ID.  There can be more than one manifold
box in a rack, and this will help us keep track of which rack position
it was installed into.  This setting is non-volatile -- it will
persist across power cycles.

##### Parameter (n) #####

Integers 0-9

##### Typical Return #####

`0`

#### SLOTID? ####

Query the manifold box's slot ID.

##### Typical Return #####

`3`

#### OPSTATE? ####

Query the system's operational state.

#### Typical Return ####

`standby`

#### TZA.SN n ####

Set the serial number for manifold (Topaz) board A.

##### Parameter (n) #####

Integers 0-65535

##### Typical Return #####

| Return | Condition             |
|--------|-----------------------|
| `0`    | Serial number set     |
| `-1`   | Topaz A not connected |

#### TZA.SN? ####

Query the serial number for manifold (Topaz) board A.

##### Typical Return #####

| Return | Condition                            |
|--------|--------------------------------------|
| `10`   | Successful return for Topaz board 10 |
| `-1`   | Topaz A not connected                |

### Channel commands ###

Each manifold box (piglet) has 8 channels.  Internally, there are 4 channels on two manifold (topaz) boards.  Channels are arranged on boards as shown below.

![Topaz channel names][topaz_channel_names]

[topaz_channel_names]: media/topaz_channel_names.png

#### CHANENA n ####

Enable channel n.

##### Parameter (n) #####

Integers 1-8

##### Typical Return #####

`0`

#### CHANENA? n ####

Returns 1 if channel n is enabled, or 0 if it's disabled.

##### Parameter (n) #####

Integers 1-8

##### Typical Return #####

`0`


#### CHANOFF n ####

Disable channel n.

##### Parameter (n) #####

Integers 1-8

##### Typical Return #####

`0`

#### CHANSET n ####

Set the channel enable register.  Each channel has a position in the
enable register bitfield, starting with channel 1 and ending with
channel 8.  Enable a channel by setting the channel's bit.  Disable a
channel by clearing the channel's bit.

##### Parameter (n) #####

Integers 0-255

##### Typical Return #####

`0`

#### CHANSET? ####

Query the channel enable register.

##### Typical Return #####

`8`

## Release history ##

### Version 1.0.0 ###

This version is only for testing the bootloader, USB enumeration, and
the basic command interface. The `*IDN?` command works to identify the
device.

**The `SERNUM` command will likely go away!**  You can use this
   command to test writing the serial number, but the command will
   likely change in the next version.
   
### Version 1.0.1 ###

This version is for testing the channel enable commands with the
bargraph LEDs.

### Version 1.0.2 ###

Added `SLOTID` command and its query.  This will help us keep track of
where the manifold box is in the rack, and thus to number its
channels.
   
### Version 1.0.3 ###

Added default log level setting to makefile.  This allows producing
hex release files tagged with the log level.

The command interface will now emit a NACK (-1) when the received
character buffer overflows.  This may allow the rack PC to simply send
characters and look for a NACK when waiting for the remote interface
to be ready.

### Version 1.0.4 ###

Added watchdog timer.  The system will reset after 1 second if it
hangs anywhere.

Added the `*RST` command to initiate a reset over the command interface.

### Version 1.0.5 ###

Added the `OPSTATE` command to query the current operating state.

### Version 1.0.6 ###

Added the `TZA.SN` and `TZA.SN?` commands to set and get the serial
number for Topaz A.  These commands, for now, simply return -1 if the
board isn't connected.
