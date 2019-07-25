/* bx_command.c */

// ----------------------- Include files ------------------------------
#include <stdio.h>
#include <string.h>

/* pgmspace.h

   Provides macros and functions for saving and reading data out of
   flash. */
#include <avr/pgmspace.h>


/* command.h 
 
   Provides the extern declaration of command_array -- an array
   containing all the commands understood by the system. */
#include "command.h"


#include "system.h"

/* usart.h 

   Provides functions for transmitting characters over the usart. */
#include "usart.h"

/* ascii.h
 
   Provides lowstring() for converting strings to lower case. */
#include "ascii.h"

/* logger.h
 
   Provides logger_msg and logger_msg_p for log messages tagged with a
   system and severity. */
#include "logger.h"

/* numbers.h

   Provides ascii to number conversion. */
#include "numbers.h"

// Provides commands to work with the eeprom
#include "eeprom.h"

// Provides commands to work with channels
#include "channel.h"

// Provides commands to work with Topaz PCBs
#include "topaz.h"

// Provides commands to work with pressure sensors
#include "pressure.h"


/* Define the remote commands recognized by the system.
 */
command_t command_array[] = {
  // *IDN? -- Print the instrument identification string.
  {"*idn?",           // Name of the command
   "none",            // Argument type (none, hex16, uint16, sint16)
   0,                 // Maximum number of characters in argument
   &cmd_idn_q},       // Address of function to execute
  // *RST -- System reset
  {"*rst",
   "none",
   0,
   &cmd_rst},
  //loglev -- Set the logger severity level.
  {"loglev",
   "uint16",
   1,
   &cmd_loglevel},
  // logreg -- Set the logger enable register.
  {"logreg",
   "uint16",
   4,
   &cmd_logreg},
  // logreg? -- Query the logger enable register.
  {"logreg?",
   "none",
   0,
   &cmd_logreg_q},
  // sernum -- Set the system's serial number
  {"sernum",
   "uint16",
   5,
   &cmd_write_sernum},
  // chanena -- Enable channel n
  {"chanena",
   "uint16",
   1,
   &cmd_chanena},
  // chanena? -- Query the enable status of channel n
  {"chanena?",
   "uint16",
   1,
   &cmd_chanena_q},
  // chanoff -- Disable channel n
  {"chanoff",
   "uint16",
   1,
   &cmd_chanoff},
  // chanset -- Set the channel enable byte
  {"chanset",
   "uint16",
   3,
   &cmd_chanset},
  // chanset? -- Query the channel enable byte
  {"chanset?",
   "none",
   0,
   &cmd_chanset_q},
  // slotid -- Set the slot ID
  {"slotid",
   "uint16",
   1,
   &cmd_write_slotid},
  // slotid? -- Query the slot ID
  {"slotid?",
   "none",
   0,
   &cmd_slotid_q},
  // opstate? -- Query the operational state
  {"opstate?",
   "none",
   0,
   &cmd_opstate_q},
  // tza.sn -- Set the serial number for the Topaz A PCB
  {"tza.sn",
   "uint16",
   5,
   &cmd_topaz_a_set_serial_number},
  // tza.sn? -- Query the serial number for the Topaz A PCB
  {"tza.sn?",
   "none",
   0,
   &cmd_topaz_a_get_serial_number},
  // prs.out.raw? -- Query the raw counts from output pressure sensor 1 or 2
  {"prs.out.raw?",
   "uint16",
   1,
   &cmd_out_prs_raw_q},
  // prs.out.pas? -- Query the output pressure sensor 1 or 2 in Pascals
  {"prs.out.pas?",
   "uint16",
   1,
   &cmd_out_prs_pas_q},
  // End of table indicator.  Must be last.
  {"","",0,0}
};

/* Declare a structure to hold function arguments
 */
command_arg_t command_arg;
command_arg_t *command_arg_ptr = &command_arg;





// ----------------------- Functions ----------------------------------


