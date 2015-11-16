#include "TCanvas.h"
#include "TFile.h"
#include "TH1F.h"
#include "THStack.h"
#include "TLegend.h"
#include "TStyle.h"
#include "TSystem.h"
#include "TTree.h"
#include <iostream>
#include <sstream>
#include <vector>
using namespace std;

const int nsubdets = 6;
const TString subdetnames[nsubdets] = {"BPIX", "FPIX", "TIB", "TID", "TOB", "TEC"};
const int maxnparams = 13;
const int nparams[nsubdets] = {3, 3, 3, 3, 13, 13};
//Actually some of TEC only has 3 parameters, but the result is the same: need 13 histograms
const TString parameternames[maxnparams] = {"sagittaX", "sagittaXY", "sagittaY", 
                                            //see comments at the top of Geometry/CommonTopologies/interface/TwoBowedSurfacesDeformation.h
                                            "deltau", "deltav", "deltaw", "deltaalpha", "deltabeta", "deltagamma",
                                            "deltasagittaX", "deltasagittaXY", "deltasagittaY", "ySplit"
};
const TString parametertitles[maxnparams] = {"sagitta_{X}", "sagitta_{XY}", "sagitta_{Y}", 
                                             "#Deltau", "#Deltav", "#Deltaw", "#Delta#alpha", "#Delta#beta", "#Delta#gamma",
                                             "#Deltasagitta_{X}", "#Deltasagitta_{XY}", "#Deltasagitta_{Y}", "ySplit"
};
const TString parameterunits[maxnparams] = {"#mum", "#mum", "#mum",
                                            "#mum", "#mum", "#mum", "mrad", "mrad", "mrad",
                                            "#mum", "#mum", "#mum", "#mum"
};
const double parameterscaleby[maxnparams] = {1e4, 1e4, 1e4,
                                             1e4, 1e4, 1e4, 1e3, 1e3, 1e3,
                                             1e4, 1e4, 1e4, 1e4};
const double xmax[maxnparams] = {100, 100, 100,
                                 100, 100, 100, 10, 10, 10,
                                 100, 100, 100, 100};
const int bins = 50;

vector<double> zerovector3(3);
vector<double> zerovector13(13);

void style(bool statbox)
{
    gStyle->SetCanvasDefH(600);
    gStyle->SetCanvasDefW(600);
    gStyle->SetCanvasDefX(0);
    gStyle->SetCanvasDefY(0);
    gStyle->SetHistLineColor(1);
    if (!statbox)
        gStyle->SetOptStat(0);
    gStyle->SetStatColor(kWhite);
    gStyle->SetStatFont(42);
    gStyle->SetStatFontSize(0.025);
    gStyle->SetStatTextColor(1);
    gStyle->SetStatFormat("6.4g");
    gStyle->SetStatBorderSize(1);
    gStyle->SetStatH(0.2);
    gStyle->SetStatW(0.2);
    gStyle->SetPadTopMargin(0.05);
    gStyle->SetPadBottomMargin(0.13);
    gStyle->SetPadLeftMargin(0.16);
    gStyle->SetPadRightMargin(0.02);
    gStyle->SetAxisColor(1, "XYZ");
    gStyle->SetStripDecimals(kTRUE);
    gStyle->SetTickLength(0.03, "XYZ");
    gStyle->SetNdivisions(510, "XYZ");
    gStyle->SetPadTickX(1);
    gStyle->SetPadTickY(1);
}

void compareSurfaceDeformations(TString file1, TString file2, TString plotsdir)
//sign of the plot: file1 - file2
{
    style(true);
    TFile *f = TFile::Open(file1);
    TFile *f2 = TFile::Open(file2);
    TTree *t = (TTree*)f->Get("alignTreeDeformations");
    TTree *t2 = (TTree*)f2->Get("alignTreeDeformations");
    int irawid, subdet, irawid2, subdet2;
    vector<double> *dpar = 0, *dpar2 = 0;
    t->SetBranchAddress("dpar", &dpar);
    t->SetBranchAddress("irawid", &irawid);
    t->SetBranchAddress("subdetid", &subdet);
    t2->SetBranchAddress("dpar", &dpar2);
    t2->SetBranchAddress("irawid", &irawid2);
    t2->SetBranchAddress("subdetid", &subdet2);
    TH1F *h[nsubdets][maxnparams] = {{0}};
    for (int l = 0; l < nsubdets; l++)
    {
        for (int k = 0; k < nparams[l]; k++)
        {
            stringstream sname, stitle;
            sname << "h" << l << k;
            stitle << ";" << parametertitles[k] << "(" << parameterunits[k] << ");number of modules / " << 2 * xmax[k] / bins << " " << parameterunits[k];
            h[l][k] = new TH1F(TString(sname.str()), TString(stitle.str()), bins, -xmax[k], xmax[k]);
            h[l][k]->SetLineColor(1);
        }
    }
    vector<bool> usedentryt2(t2->GetEntries());
    for (int i = 0; i < t->GetEntries(); i++)
    {
        t->GetEntry(i);
        for (int j = 0; j < t2->GetEntries(); j++)
        {
            if (usedentryt2[j]) continue;
            t2->GetEntry(j);
            if (irawid == irawid2)
            {
                usedentryt2[j] = true;
                break;
            }
        }
        if (irawid != irawid2)    //objects with no surface deformations are not written to the tree
        {
            if (dpar->size() == 3)
                dpar2 = &zerovector3;
            else if (dpar->size() == 13)
                dpar2 = &zerovector13;
            else
            {
                cout << "There is a problem, dpar has size " << dpar->size() << endl;
                return;
            }
        }

        for (unsigned int k = 0; k < dpar->size(); k++)
            h[subdet-1][k]->Fill((dpar->at(k) - dpar2->at(k))*parameterscaleby[k]);
            //will give a segfault if a pixel or inner strip has 13 parameters!
    }
    //Find the ones in the second tree that were not in the first tree, if any
    for (int j = 0; j < t2->GetEntries(); j++)
    {
        if (!usedentryt2[j])
        {
            t2->GetEntry(j);
            for (unsigned int k = 0; k < dpar2->size(); k++)
                h[subdet2-1][k]->Fill((0 - dpar2->at(k))*parameterscaleby[k]);
        }
    }

    TCanvas *c1 = new TCanvas();
    for (int l = 0; l < nsubdets; l++)
    {
        TString subdetdir = plotsdir + "/" + subdetnames[l];
        gSystem->mkdir(subdetdir, true);
        for (int k = 0; k < nparams[l]; k++)
        {
            h[l][k]->Draw();
            TString saveasbase = subdetdir + "/";
            if (nparams[l] > 10 && k < 10) saveasbase += "0";
            saveasbase += TString::Itoa(k, 10) + "_" + parameternames[k];
            c1->SaveAs(saveasbase + ".png");
            c1->SaveAs(saveasbase + ".eps");
            c1->SaveAs(saveasbase + ".pdf");
            c1->SaveAs(saveasbase + ".root");
            delete h[l][k];
        }
    }
    delete c1;
}

