#include <Riostream.h>
#include "TROOT.h"
#include "HIPplots.h"
	

void plotter(int j, bool only_plotting=false){
  
  char base_path[512],path[512],tag[256],dir[256],outpath[512];
  
  sprintf(base_path,"/afs/cern.ch/cms/CAF/CMSALCA/ALCA_TRACKERALIGN2/HIP/xiaomeng/CMSSW_7_4_0_pre6/src/Alignment/HIPAlignmentAlgorithm/");
  sprintf(dir,"craftnoAPE");
  //sprintf(base_path,"/afs/cern.ch/cms/CAF/CMSALCA/ALCA_TRACKERALIGN/HIP/benedetta/output/pvc/"); 
  //sprintf(dir,"step1");
	TString detname [6]= {"PXB","PXF","TIB","TID","TOB","TEC"};
  sprintf(tag,"%s_%s",dir,detname[j].Data());

  //sprintf(tag,"newLA_TOB");
  sprintf(path,"%s/%s/main",base_path,dir);
  sprintf(outpath,"%s/HIP_plots_%s.root",path,tag);
  cout<<"Path is "<<path<<endl;

  HIPplots *c=new HIPplots(path,outpath);
  int ierr=0;
  c->CheckFiles(ierr);
  if(ierr>0){
    cout<<" ERROR !!!! Missing "<<ierr<<" files. Aborting."<<endl;
    return;
  }
  else if(ierr<0){
    if(!only_plotting){
      cout<<"ERROR !!!! Output file exists already. I don't want to overwrite."<<endl;
      cout<<"Please, change name of output file or delete the old one: "<<outpath<<endl;
      cout<<"Aborting."<<endl;
      return;
    }
  }
  
  if(!only_plotting){
    //========= Produce histograms ============
    for (int i = 0; i < 6; i++){
      // c->extractAlignParams( i,20, 1);
     c->extractAlignParams( i,0,j+1);
  //   c->extractAlignParams( i,0);
      // c->extractAlignShifts( i, 20 ,5);
    }
    
    // c->extractAlignableChiSquare( 20, 1);
    //c->extractAlignableChiSquare( 0,j+1);
    c->extractAlignableChiSquare( 0);
  }
  
  cout<<"\n\nSTARTING TO PLOT "<<endl<<endl;


  gROOT->ProcessLine(" .L tdrstyle.C");
  gROOT->ProcessLine("setTDRStyle()");

  sprintf(path,"%s/%s/psfiles/",base_path,dir);
  for(int i=1;i<=6;++i){//loop over subdets
     c->plotHitMap(path,i,0);
  }

  
  
  sprintf(outpath,"%s/parsViters_%s.png",path,tag);
  c->plotAlignParams( "PARAMS", outpath);	
  
  // sprintf(outpath,"%s/shiftsViters_%s.ps",path,tag);
  // c->plotAlignParams( "SHIFTS", outpath);
  
  // int iter_you_want_to_plot=1;
  // sprintf(outpath,"%s/shiftsAtIter%d_%s.ps",path,iter_you_want_to_plot,tag);
  //  c->plotAlignParamsAtIter( iter_you_want_to_plot, "SHIFTS", outpath );
   
  sprintf(outpath,"%s/AlignableChi2n_%s",path,tag);//do not put the file extension here!!!!
  c->plotAlignableChiSquare(outpath ,0.1);

  cout<<"Deleting... "<<flush;
  delete c;
  cout<<"cleaned up HIPplots object ! We are done  and good luck !"<<endl;

  
}
