/* bx_logger.h
   
   Functions for handling log messages.
 */
#ifndef LOGGER_H
#define LOGGER_H

// Defines things like uint8_t
#include <stdint.h> 

// Provides boolean datatypes
#include <stdbool.h>

/* command.h 

   Contains the definition of command_arg_t -- the data type used to
   hold arguments to functions executed by remote commands.
   
 */
#include "command.h"

/* Define the maximum log message size 

   Remember that each character is 1 byte, and that we only have 1k of
   RAM.  50 bytes is a good number here.
*/
#define LOGGER_BUFFERSIZE 50
 
/* Each system_struct will describe one system.  Create an array of these
 * to define all systems recognized by the machine.  Each system can have
 * a unique bit in the logger configuration bitfield.  This bit controls
 * whether or not messages from that system will be printed. 
 */
typedef struct system_struct {
    char *name; // The name of the system
    uint8_t bitshift; // The system's location in the enable register
} logger_system_t;

// Log levels recognized by the logger.  Log messages must be tagged with
// one of these levels.  The messages will be sent to the output device
// if their level is at or above the logger's threshold. 
// 
// Use logger_setlevel() to set the level threshold.
typedef enum log_level {
    log_level_ISR,
    log_level_DEBUG,
    log_level_INFO,
    log_level_WARNING,
    log_level_ERROR
} logger_level_t;

/* Logging configuration structure

   Up to 32 unique systems can have logging enabled or disabled (there
   are 32 bits that can be toggled).  Systems can share bits, so you
   can have more than 32 systems total.
 */
typedef struct logger_config_struct { 
  uint32_t enable; /* Bitfield in which each bit enables or disables
		    * log messages from the system defined by an array
		    * of system_struct */
  logger_level_t loglevel; // Only display messages at or above this level
} log_config_t;


// Initialize the logging system to a set of defaults. 
//
// Arguments:
//   sound_state_ptr -- Pointer to the sound state structure
void logger_init( void );

/* Set the log level 
 * Messages with loglevels at or above this setting will be sent to the
 *     output device.
 */
void logger_setlevel( logger_level_t loglevel );

/* Function called by the remote command "loglev"
 
   Sets the logger's loglevel member.  If no level matches the user's
   parameter, issue an error and leave the level as it was.
*/
void cmd_loglevel( command_arg_t *command_arg_ptr );


// Set the corresponding bit in the logger enable bitfield.  This
// enables logging for that system.
//
// Return EXIT_FAILURE if the system wasn't found
//
// To log multiple systems, call logger_disable(), then call this
// function for each system you'd like to log.
//
// Arguments:
//   logsys -- Name of logger system to enable.
bool logger_setsystem( char *logsys );

/* Called by the remote command "logreg." Sets the logger configuration 
 * enable byte directly.  You have to know which systems correspond to 
 * which bitshifts to make use of this.
 */
void cmd_logreg( command_arg_t *command_arg_ptr );

/* Called by the remote command "logreg?" Returns the logger configuration
 * register value in hex.
 */
void cmd_logreg_q( command_arg_t *command_arg_ptr );

/* Turn off all logging. 
 */
void logger_disable( void );


/* logger_msg_p ( system, loglevel, message )

   The interface to the logging system.  Use this function to send log
   messages.
  
   The system name (logsys) is a freeform string that must match one
   of the system name strings defined in an array of system
   structures.
  
   loglevel is an enum defined above. 
  
   The message (logmsg) is a format string -- the log message payload.
   It must be located in flash memory.
*/
void logger_msg_p( char *logsys, logger_level_t loglevel,const char *logmsg, ... );



/* Decide if a message should be logged based on the logger configuration
 * and the message tag.  If it's enabled for logging, print: 
 * [The message severity] (The origin system) The message
 * 
 * Message severity tags:
 * [R] Interrupt service routine (ISR)
 * [I] Informational
 * [W] Warning
 * [E] Error
 */
void logger_system_filter( char *logsys, logger_level_t loglevel, char *logmsg );

/* Sends the final log message to the output device.  This function makes
 * the output device more modular.  The output chosen in the implementation
 * can be simply printf() for prototyping on a PC.
 */
void logger_output( char *logmsg );

#endif // End the include guard
