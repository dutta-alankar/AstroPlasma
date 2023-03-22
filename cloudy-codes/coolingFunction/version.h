/* This file is part of Cloudy and is copyright (C)1978-2022 by Gary J. Ferland and
 * others.  For conditions of distribution and use see copyright notice in license.txt */

#ifndef VERSION_H_
#define VERSION_H_

/** version.h */

class t_version : public Singleton<t_version>
{
	friend class Singleton<t_version>;
protected:
	t_version();
public:
	/** date of this version of the code as a string */
	char chDate[INPUT_LINE_LENGTH];

	/** version string of this version of the code */
	char chVersion[INPUT_LINE_LENGTH];

	/** normally zero, non-zero if this is a beta test version */
	long int nBetaVer;

	/** is this a release branch?  if so do not execute performance monitors */
	bool lgReleaseBranch;

	/** is this a release version?  if so do not print some internal comments */
	bool lgRelease;

	/** information about when and how the code was compiled, including
	 * compiler version */
	char chInfo[INPUT_LINE_LENGTH];
};

#endif /* VERSION_H_ */
