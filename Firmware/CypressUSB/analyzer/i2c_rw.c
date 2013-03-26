#include <fx2.h>
#include <fx2regs.h>

BOOL EZUSB_WriteI2C(BYTE addr, BYTE length, BYTE xdata *dat)
{
	WORD i = 1;
	EZUSB_WriteI2C_(addr, length, dat);

	while (i) {
		switch(I2CPckt.status)
		{
			case I2C_IDLE:
				return(I2C_OK);
			case I2C_NACK:
				I2CPckt.status = I2C_IDLE;
				return(I2C_NACK);
			case I2C_BERROR:
				I2CPckt.status = I2C_IDLE;
				return(I2C_BERROR);
		}
		i++;
	}
	return -1;
}
