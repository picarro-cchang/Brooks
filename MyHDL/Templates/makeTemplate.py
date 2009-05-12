import sys
import os

def process(temp,regList,result):
    for reg in regList:
        result.append(temp.replace("@r@",reg).replace("@R@",reg.upper()).replace("@b@",blockName).replace("@B@",blockName.upper()))

blockName = os.path.splitext(sys.argv[1])[0]
regList = [s.strip() for s in file(blockName+".reg","r").readlines() if s.strip()]

result = []
process("from Host.autogen.interface import @B@_@R@",regList,result)
result.append("\n>>> Insert code here <<<\n")
process("    @b@_@r@_addr = map_base + @B@_@R@",regList,result)
result.append("    dsp_data_from_regs = Signal(intbv(0)[FPGA_REG_WIDTH:])")
process("    @r@ = Signal(intbv(0)[FPGA_REG_WIDTH:])",regList,result)
result.append("\n")
result.append("    @instance")
result.append("    def logic():")
result.append("        while True:")
result.append("            yield clk.posedge, reset.posedge")
result.append("            if reset:")
process(        "                @r@.next = 0",regList,result)
result.append("            else:")
result.append("                if dsp_addr[EMIF_ADDR_WIDTH-1] == FPGA_REG_MASK:")
result.append("                    if False: pass")
process(        "                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == @b@_@r@_addr:\n                        if dsp_wr: @r@.next = dsp_data_out\n                        dsp_data_from_regs.next = @r@",regList,result)
result.append("                    else:")
result.append("                        dsp_data_from_regs.next = 0")
result.append("                else:")
result.append("                    dsp_data_from_regs.next = 0")
#result.append("                if control[%s_CONTROL_RUN_B]:" % blockName.upper())
#result.append("                    if not control[%s_CONTROL_CONT_B]:" % blockName.upper())
#result.append("                        control.next[%s_CONTROL_RUN_B] = 0" % blockName.upper())
result.append("    return instances()")

file(blockName+".template","w").write("\n".join(result))
