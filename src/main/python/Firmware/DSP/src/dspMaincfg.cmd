/*   Do *not* directly modify this file.  It was    */
/*   generated by the Configuration Tool; any  */
/*   changes risk being overwritten.                */

/* INPUT dspMain.cdb */

/* MODULE PARAMETERS */
-u _GBL_setPLLto225MHz
GBL_USERINITFXN = _GBL_setPLLto225MHz;

-u SDRAM
MEM_SEGZERO = SDRAM;
-u SDRAM
MEM_MALLOCSEG = SDRAM;

-u CLK_F_getshtime
CLK_TIMEFXN = CLK_F_getshtime;
-u HWI_F_dispatch
CLK_HOOKFXN = HWI_F_dispatch;

-u _KNL_tick
PRD_THOOKFXN = _KNL_tick;

-u IRAM
RTDX_DATAMEMSEG = IRAM;

-u IRAM
HST_DSMBUFSEG = IRAM;

-u GBL_NULL
SWI_EHOOKFXN = GBL_NULL;
-u GBL_NULL
SWI_IHOOKFXN = GBL_NULL;
-u SWI_F_exec
SWI_EXECFXN = SWI_F_exec;
-u SWI_F_run
SWI_RUNFXN = SWI_F_run;

-u MEM_NULL
TSK_STACKSEG = MEM_NULL;
-u _FXN_F_nop
TSK_VCREATEFXN = _FXN_F_nop;
-u _FXN_F_nop
TSK_VDELETEFXN = _FXN_F_nop;
-u _FXN_F_nop
TSK_VEXITFXN = _FXN_F_nop;

-u IDL_F_stub
IDL_CALIBRFXN = IDL_F_stub;

-u _UTL_doAbort
SYS_ABORTFXN = _UTL_doAbort;
-u _UTL_doError
SYS_ERRORFXN = _UTL_doError;
-u _UTL_halt
SYS_EXITFXN = _UTL_halt;
-u _UTL_doPutc
SYS_PUTCFXN = _UTL_doPutc;

-u _FXN_F_nop
GIO_CREATEFXN = _FXN_F_nop;
-u _FXN_F_nop
GIO_DELETEFXN = _FXN_F_nop;
-u _FXN_F_nop
GIO_PENDFXN = _FXN_F_nop;
-u _FXN_F_nop
GIO_POSTFXN = _FXN_F_nop;

/* OBJECT ALIASES */
_SDRAM = SDRAM;
_IRAM = IRAM;
_DSP_DATA = DSP_DATA;
_IINT = IINT;
_PRD_clock = PRD_clock;
_PRD_scheduler = PRD_scheduler;
_PRD_sentryHandler = PRD_sentryHandler;
_PRD_timeStamp = PRD_timeStamp;
_RTA_fromHost = RTA_fromHost;
_RTA_toHost = RTA_toHost;
_HWI_RESET = HWI_RESET;
_HWI_NMI = HWI_NMI;
_HWI_RESERVED0 = HWI_RESERVED0;
_HWI_RESERVED1 = HWI_RESERVED1;
_HWI_INT4 = HWI_INT4;
_HWI_INT5 = HWI_INT5;
_HWI_INT6 = HWI_INT6;
_HWI_INT7 = HWI_INT7;
_HWI_INT8 = HWI_INT8;
_HWI_INT9 = HWI_INT9;
_HWI_INT10 = HWI_INT10;
_HWI_INT11 = HWI_INT11;
_HWI_INT12 = HWI_INT12;
_HWI_INT13 = HWI_INT13;
_HWI_INT14 = HWI_INT14;
_HWI_INT15 = HWI_INT15;
_KNL_swi = KNL_swi;
_PRD_swi = PRD_swi;
_TSK_idle = TSK_idle;
_TSK_scheduler = TSK_scheduler;
_TSK_rdFitting = TSK_rdFitting;
_TSK_rdDataMoving = TSK_rdDataMoving;
_TSK_spectCntrl = TSK_spectCntrl;
_TSK_sentryHandler = TSK_sentryHandler;
_TSK_scopeHandler = TSK_scopeHandler;
_IDL_cpuLoad = IDL_cpuLoad;
_LNK_dataPump = LNK_dataPump;
_RTA_dispatcher = RTA_dispatcher;
_LOG_system = LOG_system;
_trace = trace;
_SEM_scheduler = SEM_scheduler;
_SEM_rdFitting = SEM_rdFitting;
_SEM_rdDataMoving = SEM_rdDataMoving;
_SEM_rdBuffer0Available = SEM_rdBuffer0Available;
_SEM_rdBuffer1Available = SEM_rdBuffer1Available;
_SEM_startRdCycle = SEM_startRdCycle;
_SEM_waitForRdMan = SEM_waitForRdMan;
_SEM_sentryHandler = SEM_sentryHandler;
_SEM_hpiIntBackend = SEM_hpiIntBackend;
_SEM_wfmAvailable = SEM_wfmAvailable;
_LCK_scopeBuffer = LCK_scopeBuffer;
_IDL_busyObj = IDL_busyObj;

