
#include <stdio.h>

/* stdarg.h
 * Allows functions to accept an indefinite number of arguments.
 */
#include <stdarg.h>

/* avr/io.h
 * Device-specific port definitions
 */
#include <avr/io.h>

/* pgmspace.h
 * Contains macros and functions for saving and reading data out of
 * flash.
 */
#include <avr/pgmspace.h>
#include "usart.h"

// Any file that includes usart.h will have access to PRINT_BUFFER
char PRINT_BUFFER[PRINT_BUFFER_SIZE];

/* Send a format string and parameter to the USART. 
 */
uint8_t usart_printf (usart_channel_t usart_channel, char *fmt, ...) { 
    va_list args; 

    va_start (args, fmt); 

    /* For this to work, printbuffer must be larger than 
    * anything we ever want to print. 
    */ 
    vsnprintf (PRINT_BUFFER, PRINT_BUFFER_SIZE, fmt, args);
    va_end (args); 

    /* Print the string */ 
    usart_puts(usart_channel, PRINT_BUFFER); 
    return 0; 
}

/* usart_printf_p() 

   Send a format string stored in flash memory to the USART.
*/
uint8_t usart_printf_p(usart_channel_t usart_channel, const char *fmt, ...) {
  va_list args; 

  va_start (args, fmt); 
  // To avoid truncating output, PRINT_BUFFER_SIZE must be larger than
  // anything we ever want to print.
   
  vsnprintf_P (PRINT_BUFFER , PRINT_BUFFER_SIZE, fmt, args); 
  va_end (args);

  // Print the buffer
  usart_puts(usart_channel, PRINT_BUFFER);
  return 0; 
}    

 

/* usart_receive
 * Simple USART receive function based on polling of the receive
 * complete (RXCn) flag.  The Butterfly has only one USART, so n will
 * always be zero.  The USART must be initialized before this can be used.
 *
 * The function simply waits for data to be present in the receive buffer
 * by checking the RXCn flag.  This flag is set when data is present. 
 */
unsigned char usart_receive(void) {
    while( !(UCSR0A & (1<<RXC0)));
    return UDR0;
}

// Send a character to the USART
void usart_putc(usart_channel_t usart_channel, char data) {
  switch(usart_channel) {
  case USART_CHANNEL_COMMAND:
    // Wait for empty transmit buffer
    loop_until_bit_is_set(UCSR0A,UDRE0);
    // Put data into buffer -- sends the data
    UDR0 = data;
    break;
  case USART_CHANNEL_DEBUG:
    // Wait for empty transmit buffer
    loop_until_bit_is_set(UCSR3A,UDRE3);
    // Put data into buffer -- sends the data
    UDR3 = data;
    break;
  } 
}

// Sends a string over the USART by repeatedly calling usart_putc() 
void usart_puts(usart_channel_t usart_channel, char *data_ptr) {
  uint8_t i = 0;
  while(i < PRINT_BUFFER_SIZE) // don't get stuck if it is a bad string
    {
      if( data_ptr[i] == '\0' ) break; // quit on string terminator
      usart_putc(usart_channel, data_ptr[i++]);
    }
}

/* usart_puts_p(const char *data)
 * Sends strings stored in flash memory to the usart.
 */
void usart_puts_p(usart_channel_t usart_channel, const char *data_ptr) {
    uint8_t txdata = 1; // Dummy initialization value
    while ( txdata != 0x00 ) {
        txdata = pgm_read_byte(data_ptr);
        usart_putc(usart_channel, txdata);
        data_ptr++;
    }
}


void usart_init() {
  // Initialize the USART.  The ATmega2560 has 4 USARTs, and we'll use
  // two as normal asynchronous serial interfaces.  Both will run at
  // the same speed.
  //
  // USART0 -- command interface
  // USART3 -- debug interface
  

  // Set the USART baudrate registers. UBRR is a 12-bit register, so
  // it has a high and a low byte.
  // 


  //**************************** USART0 ****************************//

  // Set speed mode and the desired baud rate
  if ( USART_U2X ) {
    // Set double speed
    UCSR0A |= _BV(U2X0); 
  } else {
    // Set single speed
    UCSR0A &= ~(_BV(U2X0));
  }
  UBRR0H = 0;
  UBRR0L = USART_UBRR;

  // Enable receiver and transmitter
  UCSR0B = _BV(RXEN0) | _BV(TXEN0);

  // Set asynchronous mode
  UCSR0C &= ~(_BV(UMSEL00)) & ~(_BV(UMSEL01));

  // Set no parity checking
  UCSR0C &= ~(_BV(UPM00)) & ~(_BV(UPM01));

  // Set 1 stop bit
  UCSR0C &= ~(_BV(USBS0));
  
  // Set 8 data bits
  UCSR0C &= ~(_BV(UCSZ02));
  UCSR0C |= _BV(UCSZ01) | _BV(UCSZ00);

  // Enable received character interrupts (command interface only)
  UCSR0B |= _BV(RXCIE0);

  //**************************** USART3 ****************************//

  // Set speed mode and the desired baud rate
  if ( USART_U2X ) {
    // Set double speed
    UCSR3A |= _BV(U2X3); 
  } else {
    // Set single speed
    UCSR3A &= ~(_BV(U2X3));
  }
  UBRR3H = 0;
  UBRR3L = USART_UBRR;

  // Enable receiver and transmitter
  UCSR3B = _BV(RXEN3) | _BV(TXEN3);

  // Set asynchronous mode
  UCSR3C &= ~(_BV(UMSEL30)) & ~(_BV(UMSEL31));

  // Set no parity checking
  UCSR3C &= ~(_BV(UPM30)) & ~(_BV(UPM31));

  // Set 1 stop bit
  UCSR3C &= ~(_BV(USBS3));
  
  // Set 8 data bits
  UCSR3C &= ~(_BV(UCSZ32));
  UCSR3C |= _BV(UCSZ31) | _BV(UCSZ30);
}

/* usart_76k8_baud()

   Set the USART's baud rate to 76.8k baud.  This is a strange baud,
   and it won't be available with slower system clocks.  Call
   usart_init() before using this.
*/
void usart_76k8_baud() {
  /* Set the USART baudrate registers for 76.8k.  With double speed
     operation enabled:
       
     fosc  UBRR0H  UBRROL
     --------------------
     8MHz    0        12
  */
  UBRR0H = 0;
  UBRR0L = 12;
} // end usart_76k8_baud
  
