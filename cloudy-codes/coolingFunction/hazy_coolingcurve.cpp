/* This file is part of Cloudy and is copyright (C)1978-2017 by Gary J. Ferland and
 * others.  For conditions of distribution and use see copyright notice in license.txt */
/* runs pure collisional models at range of temperatures, prints cooling */
#include "cddefines.h"
#include "cddrive.h"
#include <cstdlib>
#include <wchar.h>
#include <locale.h>

/*Usage: ./hazy_coolingcurve_PIE <metallicity> <dT (log_10)> <True/False (progressbar display)>  */
/*int main( void )*/
int main( int argc, char *argv[] )
{
	exit_type exit_status = ES_SUCCESS;

	DEBUG_ENTRY( "main()" );

	try {
	        setlocale(LC_CTYPE, "");
                wchar_t block = 0x2588;
                wchar_t cr    = 0x000D;

		double telog , cooling, hden , tehigh , dTelog;

		FILE *ioRES;
		char chLine[100];

		/* file to output short form of calculation's results */
		#ifdef PIE
		sprintf(chLine, "cooltable_PIE_Z=%.2f.dat",atof(argv[1]));
		ioRES = open_data(chLine,"w");
		printf("PIE\n");
		#else
		sprintf(chLine, "cooltable_CIE_Z=%.2f.dat",atof(argv[1]));
		ioRES = open_data(chLine,"w");
		printf("CIE\n");
		#endif

		/* the log of the hydrogen density cm-3 */
		hden = 1e-2;

		/* the log of the initial and final temperatures
		 * this calc has no ionization at very
		 * low temperatures, except for cosmic ray collisions and the cosmic background */
		telog = 1.;
		tehigh = 9.;

		/* increment in log of T, normally 0.1 */
		dTelog = atof(argv[2]);

		int models  = (int)ceil((tehigh-telog)/dTelog);
		int counter = 0;

		/* print simple header */
		fprintf(ioRES, "# T (K)\tLambda=e_dot/nH^2 (erg cm^3 s^-1)\n" );
		//fprintf(stderr, "# T (K)\tcool/nH^2 (erg cm^3 s^-1)\n" );

		/* we do not want to generate any output */
		#ifdef PIE
		sprintf(chLine, "hazy_coolingcurve_PIE_Z=%.2f.out",atof(argv[1]));
		cdOutput( chLine );
		#else
		sprintf(chLine, "hazy_coolingcurve_CIE_Z=%.2f.out",atof(argv[1]));
		cdOutput( chLine );
		#endif

		int totbars, nbars;
		double barsize;
		int now = 1;

		double redshift  = 0.;
		double temperature;

		/* loop over all temperature */
		while( telog <= (tehigh+0.0001) )
		{
		        counter++;
			/* initialize the code for this run */
			cdInit();

			cdTalk( false );

			/* if this is uncommented the calculation will not be done,
			 * but all parameters will be generated, as a quick way to see
			 * that grid is set up properly */
			/*cdNoExec( );*/

			/* cosmic background, microwave and hard parts */
			sprintf(chLine,"CMB redshift %.3f", redshift);
			cdRead( chLine );
			//#ifdef PIE
			sprintf(chLine, "table HM12 redshift %.3f", redshift);
			cdRead( chLine );
			//#else
			/* this is a pure collisional model to turn off photoionization */
			//cdRead( "no photoionization "  );
			//#endif

			/* do only one zone */
			cdRead( "stop zone 1 "  );

			/* set the hydrogen density */
			sprintf(chLine,"hden %f log",hden);
			cdRead( chLine  );

			sprintf(chLine, "sphere" );
			cdRead( chLine );
			sprintf(chLine, "radius 150 to 151 linear kiloparsec" );
			cdRead( chLine );

			sprintf(chLine, "abundances \"solar_GASS10.abn\"" );
			cdRead( chLine );

			/* set metallicity */
			sprintf(chLine,"metals %.3f linear",atof(argv[1]));
			cdRead( chLine  );

			/* this says to compute very small stages of ionization - we normally trim up
		 	* the ionizaton so that only important stages are done */
			sprintf(chLine, "set trim -20 "  );
			cdRead( chLine );

			/* the log of the gas temperature */
			temperature = pow(10., telog);
			/* sets the gas kinetic temperature */
			sprintf(chLine, "constant temperature, T=%.3e K linear ", temperature );
			cdRead( chLine );

			sprintf(chLine, "iterate convergence" );
			cdRead( chLine );
			sprintf(chLine, "age 1e9 years" );
			cdRead( chLine );

			/* identify sources of heating and cooling */
			cdRead( "punch heating \"hazy_coolingcurve.het\" last no hash no clobber "  );
			cdRead( "punch cooling \"hazy_coolingcurve.col\" last no hash no clobber "  );
			printf("Mark1\n");
			/* actually call the code */
			if( cdDrive() )
				exit_status = ES_FAILURE;
			printf("Mark2\n");
			/* get cooling for last zone */
			cooling = cdCooling_last();

			/* want to print cooling over density squared */
			cooling = cooling / pow(10.,hden*hden);

			fprintf(ioRES, "%12.6e\t%12.6e", pow(10,telog) , cooling ) ;
			printf("%12.6e\t%12.6e", pow(10,telog) , cooling ) ;
			//fprintf(stderr,"%12.6e\t%12.6e", pow(10,telog) , cooling ) ;

			if( exit_status == ES_FAILURE )
			{
				fprintf(ioRES ,"\t problems!!\n");
				//fprintf(stderr,"\t problems!!\n");
			}
			else
			{
				fprintf(ioRES ,"\n");
				//fprintf(stderr,"\n");
			}

			telog += dTelog;

			if ( (strcmp(argv[3],"True")==0) || (strcmp(argv[3],"true")==0))
			{
				barsize = 1.0;
				totbars = (int)(100/barsize);
				nbars = (int)floor(((double)counter/models*100)/barsize);
				wprintf(L"%lc|", cr);
				for (int i=0; i<nbars; i++) wprintf(L"%lc", block); //printf("#");
				switch (now){
				case 1:
				    wprintf(L"-");
				    break;
				case 2:
				    wprintf(L"\\");
				    break;
				case 3:
				    wprintf(L"|");
				    break;
				case 4:
				    wprintf(L"/");
				    break;
				default:
				    wprintf(L"-");
				}
				if (now==4) now = 0;
				now++;
				for (int j=1; j<(totbars-nbars); j++) wprintf(L"-");
				wprintf(L"|");
				wprintf(L" %.2f%%",((double)counter/models*100));
				fflush(stdout);
			}

		}

		wprintf(L"%lc|", cr);
		for (int i=0; i<totbars; i++) wprintf(L"%lc", block);
		wprintf(L"|");
		wprintf(L" %.2f%%\n",100.0);
		fflush(stdout);

		fclose(ioRES);

		cdEXIT(exit_status);
	}
	catch( bad_alloc )
	{
		fprintf( ioQQQ, " DISASTER - A memory allocation has failed. Most likely your computer "
			 "ran out of memory.\n Try monitoring the memory use of your run. Bailing out...\n" );
		exit_status = ES_BAD_ALLOC;
	}
	catch( out_of_range& e )
	{
		fprintf( ioQQQ, " DISASTER - An out_of_range exception was caught, what() = %s. Bailing out...\n",
			 e.what() );
		exit_status = ES_OUT_OF_RANGE;
	}
	catch( domain_error& e )
	{
		fprintf( ioQQQ, " DISASTER - A vectorized math routine threw a domain_error. Bailing out...\n" );
		fprintf( ioQQQ, " What() = %s", e.what() );
		exit_status = ES_DOMAIN_ERROR;
	}
	catch( bad_assert& e )
	{
		MyAssert( e.file(), e.line() , e.comment() );
		exit_status = ES_BAD_ASSERT;
	}
#ifdef CATCH_SIGNAL
	catch( bad_signal& e )
	{
		if( ioQQQ != NULL )
		{
			if( e.sig() == SIGINT || e.sig() == SIGQUIT )
			{
				fprintf( ioQQQ, " User interrupt request. Bailing out...\n" );
				exit_status = ES_USER_INTERRUPT;
			}
			else if( e.sig() == SIGTERM )
			{
				fprintf( ioQQQ, " Termination request. Bailing out...\n" );
				exit_status = ES_TERMINATION_REQUEST;
			}
			else if( e.sig() == SIGILL )
			{
				fprintf( ioQQQ, " DISASTER - An illegal instruction was found. Bailing out...\n" );
				exit_status = ES_ILLEGAL_INSTRUCTION;
			}
			else if( e.sig() == SIGFPE )
			{
				fprintf( ioQQQ, " DISASTER - A floating point exception occurred. Bailing out...\n" );
				exit_status = ES_FP_EXCEPTION;
			}
			else if( e.sig() == SIGSEGV )
			{
				fprintf( ioQQQ, " DISASTER - A segmentation violation occurred. Bailing out...\n" );
				exit_status = ES_SEGFAULT;
			}
#			ifdef SIGBUS
			else if( e.sig() == SIGBUS )
			{
				fprintf( ioQQQ, " DISASTER - A bus error occurred. Bailing out...\n" );
				exit_status = ES_BUS_ERROR;
			}
#			endif
			else
			{
				fprintf( ioQQQ, " DISASTER - A signal %d was caught. Bailing out...\n", e.sig() );
				exit_status = ES_UNKNOWN_SIGNAL;
			}

		}
	}
#endif
	catch( cloudy_exit& e )
	{
		if( ioQQQ != NULL )
		{
			ostringstream oss;
			oss << " [Stop in " << e.routine();
			oss << " at " << e.file() << ":" << e.line();
			if( e.exit_status() == 0 )
				oss << ", Cloudy exited OK]";
			else
				oss << ", something went wrong]";
			fprintf( ioQQQ, "%s\n", oss.str().c_str() );
		}
		exit_status = e.exit_status();
	}
	catch( std::exception& e )
	{
		fprintf( ioQQQ, " DISASTER - An unknown exception was caught, what() = %s. Bailing out...\n",
			 e.what() );
		exit_status = ES_UNKNOWN_EXCEPTION;
	}
	// generic catch-all in case we forget any specific exception above... so this MUST be the last one.
	catch( ... )
	{
		fprintf( ioQQQ, " DISASTER - An unknown exception was caught. Bailing out...\n" );
		exit_status = ES_UNKNOWN_EXCEPTION;
	}

	cdPrepareExit(exit_status);

	return exit_status;
}