/* MODULE GBL */

SECTIONS {
   .vers (COPY): {} /* version information */
}

-priority
--trampolines
-llnkrtdx.a67
-ldrivers.a67          /* device drivers support */
-lsioboth.a67          /* supports both SIO models */
-lbiosC6000.a67        /* BIOS clock specific library */
-lbios6x1x.a67         /* BIOS c6x1x specific library */
-lbios.a67             /* DSP/BIOS support */
-lrtdx.lib             /* RTDX support */
-lrts6700.lib          /* C and C++ run-time library support */

_GBL_CACHE = GBL_CACHE;

/* MODULE MEM */
-stack 0x400
MEMORY {
   SDRAM       : origin = 0x80000000,  len = 0x800000
   IRAM        : origin = 0x0,         len = 0x10000
   DSP_DATA    : origin = 0x80800000,  len = 0x800000
   IINT        : origin = 0x10000,     len = 0x20000
}
/* MODULE CLK */
SECTIONS {
   .clk: {
        
        CLK_F_gethtime = CLK_F_getshtime;
        CLK_A_TABBEG = .;
        *(.clk)
        CLK_A_TABEND = .;
        CLK_A_TABLEN = (. - CLK_A_TABBEG) / 4;
   } > IRAM 
}
_CLK_PRD = CLK_PRD;
_CLK_COUNTSPMS = CLK_COUNTSPMS;
_CLK_REGS = CLK_REGS;
_CLK_USETIMER = CLK_USETIMER;
_CLK_TIMERNUM = CLK_TIMERNUM;
_CLK_TDDR = CLK_TDDR;

/* MODULE PRD */
SECTIONS {
   .prd: {
        PRD_A_TABBEG = .;
        *(.prd)
        PRD_A_TABEND = .;
        PRD_A_TABLEN = (. - PRD_A_TABBEG) / 32;
   } > IRAM
}

/* MODULE RTDX */
_RTDX_interrupt_mask = 0x0;

/* MODULE HST */
_LNK_dspFrameReadyMask = LNK_dspFrameReadyMask; 
_LNK_dspFrameRequestMask = LNK_dspFrameRequestMask; 
_LNK_readDone = LNK_readDone; 
_LNK_readFail = LNK_readFail; 
_LNK_readPend = LNK_readPend; 
_LNK_writeFail = LNK_writeFail;
/* MODULE HWI */
SECTIONS {
    .hwi_vec: 0x0 {
        HWI_A_VECS = .;
        *(.hwi_vec)
    }
}

_HWI_CFGDISPATCHED = HWI_CFGDISPATCHED;

/* MODULE SWI */
SECTIONS {
   .swi: {
        SWI_A_TABBEG = .;
        *(.swi)
        SWI_A_TABEND = .;
        SWI_A_TABLEN = (. - SWI_A_TABBEG) / 44;
   } > IRAM
}

/* MODULE TSK */
SECTIONS {
   .tsk: {
        TSK_A_TABBEG = .;
        *(.tsk)
        TSK_A_TABEND = .;
        TSK_A_TABLEN = (. - TSK_A_TABBEG) / 96;
   } > IRAM
}

/* MODULE IDL */
SECTIONS {
   .idl: {
        IDL_A_TABBEG = .;
        *(.idl)
        IDL_A_TABEND = .;
        IDL_A_TABLEN = (. - IDL_A_TABBEG) / 4;
        IDL_A_CALBEG = .;
        *(.idlcal)
        IDL_A_CALEND = .;
        IDL_A_CALLEN = (. - IDL_A_CALBEG) / 4;
   } > IRAM
}



