#ifndef Alignment_CommonAlignment_AlignmentUserVariables_h
#define Alignment_CommonAlignment_AlignmentUserVariables_h

#include "CommonTools/Utils/interface/CloneInherit.h"

/// (Abstract) Base class for alignment algorithm user variables

class AlignmentUserVariables 
{

public:
  virtual ~AlignmentUserVariables() {}
  //derived class should inherit from CloneInherit<MyAlignmentUserVariablesClass, AlignmentUserVariables>
  //then this will be automatically defined for the inherited class
  std::unique_ptr<AlignmentUserVariables> clone() const {
    return std::unique_ptr<AlignmentUserVariables>(static_cast<AlignmentUserVariables*>(this->cloneImpl()));
  }
  virtual AlignmentUserVariables* cloneImpl( void ) const = 0;

};

#endif

