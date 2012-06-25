/*
 * FILE:
 *   scopeHandler.h
 *
 * DESCRIPTION:
 *   Task which controls access to the ringdown buffers when the analyzer
 *  is in oscilloscope mode
 *
 * SEE ALSO:
 *   Specify any related information.
 *
 * HISTORY:
 *   16-Feb-2011  sze  Initial version.
 *
 *  Copyright (c) 2011 Picarro, Inc. All rights reserved
 */
#ifndef _SCOPE_HANDLER_H_
#define _SCOPE_HANDLER_H_

void getScopeTrace(void);
void releaseScopeTrace(void);
void scopeHandler(void);

#endif /* _SCOPE_HANDLER_H_ */
