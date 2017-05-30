from abc import abstractproperty
import os
import configTemplates
from genericValidation import GenericValidation, ValidationWithPlotsSummary
from helperFunctions import replaceByMap, getCommandOutput2, boolfromstring, cppboolstring, pythonboolstring
from TkAlExceptions import AllInOneError

class GeometryComparisonBase(GenericValidation):
    """
    Object representing a geometry comparison job.
    """
    defaults = {
        "moduleList": "/store/caf/user/cschomak/emptyModuleList.txt",
    }
    mandatories = {"levels"}

    def __init__( self, valName, alignment, referenceAlignment,
                  config, copyImages=True):
        """
        Constructor of the GeometryComparison class.

        Arguments:
        - `valName`: String which identifies individual validation instances
        - `alignment`: `Alignment` instance to validate
        - `referenceAlignment`: `Alignment` instance which is compared
                                with `alignment`
        - `config`: `BetterConfigParser` instance which includes the
                    configuration of the validations
        - `copyImages`: Boolean which indicates whether png- and pdf-files
                        should be copied back from the batch farm
        """

        super(GeometryComparisonBase, self).__init__(valName, alignment, config)
        self.referenceAlignment = referenceAlignment
        referenceName = "IDEAL"
        if not self.referenceAlignment == "IDEAL":
            referenceName = self.referenceAlignment.name

        allCompares = config.getCompares()
        self.compares = {}
        self.__filesToCompare = {}
        if valName in allCompares:
            self.compares[valName] = allCompares[valName]
        else:
            msg = ("Could not find compare section '%s' in '%s'"
                   %(valName, allCompares))
            raise AllInOneError(msg)
        self.copyImages = copyImages

    def getRepMap(self, alignment = None):
        if alignment == None:
            alignment = self.alignmentToValidate
        repMap = super(GeometryComparisonBase, self).getRepMap( alignment )
        referenceName  = "IDEAL"
        referenceTitle = "IDEAL"
        if not self.referenceAlignment == "IDEAL":
            referenceName  = self.referenceAlignment.name
            referenceTitle = self.referenceAlignment.title

        assert len(self.compares) == 1, self.compares #? not sure how it can be anything else, but just in case
        common = self.compares.keys()[0]

        repMap.update({
            "common": common,
            "comparedGeometry": (".oO[alignmentName]Oo."
                                 "ROOTGeometry.root"),
            "referenceGeometry": "IDEAL", # will be replaced later
                                          #  if not compared to IDEAL
            "reference": referenceName,
            "referenceTitle": referenceTitle,
            "alignmentTitle": self.alignmentToValidate.title,
            "moduleListBase": os.path.basename(repMap["moduleList"]),
            "outputFile": ".oO[name]Oo..Comparison_common.oO[common]Oo..root",
            "nIndex": "",
            })
        if not referenceName == "IDEAL":
            repMap["referenceGeometry"] = (".oO[reference]Oo."
                                           "ROOTGeometry.root")

        repMap["name"] += "_vs_.oO[reference]Oo."
        repMap["resultFile"] = os.path.expandvars(replaceByMap("/store/caf/user/$USER/.oO[eosdir]Oo./.oO[outputFile]Oo.",
                                                               repMap))
        return repMap

    @property
    def filesToCompare(self):
        return self.__filesToCompare

    def createConfiguration(self, path ):
        # self.compares
        repMap = self.getRepMap()
        cfgFileName = "TkAlCompareToNTuple.%s_cfg.py"%(
            self.alignmentToValidate.name)
        cfgs = {cfgFileName: configTemplates.intoNTuplesTemplate}
        repMaps = {cfgFileName: repMap}
        if not self.referenceAlignment == "IDEAL":
            referenceRepMap = self.getRepMap( self.referenceAlignment )
            cfgFileName = "TkAlCompareToNTuple.%s_cfg.py"%(
                self.referenceAlignment.name )
            cfgs[cfgFileName] = configTemplates.intoNTuplesTemplate
            repMaps[cfgFileName] = referenceRepMap

        cfgSchedule = cfgs.keys()
        for common in self.compares:
            repMap.update({
                           "levels": ", ".join('"{}"'.format(_) for _ in self.compares[common]),
                           })
            cfgName = replaceByMap(("TkAlCompareCommon.oO[common]Oo.."
                                    ".oO[name]Oo._cfg.py"),repMap)
            cfgs[cfgName] = configTemplates.compareTemplate
            repMaps[cfgName] = repMap

            cfgSchedule.append( cfgName )
        super(GeometryComparisonBase, self).createConfiguration(cfgs, path, cfgSchedule, repMaps = repMaps)

    def createScript(self, path):
        repMap = self.getRepMap()
        repMap["runComparisonScripts"] = ""
        scriptName = replaceByMap(("TkAlGeomCompare.%s..oO[name]Oo..sh"
                                   %self.name), repMap)

        repMap["CommandLine"]=""
        repMap["CommandLine"]+= \
                 "# copy module list required for comparison script \n"
        if repMap["moduleList"].startswith("/store"):
            repMap["CommandLine"]+= \
                 "xrdcp root://eoscms//eos/cms.oO[moduleList]Oo. .\n"
        elif repMap["moduleList"].startswith("root://"):
            repMap["CommandLine"]+= \
                 "xrdcp .oO[moduleList]Oo. .\n"
        else:
            repMap["CommandLine"]+= \
                     "rfcp .oO[moduleList]Oo. .\n"

        try:
            getCommandOutput2(replaceByMap("cd $(mktemp -d)\n.oO[CommandLine]Oo.\ncat .oO[moduleListBase]Oo.", repMap))
        except RuntimeError:
            raise AllInOneError(replaceByMap(".oO[moduleList]Oo. does not exist!", repMap))

        for cfg in self.configFiles:
            postProcess = ""
            repMap["CommandLine"]+= \
                repMap["CommandLineTemplate"]%{"cfgFile":cfg,
                                               "postProcess":postProcess}
        repMap["CommandLine"]+= ("# overall postprocessing\n"
                                 ".oO[runComparisonScripts]Oo.\n"
                                 )

        repMap["runComparisonScripts"] = self.runComparisonScripts

        scripts = {scriptName: replaceByMap( configTemplates.scriptTemplate, repMap )}
        return super(GeometryComparisonBase, self).createScript(scripts, path)

    @abstractproperty
    def runComparisonScripts(self):
        """Any plotting or other things that are done after creating the trees"""

    def createCrabCfg(self, path):
        msg = ("Parallelization not supported for geometry comparison. Please "
               "choose another 'jobmode'.")
        raise AllInOneError(msg)

