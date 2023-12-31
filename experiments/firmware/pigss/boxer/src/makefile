# Hey Emacs, this is a -*- makefile-gmake -*- file

project_name = boxer

# Project version code.  This will set the REVCODE symbol in the image
REVCODE = 1.1.4

# Log level
#
# Known values are:
#   isr -- Emit messages inside the received character ISR
#   debug -- General purpose debugging
#   info -- Potentially interested stuff
#   warning -- Maybe bad stuff
#   error -- You want to know about this
#
# LOG_LEVEL = debug
LOG_LEVEL = error

# MCU name
#
# Use avr-gcc --target-help to see a list of MCU names
MCU = atmega2560

# PCB
#
# Known values are:
#   mega -- Arduino MEGA
#   whitfield -- Picarro's 90071 PCB
# PCB = mega
PCB = whitfield

# Enable or disable pressure reads
#
# Set this to true or false
PRESSURE_READS_ENABLED = true

# Processor frequency.
#     This will define a symbol, F_CPU, in all source code files equal to the
#     processor frequency. You can then use this symbol in your source code to
#     calculate timings. Do NOT tack on a 'UL' at the end, this will be done
#     automatically to create a 32-bit value in your source code.
#     Typical values are:
#         F_CPU =  1000000
#         F_CPU =  1843200
#         F_CPU =  2000000
#         F_CPU =  3686400
#         F_CPU =  4000000
#         F_CPU =  7372800
#         F_CPU =  8000000
#         F_CPU = 11059200
#         F_CPU = 14745600
#         F_CPU = 16000000
#         F_CPU = 18432000
#         F_CPU = 20000000
ifeq ($(PCB),mega)
# Platform is Arduino MEGA
	F_CPU = 16000000
endif

ifeq ($(PCB),whitfield)
# Platform is Picarro's 90071
	F_CPU = 14745600
endif

# Output format. (can be srec, ihex, binary)
FORMAT = ihex

# Target file name (without extension).
TARGET = main

# Object files directory
#     To put object files in current directory, use a dot (.), do NOT make
#     this an empty or blank macro!
OBJDIR = obj

# List C source files here. (C dependencies are automatically generated.)
SRC = $(TARGET).c \
      command.c \
      usart.c \
      logger.c \
      numbers.c \
      ascii.c \
      clock.c

# General system functions
SRC += system.c

# EEPROM module
SRC += eeprom.c

# SPI interface
SRC += spi.c

# I2C interface
SRC += i2c.c

# LEDs
SRC += led.c

# Periodic interrupts for the scheduler
SRC += metronome.c

# Simple scheduler (https://github.com/ferenc-nemeth/avr-simple-scheduler)
SRC += OS.c

# Chip-select module
SRC += cs.c

# LTC2601 DAC
SRC += ltc2601.c

# LTC2607 DAC
SRC += ltc2607.c

# Bargraph click board
SRC += bargraph.c

# Channel module
SRC += channel.c

# TCA9539 module
SRC += tca9539.c

# TCA954xA I2C switch module
SRC += tca954xa.c

# Honeywell MPR pressure sensor
SRC += mpr.c

# Fujitsu FRAM
SRC += mb85rc256v.c

# AVR Watchdog
SRC += watchdog.c

# Topaz board
SRC += topaz.c

# Pressure control
SRC += pressure.c

# Math functions
SRC += math.c

# Power board
SRC += vernon.c

# Whitfield (system) board
SRC += whitfield.c

# Aloha (front panel) board
SRC += aloha.c

# Identify module to help with channel identification
SRC += identify.c

# LM75A temperature sensor
SRC += lm75a.c


# List C++ source files here. (C dependencies are automatically generated.)
CPPSRC =

# List Assembler source files here.
#     Make them always end in a capital .S.  Files ending in a lowercase .s
#     will not be considered source files but generated files (assembler
#     output from the compiler), and will be deleted upon "make clean"!
#     Even though the DOS/Win* filesystem matches both .s and .S the same,
#     it will preserve the spelling of the filenames, and gcc itself does
#     care about how the name is spelled on its command-line.
ASRC =

