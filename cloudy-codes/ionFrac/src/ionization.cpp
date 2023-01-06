/* This file is part of Cloudy and is copyright (C)1978-2017 by Gary J. Ferland and
 * others.  For conditions of distribution and use see copyright notice in license.txt */
/*main program calling cloudy to produce a table giving ionization vs temperature */
#include "cddefines.h"
#include "cddrive.h"

int main( int argc, char *argv[] )
{
	exit_type exit_status = ES_SUCCESS;

	DEBUG_ENTRY( "main()" );
	if (argc!=6) {
	    fprintf(ioQQQ, " DISASTER - Parameter mismatch!\n");
	    exit_status = ES_TERMINATION_REQUEST;
	    cdPrepareExit(exit_status);
	    return exit_status;
	}
        double nH          = atof(argv[1]);
        double temperature = atof(argv[2]);
        double metallicity = atof(argv[3]);
        double redshift    = atof(argv[4]);
        
	try {
		/* following is number of ion stages per line */
#		define NELEM 15
		double xIonSave[LIMELM][LIMELM+1] ;
		long int i;
		long int nelem , ion;
		/* this is the list of element names used to query code results */
		char chElementNameShort[LIMELM][5] = { "HYDR" , "HELI" ,
						       "LITH" , "BERY" , "BORO" , "CARB" , "NITR" , "OXYG" , "FLUO" ,
						       "NEON" , "SODI" , "MAGN" , "ALUM" , "SILI" , "PHOS" , "SULP" ,
						       "CHLO" , "ARGO" , "POTA" , "CALC" , "SCAN" , "TITA" , "VANA" ,
						       "CHRO" , "MANG" , "IRON" , "COBA" , "NICK" , "COPP" , "ZINC" };
		/* this is the list of element names used to make printout */
		char chElementName[LIMELM][11] =
			{ "Hydrogen  " ,"Helium    " ,"Lithium   " ,"Beryllium " ,"Boron     " ,
			  "Carbon    " ,"Nitrogen  " ,"Oxygen    " ,"Fluorine  " ,"Neon      " ,
			  "Sodium    " ,"Magnesium " ,"Aluminium " ,"Silicon   " ,"Phosphorus" ,
			  "Sulphur   " ,"Chlorine  " ,"Argon     " ,"Potassium " ,"Calcium   " ,
			  "Scandium  " ,"Titanium  " ,"Vanadium  " ,"Chromium  " ,"Manganese " ,
			  "Iron      " ,"Cobalt    " ,"Nickel    " ,"Copper    " ,"Zinc      "};

		FILE *ioRES ;
		char chLine[100];

		/* calculation's results are saved here */
		#ifdef CIE
		sprintf(chLine,"./auto/ionization_CIE_%09d.txt", atoi(argv[5]));
		ioRES = open_data(chLine,"w");
		fprintf(ioRES,"#  log10 fractional ionization for species in CIE\n" );
		#else
		sprintf(chLine,"./auto/ionization_PIE_%09d.txt", atoi(argv[5]));
		ioRES = open_data(chLine,"w");
		fprintf(ioRES,"#  log10 fractional ionization for species in PIE\n" );
		#endif
		fprintf(ioRES,"#  nH=%.3e cm^-3, T=%.3e K, met=%.3e, redshift=%.2f\n\n", nH, temperature, metallicity, redshift );

		/* initialize the code for this run */
		cdInit();
		cdTalk(false);
		/*cdNoExec( );*/

		/* input continuum */
	        #ifndef CIE
	        sprintf(chLine,"CMB redshift %.3f", redshift);
		cdRead( chLine );
		sprintf(chLine, "table HM12 redshift %.3f", redshift);
		cdRead( chLine );
		#else
		sprintf(chLine,"CMB redshift %.3f", redshift);
		cdRead( chLine );
		/* this is a pure collisional model to turn off photoionization */
		cdRead( "no photoionization"  );
		#endif
		
		sprintf(chLine, "sphere" );
		cdRead( chLine );
		sprintf(chLine, "radius 150 to 151 linear kiloparsec" );
		cdRead( chLine );
		
		sprintf(chLine, "abundances \"solar_GASS10.abn\"" ); 
		cdRead( chLine );
		
		sprintf(chLine, "metals %.3f linear", metallicity );
		cdRead( chLine );
 
		/* just do the first zone - only want ionization distribution */
		sprintf(chLine, "stop zone 1 "  );
		cdRead( chLine );

		/* the hydrogen density entered as a log */
		sprintf(chLine, "hden %.2f log", log10(nH)  );
		cdRead( chLine );

		/* this says to compute very small stages of ionization - we normally trim up
		 * the ionizaton so that only important stages are done */
		sprintf(chLine, "set trim -20 "  );
		cdRead( chLine );

		/* the log of the gas temperature */
		sprintf(chLine, "constant temperature, T=%.3e K linear ", temperature );
		cdRead( chLine );
		
		sprintf(chLine, "iterate convergence" );
		cdRead( chLine );
		sprintf(chLine, "age 1e9 years" );
		cdRead( chLine );

		/* actually call the code */
		if( cdDrive() )
			exit_status = ES_FAILURE;

		/* now save ionization distribution for later printout */
		for( nelem=0; nelem<LIMELM; ++nelem){
			for( ion=1; ion<=nelem+2;++ion){
				if( cdIonFrac(chElementNameShort[nelem],
						ion, &xIonSave[nelem][ion],
						"radius",false) ){
					fprintf(ioRES,"\t problems!!\n");
					fprintf(stderr,"\t problems!!\n");
				}
			}
		}


		/* this generates large printout */
		#ifdef FRIENDLY
		for( nelem=0; nelem<LIMELM; ++nelem){
			fprintf(ioRES,"#   Element %li %s\n", nelem+1,chElementName[nelem]);
			fprintf(ioRES,"# ");
			for(i=1; i<=nelem+2;++i) fprintf(ioRES,"%9li",i);
			fprintf(ioRES,"\n  ");			
			for(ion=1;ion<=nelem+2;++ion) fprintf(ioRES,"%9.2f",log10(xIonSave[nelem][ion]) );				
			fprintf(ioRES,"\n");	
		}
		#else
		for( nelem=0; nelem<LIMELM; ++nelem){
			for(ion=1;ion<=nelem+2;++ion) fprintf(ioRES,"%9.2f",log10(xIonSave[nelem][ion]) );
			//fprintf(ioRES,"\n");
		}
		#endif
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

