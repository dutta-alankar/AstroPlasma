/* This file is part of Cloudy and is copyright (C)1978-2022 by Gary J. Ferland and
 * others.  For conditions of distribution and use see copyright notice in license.txt */

#ifndef CPU_H_
#define CPU_H_

/**\file cpu.h store CPU specific information */

/* disable conditional expressions is constant */
#ifdef _MSC_VER
#pragma warning( disable : 4127 )
#endif

#define UNUSED /*@unused@*/
#ifdef __GNUC__
#undef UNUSED
#define UNUSED __attribute__ ((unused)) /*@unused@*/
#endif

/** some definitions for integers with a guaranteed number of bits */
#ifndef INT16_MAX
#  define INT16_MAX 32767
#endif
#ifndef INT16_MIN
#  define INT16_MIN (-INT16_MAX - 1)
#endif

#if SHRT_MAX == INT16_MAX
   typedef short int int16;
#elif INT_MAX == INT16_MAX
   typedef int int16;
#else
#  error failed to define int16, please report this to gary@pa.uky.edu
#endif

#ifndef UINT16_MAX
#  define UINT16_MAX 65535
#endif

#if USHRT_MAX == UINT16_MAX
   typedef unsigned short int uint16;
#elif UINT_MAX == UINT16_MAX
   typedef unsigned int uint16;
#else
#  error failed to define uint16, please report this to gary@pa.uky.edu
#endif

#ifndef INT32_MAX
#  define INT32_MAX 2147483647L
#endif
#ifndef INT32_MIN
#  define INT32_MIN (-INT32_MAX - 1)
#endif

#if INT_MAX == INT32_MAX
   typedef int int32;
#elif LONG_MAX == INT32_MAX
   typedef long int int32;
#else
#  error failed to define int32, please report this to gary@pa.uky.edu
#endif

#ifndef UINT32_MAX
#  define UINT32_MAX 4294967295UL
#endif

#if UINT_MAX == UINT32_MAX
   typedef unsigned int uint32;
#elif ULONG_MAX == UINT32_MAX
   typedef unsigned long int uint32;
#else
#  error failed to define uint32, please report this to gary@pa.uky.edu
#endif

#if LONG_MAX > INT32_MAX

/* this will only be defined on LP64 systems
 * ILP32 systems may have long long support, but that is not
 * part of the ISO/ANSI standard, so we don't use it here... */

/* INT64_MAX, etc, may be defined as long long, so avoid system definitions! */

#  undef INT64_MAX
#  define INT64_MAX 9223372036854775807L

#  undef INT64_MIN
#  define INT64_MIN (-INT64_MAX - 1L)

#  if LONG_MAX == INT64_MAX
#    define HAVE_INT64 1
     typedef long int int64;
#    define INT64_LIT(X) X##L
#  endif

#endif

#if defined(HAVE_LONG_LONG) && !defined(HAVE_INT64)

/* this is fallback for 32-bit systems */
#  if LLONG_MAX > INT32_MAX

#    undef INT64_MAX
#    define INT64_MAX 9223372036854775807LL

#    undef INT64_MIN
#    define INT64_MIN (-INT64_MAX - 1LL)

#    if LLONG_MAX == INT64_MAX
#      define HAVE_INT64 1
       typedef long long int int64;
#      define INT64_LIT(X) X##LL
#    endif

#  endif

#endif

#if ULONG_MAX > UINT32_MAX

#  undef UINT64_MAX
#  define UINT64_MAX 18446744073709551615UL

#  if ULONG_MAX == UINT64_MAX
#    define HAVE_UINT64 1
     typedef unsigned long int uint64;
#    define UINT64_LIT(X) X##UL
#  endif

#endif

#if defined(HAVE_LONG_LONG) && !defined(HAVE_UINT64)

/* this is fallback for 32-bit systems */
#  if ULLONG_MAX > UINT32_MAX

#    undef UINT64_MAX
#    define UINT64_MAX 18446744073709551615ULL