# Optimization level, can be [0, 1, 2, 3, s].
#     0 = turn off optimization. s = optimize for size.
#     (Note: 3 is not always the best optimization level. See avr-libc FAQ.)
OPT = s

# Debugging format.
#     Native formats for AVR-GCC's -g are dwarf-2 [default] or stabs.
#     AVR Studio 4.10 requires dwarf-2.
#     AVR [Extended] COFF format requires stabs, plus an avr-objcopy run.
DEBUG = dwarf-2

# List any extra directories to look for include files here.
#     Each directory must be seperated by a space.
#     Use forward slashes for directory separators.
#     For a directory that has spaces, enclose it in quotes.
EXTRAINCDIRS =

# Compiler flag to set the C Standard level.
#     c89   = "ANSI" C
#     gnu89 = c89 plus GCC extensions
#     c99   = ISO C99 standard (not yet fully implemented)
#     gnu99 = c99 plus GCC extensions
CSTANDARD = -std=gnu99

# Place -D or -U options here for C sources
CDEFS = -D F_CPU=$(F_CPU)UL
CDEFS += -D REVCODE=\"$(strip $(REVCODE))\"
CDEFS += -D LOG_LEVEL=\"$(strip $(LOG_LEVEL))\"
CDEFS += -D PCB=\"$(strip $(PCB))\"
CDEFS += -D PRESSURE_READS_ENABLED=\"$(strip $(PRESSURE_READS_ENABLED))\"

# Place -D or -U options here for ASM sources
ADEFS = -DF_CPU=$(F_CPU)

# Place -D or -U options here for C++ sources
CPPDEFS = -DF_CPU=$(F_CPU)UL
#CPPDEFS += -D__STDC_LIMIT_MACROS
#CPPDEFS += -D__STDC_CONSTANT_MACROS

#---------------- Compiler Options C ----------------
#  -g*:          generate debugging information
#  -O*:          optimization level
#  -f...:        tuning, see GCC manual and avr-libc documentation
#  -Wall...:     warning level
#  -Wa,...:      tell GCC to pass this to the assembler.
#    -adhlns...: create assembler listing
CFLAGS = -g$(DEBUG)
CFLAGS += $(CDEFS)
CFLAGS += -O$(OPT)
CFLAGS += -funsigned-char
CFLAGS += -funsigned-bitfields
CFLAGS += -fpack-struct
CFLAGS += -fshort-enums
CFLAGS += -Wall
CFLAGS += -Wstrict-prototypes
#CFLAGS += -mshort-calls
#CFLAGS += -fno-unit-at-a-time
#CFLAGS += -Wundef
#CFLAGS += -Wunreachable-code
#CFLAGS += -Wsign-compare
CFLAGS += -Wa,-adhlns=$(<:%.c=$(OBJDIR)/%.lst)
CFLAGS += $(patsubst %,-I%,$(EXTRAINCDIRS))
CFLAGS += $(CSTANDARD)

#---------------- Compiler Options C++ ----------------
#  -g*:          generate debugging information
#  -O*:          optimization level
#  -f...:        tuning, see GCC manual and avr-libc documentation
#  -Wall...:     warning level
#  -Wa,...:      tell GCC to pass this to the assembler.
#    -adhlns...: create assembler listing
CPPFLAGS = -g$(DEBUG)
CPPFLAGS += $(CPPDEFS)
CPPFLAGS += -O$(OPT)
CPPFLAGS += -funsigned-char
CPPFLAGS += -funsigned-bitfields
CPPFLAGS += -fpack-struct
CPPFLAGS += -fshort-enums
CPPFLAGS += -fno-exceptions
CPPFLAGS += -Wall
CPPFLAGS += -Wundef
#CPPFLAGS += -mshort-calls
#CPPFLAGS += -fno-unit-at-a-time
#CPPFLAGS += -Wstrict-prototypes
#CPPFLAGS += -Wunreachable-code
#CPPFLAGS += -Wsign-compare
CPPFLAGS += -Wa,-adhlns=$(<:%.cpp=$(OBJDIR)/%.lst)
CPPFLAGS += $(patsubst %,-I%,$(EXTRAINCDIRS))
#CPPFLAGS += $(CSTANDARD)

