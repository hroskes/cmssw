#!/usr/bin/env python

from array import array
from collections import namedtuple
import os

import ROOT

from Alignment.OfflineValidation.TkAlAllInOneTool.helperFunctions import cache, mkdir_p

ROOT.gROOT.ProcessLine("#include <Alignment/OfflineValidation/plugins/TkAlStyle.cc>")

class WrongSubdetError(Exception): pass

@cache
def position(filename, subdetid, side=None):
  f = ROOT.TFile.Open(filename)
  t = f.alignTree
  entries = set()
  for i, entry in enumerate(t):
    if t.sublevel == subdetid and (side is None or side*t.z > 0):
      entries.add(i)
  if len(entries) == 0: raise WrongSubdetError  #this subdetector was not included in the validation
  assert len(entries) == 1, entries

  t.GetEntry(entries.pop())
  result = ROOT.TVector3(t.x-t.dx, t.y-t.dy, t.z-t.dz)
  if subdetid in (2, 4, 6): #FPIX, TID, TEC - subtract ideal z position
    result -= ROOT.TVector3(0, 0, t.z)

  return result

class Barycenter(namedtuple("Barycenter", "filename title color style x leftorright")):
  @cache
  def y(self, axis, subdetid, side, subtractTOB):
    result = getattr(position(self.filename, subdetid, side), axis.upper())() * 10
    if subtractTOB: result -= getattr(position(self.filename, 5, side=None), axis.upper())() * 10
    return result
  @cache
  def graph(self, *args):
    x = array("d", [self.x])
    y = array("d", [self.y(*args)])
    g = ROOT.TGraph(1, x, y)
    g.SetMarkerColor(self.color)
    g.SetMarkerStyle(self.style)
    g.SetMarkerSize(3)
    return g

  @cache
  def text(self, axis, subdetid, side, xrange, yrange, subtractTOB):
    args = axis, subdetid, side, subtractTOB
    xoffset = .07 * xrange / 2.5
    xsize = .4 * xrange / 2.5
    if self.leftorright == "right":
      x1, x2 = self.x+xoffset, self.x+xoffset+xsize
      align = 12
    elif self.leftorright == "left":
      x1, x2 = self.x-xoffset-xsize, self.x-xoffset
      align = 32
    yoffset = .6 * yrange / 8
    y1, y2 = self.y(*args)+yoffset, self.y(*args)-yoffset
    pt = ROOT.TPaveText(x1, y1, x2, y2, "br")
    pt.SetTextAlign(align)
    pt.SetTextColor(self.color)
    pt.SetTextFont(42)
    for thing in self.title, "{:.2f}".format(self.y(*args)):
      text = pt.AddText(thing)
      text.SetTextSize(0.05)
      text.SetTextColor(self.color)
    pt.SetBorderSize(0)
    pt.SetFillStyle(0)
    return pt

  def addtolegend(self, legend, *args):
    legend.AddEntry(self.graph(*args), self.title, "p")

def plotsubdetcenter(xmin, xmax, saveasdir, subtractTOB, *alignments):
  c = ROOT.TCanvas()
  mkdir_p(saveasdir)
  with open(os.path.join(saveasdir, "BarycenterComparisonSummary.txt"), "w") as summaryfile:
    summaryfile.write("(mm)")
    for alignment in alignments:
      summaryfile.write("\t"+alignment.title.replace("#", "\\"))
    summaryfile.write("\tformat={}\tlatexformat={}\n")

    if ROOT.TkAlStyle.status() == ROOT.NO_STATUS:
      ROOT.TkAlStyle.set(ROOT.INTERNAL)

    for subdetid, subdet in enumerate(("BPIX", "FPIX", "TIB", "TID", "TOB", "TEC"), start=1):
      if subdet == "TOB" and subtractTOB: continue
      if subdet in ("BPIX", "TIB", "TOB"):
        sides = None,
      else:
        sides = -1, 1

      for side in sides:
        if side ==    1: sidename = "+"
        if side ==   -1: sidename = "-"
        if side is None: sidename = ""
        for axis in "xyz":
          print "{}{}".format(subdet, sidename), axis

          summaryfile.write("{:>4}{:<1} {}\t".format(subdet, sidename, axis))
          summaryfile.write("latexname={:>4}${:<1}$ ${}$\t".format(subdet, sidename, axis))
          summaryfile.write("format={:>5.2f}\tlatexformat=${:.2f}$")
          for alignment in alignments:
            summaryfile.write("\t"+str(alignment.y(axis, subdetid, side, subtractTOB)))
          summaryfile.write("\n")

          mg = ROOT.TMultiGraph()
          try:
            for alignment in alignments:
              mg.Add(alignment.graph(axis, subdetid, side, subtractTOB))
          except WrongSubdetError:
            continue #subdetector was not included in the validation
          if xmin is None: xmin = min(alignment.x for alignment in alignments)
          if xmax is None: xmax = max(alignment.x for alignment in alignments)
          ymin = min([alignment.y(axis, subdetid, side, subtractTOB) for alignment in alignments]+[0])
          ymax = max([alignment.y(axis, subdetid, side, subtractTOB) for alignment in alignments]+[0])
          if ymin == ymax: ymax += .1
          x = array("d", [xmin, xmax, xmax])
          y = array("d", [0, ymin - .1*(ymax-ymin), ymax + .1*(ymax-ymin)])
          assert len(x) == len(y) == 3, (x, y)
          g = ROOT.TGraph(3, x, y)
          g.SetMarkerSize(0)
          g.SetMarkerStyle(20)  #default marker style is not resizable, even to 0
          mg.Add(g)
          mg.Draw("AP")
          mg.GetHistogram().GetXaxis().SetTickLength(0)
          mg.GetHistogram().GetXaxis().SetLabelOffset(999)
          ymin = mg.GetHistogram().GetMinimum()
          ymax = mg.GetHistogram().GetMaximum()
          #xmin = mg.GetXaxis().GetXmin()
          #xmax = mg.GetXaxis().GetXmax()
          title = "{axis}({subdet}{side}{ideal})"
          if subtractTOB: title += " - {axis}(TOB) [mm]"
          title = title.format(axis=axis, subdet=subdet, side=sidename, ideal=(" - ideal" if subdet in ("FPIX", "TID", "TEC") and axis == "z" else ""))
          mg.GetYaxis().SetTitle(title)
          for alignment in alignments:
            alignment.text(axis, subdetid, side, xrange=xmax-xmin, yrange=ymax-ymin, subtractTOB=subtractTOB).Draw()
          ROOT.TkAlStyle.drawStandardTitle()
          for ext in "png eps root pdf".split():
            c.SaveAs(os.path.join(saveasdir, subdet+sidename+axis+"."+ext))