#    if ULLONG_MAX == UINT64_MAX
#      define HAVE_UINT64 1
       typedef unsigned long long int uint64;
#      define UINT64_LIT(X) X##ULL
#    endif

#  endif

#endif

#ifdef __AVX__
#  ifdef __AVX512F__
#    define CD_ALIGN 64
#  else
#    define CD_ALIGN 32
#  endif
#else
#  define CD_ALIGN 16
#endif

/** all vendors supply predefined preprocessor symbols to
 * help identify their hardware/operating system/compiler, the
 * following symbols will be used to bracket hardware/OS/compiler
 * specific code:
 *
 * Sun Sparc:      __sun
 * DEC Alpha:      __alpha
 * SGI Iris:       __sgi
 * HP Unix:        __hpux
 * Cray:           __cray
 * IA32:           __i386
 * AMD64/EM64T:    __amd64
 * UNIX:           __unix (includes Linux)
 * Linux:          __linux__
 * MS Vis C:       _MSC_VER
 * Intel compiler: __ICC, __INTEL_COMPILER
 * g++/icc/pathCC: __GNUC__ (also set by icc and pathCC!)
 * g++:            __GNUC_EXCL__ (excludes icc, pathCC)
 *
 * NOTE: the user should NOT define these symbols at compile time.
 */
#ifdef cray
#ifndef __cray
#define __cray 1
#endif
#endif

/** the Intel EM64T compiler does not set the __amd64 flag... */
#ifdef __x86_64
#ifndef __amd64
#define __amd64 1
#endif
#endif

#if defined(_ARCH_PPC) || defined(__POWERPC__) || defined(__powerpc__) || defined(PPC)
#ifndef __ppc__
#define __ppc__ 1
#endif
#endif

/** on some UNIX systems only the preprocessor symbol "unix"
 * is predefined (e.g. DEC alpha), on others only "__unix"
 * (e.g. Cray), and on yet others both... This ensures
 * "__unix" is always defined on all UNIX systems.
 */
#if defined(unix) || defined(__unix__)
#ifndef __unix
#define __unix 1
#endif
#endif

/** failsafe for obsolete or buggy systems to assure that the POSIX symbol __linux__ is defined */
#if defined(linux) || defined(__linux)
#ifndef __linux__
#define __linux__ 1
#endif
#endif

/** on SGI IA64 systems, icc calls itself ecc... */
#ifdef __ECC
#ifndef __ICC
#define __ICC __ECC
#endif
#endif

/** this is needed to discriminate between g++ and icc/pathCC/openCC/clang++ */
#undef __GNUC_EXCL__
#if defined(__GNUC__) && ! ( defined(__ICC) || defined(__PATHSCALE__) || defined(__OPENCC__) || defined(__clang__) )
#define __GNUC_EXCL__ 1
#endif

/* make sure __func__ is defined, this can be removed once C++11 is in effect */
#ifndef HAVE_FUNC
#  undef __func__
#  ifdef __FUNCTION__
#    define __func__ __FUNCTION__
#  else
#    define __func__ DEBUG_ENTRY.name()
#  endif
#endif

/* safe, small, numbers for the float and double */
/** set something that is too small to max of quantity and SMALLFLOAT,
 * but then compare with SMALLFLOAT */
/*FLT_MAX is 3.40e38 on wintel, so BIGFLOAT is 3.40e36 */
const realnum BIGFLOAT = numeric_limits<realnum>::max()/realnum(100.f);
/**FLT_MIN is 1.175494351e-38 on wintel, so SMALLFLOAT is 1.175e-36 */
const realnum SMALLFLOAT = numeric_limits<realnum>::min()*realnum(100.f);

/**DBL_MAX is 1.797e308 on wintel so BIGDOUBLE is 1.797e306 */
const double BIGDOUBLE = DBL_MAX/100.;
const double SMALLDOUBLE = DBL_MIN*100.;

const int STDLEN = 32;

