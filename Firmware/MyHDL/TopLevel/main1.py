from myhdl import *
from Host.autogen.interface import *

LOW, HIGH = bool(0), bool(1)

def main(clk0,clk180,clk3f,clk3f180,clk_locked,
         reset,intronix,fpga_led,
         dsp_emif_we,dsp_emif_re,dsp_emif_oe,dsp_emif_ardy,
         dsp_emif_ea,dsp_emif_din, dsp_emif_dout,
         dsp_emif_ddir, dsp_emif_be, dsp_emif_ce,
         i2c_rst0, i2c_rst1,
         i2c_scl0, i2c_sda0, i2c_scl1, i2c_sda1,
         rd_adc, rd_adc_clk, rd_adc_oe):

    NSTAGES = 28
    counter = Signal(intbv(0)[NSTAGES:])

    @instance
    def  logic():
        while True:
            yield clk0.posedge, reset.posedge
            if reset:
                counter.next = 0
            else:
                counter.next = counter + 1

    @always_comb
    def  comb():
        intronix.next[16:] = rd_adc
        rd_adc_clk.next = counter[0]
        rd_adc_oe.next = 1
        fpga_led.next = counter[NSTAGES:NSTAGES-4]
        dsp_emif_ardy.next = 1   # Ensure DSP can continue
        dsp_emif_ddir.next = 0   # DSP writes to dsp_emif_dout
        dsp_emif_din.next = 0
        i2c_rst0.next = reset
        i2c_rst1.next = reset
        intronix.next[28] = i2c_scl0
        intronix.next[29] = i2c_sda0
        intronix.next[30] = i2c_scl1
        intronix.next[31] = i2c_sda1
        intronix.next[32] = reset
        intronix.next[33] = clk0

    return instances()

# Clock generator
clk0, clk180, clk3f, clk3f180, clk_locked = \
    [Signal(LOW) for i in range(5)]
# Reset
reset = Signal(LOW)
# Mictor connector to Intronix probe
intronix = Signal(intbv(0)[34:])
# FPGA LEDS
fpga_led = Signal(intbv(0)[4:])
# DSP EMIF signals
dsp_emif_we, dsp_emif_re, dsp_emif_oe, dsp_emif_ddir, dsp_emif_ardy =  \
    [Signal(LOW) for i in range(5)]
dsp_emif_ea = Signal(intbv(0)[EMIF_ADDR_WIDTH:])
dsp_emif_din = Signal(intbv(0)[EMIF_DATA_WIDTH:])
dsp_emif_dout = Signal(intbv(0)[EMIF_DATA_WIDTH:])
dsp_emif_be = Signal(intbv(0)[4:])
dsp_emif_ce = Signal(intbv(0)[4:])
i2c_rst0, i2c_rst1 = [Signal(LOW) for i in range(2)]
i2c_scl0, i2c_sda0, i2c_scl1, i2c_sda1 = [Signal(LOW) for i in range(4)]
rd_adc = Signal(intbv(0)[16:])
rd_adc_clk, rd_adc_oe = [Signal(LOW) for i in range(2)]

def makeVHDL():
    toVHDL(main,clk0,clk180,clk3f,clk3f180,clk_locked,reset,
                intronix,fpga_led,dsp_emif_we,dsp_emif_re,
                dsp_emif_oe,dsp_emif_ardy,dsp_emif_ea,dsp_emif_din,
                dsp_emif_dout,dsp_emif_ddir, dsp_emif_be, dsp_emif_ce,
                i2c_rst0, i2c_rst1,
                i2c_scl0, i2c_sda0, i2c_scl1, i2c_sda1,
                rd_adc, rd_adc_clk, rd_adc_oe)

if __name__ == "__main__":
    makeVHDL()
