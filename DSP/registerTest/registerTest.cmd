SECTIONS {
   .bss:     {}                      > IRAM
   .cinit:   {}                      > SDRAM
   .text:    {}                      > SDRAM
   .printf:  {}                      > IRAM
   .const:   {}                      > SDRAM
   .far:     {}                      > IRAM
   .pinit:   {}                      > SDRAM
   .switch:  {}                      > SDRAM
   .interface: {}                    > IINT
   .dsp_data: {}                     > DSP_DATA
   .cio:     {}                      > SDRAM
}
