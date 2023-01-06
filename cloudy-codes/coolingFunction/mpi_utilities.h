/* This file is part of Cloudy and is copyright (C)1978-2022 by Gary J. Ferland and
 * others.  For conditions of distribution and use see copyright notice in license.txt */

#ifndef MPI_UTILITIES_H_
#define MPI_UTILITIES_H_

#ifdef MPI_ENABLED

//!
//! Create a set of overloaded functions that allows us to pull in MPI
//! data types in a safer and more C++ way.
//!
//! Some typical ways to use it are:
//!   double x;
//!   MPI_Bcast( &x, 1, MPI_type(x), 0, MPI_COMM_WORLD );
//!
//! But also:
//!   typedef unsigned int myType;
//!   myType t;
//!   MPI_Bcast( &t, 1, MPI_type(t), 0, MPI_COMM_WORLD );
//!
//! or:
//!   realnum v[20];
//!   MPI_Bcast( v, 20, MPI_type(v), 0, MPI_COMM_WORLD );
//!
//! This is very useful for realnum: MPI_type(v) will do the right thing,
//! no matter what the setting of FLT_IS_DBL is. Also note that MPI_type
//! can take both variables and arrays as its argument.
//!
//! The list below should cover all POD types that are currently used in
//! Cloudy.
//!
//! PS - the "t" in MPI_type is deliberately chosen to be lower case
//!      so that it cannot possibly clash with existing MPI symbols.
//!

//inline MPI_Datatype MPI_type(bool) { return MPI_BOOL; }
//inline MPI_Datatype MPI_type(const bool*) { return MPI_BOOL; }
inline MPI_Datatype MPI_type(char) { return MPI_CHAR; }
inline MPI_Datatype MPI_type(const char*) { return MPI_CHAR; }
inline MPI_Datatype MPI_type(unsigned char) { return MPI_UNSIGNED_CHAR; }
inline MPI_Datatype MPI_type(const unsigned char*) { return MPI_UNSIGNED_CHAR; }
inline MPI_Datatype MPI_type(short int) { return MPI_SHORT; }
inline MPI_Datatype MPI_type(const short int*) { return MPI_SHORT; }
inline MPI_Datatype MPI_type(unsigned short int) { return MPI_UNSIGNED_SHORT; }
inline MPI_Datatype MPI_type(const unsigned short int*) { return MPI_UNSIGNED_SHORT; }
inline MPI_Datatype MPI_type(int) { return MPI_INT; }
inline MPI_Datatype MPI_type(const int*) { return MPI_INT; }
inline MPI_Datatype MPI_type(unsigned int) { return MPI_UNSIGNED; }
inline MPI_Datatype MPI_type(const unsigned int*) { return MPI_UNSIGNED; }
inline MPI_Datatype MPI_type(long) { return MPI_LONG_INT; }
inline MPI_Datatype MPI_type(const long*) { return MPI_LONG_INT; }
inline MPI_Datatype MPI_type(unsigned long) { return MPI_UNSIGNED_LONG; }
inline MPI_Datatype MPI_type(const unsigned long*) { return MPI_UNSIGNED_LONG; }
#ifdef HAVE_LONG_LONG
inline MPI_Datatype MPI_type(long long) { return MPI_LONG_LONG; }
inline MPI_Datatype MPI_type(const long long*) { return MPI_LONG_LONG; }
inline MPI_Datatype MPI_type(unsigned long long) { return MPI_UNSIGNED_LONG_LONG; }
inline MPI_Datatype MPI_type(const unsigned long long*) { return MPI_UNSIGNED_LONG_LONG; }
#endif
inline MPI_Datatype MPI_type(sys_float) { return MPI_FLOAT; }
inline MPI_Datatype MPI_type(const sys_float*) { return MPI_FLOAT; }
inline MPI_Datatype MPI_type(double) { return MPI_DOUBLE; }
inline MPI_Datatype MPI_type(const double*) { return MPI_DOUBLE; }
inline MPI_Datatype MPI_type(complex<sys_float>) { return MPI_COMPLEX; }
inline MPI_Datatype MPI_type(const complex<sys_float>*) { return MPI_COMPLEX; }
inline MPI_Datatype MPI_type(complex<double>) { return MPI_DOUBLE_COMPLEX; }
inline MPI_Datatype MPI_type(const complex<double>*) { return MPI_DOUBLE_COMPLEX; }

#else /* MPI_ENABLED */

typedef long MPI_Offset;
typedef long MPI_Status;
typedef void* MPI_File;

extern int MPI_SUCCESS;
extern int MPI_ERR_INTERN;
extern MPI_File MPI_FILE_NULL;

int total_insanity(MPI_File, int, MPI_Status*);

// define MPI stubs here, so that we don't get endless #ifdef MPI_ENBLED in the code...
// this way we can use if( cpu.i().lgMPI() ) { .... } instead
#define MPI_Barrier(Z) TotalInsanityAsStub<int>()
#define MPI_Bcast(V,W,X,Y,Z) TotalInsanityAsStub<int>()
#define MPI_Finalize() TotalInsanityAsStub<int>()
#define MPI_Comm_size(Y,Z) TotalInsanityAsStub<int>()
#define MPI_Comm_rank(Y,Z) TotalInsanityAsStub<int>()
#define MPI_Init(Y,Z) TotalInsanityAsStub<int>()
#define MPI_Reduce(T,U,V,W,X,Y,Z) TotalInsanityAsStub<int>()
#define MPI_File_open(V,W,X,Y,Z) TotalInsanityAsStub<int>()
#define MPI_File_set_view(U,V,W,X,Y,Z) TotalInsanityAsStub<int>()
#define MPI_File_get_size(Y,Z) TotalInsanityAsStub<int>()
#define MPI_File_write(V,W,X,Y,Z) total_insanity(V,X,Z)
#define MPI_File_close(Z) TotalInsanityAsStub<int>()

#endif /* MPI_ENABLED */

class load_balance
{
	vector<int> p_jobs;
	unsigned int p_ptr;
	unsigned int p_rank;
	unsigned int p_ncpu;
	void p_clear0()
	{
		p_jobs.clear();
	}
	void p_clear1()
	{
		p_ptr = 0;
		p_rank = 0;
		p_ncpu = 0;
	}
public:
	load_balance()
	{
		p_clear1();
	}
	load_balance( unsigned int nJobs, unsigned int nCPU )
	{
		p_clear1();
		init( nJobs, nCPU );
	}
	~load_balance()
	{
		p_clear0();
	}
	void clear()
	{
		p_clear0();
		p_clear1();
	}
	void init( unsigned int nJobs, unsigned int nCPU );
	int next_job()
	{
		if( p_ptr < p_jobs.size() )
		{
			int res = p_jobs[p_ptr];
			p_ptr += p_ncpu;
			return res;
		}
		else
			return -1;
	}
	void finalize( exit_type exit_status );
};

extern int mpi_mode_r;
extern int mpi_mode_w;
extern int mpi_mode_a;

/** GridPointPrefix: generate filename prefix for any files associated with a single point in a grid */
inline string GridPointPrefix(int n)
{
	ostringstream oss;
	oss << "grid" << setfill( '0' ) << setw(9) << n << "_";
	return oss.str();
}

/** process_output: concatenate output files produced in MPI grid run */
void process_output();

/** append_file: append output produced on file <source> to open file descriptor <dest> */
void append_file( FILE*, const char* );
void append_file( MPI_File, const char* );

#endif /* _MPI_UTILITIES_H_ */