/** flag used as third parameter for open_data, indicates how data files are searched
 *  AS_DEFAULT: use default behavior: AS_DATA_ONLY for reading, AS_LOCAL_ONLY for writing
 *  AS_DATA_ONLY: search only in the data directories, not in the current working directory
 *  AS_DATA_OPTIONAL: same as AS_DATA_ONLY, except that the precense of the file is optional
 *  AS_LOCAL_DATA: search in the current working directory first, then in the data directories
 *  AS_LOCAL_ONLY: search in the current working directory only
 *  versions with _TRY appended have the same meaning, except that they don't abort
 *  AS_SILENT_TRY: same as AS_LOCAL_ONLY_TRY, but does not write to ioQQQ in trace mode */
typedef enum { AS_DEFAULT, AS_DATA_ONLY_TRY, AS_LOCAL_DATA_TRY, AS_LOCAL_ONLY_TRY, AS_DATA_ONLY, 
	       AS_DATA_OPTIONAL, AS_LOCAL_DATA, AS_LOCAL_ONLY, AS_SILENT_TRY } access_scheme;

// the C++ openmodes below give the exact equivalent of the C modes "r", "w", "a", etc.
// the "+" sign in the C mode has been replaced by "p", so, e.g., mode_rpb is equivalent to "r+b"
const ios_base::openmode mode_r = ios_base::in;
const ios_base::openmode mode_w = ios_base::out | ios_base::trunc;
const ios_base::openmode mode_a = ios_base::out | ios_base::app;
const ios_base::openmode mode_rp = ios_base::in | ios_base::out;
const ios_base::openmode mode_wp = ios_base::in | ios_base::out | ios_base::trunc;
const ios_base::openmode mode_ap = ios_base::in | ios_base::out | ios_base::app;

const ios_base::openmode UNUSED mode_rb = mode_r | ios_base::binary;
const ios_base::openmode UNUSED mode_wb = mode_w | ios_base::binary;
const ios_base::openmode UNUSED mode_ab = mode_a | ios_base::binary;
const ios_base::openmode UNUSED mode_rpb = mode_rp | ios_base::binary;
const ios_base::openmode UNUSED mode_wpb = mode_wp | ios_base::binary;
const ios_base::openmode UNUSED mode_apb = mode_ap | ios_base::binary;

#include "mpi_utilities.h"

FILE* open_data( const char* fname, const char* mode, access_scheme scheme=AS_DEFAULT );
void open_data( fstream& stream, const char* fname, ios_base::openmode mode, access_scheme scheme=AS_DEFAULT );
MPI_File open_data( const char* fname, int mode, access_scheme scheme=AS_DEFAULT );
void check_data( const char* fpath, const char* fname );

/* this class is deliberately kept global so that the constructor is executed before
 * any of the user code; this assures a correct FP environment right from the start */
class t_cpu_i
{
	/** alias an int32 to 4 chars to test if we are on a big-endian or little-endian CPU
	    the array cpu.endian.c[] is initialized in cdInit() */
	union
	{
		char c[4];
		int32 i;
	} endian;

	sys_float test_float;
	double test_double;

	int32 Float_SNaN_Value;
#	ifdef HAVE_INT64
	int64 Double_SNaN_Value;
#	else
	int32 Double_SNaN_Value[2];
#	endif

#	ifdef __unix
	struct sigaction p_action;
	struct sigaction p_default;
#	endif

	/** should a failed assert raise SIGABRT so that we can catch it in a debugger? */
	bool p_lgAssertAbort;