/* command_init( received command state pointer ) 

   Making this function explicitly take a pointer to the received
   command state structure makes it clear that it modifies this
   structure.
 
*/
void command_init( recv_cmd_state_t *recv_cmd_state_ptr ) {
    memset((recv_cmd_state_ptr -> rbuffer),0,RECEIVE_BUFFER_SIZE);
    recv_cmd_state_ptr -> rbuffer_write_ptr =
        recv_cmd_state_ptr -> rbuffer; // Initialize write pointer
    memset((recv_cmd_state_ptr -> pbuffer),0,RECEIVE_BUFFER_SIZE);
    recv_cmd_state_ptr -> pbuffer_arg_ptr =
        recv_cmd_state_ptr -> pbuffer; // Initialize argument pointer
    recv_cmd_state_ptr -> rbuffer_count = 0;
    recv_cmd_state_ptr -> pbuffer_locked = false; // Parse buffer unlocked
    return;
}


/* check_argsize( pointer to received command state,
 *                pointer to list of commands )
 * Returns 0 if the argument size is less than or equal to the number
 * of characters specified in the command list.  Returns -1 otherwise. 
 */
uint8_t check_argsize(recv_cmd_state_t *recv_cmd_state_ptr ,
                      struct command_struct *command_array) {
    uint8_t isok = 0;
    uint8_t argsize = strlen(recv_cmd_state_ptr -> pbuffer_arg_ptr);
    logger_msg_p("command",log_level_INFO,
        PSTR("Argument size is %d"), argsize);
    if (argsize > (command_array -> arg_max_chars)) {
        isok = -1;
    }
    return isok;
}

void rbuffer_erase( recv_cmd_state_t *recv_cmd_state_ptr ) {
    memset((recv_cmd_state_ptr -> rbuffer),0,RECEIVE_BUFFER_SIZE);
    recv_cmd_state_ptr -> rbuffer_write_ptr =
        recv_cmd_state_ptr -> rbuffer; // Initialize write pointer
    recv_cmd_state_ptr -> rbuffer_count = 0;
    return;
}

void command_process_pbuffer( recv_cmd_state_t *recv_cmd_state_ptr ,
			      struct command_struct *command_array ) {
  // Process the commmand (if there is one) in the parse buffer.
  if ((recv_cmd_state_ptr -> pbuffer_locked) == true) {
    // Parse buffer is locked -- there's a command to process
    logger_msg_p("command",log_level_INFO,
		 PSTR("The parse buffer is locked."));
    recv_cmd_state_ptr -> pbuffer_arg_ptr = 
      strchr(recv_cmd_state_ptr -> pbuffer,' ');
    if (recv_cmd_state_ptr -> pbuffer_arg_ptr != NULL) {
      // Parse buffer contains a space -- there's an argument
      logger_msg_p("command",log_level_INFO,
		   PSTR("The command contains a space."));
      // Terminate the command string
      *(recv_cmd_state_ptr -> pbuffer_arg_ptr) = '\0';
      (recv_cmd_state_ptr -> pbuffer_arg_ptr)++;
      while (*(recv_cmd_state_ptr -> pbuffer_arg_ptr) == ' ') {
	// Move to first non-space character
	(recv_cmd_state_ptr -> pbuffer_arg_ptr)++;
      }
      // pbuffer_arg_ptr now points to the beginning of the argument
      logger_msg_p("command",log_level_INFO,
		   PSTR("The command's argument is '%s'."),
		   (recv_cmd_state_ptr -> pbuffer_arg_ptr));
    }
    // Convert command to lower case
    lowstring(recv_cmd_state_ptr -> pbuffer);
    // Look through the command list for a match
    uint8_t pbuffer_match = 0;
    while ((command_array -> execute) != 0) {
      if (strcmp( recv_cmd_state_ptr -> pbuffer,
		  command_array -> name ) == 0) {
	// We've found a matching command
	logger_msg_p("command",log_level_INFO,
		     PSTR("Command '%s' recognized."),command_array -> name);
	pbuffer_match = 1;
	if (strcmp( command_array -> arg_type, "none") != 0) {
	  // The command is specified to have an argument
	  uint8_t arg_ok = check_argsize(recv_cmd_state_ptr,command_array);
	  if (arg_ok != 0) {
	    // The argument is too large
	    logger_msg_p("command",log_level_ERROR,
			 PSTR("Argument to '%s' is out of range."),
			 command_array -> name);
	    command_nack(NACK_ARGUMENT_OUT_OF_RANGE);
	    return;
	  }
	  else {
	    // The argument is the right size
	    logger_msg_p("command",log_level_INFO,
			 PSTR("Argument to '%s' is within limits."),
			 command_array -> name);
	    command_exec(command_array,recv_cmd_state_ptr -> pbuffer_arg_ptr,
			 command_arg_ptr);
	  }
	}
	else  {
	  // There's no argument specified
	  if (recv_cmd_state_ptr -> pbuffer_arg_ptr != NULL) {
	    // There's an argument, but we didn't expect one
	    logger_msg_p("command",log_level_WARNING,
			 PSTR("Ignoring argument for command '%s'."),
			 command_array -> name);
	  }
	  command_exec(command_array,NULL,command_arg_ptr);
	}
	recv_cmd_state_ptr -> pbuffer_locked = false;
	break;
      }
      command_array++;
    }
    // If we didn't find a match, send an error message to the logger
    // and a NACK to the command interface.
    if (pbuffer_match == 0) {
      logger_msg_p("command",log_level_ERROR,
		   PSTR("Unrecognized command: '%s'."),
		   recv_cmd_state_ptr -> pbuffer);
      // usart_printf(USART_CHANNEL_COMMAND, "-1%s", LINE_TERMINATION_CHARACTERS);
      command_nack(NACK_COMMAND_NOT_RECOGNIZED);
      recv_cmd_state_ptr -> pbuffer_locked = false;
    }
  }
  return;
}


