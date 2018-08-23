import datetime
now = datetime.datetime.now()

# Boilerplate code for dsp C output file

header = """/*
 * FILE:
 *   dspAutogen.c
 *
 * DESCRIPTION:
 *   Automatically generated DSP C file for Picarro gas analyzer. DO NOT EDIT.
 *
 * SEE ALSO:
 *   Specify any related information.
 *
 *  Copyright (c) 2008-%d Picarro, Inc. All rights reserved
 */

#include <stdlib.h>
#include "dspAutogen.h"
#include "interface.h"
""" % (now.year, )