	/** the number of available CPUs on the system, not detected on all systems */
	long n_avail_CPU;
	/** the number of used CPUs */
	long n_use_CPU;
	/** flag whether we are doing an MPI run or not */
	bool p_lgMPI;
	/** flag indicating whether each rank runs its own model
	 * true means that each rank runs a different sim (e.g. in a grid)
	 * false means that all ranks cooperate on the same sim
	 * this flag is moot in a non-MPI run */
	bool p_lgMPISingleRankMode;
	/** the rank number in an MPI run, -1 otherwise */
	long n_rank;
	/** the name of the computer, not detected on all systems */
	char HostName[STDLEN];
	/** the default search path to the data files */
	vector<string> chSearchPath;
	/** the directory separator character for this OS */
	char p_chDirSeparator;
	/** how many data files have been opened? */
	int nFileDone;
	/** how many modified data files were found? */
	int nMD5Mismatch;
	/** the map of the MD5 sums of all the data files */
	map<string,string> md5sum_expct;

	void enable_traps() const;
	static void signal_handler(int sig);

	vector<string> p_exit_status;

	void getPathList( const char* fname, vector<string>& PathList, access_scheme scheme, bool lgRead ) const;
	void getMD5sums( const char* fname );
public:
	t_cpu_i();

	bool big_endian() const { return ( endian.i == 0x12345678 ); }
	bool little_endian() const { return ( endian.i == 0x78563412 ); }

	sys_float min_float() const { return test_float; }
	double min_double() const { return test_double; }

#	ifdef __unix
	const struct sigaction* action() const { return &p_action; }
	const struct sigaction* deflt() const { return &p_default; }
#	endif

	void set_signal_handlers();

	void setAssertAbort(bool val)
	{
		p_lgAssertAbort = val;
#ifdef CATCH_SIGNAL
#		ifdef __unix
		if( val )
			sigaction( SIGABRT, deflt(), NULL );
		else
			sigaction( SIGABRT, action(), NULL );
#		endif
#		ifdef _MSC_VER
		if( val )
			signal( SIGABRT, SIG_DFL );
		else
			signal( SIGABRT, &signal_handler );
#		endif
#endif
	}
	bool lgAssertAbort() const { return p_lgAssertAbort; }

	void set_nCPU(long n) { n_avail_CPU = n; }
	long nCPU() const { return n_avail_CPU; }
	void set_used_nCPU(long n) { n_use_CPU = n; }
	long used_nCPU() const { return n_use_CPU; }
	bool lgMPI() const { return p_lgMPI; }
	void set_MPISingleRankMode( bool mode ) { p_lgMPISingleRankMode = mode; }
	bool lgMPISingleRankMode() const { return p_lgMPISingleRankMode; }
	void set_nRANK(long n) { n_rank = n; }
	long nRANK() const { return n_rank; }
	bool lgMaster() const { return ( n_rank == 0 ); }
	bool lgMPI_talk() const { return lgMaster() || lgMPISingleRankMode(); }
	const char *host_name() const { return HostName; }
	void printDataPath() const;
	char chDirSeparator() const { return p_chDirSeparator; }
	bool firstOpen() const { return ( nFileDone == 0 ); }
	bool foundMD5Mismatch() const { return ( nMD5Mismatch > 0 ); }
	const string& chExitStatus(exit_type s) const { return p_exit_status[s]; }

	friend FILE* open_data( const char* fname, const char* mode, access_scheme scheme );
	friend void open_data( fstream& stream, const char* fname, ios_base::openmode mode, access_scheme scheme );
	friend MPI_File open_data( const char* fname, int mode, access_scheme scheme );
	friend void check_data( const char* fpath, const char* fname );

	friend void set_NaN(sys_float &x);
	friend void set_NaN(sys_float x[], long n);
	friend void set_NaN(double &x);
	friend void set_NaN(double x[], long n);
};
class t_cpu
{
	static t_cpu_i *m_i;
public:
	t_cpu_i &i()
	{
		return *m_i;
	}
	t_cpu();
	~t_cpu();
};
// Generate a (static) instance of this variable in *every* file.
static t_cpu cpu;

// The static (class) pointer is set in the first of these.  Obviously 
// this is not thread safe...

// Better engineered variants are available in Alexandrescu's book; 
// better yet to reduce the number of globals and file-statics so 
// this can just be initialized at the start of main().

/** set_NaN - set variable or array to SNaN */
void set_NaN(sys_float &x);
void set_NaN(sys_float x[], /* x[n] */
	     long n);