#---------------- Assembler Options ----------------
#  -Wa,...:   tell GCC to pass this to the assembler.
#  -adhlns:   create listing
#  -gstabs:   have the assembler create line number information; note that
#             for use in COFF files, additional information about filenames
#             and function names needs to be present in the assembler source
#             files -- see avr-libc docs [FIXME: not yet described there]
#  -listing-cont-lines: Sets the maximum number of continuation lines of hex
#       dump that will be displayed for a given single line of source input.
ASFLAGS = $(ADEFS) -Wa,-adhlns=$(<:%.S=$(OBJDIR)/%.lst),-gstabs,--listing-cont-lines=100

#---------------- Library Options ----------------
# Minimalistic printf version
PRINTF_LIB_MIN = -Wl,-u,vfprintf -lprintf_min

# Floating point printf version (requires MATH_LIB = -lm below)
PRINTF_LIB_FLOAT = -Wl,-u,vfprintf -lprintf_flt

# If this is left blank, then it will use the Standard printf version.
# PRINTF_LIB =
# PRINTF_LIB = $(PRINTF_LIB_MIN)
PRINTF_LIB = $(PRINTF_LIB_FLOAT)

# Minimalistic scanf version
SCANF_LIB_MIN = -Wl,-u,vfscanf -lscanf_min

# Floating point + %[ scanf version (requires MATH_LIB = -lm below)
SCANF_LIB_FLOAT = -Wl,-u,vfscanf -lscanf_flt

# If this is left blank, then it will use the Standard scanf version.
SCANF_LIB =
#SCANF_LIB = $(SCANF_LIB_MIN)
#SCANF_LIB = $(SCANF_LIB_FLOAT)

MATH_LIB = -lm

# List any extra directories to look for libraries here.
#     Each directory must be seperated by a space.
#     Use forward slashes for directory separators.
#     For a directory that has spaces, enclose it in quotes.
#EXTRALIBDIRS =/usr/libexec/gcc/avr

#---------------- External Memory Options ----------------

# 64 KB of external RAM, starting after internal RAM (ATmega128!),
# used for variables (.data/.bss) and heap (malloc()).
#EXTMEMOPTS = -Wl,-Tdata=0x801100,--defsym=__heap_end=0x80ffff

# 64 KB of external RAM, starting after internal RAM (ATmega128!),
# only used for heap (malloc()).
#EXTMEMOPTS = -Wl,--section-start,.data=0x801100,--defsym=__heap_end=0x80ffff

EXTMEMOPTS =

#---------------- Linker Options ----------------
#  -Wl,...:     tell GCC to pass this to linker.
#    -Map:      create map file
#    --cref:    add cross reference to  map file
LDFLAGS = -Wl,-Map=$(TARGET).map,--cref
LDFLAGS += $(EXTMEMOPTS)
LDFLAGS += $(patsubst %,-L %,$(EXTRALIBDIRS))
LDFLAGS += $(PRINTF_LIB) $(SCANF_LIB) $(MATH_LIB)
# my extra lines
LDFLAGS += --verbose

################### Programming Options (avrdude) ####################

# Part string for avrdude.  This is usually the same as $(MCU), but
# not always.
# AVRDUDE_PART = $(MCU)
avrdude_part = m2560

# Programming hardware
# Type: avrdude -c ?
# to get a full listing.
#
# AVRDUDE_PROGRAMMER = dragon_isp
AVRDUDE_PROGRAMMER = atmelice_isp

# The Pocket AVR Programmer from Sparkfun
# Sparkfun part PGM-09825
# AVRDUDE_PROGRAMMER = usbtiny

# com1 = serial port. Use lpt1 to connect to parallel port.
AVRDUDE_PORT = usb

# Baud rate for bootloader
ifeq ($(PCB),mega)
# Platform is Arduino MEGA
	avrdude_baud = 38400