/* command_exec( remote command string, argument string,
                 command argument structure pointer )

   Execute a valid command received over the remote interface.  The
   command's arguments simply come in as strings.  The command's
   definition sets the argument type.  This function matches a string
   to that argument type string to figure out how to convert the
   argument string to a number.
*/
void command_exec( command_t *command, char *argument, 
		   command_arg_t *command_arg_ptr ) {
  if (strcmp( command -> arg_type,"none" ) == 0) {
    // There's no argument
    logger_msg_p("command",log_level_INFO,
		 PSTR("Executing command with no argument."));
    command -> execute(command_arg_ptr);
  }
  else if (strcmp( command -> arg_type,"hex16" ) == 0) {
    // There's a hex argument
    logger_msg_p("command",log_level_INFO,
		 PSTR("Executing command with hex argument."));
    command_arg_ptr -> uint16_arg = hex2num(argument);

    logger_msg_p("command",log_level_INFO,
		 PSTR("The argument value is %u."),
		 command_arg_ptr -> uint16_arg);

    command -> execute(command_arg_ptr);
  }
  else if (strcmp( command -> arg_type,"uint16" ) == 0) {
    // There's a unsigned 16-bit integer argument
    logger_msg_p("command",log_level_INFO,
		 PSTR("Executing command with unsigned int argument."));
    command_arg_ptr -> uint16_arg = uint2num(argument);
    command -> execute(command_arg_ptr);
  }
  else if (strcmp( command -> arg_type,"sint16" ) == 0) {
    // There's a signed 16-bit integer argument
    logger_msg_p("command",log_level_INFO,
		 PSTR("Executing command with signed int argument."));
    command_arg_ptr -> sint16_arg = sint2num(argument);
    command -> execute(command_arg_ptr);
  }
  /* If we've reached the end, we haven't found a match for the
     command's argument type.  That's an error.
   */
  else {
    logger_msg_p("command",log_level_ERROR,
		 PSTR("No handler specified for %s argument."),
		 command -> arg_type);
  }
}

void command_ack() {
  usart_printf(USART_CHANNEL_COMMAND, "0%s", LINE_TERMINATION_CHARACTERS);
}

void command_nack( int8_t nack_code ) {
  usart_printf(USART_CHANNEL_COMMAND, "%i%s", nack_code,
	       LINE_TERMINATION_CHARACTERS);
}
