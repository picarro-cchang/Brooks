# Boxer -- Manifold Box Controller version REVCODE #

Boxer code will run on two incarnations of the system board: Out of
Form Factor (OFF) and In Form Factor (IFF).  OFF hardware will use the
[Arduino Mega](https://www.sparkfun.com/products/11061), while IFF
hardware will be a custom PCB.

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
<a id="*IDN?"></a>

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

### System-level commands ###

#### SERNUM ####
<a id="SERNUM"></a>

Set the instrument's serial number.  Query the serial number with [*IDN?](#*IDN?).

##### Parameter #####

16-bit integer (0-65535) formatted as a decimal.

##### Typical Return #####

`0`




## Release history ##

### Version 1.0.0 ###

This version is only for testing the bootloader, USB enumeration, and
the basic command interface. The `*IDN?` command works to identify the
device.

**The `SERNUM` command will likely go away!**  You can use this
   command to test writing the serial number, but the command will
   likely change in the next version.