endif

ifeq ($(PCB),whitfield)
# Platform is Picarro's 90071
	avrdude_baud = 230400
endif

# Set the delay between programmer clock cycles.
#
# Set to ~1/10 of the AVR's default (by fuses) clock setting.
ifeq ($(PCB),mega)
# Platform is Arduino MEGA
	avrdude_bitdelay_us = 10	
endif

ifeq ($(PCB),whitfield)
# Platform is Picarro's 90071
	avrdude_bitdelay_us = 10
endif



AVRDUDE_WRITE_FLASH = -U flash:w:$(TARGET).hex
#AVRDUDE_WRITE_EEPROM = -U eeprom:w:$(TARGET).eep

# Uncomment the following if you want avrdude's erase cycle counter.
# Note that this counter needs to be initialized first using -Yn,
# see avrdude manual.
#AVRDUDE_ERASE_COUNTER = -y

# Uncomment the following if you do /not/ wish a verification to be
# performed after programming the device.
# AVRDUDE_NO_VERIFY = -V

# Increase verbosity level.  Please use this when submitting bug
# reports about avrdude. See <http://savannah.nongnu.org/projects/avrdude>
# to submit bug reports.
#AVRDUDE_VERBOSE = -v -v

avrdude_flags = -p $(avrdude_part) -P $(AVRDUDE_PORT) -c $(AVRDUDE_PROGRAMMER)
avrdude_flags += $(AVRDUDE_NO_VERIFY)
avrdude_flags += $(AVRDUDE_VERBOSE)
avrdude_flags += $(AVRDUDE_ERASE_COUNTER)
avrdude_flags += -B $(avrdude_bitdelay_us)


####################### Fuse settings ########################

ifeq ($(PCB),mega)
# Platform is Arduino MEGA

# Fuse settings for development without a bootloader
	devfuse_low = 0xff
	devfuse_high = 0xd8
	devfuse_extended = 0xfd

# Fuse settings for use with Optiboot
	bootfuse_low = 0xff
	bootfuse_high = 0xde
	bootfuse_extended = 0xfd

# Bootloader
	bootloader_hex = ../bootloader/optiboot_atmega2560_16000000Hz_38400baud.hex
endif

ifeq ($(PCB),whitfield)
# Platform is Picarro's 90071

# Fuse settings for development without a bootloader
	devfuse_low = 0xf0
	devfuse_high = 0xdf
	devfuse_extended = 0xfd

# Fuse settings for use with Optiboot
	bootfuse_low = 0xf0
	bootfuse_high = 0xde
	bootfuse_extended = 0xfd

# Bootloader
	bootloader_hex = ../bootloader/optiboot_atmega2560_14745600Hz_230400baud.hex
endif




#---------------- Debugging Options ----------------

# For simulavr only - target MCU frequency.
DEBUG_MFREQ = $(F_CPU)

# Set the DEBUG_UI to either gdb or insight.
# DEBUG_UI = gdb
DEBUG_UI = insight

# Set the debugging back-end to either avarice, simulavr.
DEBUG_BACKEND = avarice
#DEBUG_BACKEND = simulavr

# GDB Init Filename.
GDBINIT_FILE = __avr_gdbinit

# When using avarice settings for the JTAG
JTAG_DEV = /dev/com1

# Debugging port used to communicate between GDB / avarice / simulavr.
DEBUG_PORT = 4242

# Debugging host used to communicate between GDB / avarice / simulavr, normally
#     just set to localhost unless doing some sort of crazy debugging when
#     avarice is running on a different computer.
DEBUG_HOST = localhost

########################### Documentation ############################

doc_directory = ../doc

html_documentation_file = $(doc_directory)/$(project_name)_$(REVCODE).html

readme_file = ../README.markdown

pandoc = "d:/programs/pandoc/pandoc.exe"

# Web browser executable
browser = chrome

# CSS url
#
# I can't find anywhere to host my css, so I'm just doing it on the
# eventuallabs site.
css_url = http://www.eventuallabs.com/pandoc.css

