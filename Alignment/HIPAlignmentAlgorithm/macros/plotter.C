#include <Riostream.h>
#include "TROOT.h"
#include "Alignment/HIPAlignmentAlgorithm/interface/HIPplots.h"
	

void plotter(TString jobdir, int j, bool only_plotting=false){

  char path[512],tag[256],outpath[512];

  while (jobdir.EndsWith("/"))
    jobdir.Chop();

  TString base_path = jobdir;
  base_path.Remove(base_path.Last('/'));
  while (base_path.EndsWith("/"))
    base_path.Chop();

  TString dir = jobdir;
  dir.Remove(0, dir.Last('/') + 1);

  TString detname [6]= {"PXB","PXF","TIB","TID","TOB","TEC"};
  sprintf(tag,"%s_%s",dir.Data(),detname[j].Data());

  //sprintf(tag,"newLA_TOB");
  sprintf(path,"%s/%s/main",base_path.Data(),dir.Data());
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

  sprintf(path,"%s/%s/psfiles/",base_path.Data(),dir.Data());
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

void plotter(TString jobdir, bool only_plotting = false)
{
    for (int i = 0; i < 6; i++)
        plotter(jobdir, i);
}