class GeometryComparisonTrees(GeometryComparisonBase):
    """
    No restriction on allowed levels, but only makes the tree.
    Any plotting or analysis has to be done manually.
    """
    valType = "comparetree"
    @property
    def runComparisonScripts(self):
        return ""

class GeometryComparison(GeometryComparisonBase):
    """
    Object representing a standard, module level geometry comparison job.
    """
    defaults = {
        "3DSubdetector1":"1",
        "3DSubdetector2":"2",
        "3DTranslationalScaleFactor":"50",
        "modulesToPlot":"all",
        "useDefaultRange":"false",
        "plotOnlyGlobal":"false",
        "plotPng":"true",
        "makeProfilePlots":"true",
        "dx_min":"-99999",
        "dx_max":"-99999",
        "dy_min":"-99999",
        "dy_max":"-99999",
        "dz_min":"-99999",
        "dz_max":"-99999",
        "dr_min":"-99999",
        "dr_max":"-99999",
        "rdphi_min":"-99999",
        "rdphi_max":"-99999",
        "dalpha_min":"-99999",
        "dalpha_max":"-99999",
        "dbeta_min":"-99999",
        "dbeta_max":"-99999",
        "dgamma_min":"-99999",
        "dgamma_max":"-99999",
        }
    valType = "compare"
    def __init__( self, valName, alignment, referenceAlignment,
                  config, copyImages=True):
        super(GeometryComparison, self).__init__(valName, alignment, referenceAlignment, config, copyImages)
        for name in "useDefaultRange", "plotOnlyGlobal", "plotPng":
            self.general[name] = cppboolstring(self.general[name], name)

    @property
    def runComparisonScripts(self):
        repMap = self.getRepMap()
        y_ranges = ""
        plottedDifferences = ["dx","dy","dz","dr","rdphi","dalpha","dbeta","dgamma"]
        for diff in plottedDifferences:
                        y_ranges += ","+repMap["%s_min"%diff]
                        y_ranges += ","+repMap["%s_max"%diff]

        for name in self.compares:
            if  'DetUnit' in self.compares[name]:
                repMap["runComparisonScripts"] += \
                    ("rfcp .oO[Alignment/OfflineValidation]Oo."
                     "/scripts/comparisonScript.C .\n"
                     "rfcp .oO[Alignment/OfflineValidation]Oo."
                     "/scripts/GeometryComparisonPlotter.h .\n"
                     "rfcp .oO[Alignment/OfflineValidation]Oo."
                     "/scripts/GeometryComparisonPlotter.cc .\n"
                     "root -b -q 'comparisonScript.C+(\""
                     ".oO[name]Oo..Comparison_common"+name+".root\",\""
                     "./\",\".oO[modulesToPlot]Oo.\",\".oO[alignmentName]Oo.\",\".oO[reference]Oo.\",.oO[useDefaultRange]Oo.,.oO[plotOnlyGlobal]Oo.,.oO[plotPng]Oo.,.oO[makeProfilePlots]Oo."+y_ranges+")'\n"
                     "rfcp "+path+"/TkAl3DVisualization_.oO[common]Oo._.oO[name]Oo..C .\n"
                     "root -l -b -q TkAl3DVisualization_.oO[common]Oo._.oO[name]Oo..C+\n")
                if  self.copyImages:
                   repMap["runComparisonScripts"] += \
                       ("rfmkdir -p .oO[datadir]Oo./.oO[name]Oo."
                        ".Comparison_common"+name+"_Images\n")
                   repMap["runComparisonScripts"] += \
                       ("rfmkdir -p .oO[datadir]Oo./.oO[name]Oo."
                        ".Comparison_common"+name+"_Images/Translations\n")
                   repMap["runComparisonScripts"] += \
                       ("rfmkdir -p .oO[datadir]Oo./.oO[name]Oo."
                        ".Comparison_common"+name+"_Images/Rotations\n")


                   ### At the moment translations are images with suffix _1 and _2, rotations _3 and _4
                   ### The numeration depends on the order of the MakePlots(x, y) commands in comparisonScript.C
                   ### If comparisonScript.C is changed, check if the following lines need to be changed as well

                   if repMap["plotPng"] == "true":
                           repMap["runComparisonScripts"] += \
                               ("find . -maxdepth 1 -name \"*_1*\" "
                                "-print | xargs -I {} bash -c \"rfcp {} .oO[datadir]Oo."
                                "/.oO[name]Oo..Comparison_common"+name+"_Images/Translations/\" \n")
                           repMap["runComparisonScripts"] += \
                               ("find . -maxdepth 1 -name \"*_2*\" "
                                "-print | xargs -I {} bash -c \"rfcp {} .oO[datadir]Oo."
                                "/.oO[name]Oo..Comparison_common"+name+"_Images/Translations/\" \n")

                           repMap["runComparisonScripts"] += \
                               ("find . -maxdepth 1 -name \"*_3*\" "
                                "-print | xargs -I {} bash -c \"rfcp {} .oO[datadir]Oo."
                                "/.oO[name]Oo..Comparison_common"+name+"_Images/Rotations/\" \n")
                           repMap["runComparisonScripts"] += \
                               ("find . -maxdepth 1 -name \"*_4*\" "
                                "-print | xargs -I {} bash -c \"rfcp {} .oO[datadir]Oo."
                                "/.oO[name]Oo..Comparison_common"+name+"_Images/Rotations/\" \n")

                   else:
                           repMap["runComparisonScripts"] += \
                               ("find . -maxdepth 1 -name \"*_1*\" "
                                "-print | xargs -I {} bash -c \"rfcp {} .oO[datadir]Oo."
                                "/.oO[name]Oo..Comparison_common"+name+"_Images/Translations/\" \n")

                           repMap["runComparisonScripts"] += \
                               ("find . -maxdepth 1 -name \"*_2*\" "
                                "-print | xargs -I {} bash -c \"rfcp {} .oO[datadir]Oo."
                                "/.oO[name]Oo..Comparison_common"+name+"_Images/Rotations/\" \n")

                   repMap["runComparisonScripts"] += \
                       ("find . -maxdepth 1 -name "
                        "\"*.tex\" -print | xargs -I {} bash -c"
                        " \"rfcp {} .oO[datadir]Oo./.oO[name]Oo."
                        ".Comparison_common"+name+"_Images/\" \n")
                   repMap["runComparisonScripts"] += \
                       ("find . -maxdepth 1 -name "
                        "\"TkMap_SurfDeform*.pdf\" -print | xargs -I {} bash -c"
                        " \"rfcp {} .oO[datadir]Oo./.oO[name]Oo."
                        ".Comparison_common"+name+"_Images/\" \n")
                   repMap["runComparisonScripts"] += \
                       ("find . -maxdepth 1 -name "
                        "\"TkMap_SurfDeform*.png\" -print | xargs -I {} bash -c"
                        " \"rfcp {} .oO[datadir]Oo./.oO[name]Oo."
                        ".Comparison_common"+name+"_Images/\" \n")
                   repMap["runComparisonScripts"] += \
                       ("if [[ $HOSTNAME = lxplus[0-9]*[.a-z0-9]* ]]\n"
                        "then\n"
                        "    rfmkdir -p .oO[workdir]Oo./.oO[name]Oo.."+name
                        +"_ArrowPlots\n"
                        "else\n"
                        "    mkdir -p $CWD/TkAllInOneTool/.oO[name]Oo.."+name
                        +"_ArrowPlots\n"
                        "fi\n")
                   repMap["runComparisonScripts"] += \
                       ("rfcp .oO[Alignment/OfflineValidation]Oo."
                        "/scripts/makeArrowPlots.C "
                        ".\n"
                        "root -b -q 'makeArrowPlots.C(\""
                        ".oO[name]Oo..Comparison_common"+name
                        +".root\",\".oO[name]Oo.."
                        +name+"_ArrowPlots\")'\n")
                   repMap["runComparisonScripts"] += \
                       ("rfmkdir -p .oO[datadir]Oo./.oO[name]Oo."
                        ".Comparison_common"+name+"_Images/ArrowPlots\n")
                   repMap["runComparisonScripts"] += \
                       ("find .oO[name]Oo.."+name+"_ArrowPlots "
                        "-maxdepth 1 -name \"*.png\" -print | xargs -I {} bash "
                        "-c \"rfcp {} .oO[datadir]Oo./.oO[name]Oo."
                        ".Comparison_common"+name+"_Images/ArrowPlots\"\n")
                   repMap["runComparisonScripts"] += \
                       ("find . "
                        "-maxdepth 1 -name \".oO[common]Oo._.oO[name]Oo..Visualization_rotated.gif\" -print | xargs -I {} bash "
                        "-c \"rfcp {} .oO[datadir]Oo./.oO[name]Oo."
                        ".Comparison_common"+name+"_Images/.oO[common]Oo._.oO[name]Oo..Visualization.gif\"\n")

                resultingFile = replaceByMap(("/store/caf/user/$USER/.oO[eosdir]Oo./compared%s_"
                                              ".oO[name]Oo..root"%name), repMap)
                resultingFile = os.path.expandvars( resultingFile )
                resultingFile = os.path.abspath( resultingFile )
                resultingFile = "root://eoscms//eos/cms" + resultingFile   #needs to be AFTER abspath so that it doesn't eat the //
                self.__filesToCompare[ name ] = resultingFile

            else:
                raise AllInOneError("Need to have DetUnit in levels!")

        #~ print configTemplates.scriptTemplate
        files = {replaceByMap("TkAl3DVisualization_.oO[common]Oo._.oO[name]Oo..C", repMap ): replaceByMap(configTemplates.visualizationTrackerTemplate, repMap )}
        self.createFiles(files, path)
        return replaceByMap(".oO[runComparisonScripts]Oo.", repMap)