########################## Release settings ##########################

release_directory = ../bin

ifeq ($(PRESSURE_READS_ENABLED),true)
	pressure_tag = pres
endif

ifeq ($(PRESSURE_READS_ENABLED),false)
	pressure_tag = nopres
endif

release_file = $(project_name)_$(REVCODE)_$(LOG_LEVEL)_$(PCB)_$(pressure_tag).hex



###################### Done with configuration #######################

# What platform are we on?
uname_value := "$(shell uname)"
ifeq ($(uname_value),"Linux")
	# Platform is Linux
	platform = linux
endif

ifeq ($(findstring CYGWIN, $(uname_value)), CYGWIN)
	# Platform is cygwin, but make may be called from eshell.  So
	# the shell is bash, but the PATH variable won't be set
	# correctly.
	platform = cygwin
	tclsh = "c:/Tcl/bin/tclsh.exe"
	etags = "d:/programs/emacs-26.2-x86_64/bin/etags.exe"
endif

ifeq ($(findstring MINGW32, $(uname_value)), MINGW32)
	# Platform is windows, and we're probably executing out of
	# eshell for emacs compiled with MinGW.
	platform = windows
	tclsh = "c:/Tcl/bin/tclsh.exe"
endif

# Define programs and commands.
SHELL = sh
CC = avr-gcc
OBJCOPY = avr-objcopy
OBJDUMP = avr-objdump
SIZE = avr-size
AR = avr-ar rcs
NM = avr-nm
AVRDUDE = avrdude
REMOVE = rm -f
REMOVEDIR = rm -rf
COPY = cp
WINSHELL = cmd

# Define Messages
# English
MSG_ERRORS_NONE = Errors: none
MSG_BEGIN = -------- begin --------
MSG_END = --------  end  --------
MSG_SIZE_BEFORE = Size before:
MSG_SIZE_AFTER = Size after:
MSG_COFF = Converting to AVR COFF:
MSG_EXTENDED_COFF = Converting to AVR Extended COFF:
MSG_FLASH = Creating load file for Flash:
MSG_EEPROM = Creating load file for EEPROM:
MSG_EXTENDED_LISTING = Creating Extended Listing:
MSG_SYMBOL_TABLE = Creating Symbol Table:
MSG_LINKING = Linking:
MSG_COMPILING = Compiling C:
MSG_COMPILING_CPP = Compiling C++:
MSG_ASSEMBLING = Assembling:
MSG_CLEANING = Cleaning project:
MSG_CREATING_LIBRARY = Creating library:

# Define all object files.
OBJ = $(SRC:%.c=$(OBJDIR)/%.o) $(CPPSRC:%.cpp=$(OBJDIR)/%.o) $(ASRC:%.S=$(OBJDIR)/%.o)

# Define all listing files.
LST = $(SRC:%.c=$(OBJDIR)/%.lst) $(CPPSRC:%.cpp=$(OBJDIR)/%.lst) $(ASRC:%.S=$(OBJDIR)/%.lst)

# Compiler flags to generate dependency files.
GENDEPFLAGS = -MMD -MP -MF .dep/$(@F).d

# Combine all necessary flags and optional flags.
# Add target processor to flags.
ALL_CFLAGS = -mmcu=$(MCU) -I. $(CFLAGS) $(GENDEPFLAGS)
ALL_CPPFLAGS = -mmcu=$(MCU) -I. -x c++ $(CPPFLAGS) $(GENDEPFLAGS)
ALL_ASFLAGS = -mmcu=$(MCU) -I. -x assembler-with-cpp $(ASFLAGS)

