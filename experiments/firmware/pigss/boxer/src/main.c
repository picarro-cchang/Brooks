
#include <stdio.h>
#include <string.h>
#include <avr/interrupt.h>

// Convenience functions for busy-wait loops
#include <util/delay.h>

#include "functions.h"
#include "main.h"

// Functions for setting the system clock prescaler
#include "clock.h"

/* command.h

   Contains the extern declaration of command_array -- an array
   containing all the commands understood by the system.

   Defines the received command state structure recv_cmd_state_t.  Use
   this to keep track of the remote interface state. */
#include "command.h"
#include "usart.h"

/* pgmspace.h

   Contains macros and functions for saving and reading data out of
   flash.
*/
#include <avr/pgmspace.h>

/* logger.h

   Sets up logging
*/
#include "logger.h"

// Functions dealing with periodic interrupts
#include "metronome.h"

// Functions for setting SPI chip-selects
#include "cs.h"

// Functions for simple scheduling
#include "OS.h"



/* eeprom.h

   Provides functions for writing to and reading from the eeprom.
*/
// #include "eeprom.h"

/* led.h

   Provides functions for turning the LED on and off.
*/
#include "led.h"


// Provide support for i2c devices
#include "i2c.h"

/* Set the measurement array size.

   As things are now, this will also be the number of readings to
   average to create an output datum.  But this size can grow
   independent of the number of averages.
*/
#define MEASUREMENT_ARRAY_SIZE 4

/* This array will hold measurements made in the main loop.
 */
uint16_t measurement_array[MEASUREMENT_ARRAY_SIZE];

// Define a pointer to the received command state
recv_cmd_state_t  recv_cmd_state;
recv_cmd_state_t *recv_cmd_state_ptr = &recv_cmd_state;

int main() {

  sei(); // Enable interrupts

  // Set up the system clock.  Do this before setting up the USART,
  // as the USART depends on this for an accurate buad rate.
  fosc_16MHz();

  LED_init();

  //  Set up the USART before setting up the logger -- the logger uses
  //  the USART for output.
  usart_init();

  // Initialize the logger.  Note that nothing can be logged before
  // this line.  Also note that the logger won't be able to make error
  // sounds until sound_init() is called.
  logger_init();
  logger_setlevel(log_level_DEBUG);

  // Start the SPI chip-select module
  cs_init();

  // Start the SPI module
  spi_init();

  // Start the I2C module
  i2c_init();

  /* To configure the logger, first clear the logger enable register
     by disabling it with logger_disable().  Then set individual bits
     with logger_setsystem().
  */
  logger_disable(); // Disable logging from all systems
  

  // Enable logger system logging
  logger_setsystem( "logger" );

  // Enable metronome logging
  logger_setsystem( "metronome" );

  // Enable channel module logging
  logger_setsystem( "channel" );
  
  logger_setsystem( "rxchar" ); // Enable received character logging
  logger_setsystem( "command" ); // Enable command system logging
  logger_setsystem( "adc" ); // Enable adc module logging
  logger_setsystem( "sound" ); // Enable sound module logging
  logger_setsystem( "rtc" ); // Enable real time clock module logging
  logger_setsystem( "eeprom" ); // Enable eeprom module logging
  logger_setsystem( "cal" ); // Enable calibration module logging
  // logger_setsystem( "mcp79411" ); // Enable mcp79411 RTC logging
  logger_setsystem( "spi" );
  logger_setsystem( "ltc2601" );

  logger_setsystem( "lm75" );
  logger_setsystem( "main" );
  functions_init(); // Load the serial number
  // adc_init(); // Set the ADCs reference and SAR prescaler
  // adc_mux(4); // Set the ADC mux to channel 4

  
  
  
  // Start the metronome
  metronome_init();

  // Start the channel module
  channel_init();

  command_init( recv_cmd_state_ptr );

  // current_init();
  memset(measurement_array,0,MEASUREMENT_ARRAY_SIZE);


  // The main loop


  logger_msg_p("main", log_level_INFO, PSTR("Firmware version is %s\r\n"),
	       REVCODE);

  // Schedule some tasks
  OS_TaskCreate(&test_task, 1000, BLOCKED);

  for(;;) {
    // Process the parse buffer to look for commands loaded with the
    // received character ISR.
    command_process_pbuffer( recv_cmd_state_ptr, command_array );

    // Execute scheduled tasks
    OS_TaskExecution();
    

  }// end main for loop

} // end main

//*************************** Interrupts ***************************//

// Find the name of interrupt signals in iomxx0_1.h.

// See the naming convention outlined at
// http://www.nongnu.org/avr-libc/user-manual/group__avr__interrupts.html
// to make sure you don't use depricated names.

// Interrupt on character received via the USART
ISR(USART0_RX_vect) {
  // Write the received character to the buffer
  *(recv_cmd_state_ptr -> rbuffer_write_ptr) = UDR0;
  if (*(recv_cmd_state_ptr -> rbuffer_write_ptr) == '\r') {
    logger_msg_p("rxchar",log_level_ISR,
		 PSTR("Received a command terminator"));
    if ((recv_cmd_state_ptr -> rbuffer_count) == 0) {
      // We got a terminator, but the received character buffer is
      // empty.  The user is trying to clear the transmit and
      // receive queues.
      return;
    }
    else {
      if ((recv_cmd_state_ptr -> pbuffer_locked) == true) {
	// We got a terminator, and there are characters in the
	// received character buffer, but the parse buffer is locked.
	// This is bad -- we're receiving commands faster than we can
	// process them.
	logger_msg_p("rxchar",log_level_ERROR,
		     PSTR("Command process speed error!"));
	rbuffer_erase(recv_cmd_state_ptr);
	return;
      }
      else {
	// We got a terminator, and there are characters in the
	// received character buffer.  The parse buffer is
	// unlocked so terminate the received string and copy it
	// to the parse buffer.
	*(recv_cmd_state_ptr -> rbuffer_write_ptr) = '\0';
	strcpy((recv_cmd_state_ptr -> pbuffer),
	       (recv_cmd_state_ptr -> rbuffer));
	recv_cmd_state_ptr -> pbuffer_locked = true;
	logger_msg_p("rxchar",log_level_ISR,
		     PSTR("Parse buffer contains '%s'"),
		     (recv_cmd_state_ptr -> pbuffer));
	rbuffer_erase(recv_cmd_state_ptr);
	return;
      }
    }
  }
  else {
    // The character is not a command terminator.
    (recv_cmd_state_ptr -> rbuffer_count)++;
    logger_msg_p("rxchar",log_level_ISR,
		 PSTR("%c  <-- copied to receive buffer.  Received count is %d"),
		 *(recv_cmd_state_ptr -> rbuffer_write_ptr),
		 recv_cmd_state_ptr -> rbuffer_count);
    if ((recv_cmd_state_ptr -> rbuffer_count) >= (RECEIVE_BUFFER_SIZE-1)) {
      logger_msg_p("rxchar",log_level_ERROR,
		   PSTR("Received character number above limit"));
      rbuffer_erase(recv_cmd_state_ptr);
      return;
    }
    else {
      // Increment the write pointer
      (recv_cmd_state_ptr -> rbuffer_write_ptr)++;
    }
  }
  return;
}

