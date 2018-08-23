import datetime
now = datetime.datetime.now()

# Boilerplate code for dspAutogen.h output file

header = """/*
 * FILE:
 *   dspAutogen.h
 *
 * DESCRIPTION:
 *   Automatically generated DSP H file for Picarro gas analyzer. DO NOT EDIT.
 *
 * SEE ALSO:
 *   Specify any related information.
 *
 *  Copyright (c) 2008-%d Picarro, Inc. All rights reserved
 */
#ifndef _DSP_AUTOGEN_H
#define _DSP_AUTOGEN_H

#include "interface.h"
""" % (now.year, )

trailer = "#endif"