# Default target.
help:
	@echo 'Makefile for $(project_name) on $(platform) targeting $(PCB)      '
	@echo '                                                         '
	@echo 'Usage:                                                   '
	@echo '   make gccversion              Show the avr-gcc version          '
	@echo '   make fuseread                Read fuses                        '
	@echo '   make hex                     Just build to create the hex file for $(PCB) '
	@echo '   make lockprom                EEPROM not erased during program  '
	@echo '   make unlockprom              EEPROM erased during program      '
	@echo '   make appflash                Build for $(PCB) and program using avrdude and $(AVRDUDE_PROGRAMMER)'
	@echo '   make bootflash               Flash the bootloader to $(PCB) with avrdude and $(AVRDUDE_PROGRAMMER)'
	@echo '   make bootload VCP=comxx      Build for $(PCB), flash the application via bootloader'
	@echo '                                with VCP com port'
	@echo '   make bootfuse                Write fuses to execute bootloader on $(PCB)  '
	@echo '   make devfuse                 Write fuses to skip bootloader on $(PCB)    '
	@echo '   make debug_make              Debug the makefile                '
	@echo '   make doc                     Create html documentation         '
	@echo '   make docview                 View the documentation in a browser '
	@echo '   make release                 Create release hex file           '
	@echo '   make clean                   Clean up temporary files          '
	@echo '                                                         '

.PHONY: debug_make
debug_make:
	@echo 'Output from uname is $(uname_value)'
	@echo 'Source files are $(SRC)'
	@echo 'Processor frequency is $(F_CPU) Hz'
	@echo 'PCB is $(PCB)'
	@echo 'Shell is $(SHELL)'



pandoc_source = $(doc_directory)/pandoc_source.markdown

.PHONY: doc
doc: $(html_documentation_file) $(pandoc_source) $(readme_file)
$(html_documentation_file): $(pandoc_source) $(readme_file) 
	$(pandoc) -o $@ --toc --toc-depth=5 --standalone \
          --css $(css_url) \
          --metadata pagetitle="boxer" $< 

# Replace REVCODE in README file with the correct version
$(pandoc_source): $(readme_file)
	sed 's/REVCODE/$(REVCODE)/g' $< > $@

.PHONY: docview
docview:
	$(browser) $(html_documentation_file)

.PHONY: tags
tags:
	$(ctags) -R 

.PHONY: release
release: $(release_directory)/$(release_file)

$(release_directory)/$(project_name)_$(REVCODE).hex: $(TARGET).hex
	cp $< $@


.PHONY: fuseread
fuseread:
	avrdude $(avrdude_flags) -U lfuse:r:lowfuse:h \
	                         -U hfuse:r:highfuse:h \
	                         -U efuse:r:extfuse:h
	@echo 'Low fuse ($(devfuse_low) without, $(bootfuse_low) with bootloader)'
	@cat lowfuse
	@echo 'High fuse: ($(devfuse_high) without, $(bootfuse_high) with bootloader)'
	@cat highfuse
	@echo 'Extended fuse: ($(devfuse_extended) without, $(bootfuse_extended) with bootloader)'
	@cat extfuse

.PHONY: devfuse
devfuse:
	avrdude $(avrdude_flags) -U lfuse:w:$(devfuse_low):m \
                                 -U hfuse:w:$(devfuse_high):m \
                                 -U efuse:w:$(devfuse_extended):m

.PHONY: bootfuse
bootfuse:
	avrdude $(avrdude_flags) -U lfuse:w:$(bootfuse_low):m \
                                 -U hfuse:w:$(bootfuse_high):m \
                                 -U efuse:w:$(bootfuse_extended):m

# Lock the eeprom values by clearing EESAVE bit in high fuse byte
.PHONY: lockprom
lockprom :
	$(AVRDUDE) $(avrdude_flags) -U hfuse:w:0x90:m

# Unlock the eeprom values by setting EESAVE bit in high fuse byte
.PHONY: unlockprom
unlockprom :
	$(AVRDUDE) $(avrdude_flags) -U hfuse:w:0x98:m

all: begin gccversion sizebefore build sizeafter end

# Change the build target to build a HEX file or a library.
build: elf hex eep lss sym
#build: lib

elf: $(TARGET).elf
hex: $(TARGET).hex
eep: $(TARGET).eep
lss: $(TARGET).lss
sym: $(TARGET).sym
LIBNAME=lib$(TARGET).a
lib: $(LIBNAME)