class BarycenterComparison(GeometryComparisonBase, ValidationWithPlotsSummary):
    valType = "barycenter"
    mandatories = {"xpos", "textside"}
    def __init__( self, valName, alignment, config):
        referenceAlignment = "IDEAL"
        super(BarycenterComparison, self).__init__(valName, alignment, referenceAlignment, config, True)

    @property
    def runComparisonScripts(self):
        #do some checking
        allowedlevels = ("P1PXBBarrel", "P1PXECEndcap", "TPBBarrel", "TPEEndcap",
                         "TIBBarrel", "TIDEndcap", "TOBBarrel", "TECEndcap")
        assert len(self.compares) == 1, self.compares #do this elsewhere, but we assume it again here
        if not all(_ in allowedlevels for _ in self.compares.values()[0]):
            raise AllInOneError("For a barycenter comparison the only allowed levels are:\n{}".format(", ".join(allowedlevels)))
        if self.subtractTOB and "TOBBarrel" not in self.compares.values()[0]:
            raise AllInOneError("You need to include TOBBarrel in levels or turn off subtractTOB in [plots:barycenter].")

        return "" #nothing is done at this stage, plots are made in the merge step

    @property
    def subtractTOB(self):
        return boolfromstring(self.getRepMap()["subtractTOB"], "subtractTOB")

    @classmethod
    def runPlots(cls, validations):
        return ("rfcp .oO[plottingscriptpath]Oo. .\n"
                "python .oO[plottingscriptname]Oo.")

    @classmethod
    def plottingscriptname(cls):
        return "TkAlCompareBarycenter.py"
    @classmethod
    def plottingscripttemplate(cls):
        return configTemplates.barycenterPlotTemplate
    @classmethod
    def plotsdirname(cls):
        return "BarycenterPlots"
    def appendToPlots(self):
        repmap = self.getRepMap()
        repmap.update(
            resultFile = repr(replaceByMap("root://eoscms//eos/cms.oO[resultFile]Oo.", repmap)),
            title = repr(replaceByMap(".oO[title]Oo.", repmap)),
            textside = repr(replaceByMap(".oO[textside]Oo.", repmap)).lower(),
        )
        if eval(repmap["textside"]) not in ["left", "right"]:  #eval to get rid of the quotes put in by repr
            raise AllInOneError("invalid textside {textside}, has to be left or right!".format(**repmap))
        return replaceByMap("    Barycenter(.oO[resultFile]Oo., .oO[title]Oo., .oO[color]Oo., .oO[style]Oo., .oO[xpos]Oo., .oO[textside]Oo.),\n",
                            repmap)
