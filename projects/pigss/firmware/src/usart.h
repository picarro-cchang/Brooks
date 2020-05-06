/* bx_usart.h
 
   Used to set up the USART for the boxcom project. 
*/

/* stdint.h
 * Defines fixed-width integer types like uint8_t
 */
#include <stdint.h>


// Set baud rate
// |--------+-------+----+--------+--------|
// |   Baud | fosc  | 2x | UBRR0H | UBRR0L |
// |--------+-------+----+--------+--------|
// |   9600 | 16MHz |  0 |      0 |    103 |
// |  38400 | 16MHz |  0 |      0 |     25 |
// | 115200 | 16MHz |  0 |      0 |      8 |
// | 115200 | 16MHz |  1 |      0 |     16 |
// |--------+-------+----+--------+--------|
#define USART_UBRR 25

// Set double or single speed
#define USART_U2X 0

// Communication channels
typedef enum usart_channel {
  USART_CHANNEL_COMMAND,
  USART_CHANNEL_DEBUG
} usart_channel_t;

// Line termination characters
#define LINE_TERMINATION_CHARACTERS "\n"

// The maximum string length that can be sent as output over the
// command  or debug interfaces
#define PRINT_BUFFER_SIZE 150

// Declare a buffer for printing log and remote interface output over
// USB.  Make this extern so that we can use it in any source file
// that includes this file.
//
// Making this statically allocated makes the RAM footprint more
// predictable.
extern char PRINT_BUFFER[];


/* Send a format string to the USART interface 
 */
uint8_t usart_printf (usart_channel_t usart_channel, char *fmt, ...);

/* Send a format string stored in flash memory to the USART interface.
 */
uint8_t usart_printf_p(usart_channel_t usart_channel, const char *fmt, ...);

/* usart_receive
 * Simple USART receive function based on polling of the receive
 * complete (RXCn) flag.  The Butterfly has only one USART, so n will
 * always be zero.  The USART must be initialized before this can be used.
 *
 * The function simply waits for data to be present in the receive buffer
 * by checking the RXCn flag.  This flag is set when data is present. 
 */
unsigned char usart_receive(void);

/* usart_putc(char data)
 * Sends a character to the USART 
 */
void usart_putc(usart_channel_t usart_channel, char data);

/* usart_puts(char s[])
 * Sends a string over the USART by repeatedly calling usart_putc() 
 */
void usart_puts(usart_channel_t usart_channel, char s[]);

/* usart_puts_p(const char *data)
 * Sends strings stored in flash memory to the USART.
 */
void usart_puts_p(usart_channel_t usart_channel, const char *data);

/* usart_init() 

   Initialize the USART for 9600 baud, 8 data bits, 1
   stop bit, no parity checking.
*/
void usart_init(void);

/* usart_76k8_baud()

   Set the USART's baud rate to 76.8k baud.  This is a strange baud,
   and it won't be available with slower system clocks.  Call
   usart_init() before using this.
*/
void usart_76k8_baud(void);