# Eye candy.
# AVR Studio 3.x does not check make's exit code but relies on
# the following magic strings to be generated by the compile job.
begin:
	@echo
	@echo $(MSG_BEGIN)

end:
	@echo $(MSG_END)
	@echo

# Display size of file.
# HEXSIZE = $(SIZE) --target=$(FORMAT) $(TARGET).hex
HEXSIZE = $(SIZE) $(TARGET).hex
# ELFSIZE = $(SIZE) --mcu=$(MCU) --format=avr $(TARGET).elf
ELFSIZE = $(SIZE) $(TARGET).elf

sizebefore:
	@if test -f $(TARGET).elf; then echo; echo $(MSG_SIZE_BEFORE); $(ELFSIZE); \
	2>/dev/null; echo; fi

sizeafter:
	@if test -f $(TARGET).hex; then echo; echo $(MSG_SIZE_AFTER); $(HEXSIZE); \
	2>/dev/null; echo; fi

# Display compiler version information.
gccversion :
	@$(CC) --version

# Program the application hex
.PHONY: appflash
appflash: $(TARGET).hex $(TARGET).eep
	$(AVRDUDE) $(avrdude_flags) $(AVRDUDE_WRITE_FLASH) $(AVRDUDE_WRITE_EEPROM)

.PHONHY: bootload
bootload: $(TARGET).hex $(TARGET).eep
	$(AVRDUDE) -v -p $(avrdude_part) -P $(VCP) -c arduino -b $(avrdude_baud) \
          -F -u -U flash:w:$(TARGET).hex

# Write the bootloader to flash
.PHONY: bootflash
bootflash:
	$(AVRDUDE) $(avrdude_flags) -U flash:w:$(bootloader_hex)


# Generate avr-gdb config/init file which does the following:
#     define the reset signal, load the target file, connect to target, and set
#     a breakpoint at main().
gdb-config:
	@$(REMOVE) $(GDBINIT_FILE)
	@echo define reset >> $(GDBINIT_FILE)
	@echo SIGNAL SIGHUP >> $(GDBINIT_FILE)
	@echo end >> $(GDBINIT_FILE)
	@echo file $(TARGET).elf >> $(GDBINIT_FILE)
	@echo target remote $(DEBUG_HOST):$(DEBUG_PORT)  >> $(GDBINIT_FILE)
ifeq ($(DEBUG_BACKEND),simulavr)
	@echo load  >> $(GDBINIT_FILE)
endif
	@echo break main >> $(GDBINIT_FILE)

debug: gdb-config $(TARGET).elf
ifeq ($(DEBUG_BACKEND), avarice)
	@echo Starting AVaRICE - Press enter when "waiting to connect" message displays.
	@$(WINSHELL) /c start avarice --jtag $(JTAG_DEV) --erase --program --file \
	$(TARGET).elf $(DEBUG_HOST):$(DEBUG_PORT)
	@$(WINSHELL) /c pause

else
	@$(WINSHELL) /c start simulavr --gdbserver --device $(MCU) --clock-freq \
	$(DEBUG_MFREQ) --port $(DEBUG_PORT)
endif
	@$(WINSHELL) /c start avr-$(DEBUG_UI) --command=$(GDBINIT_FILE)

# Convert ELF to COFF for use in debugging / simulating in AVR Studio or VMLAB.
COFFCONVERT = $(OBJCOPY) --debugging
COFFCONVERT += --change-section-address .data-0x800000
COFFCONVERT += --change-section-address .bss-0x800000
COFFCONVERT += --change-section-address .noinit-0x800000
COFFCONVERT += --change-section-address .eeprom-0x810000

coff: $(TARGET).elf
	@echo
	@echo $(MSG_COFF) $(TARGET).cof
	$(COFFCONVERT) -O coff-avr $< $(TARGET).cof

extcoff: $(TARGET).elf
	@echo
	@echo $(MSG_EXTENDED_COFF) $(TARGET).cof
	$(COFFCONVERT) -O coff-ext-avr $< $(TARGET).cof

