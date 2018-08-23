SECTIONS {
   .bss:     {}                      > IRAM
   .cinit:   {}                      > SDRAM
   .text:    {}                      > SDRAM
   .printf:  {}                      > IRAM
   .iram:    {}                      > IRAM
   .const:   {}                      > SDRAM
   .far:     {}                      > SDRAM
   .pinit:   {}                      > SDRAM
   .switch:  {}                      > SDRAM
   .interface: {}                    > IINT
   .dsp_data: {}                     > DSP_DATA
   .cio:     {}                      > SDRAM
}
