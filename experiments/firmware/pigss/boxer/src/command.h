
#ifndef COMMAND_H
#define COMMAND_H

// Provides boolean datatypes
#include <stdbool.h>

// Received character (and parse) buffer size
// 
// Define the size of the received character buffer.  This buffer must
// be big enough to hold the biggest remote command along with its
// biggest argument and a space between the two.
// 
// The parse buffer will also be made this size, since I don't allow
// received commands to pile up -- they have to be processed one at a
// time.
#define RECEIVE_BUFFER_SIZE 20

// NACK return codes
#define NACK_COMMAND_NOT_RECOGNIZED -1
#define NACK_SYSTEM_BUSY -2
#define NACK_COMMAND_FAILED -3
#define NACK_BUFFER_OVERFLOW -4
#define NACK_ARGUMENT_OUT_OF_RANGE -5


/* Define the received command state structure.
  
   A structure of this type must be instantiated in the file
   containing main() so that it can work with the received character
   ISR.
 
*/
typedef struct recv_cmd_struct { 
    char rbuffer[RECEIVE_BUFFER_SIZE]; // Received character buffer
    /* rbuffer_write_ptr will always point to the next write location
     * in the received character buffer. */
    char *rbuffer_write_ptr;
    /* Properly terminated strings will wait in the parse buffer to be
     * processed.  These strings may or may not have one argument, separated
     * from the command by 1 or a few spaces (the entire string isn't
     * allowed to exceed the buffer size).  Since I don't queue up commands,
     * this buffer can be the same size as the received character buffer. */
    char pbuffer[RECEIVE_BUFFER_SIZE];
    char *pbuffer_arg_ptr; // Points to the beginning of the argument
    uint8_t rbuffer_count; // Counts up as characters go into receive buffer.
    bool pbuffer_locked; // Parse buffer locked.  true = locked
} recv_cmd_state_t;

/* Define a remote command argument structure

   This makes dealing with remote commands more flexible, in that
   functions called by remote commands need only accept pointer to
   remote command argument types, instead of some fixed type like int.

*/
typedef struct command_arg_struct {
  uint16_t uint16_arg; // Signed 16-bit
  int16_t sint16_arg; // Unsigned 16-bit
} command_arg_t;


/* Define a pointer to a function called by a remote command.
  
   In order to make all functions called by remote commands take the
   same arguments, we settle on them all taking a 16-bit argument.
   Functions called by remote commands should be prefixed by 'cmd_' to
   make the reason for their argument type clear.
*/
typedef void (*fpointer_t)(command_arg_t *command_arg_ptr);


/* Define a remote command structure 
 */
typedef struct command_struct {
  char *name; // The name of the command
  char *arg_type; // A string representing the type of argument expected
  uint8_t arg_max_chars; // The maximum number of characters in the argument
  fpointer_t execute; // The function to execute
} command_t;


/* The array of command structures will have global scope.  The
   variable command_array should be initialized in command.c
*/
extern command_t command_array[];


/* command_init()
 * Initialize the received command state: Erase the buffers, reset
 * the write and argument pointers, zero the received character
 * counter, and unlock the parse buffer. 
 */
void command_init( recv_cmd_state_t *recv_cmd_state_ptr );

/* Execute a valid command received over the remote interface.
 */
void command_exec( command_t *command, char *argument,
		   command_arg_t *command_arg_ptr);


/* check_argsize( pointer to received command state,
 *                pointer to list of commands )
 * Returns 0 if the argument size is less than or equal to the number
 * of characters specified in the command list.  Returns -1 otherwise. */
uint8_t check_argsize(recv_cmd_state_t *recv_cmd_state_ptr ,
                  struct command_struct *command_array);

void command_process_pbuffer( recv_cmd_state_t *recv_cmd_state_ptr ,
			      struct command_struct *command_array );
                    
/* Erases the received character buffer, resets the received character
 * number, and resets the write pointer. */
void rbuffer_erase( recv_cmd_state_t *recv_cmd_state_ptr );

// Send an acknowledge signal
void command_ack( void );

// Send a non-acknowledged signal
//
// Arguments:
//   nack_code -- Negative integer corresponding to failure condition
void command_nack( int8_t nack_code );

#endif // End the include guard