void compareSurfaceDeformations(vector<TString> files, vector<TString> titles, vector<int> colors, vector<int> linestyles, TString plotsdir)
{
    style(false);
    if (files.size() != titles.size() || files.size() != colors.size() || files.size() != linestyles.size())
    {
        cout << "files, titles, colors, and linestyles all need to be the same size!" << endl;
        return;
    }
    THStack *hstack[nsubdets][maxnparams];
    TLegend *leg[nsubdets][maxnparams];
    for (int l = 0; l < nsubdets; l++)
    {
        for (int k = 0; k < nparams[l]; k++)
        {
            stringstream sname, stitle;
            sname << "h" << l << k;
            stitle << ";" << parametertitles[k] << "(" << parameterunits[k] << ");number of modules / " << 2 * xmax[k] / bins << " " << parameterunits[k];
            hstack[l][k] = new THStack(TString(sname.str()), TString(stitle.str()));
            float lxmin = 0.22, lxwidth = 0.68;
            float lymax = 0.9, lywidth = 0.15*files.size()/3;
            float lxmax = lxmin + lxwidth;
            float lymin = lymax - lywidth;
            leg[l][k] = new TLegend(lxmin, lymin, lxmax, lymax);
            leg[l][k]->SetBorderSize(0);
            leg[l][k]->SetTextFont(42);
            leg[l][k]->SetLineColor(1);
            leg[l][k]->SetLineStyle(1);
            leg[l][k]->SetLineWidth(1);
            leg[l][k]->SetFillColor(0);
            leg[l][k]->SetFillStyle(0);
            leg[l][k]->SetNColumns(2);
        }
    }
    auto h = new TH1F*[files.size()][nsubdets][maxnparams];
    for (unsigned int i = 0; i < files.size(); i++)
    {
        vector<double> *dpar = 0;
        int subdet;
        for (int l = 0; l < nsubdets; l++)
        {
            for (int k = 0; k < nparams[l]; k++)
            {
                h[i][l][k] = new TH1F(titles[i] + subdetnames[l] + parameternames[k], "", 50, -xmax[k], xmax[k]);
                h[i][l][k]->SetLineColor(colors[i]);
                hstack[l][k]->Add(h[i][l][k]);
            }
        }

        TFile *f = TFile::Open(files[i]);
        TTree *t = (TTree*)f->Get("alignTreeDeformations");
        t->SetBranchAddress("dpar", &dpar);
        t->SetBranchAddress("subdetid", &subdet);

        const int length = t->GetEntries();
        for (int j = 0; j < length; j++)
        {
            t->GetEntry(j);
            for (unsigned int k = 0; k < dpar->size(); k++)
                h[i][subdet-1][k]->Fill(dpar->at(k)*parameterscaleby[k]);
        }
        delete f;
        for (int l = 0; l < nsubdets; l++)
        {
            for (int k = 0; k < nparams[l]; k++)
            {
                h[i][l][k]->SetMinimum(0);
                h[i][l][k]->SetMaximum(h[i][l][k]->GetMaximum() * 1.4);
                leg[l][k]->AddEntry(h[i][l][k], titles[i], "l");
                stringstream meanrms;
                meanrms << "#mu=" << h[i][l][k]->GetMean() << ", rms=" << h[i][l][k]->GetRMS();
                leg[l][k]->AddEntry((TObject*)0, meanrms.str().c_str(), "");
            }
        }
    }

    TCanvas *c1 = new TCanvas();
    for (int l = 0; l < nsubdets; l++)
    {
        TString subdetdir = plotsdir + "/" + subdetnames[l];
        gSystem->mkdir(subdetdir, true);
        for (int k = 0; k < nparams[l]; k++)
        {
            hstack[l][k]->Draw("nostack");
            leg[l][k]->Draw();
            TString saveasbase = subdetdir + "/";
            if (nparams[l] > 10 && k < 10) saveasbase += "0";
            saveasbase += TString::Itoa(k, 10) + "_" + parameternames[k];
            c1->SaveAs(saveasbase + ".png");
            c1->SaveAs(saveasbase + ".eps");
            c1->SaveAs(saveasbase + ".pdf");
            c1->SaveAs(saveasbase + ".root");
            delete hstack[l][k];
            delete leg[l][k];
            for (unsigned int i = 0; i < files.size(); i++)
                delete h[i][l][k];
        }
    }
    delete[] h;
    delete c1;
}
