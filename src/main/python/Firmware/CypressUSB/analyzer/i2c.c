#include <stdio.h>
#include <fx2.h>
#include <fx2regs.h>

I2CPCKT volatile	I2CPckt;

void EZUSB_InitI2C(void)
{
	I2CPckt.status = I2C_IDLE;

	EI2C = 1;	// Enable I2C interrupt				
	EA = 1;		// Enable 8051 interrupts
#ifdef TNG
   I2CMODE |= 0x02;  // enable I2C Stop interrupt
#endif

}

BOOL EZUSB_WriteI2C_(BYTE addr, BYTE length, BYTE xdata *dat)
{
#ifndef TNG
   // if in progress, wait for STOP to complete
   while (I2CS & bmSTOP);
#endif

	if(I2CPckt.status == I2C_IDLE)
	{	
		I2CS |= bmSTART;
		I2DAT = addr << 1;

		I2CPckt.length = length;
		I2CPckt.dat = dat;
		I2CPckt.count = 0;
		I2CPckt.status = I2C_SENDING;

		return(TRUE);
	}
	
	return(FALSE);
}

void i2c_isr(void) interrupt I2C_VECT
{													// I2C State Machine
	if(I2CS & bmBERR)
		I2CPckt.status = I2C_BERROR;
	else if ((!(I2CS & bmACK)) && (I2CPckt.status != I2C_RECEIVING))
		I2CPckt.status = I2C_NACK;
	else
		switch(I2CPckt.status)
		{
			case I2C_SENDING:
				I2DAT = I2CPckt.dat[I2CPckt.count++];
				if(I2CPckt.count == I2CPckt.length)
					I2CPckt.status = I2C_STOP;
				break;
			case I2C_PRIME:
				I2CPckt.dat[I2CPckt.count] = I2DAT;
				I2CPckt.status = I2C_RECEIVING;
				if(I2CPckt.length == 1) // may be only one byte read
					I2CS |= bmLASTRD;
				break;
			case I2C_RECEIVING:
				if(I2CPckt.count == I2CPckt.length - 2)
					I2CS |= bmLASTRD;
				if(I2CPckt.count == I2CPckt.length - 1)
				{
					I2CS |= bmSTOP;
					I2CPckt.status = I2C_IDLE;
				}
				I2CPckt.dat[I2CPckt.count] = I2DAT;
				++I2CPckt.count;
				break;
			case I2C_STOP:
				I2CS |= bmSTOP;
#ifdef TNG
				I2CPckt.status = I2C_WAITSTOP;
#else
				I2CPckt.status = I2C_IDLE;
#endif
				break;
			case I2C_WAITSTOP:
				I2CPckt.status = I2C_IDLE;
				break;
		}
	EXIF &= ~0x20;		// Clear interrupt flag IE3_ // IE3 = 0;
}

