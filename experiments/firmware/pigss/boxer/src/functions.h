
#ifndef FUN_H
#define FUN_H

/* command.h 

   Contains the definition of command_t -- the variable type containing
   the attributes of each remote command. */
#include "command.h"


// Overall system state structure
typedef struct system_status_struct {
  uint16_t sernum;
} system_state_t;


/* cmd_idn_q( pointer to command argument structure )

   The function called by the "*IDN?" query
*/
void cmd_idn_q( command_arg_t *command_arg_ptr );

/* functions_init()

   Calls cal_load_sernum(pointer to system status structure) to fill
   in the serial number.
*/
void functions_init( void );

#endif // End the include guard
