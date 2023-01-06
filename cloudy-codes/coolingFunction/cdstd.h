/* This file is part of Cloudy and is copyright (C)1978-2022 by Gary J. Ferland and
 * others.  For conditions of distribution and use see copyright notice in license.txt */

#ifndef CDSTD_H_
#define CDSTD_H_

// cdstd.h: define macros to select library API version.

// This must be included before all library #includes.
// Typically this done as part of cddefines.h, only required
// independently when cddefines.h is not first include.

// We *require* POSIX.1-2008 as a minimum (for strnlen()).
// See e.g. Rochkind, Advanced UNIX Programming for more details.

// There appears to be a bug in the POSIX implementation in FreeBSD that was
// imported into Apple Darwin (at least version 11.4.2) where defining _POSIX_SOURCE
// will cause compilation errors as a result of missing type definitions (e.g., u_int)
// when including certain system header files. See e.g. this report:
// http://lists.freebsd.org/pipermail/freebsd-bugs/2011-April/044049.html
#if !defined(__APPLE__) && !defined(__FreeBSD__)
#define _POSIX_C_SOURCE 200112L
#define _XOPEN_SOURCE 600
#endif

#ifdef MPI_GRID_RUN
#define MPI_ENABLED
#endif

// the Intel MPI implementation wants this file included before cstdio...
// http://www.saii.ull.es/files/doc_intel/doc/HelpMe_FAQ.htm
// so we include it here to make really sure that it is in front of
// the system includes that may be done before cddefines.h is included
//
// we define OMPI_SKIP_MPICXX to silence compiler warnings/errors about a
// poorly designed C++ interface in openmpi, see this thread for more details:
// https://github.com/open-mpi/ompi/issues/5157
#ifdef MPI_ENABLED
#define OMPI_SKIP_MPICXX 1
#include <mpi.h>
#endif

#endif // CDSTD_H_