# Create final output files (.hex, .eep) from ELF output file.
%.hex: %.elf
	@echo
	@echo $(MSG_FLASH) $@
	$(OBJCOPY) -O $(FORMAT) -R .eeprom -R .fuse -R .lock $< $@

%.eep: %.elf
	@echo
	@echo $(MSG_EEPROM) $@
	-$(OBJCOPY) -j .eeprom --set-section-flags=.eeprom="alloc,load" \
	--change-section-lma .eeprom=0 --no-change-warnings -O $(FORMAT) $< $@ || exit 0

# Create extended listing file from ELF output file.
%.lss: %.elf
	@echo
	@echo $(MSG_EXTENDED_LISTING) $@
	$(OBJDUMP) -h -S -z $< > $@

# Create a symbol table from ELF output file.
%.sym: %.elf
	@echo
	@echo $(MSG_SYMBOL_TABLE) $@
	$(NM) -n $< > $@

# Create library from object files.
.SECONDARY : $(TARGET).a
.PRECIOUS : $(OBJ)
%.a: $(OBJ)
	@echo
	@echo $(MSG_CREATING_LIBRARY) $@
	$(AR) $@ $(OBJ)

# Link: create ELF output file from object files.
.SECONDARY : $(TARGET).elf
.PRECIOUS : $(OBJ)
%.elf: $(OBJ)
	@echo
	@echo $(MSG_LINKING) $@
	$(CC) $(ALL_CFLAGS) $^ --output $@ $(LDFLAGS)

# Compile: create object files from C source files.
$(OBJDIR)/%.o : %.c
	@echo
	@echo $(MSG_COMPILING) $<
	$(CC) -c $(ALL_CFLAGS) $< -o $@

# Compile: create object files from C++ source files.
$(OBJDIR)/%.o : %.cpp
	@echo
	@echo $(MSG_COMPILING_CPP) $<
	$(CC) -c $(ALL_CPPFLAGS) $< -o $@

# Compile: create assembler files from C source files.
%.s : %.c
	$(CC) -S $(ALL_CFLAGS) $< -o $@

# Compile: create assembler files from C++ source files.
%.s : %.cpp
	$(CC) -S $(ALL_CPPFLAGS) $< -o $@

# Assemble: create object files from assembler source files.
$(OBJDIR)/%.o : %.S
	@echo
	@echo $(MSG_ASSEMBLING) $<
	$(CC) -c $(ALL_ASFLAGS) $< -o $@

# Create preprocessed source for use in sending a bug report.
%.i : %.c
	$(CC) -E -mmcu=$(MCU) -I. $(CFLAGS) $< -o $@

scripts/tonegen.h: scripts/tonegen.tcl
	cd scripts; $(tclsh) tonegen.tcl

# Target: clean project.
clean: begin clean_list end

clean_list :
	@echo
	@echo $(MSG_CLEANING)
	$(REMOVE) $(TARGET).hex
	$(REMOVE) $(TARGET).eep
	$(REMOVE) $(TARGET).cof
	$(REMOVE) $(TARGET).elf
	$(REMOVE) $(TARGET).map
	$(REMOVE) $(TARGET).sym
	$(REMOVE) $(TARGET).lss
	$(REMOVE) $(SRC:%.c=$(OBJDIR)/%.o)
	$(REMOVE) $(SRC:%.c=$(OBJDIR)/%.lst)
	$(REMOVE) \#*
	$(REMOVE) *~
	$(REMOVE) $(SRC:.c=.s)
	$(REMOVE) $(SRC:.c=.d)
	$(REMOVE) $(SRC:.c=.i)
	$(REMOVEDIR) .dep

# Create object files directory
$(shell mkdir $(OBJDIR) 2>/dev/null)

# Include the dependency files.
-include $(shell mkdir .dep 2>/dev/null) $(wildcard .dep/*)

# Listing of phony targets.
.PHONY : all begin finish end sizebefore sizeafter gccversion \
build elf hex eep lss sym coff extcoff \
clean clean_list program debug gdb-config

