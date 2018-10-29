#ifndef PROCESSTESTSIGNAL_H 
#define PROCESSTESTSIGNAL_H 1

// Include files

#include "L1Trigger/RPCTechnicalTrigger/interface/RBCInput.h" 
#include "L1Trigger/RPCTechnicalTrigger/interface/RPCInputSignal.h"
#include "L1Trigger/RPCTechnicalTrigger/interface/RPCData.h"
#include "L1Trigger/RPCTechnicalTrigger/interface/ProcessInputSignal.h"

#include <cstdlib>
#include <iostream>
#include <fstream>
#include <ios>
#include <cmath>
#include <vector>


/** @class ProcessTestSignal ProcessTestSignal.h
 *  
 * 
 *
 *
 *
 *  @author Andres Osorio
 *  @date   2008-11-14
 */
class ProcessTestSignal : public ProcessInputSignal {
public: 
  /// Standard constructor
  ProcessTestSignal( ) { }; 
  
  ProcessTestSignal( const char * );
  
  ~ProcessTestSignal( ) override; ///< Destructor
  
  int  next() override;
  
  void rewind();
  
  void showfirst();
  
  void reset();
  
  RPCInputSignal * retrievedata() override {
    return  m_lbin;
  };
  
  void mask() {};
  void force() {};
  
protected:
  
private:
  
  void builddata();
  
  std::ifstream * m_in;
  
  RPCData  * m_block;
  
  RBCInput * m_rbcinput;
  
  RPCInputSignal * m_lbin;
  
  std::vector<RPCData*> m_vecdata;
  
  std::map<int,RBCInput*> m_data;
  
  
};
#endif // PROCESSTESTSIGNAL_H
