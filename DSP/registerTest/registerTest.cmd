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
}
