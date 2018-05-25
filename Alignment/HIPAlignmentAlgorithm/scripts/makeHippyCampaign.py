#!/usr/bin/env python

import argparse
import contextlib
import errno
import glob
import os
import re
import shutil
import stat
import subprocess
import sys

basedir = "/afs/cern.ch/cms/CAF/CMSALCA/ALCA_TRACKERALIGN2/HipPy"

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("foldername", help="folder name for the campaign.  Example: CRUZET20xy")
  parser.add_argument("--cmssw", default=os.environ["CMSSW_VERSION"])
  parser.add_argument("--scram-arch", default=os.environ["SCRAM_ARCH"])
  parser.add_argument("--subfolder", default="", help="subfolder within "+basedir+" to make 'foldername' in.")
  parser.add_argument("--merge-topic", action="append", help="things to cms-merge-topic within the CMSSW release created")
  parser.add_argument("--print-sys-path", action="store_true", help=argparse.SUPPRESS) #internal, don't use this
  args = parser.parse_args()

  if args.print_sys_path:
    print repr(sys.path)
    return

  folder = os.path.join(basedir, args.subfolder, args.foldername)

  mkdir_p(folder)

  with cd(folder):
    if not os.path.exists(args.cmssw):
      os.environ["SCRAM_ARCH"] = args.scram_arch
      subprocess.check_call(["scram", "p", "CMSSW", args.cmssw])
    with cd(args.cmssw):
       cmsenv()
       for _ in args.merge_topic:
         subprocess.check_call(["git", "cms-merge-topic", _])
       subprocess.check_call(["scram", "b", "-j", "10"])

       if os.path.exists("src/Alignment/HIPAlignmentAlgorithm"):
         HIPAlignmentAlgorithm = os.path.abspath("src/Alignment/HIPAlignmentAlgorithm")
       else:
         with cd(os.environ["CMSSW_RELEASE_BASE"]):
           HIPAlignmentAlgorithm = os.path.abspath("src/Alignment/HIPAlignmentAlgorithm")

       assert os.path.exists(HIPAlignmentAlgorithm), HIPAlignmentAlgorithm

    mkdir_p("Jobs")
    mkdir_p("run")

    commit = False

    with cd("run"):
      subprocess.check_call(["git", "init"])

      mkdir_p("Configurations")
      with cd("Configurations"):
        if not os.path.exists("align_tpl_py.txt"):
          shutil.copy(os.path.join(HIPAlignmentAlgorithm, "python", "align_tpl_py.txt"), ".")
          subprocess.check_call(["git", "add", "align_tpl_py.txt"])
          commit = True
        if not os.path.exists("common_cff_py_TEMPLATE.txt"):
          shutil.copy(os.path.join(HIPAlignmentAlgorithm, "python", "common_cff_py.txt"), "common_cff_py_TEMPLATE.txt")
          subprocess.check_call(["git", "add", "common_cff_py_TEMPLATE.txt"])
          commit = True
        mkdir_p("TrackSelection")
        with cd("TrackSelection"):
          for _ in glob.iglob(os.path.join(HIPAlignmentAlgorithm, "python", "*TrackSelection_cff_py.txt")):
            if not os.path.exists(os.path.basename(_)):
              shutil.copy(_, ".")
              subprocess.check_call(["git", "add", os.path.basename(_)])
              commit = True

      mkdir_p("DataFiles")
      with cd("DataFiles"):
        if not os.path.exists("data_example.lst"):
          with open("data_example.lst", "w") as f:
            f.write(os.path.join(os.getcwd(), "minbias.txt") + ",,MBVertex,Datatype:0\n")
            f.write(os.path.join(os.getcwd(), "cosmics.txt") + ",,COSMICS,Datatype:1 APVMode:deco Bfield:3.8T\n")
            f.write(os.path.join(os.getcwd(), "CDCs.txt") + ",,CDCS,Datatype:1 APVMode:deco Bfield:3.8T\n")
          subprocess.check_call(["git", "add", "data_example.lst"])
          commit = True

      mkdir_p("IOV")
      with cd("IOV"):
        if not os.path.exists("RunXXXXXX"):
          with open("RunXXXXXX", "w") as f:
            f.write("XXXXXX")
          subprocess.check_call(["git", "add", "RunXXXXXX"])
          commit = True

      if not os.path.exists("submit_template.sh"):
        shutil.copy(os.path.join(HIPAlignmentAlgorithm, "test", "hippysubmittertemplate.sh"), "submit_template.sh")
        os.chmod("submit_template.sh", os.stat("submit_template.sh").st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        commit = True

      if commit: subprocess.check_call(["git", "commit", "-m", "commit templates"])

def mkdir_p(path):
  """http://stackoverflow.com/a/600612/5228524"""
  try:
    os.makedirs(path)
  except OSError as exc:
    if exc.errno == errno.EEXIST and os.path.isdir(path):
      pass
    else:
      raise

@contextlib.contextmanager
def cd(newdir):
  """http://stackoverflow.com/a/24176022/5228524"""
  prevdir = os.getcwd()
  os.chdir(os.path.expanduser(newdir))
  try:
    yield
  finally:
    os.chdir(prevdir)

def cmsenv():
  output = subprocess.check_output(["scram", "ru", "-sh"])
  for line in output.split(";\n"):
    if not line.strip(): continue
    match = re.match(r'^export (\w*)="([^"]*)"$', line)
    if not match: raise ValueError("Bad scram ru -sh line:\n"+line)
    variable, value = match.groups()
    os.environ[variable] = value
  sys.path[:] = eval(subprocess.check_output([__file__, "dummy", "--print-sys-path"]))

if __name__ == "__main__":
  main()
