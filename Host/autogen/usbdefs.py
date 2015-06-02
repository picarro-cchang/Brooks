IOC = 'Cypress port C'
IOE = 'Cypress port E'
USB_VERSION = 1001
CYPRESS_FX2_VID = 0x4B4
CYPRESS_FX2_PID = 0x8613
INITIAL_VID = 0x3EF
INITIAL_PID = 0x1000
INSTRUMENT_VID = 0x3EF
INSTRUMENT_PID = 0x1001
VENDOR_GET_VERSION = 0xB0
VENDOR_FPGA_CONFIGURE = 0xC0
VENDOR_READ_HPIC = 0xC1
VENDOR_WRITE_HPIC = 0xC2
VENDOR_READ_HPIA = 0xC3
VENDOR_WRITE_HPIA = 0xC4
VENDOR_SET_HPID_IN_BYTES = 0xC5
VENDOR_RESET_HPID_IN_FIFO = 0xC6
VENDOR_GET_STATUS = 0xC7
VENDOR_DSP_CONTROL = 0xC8
VENDOR_SET_DAC = 0xC9
VENDOR_DAC_QUEUE_CONTROL = 0xCA
VENDOR_DAC_QUEUE_STATUS = 0xCB
VENDOR_DAC_ENQUEUE_DATA = 0xCC
FPGA_START_PROGRAM = 0x01
FPGA_SEND_DATA = 0x02
FPGA_GET_STATUS = 0x03
USB_STATUS_SPEED = 0x01
USB_STATUS_GPIFTRIG = 0x02
USB_STATUS_GPIFTC = 0x03
VENDOR_DSP_CONTROL_RESET = 0x01
VENDOR_DSP_CONTROL_HINT = 0x02
DAC_QUEUE_RESET = 0x01
DAC_QUEUE_SERVE = 0x02
DAC_QUEUE_SET_PERIOD = 0x03
DAC_SET_TIMESTAMP = 0x04
DAC_SET_RELOAD_COUNT = 0x05
DAC_QUEUE_GET_FREE = 0x01
DAC_QUEUE_GET_ERRORS = 0x02
DAC_GET_TIMESTAMP = 0x03
DAC_GET_RELOAD_COUNT = 0x04
IO_FPGA_CONF = IOE
CYP_LED0 = 0x01
CYP_LED1 = 0x02
CYP_LED2 = 0x80
FPGA_SS_CCLK = 0x04
FPGA_SS_DIN = 0x08
FPGA_SS_PROG = 0x10
FPGA_SS_INIT = 0x20
FPGA_SS_DONE = 0x40
CYP_LED3 = 0x10
DAC_QUEUE_OVERFLOW = 0x1
DAC_QUEUE_UNDERFLOW = 0x2