void set_NaN(double &x);
void set_NaN(double x[], /* x[n] */
	     long n);

/** detect quiet and signaling NaNs in FP numbers */
bool MyIsnan(const sys_float &x);
bool MyIsnan(const double &x);

/* Apply compiler directive saying that current routine does not
	 return as modifier, as in "NORETURN void MyExit() { ... }"  */
#ifdef _MSC_VER
#define NORETURN __declspec(noreturn) /*@noreturn@*/
#elif defined(__GNUC__) || ( defined(__INTEL_COMPILER) && defined(__linux__) )
#define NORETURN __attribute__ ((noreturn)) /*@noreturn@*/
#else
#define NORETURN /*@noreturn@*/
#endif

#define FALLTHROUGH (void)0
#ifdef __GNUC_EXCL__
#if (__GNUC__ >= 7)
#undef  FALLTHROUGH
#define FALLTHROUGH __attribute__ ((fallthrough))
#endif
#endif

#ifdef _MSC_VER
#define ALIGNED(X) __declspec(align(X))
#else
#define ALIGNED(X) __attribute__ ((aligned(X)))
#endif

#define RESTRICT
#define UNLIKELY(x) (x)
#ifdef __GNUC__
#if (__GNUC__ >= 3)
#undef UNLIKELY
#define UNLIKELY(x) __builtin_expect((x),0)
#endif
#undef RESTRICT
#define RESTRICT __restrict
#else
#endif

/* Some hackery needed to test if a preprocessor macro is empty. Use as follows:
 *  #if EXPAND(SOME_DODGY_MACRO) == 1
 *      get here if SOME_DODGY_MACRO expands to empty string
 *  #endif */
#define DO_EXPAND(VAL)  VAL ## 1
#define EXPAND(VAL)     DO_EXPAND(VAL)

/* Define __COMP and __COMP_VER macros for all systems */
/* the Intel compiler */
/* this needs to be before g++ since icc also sets __GNUC__ */
#if defined __INTEL_COMPILER
#	define	__COMP	"icc"
#	define	__COMP_VER	__INTEL_COMPILER 

/* PathScale EKOPath compiler */
/* this needs to be before g++ since pathCC also sets __GNUC__ */
#elif defined __PATHSCALE__
#	define	__COMP	"pathCC"
#	define	__COMP_VER	__PATHCC__ * 100 + __PATHCC_MINOR__ * 10 + __PATHCC_PATCHLEVEL__

/* Open64 compiler */
/* this needs to be before g++ since openCC also sets __GNUC__ */
#elif defined __OPENCC__
#	define	__COMP	"Open64"
#	if EXPAND(__OPENCC_PATCHLEVEL__) == 1
#		define	__COMP_VER	__OPENCC__ * 100 + __OPENCC_MINOR__ * 10
#	else
#		define	__COMP_VER	__OPENCC__ * 100 + __OPENCC_MINOR__ * 10 + __OPENCC_PATCHLEVEL__
#	endif

/* LLVM clang++ */
/* this needs to be before g++ since clang++ also sets __GNUC__ */
#elif defined __clang__
#	define	__COMP	"clang++"
#	define	__COMP_VER	__clang_major__ * 100 + __clang_minor__ * 10 + __clang_patchlevel__

/* g++ */
#elif defined __GNUC__
#	define	__COMP	"g++"
#	if defined(__GNUC_PATCHLEVEL__)
#		define __COMP_VER (__GNUC__ * 10000 + __GNUC_MINOR__ * 100 + __GNUC_PATCHLEVEL__)
#	else
#		define __COMP_VER (__GNUC__ * 10000 + __GNUC_MINOR__ * 100)
#	endif

#elif defined __PGI
#	define	__COMP	"Portland Group"
#	if defined(__PGIC__)
#		define __COMP_VER (__PGIC__ * 100 + __PGIC_MINOR__ * 10 + __PGIC_PATCHLEVEL__)
#	else
#		define __COMP_VER 0
#	endif

