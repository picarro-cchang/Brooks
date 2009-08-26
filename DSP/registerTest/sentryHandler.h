/*
 * FILE:
 *   sentryHandler.h
 *
 * DESCRIPTION:
 *   Routines to manage sentries and place the instrument in a safe state under
 *    various error conditions. This is a high priority task executed periodically
 *    under the control of a semaphore posted by a PRD.
 * 
 *   We detect problems with the scheduler thread being unable to run as well as
 *    sentry breaches. Since the scheduler thread is responsible for updating the
 *    sensor values, its failure to run correctly is more serious than a sentry
 *    being breached.
 *
 * SEE ALSO:
 *   Specify any related information.
 *
 * HISTORY:
 *   25-Aug-2009  sze  Initial version.
 *
 *  Copyright (c) 2009 Picarro, Inc. All rights reserved
 */
#ifndef _SENTRY_HANDLER_H_
#define _SENTRY_HANDLER_H_

extern unsigned int schedulerAlive;
void initSentryChecks(void);
void sentryHandler(void);
void safeMode(void);

#endif /* _SENTRY_HANDLER_H_ */
