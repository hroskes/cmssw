#include <vector>
#include <string>
#include <fstream>
#include "TCanvas.h"
#include "TCut.h"
#include "TDirectory.h"
#include "TFile.h"
#include "TGraph.h"
#include "TH1D.h"
#include "TH2F.h"
#include "TLegend.h"
#include "TMath.h"
#include "TMatrixD.h"
#include "TPad.h"
#include "TString.h"
#include "TStyle.h"
#include "TText.h"
#include "TTree.h"
#include "TVectorD.h"

class HIPplots{
public:
	HIPplots( TString path, TString outFile );
	void extractAlignParams( int i, int minHits = 0, int subDet = 0, int doubleSided = 0 );
	void extractAlignShifts( int i, int minHits = 0, int subDet = 0 );
	void plotAlignParams( TString ShiftsOrParams, TString plotName = "test.png" );
	void plotAlignParamsAtIter( int iter, TString ShiftsOrParams, TString plotName = "test.png" );
	void plotHitMap( TString outpath,int subDet,int minHits=0  );
	void extractAlignableChiSquare( int minHits=0, int subDet =0 , int doubleSided = 0 );
	void plotAlignableChiSquare( TString plotName ="testchi2.png",float minChi2n=-1.0);
	void extractSurveyResiduals( int currentPar,int subDet =0);
	void dumpAlignedModules(int nhits=0);
	void CheckFiles(int &ierr);
private:
	
	char _path[256];
	char _outFile[256];
	char _inFile_params[256];
	char _inFile_uservars[256];	
	char _inFile_truepos[256];
	char _inFile_alipos[256];	
	char _inFile_mispos[256];
	char _inFile_HIPalign[256];
	char _inFile_surveys[256];
	enum TKdetector_id{unknown=0,TPBid=1,TPEid=2,TIBid=3,TIDid=4,TOBid=5,TECid=6,ALLid=99};	
	
	int GetNIterations(TDirectory *f,TString tag,int startingcounter=0);
	int GetSubDet( unsigned int id );
        int GetBarrelLayer( unsigned int id );
	void SetMinMax( TH1* h );
	int FindPeaks(TH1F *h1,float *peaklist,const int maxNpeaks,int startbin=-1,int endbin=-1);
	void SetPeakThreshold(float newpeakthreshold);
	bool CheckFileExistence(TString filename);
	bool CheckHistoRising(TH1D *h);
	float peakthreshold;
	bool plotbadchi2;



};