/* SGI MIPSpro */
/* this needs to be after g++, since g++ under IRIX also sets _COMPILER_VERSION */
#elif defined(__sgi) && defined(_COMPILER_VERSION)
#	define	__COMP	"MIPSpro"
#	define	__COMP_VER	_COMPILER_VERSION

/* HP */
#elif defined __HP_aCC 
#	define	__COMP	"HP aCC"
#	define	__COMP_VER	__HP_aCC  

/* DEC - this one may be broken for C++, no way to test it... */
#elif defined __DECC 
#	define	__COMP	"DEC CC"
#	define	__COMP_VER	__DECC_VER   

/* MS VS */
#elif defined	_MSC_VER
#	define	__COMP	"vs"
#	define	__COMP_VER	_MSC_VER  

/* Oracle Solaris Studio */
#elif defined	__SUNPRO_CC
#	define	__COMP	"Solaris Studio"
#	define	__COMP_VER	__SUNPRO_CC

/* unknown */
#else
#	define	__COMP	"unknown"
#	define	__COMP_VER	0 
#endif

/* ----------------------------  OS ---------------------------- */
/* linux */
#if defined	__linux__
#	if defined __i386
#		define	__OS	"Linux (IA32)"
#	elif defined __amd64
#		define	__OS	"Linux (AMD64)"
#	elif defined __ia64
#		define	__OS	"Linux (IA64)"
#	elif defined __ppc__
#		define	__OS	"Linux (PowerPC)"
#	else
#		define	__OS	"Linux (other)"
#	endif

/* macintosh */
#elif defined	macintosh
#	define	__OS	"Mac OS 9"

/* macintosh */
#elif defined	__MACOSX__
#	define	__OS	"Mac OS X"

/* apple mac, ... */
#elif defined	__APPLE__
#	define	__OS	"Apple MacOS"

/* HP */
#elif defined	hpux
#	define	__OS	"HP-UX"

/* Oracle Solaris */
#elif defined	__sun
#	define	__OS	"Solaris"

/* IBM AIX */
#elif defined	_AIX
#	define	__OS	"AIX"

/* Compaq alpha */
#elif defined	ultrix
#	define	__OS	"Ultrix"

/* the BSD variants */
#elif defined	__FreeBSD__
#	define	__OS	"FreeBSD"

#elif defined	__NetBSD__
#	define	__OS	"NetBSD"

#elif defined	__OpenBSD__
#	define	__OS	"OpenBSD"

/* Windows64 */
/* this needs to be before _WIN32 since Windows64 also sets _WIN32 */
#elif defined	_WIN64
#	define	__OS	"Win64"

/* Windows */
#elif defined	_WIN32
#	define	__OS	"Win32"

/* Cygwin */
#elif defined	__CYGWIN__
#	define	__OS	"Cygwin"

/* SGI */
#elif defined	__sgi
#	define	__OS	"IRIX"

/* unknown */
#else
#	define	__OS	"unknown"
#endif

/* don't perform this check when we are generating dependencies */
#ifndef MM
/* bomb out if the compiler is broken.... */
#  if defined(__GNUC_EXCL__) && ((__GNUC__ == 2 && __GNUC_MINOR__ == 96) || (__GNUC__ == 3 && __GNUC_MINOR__ == 4))
#  error "This g++ version cannot compile Cloudy and must not be used! Please update g++ to a functional version. See http://wiki.nublado.org/wiki/CompileCode for more details."
#  endif

#  if __INTEL_COMPILER >= 1200 &&  __INTEL_COMPILER < 1300
#  error "This icc version cannot compile Cloudy and must not be used! Please use a functional version of icc, or g++. See http://wiki.nublado.org/wiki/CompileCode for more details."
#  endif
#endif

#ifdef _MSC_VER
#pragma warning( default : 4127 )/* disable warning that conditional expression is constant*/
#endif

#endif /* CPU_H_ */
