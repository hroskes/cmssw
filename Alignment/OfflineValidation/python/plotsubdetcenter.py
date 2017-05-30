#!/usr/bin/env python

from array import array
from collections import namedtuple
import os

import ROOT

from Alignment.OfflineValidation.TkAlAllInOneTool.helperFunctions import cache, mkdir_p

class WrongSubdetError(Exception): pass

@cache
def position(filename, subdetid, side=None):
  f = ROOT.TFile.Open(filename)
  t = f.alignTree
  entries = set()
  for i, entry in enumerate(t):
    print t.sublevel == subdetid and (side is None or side*t.z > 0), t.sublevel, subdetid, t.z, side
    if t.sublevel == subdetid and (side is None or side*t.z > 0):
      entries.add(i)
  if len(entries) == 0: raise WrongSubdetError  #this subdetector was not included in the validation
  assert len(entries) == 1, entries

  t.GetEntry(entries.pop())
  result = ROOT.TVector3(t.x+t.dx, t.y+t.dy, t.z+t.dz)
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
  def text(self, axis, subdetid, side, yrange, subtractTOB):
    args = axis, subdetid, side, subtractTOB
    if self.leftorright == "left":
      x1, x2 = self.x+.1, self.x+.5
      align = 12
    elif self.leftorright == "right":
      x1, x2 = self.x-.5, self.x-.1
      align = 32
    yoffset = .4 * yrange / 8
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
  for axis in "xyz":
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
        mg = ROOT.TMultiGraph()
        try:
          for alignment in alignments:
            mg.Add(alignment.graph(axis, subdetid, side, subtractTOB))
        except WrongSubdetError:
          continue #subdetector was not included in the validation
        mg.Draw("AP")
        if xmin is None: xmin = mg.GetXaxis().GetXmin()
        if xmax is None: xmax = mg.GetXaxis().GetXmax()
        mg.GetXaxis().SetRangeUser(xmin, xmax)
        mg.Draw("AP")
        c.Update()
        mg.GetHistogram().GetXaxis().SetTickLength(0)
        mg.GetHistogram().GetXaxis().SetLabelOffset(999)
        ymin = mg.GetHistogram().GetMinimum()
        ymax = mg.GetHistogram().GetMaximum()
        title = "{axis}({subdet}{side}{ideal})"
        if subtractTOB: title += " - {axis}(TOB) [mm]"
        title = title.format(axis=axis, subdet=subdet, side=sidename, ideal=(" - ideal" if subdet in ("FPIX", "TID", "TEC") and axis == "z" else ""))
        mg.GetYaxis().SetTitle(title)
        for alignment in alignments:
          alignment.text(axis, subdetid, side, yrange=ymax-ymin, subtractTOB=subtractTOB).Draw()
        for ext in "png eps root pdf".split():
          c.SaveAs(os.path.join(saveasdir, subdet+sidename+axis+"."+ext))

if __name__ == "__main__":
  makeplots()
