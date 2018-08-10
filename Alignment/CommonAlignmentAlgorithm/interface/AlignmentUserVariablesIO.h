#ifndef AlignmentUserVariablesIO_H
#define AlignmentUserVariablesIO_H

#include "Alignment/CommonAlignment/interface/Utilities.h"

/// \class AlignmentUserVariablesIO
///
/// Abstract base class for I/O of AlignmentUserVariables.
///
///  $Date: 2007/01/23 16:07:08 $
///  $Revision: 1.4 $
///  $Author: fronga $ (at least last update...)

class AlignmentUserVariables;

class AlignmentUserVariablesIO 
{

  protected:

  virtual ~AlignmentUserVariablesIO() {}

  /** open IO */
  virtual int open(const char* filename, int iteration, bool writemode) =0;

  /** close IO */
  virtual int close(void) =0;

  /** write AlignmentUserVariables of one Alignable */
  virtual int writeOne(Alignable* ali) =0;

  /** read AlignmentUserVariables of one Alignable*/
  virtual std::shared_ptr<AlignmentUserVariables> readOne(Alignable* ali, int& ierr) =0;

  /** write AlignmentUserVariables of many Alignables */
  int write(const align::Alignables& alivec, bool validCheck);

  /** read AlignmentUserVariables of many Alignables (using readOne, so take care of memory!) */
  std::vector<std::shared_ptr<AlignmentUserVariables>> read(const align::Alignables& alivec, int& ierr);

};

#endif