SECTIONS {
        .sysdata: {} > IRAM

        .dsm: {} > IRAM

        .lck: {} > IRAM

        .sem: {} > IRAM

        .mem: 	  {} > IRAM

        .bios:    {} > IRAM

        .gio:     {} > IRAM

        .sys:     {} > IRAM

        .sysregs: {} > IRAM

        .gblinit:    {} > IRAM

        .sysinit:    {} > IRAM

        .trcdata:    {} > IRAM

        .hwi: {}  > IRAM

        .rtdx_data: {}  > IRAM

        .rtdx_text: {}  > IRAM

        .TSK_idle$stk: {
            *(.TSK_idle$stk)
        } > IRAM

        .TSK_scheduler$stk: {
            *(.TSK_scheduler$stk)
        } > IRAM

        .TSK_rdFitting$stk: {
            *(.TSK_rdFitting$stk)
        } > IRAM

        .TSK_rdDataMoving$stk: {
            *(.TSK_rdDataMoving$stk)
        } > IRAM

        .TSK_spectCntrl$stk: {
            *(.TSK_spectCntrl$stk)
        } > IRAM

        .TSK_sentryHandler$stk: {
            *(.TSK_sentryHandler$stk)
        } > IRAM

        .TSK_scopeHandler$stk: {
            *(.TSK_scopeHandler$stk)
        } > IRAM

        /* LOG_system buffer */
        .LOG_system$buf: align = 0x100 {} > IRAM

        /* trace buffer */
        .trace$buf: align = 0x100 {} > IRAM

       /* RTA_fromHost buffer */
       .hst1: align = 0x4 {} > IRAM

       /* RTA_toHost buffer */
       .hst0: align = 0x4 {} > IRAM

        .args: align=4 fill=0 {
            *(.args)
            . += 0x4;
        } > IRAM

        .trace: fill = 0x0  align = 0x4 {
           _SYS_PUTCBEG = .;
           . += 0x200;
           _SYS_PUTCEND = . - 1;
        } > IRAM

        .stack: {
            GBL_stackbeg = .;
            *(.stack)
            GBL_stackend = GBL_stackbeg + 0x400 - 1;
            _HWI_STKBOTTOM = GBL_stackbeg + 0x400 - 4 & ~7;
            _HWI_STKTOP = GBL_stackbeg;
        } > IRAM

        .hst: {
             HST_A_TABBEG = .;
            _HST_A_TABBEG = .;
            *(.hst)
            HST_A_TABEND = .;
            _HST_A_TABEND = .;
             HST_A_TABLEN = (. - _HST_A_TABBEG) / 20;
            _HST_A_TABLEN = (. - _HST_A_TABBEG) / 20;
        } > IRAM

        .log: {
             LOG_A_TABBEG = .;
            _LOG_A_TABBEG = .;
            *(.log)
            LOG_A_TABEND = .;
            _LOG_A_TABEND = .;
             LOG_A_TABLEN = (. - _LOG_A_TABBEG) / 24;
            _LOG_A_TABLEN = (. - _LOG_A_TABBEG) / 24;
        } > IRAM

        .pip: {
             PIP_A_TABBEG = .;
            _PIP_A_TABBEG = .;
            *(.pip)
            PIP_A_TABEND = .;
            _PIP_A_TABEND = .;
             PIP_A_TABLEN = (. - _PIP_A_TABBEG) / 100;
            _PIP_A_TABLEN = (. - _PIP_A_TABBEG) / 100;
        } > IRAM

        .sts: {
             STS_A_TABBEG = .;
            _STS_A_TABBEG = .;
            *(.sts)
            STS_A_TABEND = .;
            _STS_A_TABEND = .;
             STS_A_TABLEN = (. - _STS_A_TABBEG) / 16;
            _STS_A_TABLEN = (. - _STS_A_TABBEG) / 16;
        } > IRAM

        .SDRAM$heap: {
            SDRAM$B = .;
            _SDRAM_base = .;
            SDRAM$L = 0x8000;
            _SDRAM_length = 0x8000;
            . += 0x8000;
        } > SDRAM

}
