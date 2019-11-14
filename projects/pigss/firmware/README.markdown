# Boxer -- Manifold Box Controller #

Boxer code will run on two incarnations of the system board: Out of
Form Factor (OFF) and In Form Factor (IFF).  OFF hardware will use the
[Arduino Mega](https://www.sparkfun.com/products/11061), while IFF
hardware will be a custom PCB.

<!-- markdown-toc start - Don't edit this section. Run M-x markdown-toc-refresh-toc -->
**Table of Contents**

- [Boxer -- Manifold Box Controller](#boxer----manifold-box-controller)
    - [Serial connection details](#serial-connection-details)
        - [Command interface](#command-interface)
        - [Debug interface](#debug-interface)
    - [Uploading new firmware](#uploading-new-firmware)
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
            - [STANDBY](#standby)
                - [Typical Return](#typical-return-6)
            - [CLEAN](#clean)
                - [Typical Return](#typical-return-7)
            - [TZA.SN n](#tzasn-n)
                - [Parameter (n)](#parameter-n-2)
                - [Typical Return](#typical-return-8)
            - [TZA.SN?](#tzasn)
                - [Typical Return](#typical-return-9)
            - [TZB.SN n](#tzbsn-n)
                - [Parameter (n)](#parameter-n-3)
                - [Typical Return](#typical-return-10)
            - [TZB.SN?](#tzbsn)
                - [Typical Return](#typical-return-11)
        - [Channel commands](#channel-commands)
            - [CHANENA n](#chanena-n)
                - [Parameter (n)](#parameter-n-4)
                - [Typical Return](#typical-return-12)
            - [CHANENA? n](#chanena-n)
                - [Parameter (n)](#parameter-n-5)
                - [Typical Return](#typical-return-13)
            - [CHANOFF n](#chanoff-n)
                - [Parameter (n)](#parameter-n-6)
                - [Typical Return](#typical-return-14)
            - [CHANSET n](#chanset-n)
                - [Parameter (n)](#parameter-n-7)
                - [Typical Return](#typical-return-15)
            - [CHANSET?](#chanset)
                - [Typical Return](#typical-return-16)
        - [Pressure commands](#pressure-commands)
            - [PRS.IN.RAW? n](#prsinraw-n)
                - [Parameter (n)](#parameter-n-8)
                - [Typical Return](#typical-return-17)
            - [PRS.OUT.RAW? n](#prsoutraw-n)
                - [Typical Return](#typical-return-18)
            - [PRS.ALPHA n](#prsalpha-n)
                - [Parameter (n)](#parameter-n-9)
                - [Typical Return](#typical-return-19)
            - [PRS.ALPHA?](#prsalpha)
                - [Typical Return](#typical-return-20)
        - [Proportional bypass valve commands](#proportional-bypass-valve-commands)
            - [CHx.BYP.DAC n](#chxbypdac-n)
                - [Parameter (n)](#parameter-n-10)
                - [Typical return](#typical-return)
            - [BYP.DAC? n](#bypdac-n)
                - [Parameter (n)](#parameter-n-11)
                - [Typical return](#typical-return-1)
        - [Channel identification commands](#channel-identification-commands)
            - [MFCVAL?](#mfcval)
                - [Typical Return](#typical-return-21)
            - [IDENTIFY](#identify)
                - [Typical Return](#typical-return-22)
            - [IDSTATE?](#idstate)
                - [Typical Return](#typical-return-23)
            - [ACTIVECH?](#activech)
                - [Typical Return](#typical-return-24)
    - [Release history](#release-history)
        - [Version 1.0.0](#version-100)
        - [Version 1.0.1](#version-101)
        - [Version 1.0.2](#version-102)
        - [Version 1.0.3](#version-103)
        - [Version 1.0.4](#version-104)
        - [Version 1.0.5](#version-105)
        - [Version 1.0.6](#version-106)
        - [Version 1.0.7](#version-107)
        - [Version 1.0.8](#version-108)
        - [Version 1.0.9](#version-109)
        - [Version 1.0.10](#version-1010)
        - [Version 1.1.0](#version-110)
        - [Version 1.1.1](#version-111)
        - [Version 1.1.2](#version-112)
        - [Version 1.1.3](#version-113)
        - [Version 1.1.4](#version-114)

<!-- markdown-toc end -->

## Serial connection details ##

### Command interface ###

The command interface is via USB, but the hardware will enumerate as a
virtual serial port.  The port will need to be configured with these
settings:

| Platform | Baud   | Data bits | Stop bits | Parity checking |
|----------|--------|-----------|-----------|-----------------|
| OFF      | 38400  | 8         | 1         | None            |
| IFF      | 230400 | 8         | 1         | None            |

### Debug interface ###

The debug interface is via USB, but the hardware will enumerate as a
virtual serial port.  The port will need to be configured with these
settings:

| Platform | Baud   | Data bits | Stop bits | Parity checking |
|----------|--------|-----------|-----------|-----------------|
| OFF      | 38400  | 8         | 1         | None            |
| IFF      | 230400 | 8         | 1         | None            |

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
examples are `/dev/ttyUSB0`, `/dev/ttyUSB1`, etc.  Baud rates for our
two platforms are shown below.

| Platform                  | Baud   |
|---------------------------|--------|
| OFF (Arduino Mega)        | 38400  |
| IFF (Picarro's Whitfield) | 230400 |

## Command reference ##

Commands are not case-sensitive -- the command `*IDN?` is the same as
`*idn?`.

Commands always return something.  If the command doesn't have an
explicit return value or string, it will return 0 (ACK).  Unrecognized
commands or commands causing other problems will return one of the
not-acknowledged (NACK) codes shown below.

| NACK code | Condition                |
|-----------|--------------------------|
| -1        | Command not recognized   |
| -2        | System is busy           |
| -3        | Command execution failed |
| -4        | Buffer overflow          |
| -5        | Argument out of range    |

A command may fail with the "command execution failed" code if some
hardware is missing.  For example, CH5.BYP.DAC 100 will fail if one of
the **Topaz** boards isn't plugged in.

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

##### Typical Return #####

`standby`

#### STANDBY ####

Put the system in standby mode.  This will disable all channels and
configure their bypass valves for the default flow.  This command may
fail if the `standby` state isn't accessible from the current state.

##### Typical Return #####

`0`

#### CLEAN ####

Put the system in clean mode.  As with `standby`, this will disable
all channels and configure their bypass valves for the default flow.
Unlike `standby`, this will open the clean solenoid to allow clean gas
to go to the analyzers.

You can exit clean mode by enabling a sample channel or going back to
standby mode.

##### Typical Return #####

`0`

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

#### TZB.SN n ####

Set the serial number for manifold (Topaz) board B.

##### Parameter (n) #####

Integers 0-65535

##### Typical Return #####

| Return | Condition             |
|--------|-----------------------|
| `0`    | Serial number set     |
| `-1`   | Topaz B not connected |

#### TZB.SN? ####

Query the serial number for manifold (Topaz) board B.

##### Typical Return #####

| Return | Condition                            |
|--------|--------------------------------------|
| `10`   | Successful return for Topaz board 10 |
| `-1`   | Topaz A not connected                |

### Channel commands ###

Each manifold box (piglet) has 8 channels.  Internally, there are 4 channels on two manifold (topaz) boards.  Channels are arranged on boards as shown below.

![Topaz channel names][topaz_channel_names]

[topaz_channel_names]: media/topaz_channel_names_600.png

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

### Pressure commands ###

#### PRS.IN.RAW? n ####

Query the raw digital pressure reading from one of the inlet sensors.
Each channel has one inlet sensor.  The raw pressure reading is a
24-bit number.

##### Parameter (n) #####

Channel number 1-8.

##### Typical Return #####

14799059

#### PRS.OUT.RAW? n ####

Query the raw digital pressure reading from one of the outlet sensors.
Each manifold (Topaz) board has one outlet sensor.  Outlet sensor 1 is
on the board with channels 1-4, and sensor 2 is on the board with
channels 5-8.

##### Typical Return #####

14799059

#### PRS.ALPHA n ####

Set the exponential moving average factor for pressure readings.  See
[this Wikipedia
page](https://en.wikipedia.org/wiki/Moving_average#Exponential_moving_average)
for a description of this factor.  In our case, alpha values of 0-1
are represented by settings of 0-65535, where 65535 gives the least
averaging, and 0 gives the most.

##### Parameter (n) #####

Integers 0-65535

##### Typical Return #####

0

#### PRS.ALPHA? ####

Query the exponential averaging factor used for pressure readings.

##### Typical Return #####

65535

### Proportional bypass valve commands ###

#### CHx.BYP.DAC n ####

Set the voltage DAC output controlling the proportional valve current
source.  There are 8 of these commands: CH1.BYP.DAC, CH2.BYP.DAC, ...,
CH8.BYP.DAC. The table below relates DAC codes to output current.  For
example, the revision A Topaz boards will produce 65535 * 3.4492
uA/count = 226 mA maximum.

| Hardware version | uA / count |
|------------------|------------|
| A                | 3.4492     |

##### Parameter (n) #####

0-65535

##### Typical return #####

0

#### BYP.DAC? n ####

Query the bypass DAC setting for channel `n`.  Returns a value in counts.

##### Parameter (n) #####

1-8

##### Typical return #####

17134

### Channel identification commands ###

#### MFCVAL? ####

Query this piglet's required Mass Flow Controller (MFC) setting
contribution.  The sample lines coming from each piglet will flow
through a single MFC, and the piglet firmware has no idea if other
piglets are present.  This number thus represents the number that
needs to be added to all the other `MFCVAL?` outputs to form the
ultimate MFC setting.

The output will be a floating-point number.

##### Typical Return #####

40.0

#### IDENTIFY ####

Start the channel identification process.  This can only be invoked in `standby` mode.

##### Typical Return #####

0

#### IDSTATE? ####

Query the channel identification substate.

| Substate             | Returned string |
|----------------------|-----------------|
| Ambient              | ambient         |
| Calculate            | calculate       |
| Not in identify mode | none            |

##### Typical Return #####

none

#### ACTIVECH? ####

Return a number corresponding to the active channels discovered during
channel identification.  Each bit in the 8-bit number corresponds to a
channel, and bits are set when the channel is active.

| Active channels | ACTIVECH? |
|-----------------|-----------|
| none            | 0         |
| all             | 255       |
| 3               | 4         |

##### Typical Return #####

255

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

### Version 1.0.7 ###

Started to add NACK codes.  See the [command
reference](#command-reference) for the current list.  Commands without
an explicit return will still simply return 0 for successful
completion.

### Version 1.0.8 ###

Added the [PRS.IN.RAW?](#prsinraw-n) query for the 8 inlet pressure
sensors.  This is the first sensor data command.  The command takes an
argument (1-8) to select the inlet channel.  The return is raw counts
from the sensor.  Revision A boards have 15 PSI sensors, while newer
revisions will probably have 25 PSI sensors.

Pressures are currently sampled at a **very slow** rate -- about once
every 2 seconds.  This is to make room for debug messages.  I'll
increase the speed when I'm more confident.

### Version 1.0.9 ###

Added the [CHx.BYP.DAC n](#chxbypdac-n) commands to set the sample
bypass proportional valve positions.  Note that the proportional valve
current control circuit has some offset issues with revision A
**Topaz**.  The current through the proportional valves will change
when solenoid valve selections change.

Pressures are now sampled at 100Hz when the log level is set to "error."

### Version 1.0.10 ###

Increased pressure sensor read frequency to 100Hz.  The delay between
pressure sensor triggers and reads is now 6ms.  The minimum value here
is 5ms, but I worry about timing variations at that level violating
this 5ms limit.  100Hz is a safe reading frequency.

Hex file releases now have an extra attribute: `_mega` or
`_whitfield`.  Use `_mega` releases for the Arduino Mega, and
`_whitfield` for Picarro's 90071 PCBs.

### Version 1.1.0 ###

This release supports two Topaz boards with the new system board --
Whitfield.  You'll need to use the new 230.4k baud rate instead of the
old 38.4k.  The Topaz boards need to be modified to have an I2C
multiplexer address of 0x71 instead of the default 0x70.

Added the TZB.SN command.  Note that you can't communicate with new
Topaz boards until they have serial numbers.  Getting the serial
number is the system board's way of discovering the hardware.

This firmware reads the 10 pressure sensors at about 35 Hz.

### Version 1.1.1 ###

Added the `clean` command and support for the clean solenoid.  Sending
the `clean` command will disable all sample channels and open the
clean solenoid.

### Version 1.1.2 ###

Added support for the front panel PCB "Aloha."  There are no new
remote commands to go with this.

### Version 1.1.3 ###

This version **does not read the pressure sensors**.  All `prs.*`
commands will return 0.  This will be an interim release while we fix
the pressure sensors.

Added the [MFCVAL?](#mfcval) query to get the Mass Flow Controller (MFC)
setting contribution required for a piglet.

Bypass valves for enabled channels now get set to zero.

Added the [IDENTIFY](#identify) command to kick off the channel
identification process.

Added the [IDSTATE?](#idstate) query to get the channel identification
substate.  The [OPSTATE?](#opstate) query will return the `identify`
parent state ID during channel identification.

Added the [ACTIVECH?](#activech) query to return the active channels
discovered during channel identification.

### Version 1.1.4 ###

  * Turned pressure reads back on at 40 Hz.  This slow rate is
    designed to accommodate rev A Topaz boards.  Use the new
    [PRS.ALPHA](#prsalpha-n) command to set the exponential averaging
    factor.
  * A broken USB channel or physical connection now puts the system
    into `standby` instead of `shutdown`.  The system will show a red
    communication light on the front panel while the connection is
    broken, but at least the light will stay on.
