import math
#=================================
#inputs
globaltag = '74X_dataRun2_Prompt_v4'    #APEs are copied from this GT (and IdealGeometry is used)
inputsqlitefile = '/afs/cern.ch/cms/CAF/CMSALCA/ALCA_TRACKERALIGN2/HIP/xiaomeng/develop/CMSSW_7_4_12_patch4/src/Alignment/HIPAlignmentAlgorithm/hp1519.db'                  #if None, uses the GT alignment
alignmenttag = 'Alignments'             #tag name for TrackerAlignmentRcd in the input file, also used for the output file
runnumberalignmentIOV = 257968          #any run number in the iov that you want to start from



#misalignment amplitudes, -999 means no misalignment
#the commented numbers are the default magnitudes, which produce a maximum movement of around 600 microns
#see Alignment/TrackerAlignment/plugins/TrackerSystematicMisalignments.cc for definitions
#see also https://twiki.cern.ch/twiki/bin/viewauth/CMS/SystematicMisalignmentsofTracker
radialEpsilon            = -1000. # 5e-4
telescopeEpsilon         = -1000. # 5e-4
layerRotEpsilon          = -1000. # 9.43e-6               #cm^-1
modulatedLayerRotEpsilon = -1000.            #cm^-2
modulatedLayerRotDoubleSineEpsilon = -1000. # 3.46888e-8            #cm^-2
bowingEpsilon            = -1000. # 6.77e-9               #cm^-2
zExpEpsilon              = -1000. # 2.02e-4
twistEpsilon             = -1000. # 2.04e-6               #cm^-1
ellipticalEpsilon        = -5e-4 # 5e-4
skewEpsilon              = -1000. # 5.5e-2                #cm
sagittaEpsilon           = -1000. # 5.0e-4

#phases for phi dependent misalignments
ellipticalDelta          = -90.  #converted to radians later
skewDelta                = 0.
sagittaDelta             = 0.
modulatedLayerRotDelta   = 0.   #converted to radians later

outputfilename = 'dbfiles/trytofix/TEC+/hp1519_runDIOV3_elliptical_TEC+only_epsilon%s_delta%s.db' % (ellipticalEpsilon, ellipticalDelta)

#=================================




import FWCore.ParameterSet.Config as cms

process = cms.Process("TrackerSystematicMisalignments")
process.load("FWCore.MessageService.MessageLogger_cfi")

process.load("Configuration.Geometry.GeometryRecoDB_cff")

process.load("CondCore.DBCommon.CondDBSetup_cfi")
process.source = cms.Source("EmptySource",
                            firstRun=cms.untracked.uint32(runnumberalignmentIOV),
)

process.maxEvents = cms.untracked.PSet(
    input = cms.untracked.int32(1)
)

# initial geom
# configure the database file - use survey one for default
process.load("Configuration.StandardSequences.FrontierConditions_GlobalTag_condDBv2_cff")
process.GlobalTag.globaltag=globaltag
if inputsqlitefile is not None:
    process.GlobalTag.toGet = cms.VPSet(
                                        cms.PSet(
                                                 record = cms.string('TrackerAlignmentRcd'),
                                                 tag = cms.string(alignmenttag),
                                                 connect = cms.untracked.string('sqlite_file:'+inputsqlitefile),
                                        ),
    )


# input
process.load("Alignment.TrackerAlignment.TrackerSystematicMisalignments_cfi")
process.TrackerSystematicMisalignments.fromDBGeom = True

#uncomment one or more of these to apply the misalignment(s)

process.TrackerSystematicMisalignments.radialEpsilon     = radialEpsilon
process.TrackerSystematicMisalignments.telescopeEpsilon  = telescopeEpsilon
process.TrackerSystematicMisalignments.layerRotEpsilon   = layerRotEpsilon
process.TrackerSystematicMisalignments.modulatedLayerRotEpsilon   = modulatedLayerRotEpsilon
process.TrackerSystematicMisalignments.modulatedLayerRotDoubleSineEpsilon   = modulatedLayerRotDoubleSineEpsilon
process.TrackerSystematicMisalignments.bowingEpsilon     = bowingEpsilon
process.TrackerSystematicMisalignments.zExpEpsilon       = zExpEpsilon
process.TrackerSystematicMisalignments.twistEpsilon      = twistEpsilon
process.TrackerSystematicMisalignments.ellipticalEpsilon = ellipticalEpsilon
process.TrackerSystematicMisalignments.skewEpsilon       = skewEpsilon
process.TrackerSystematicMisalignments.sagittaEpsilon    = sagittaEpsilon

#misalignment phases
process.TrackerSystematicMisalignments.ellipticalDelta   = math.radians(ellipticalDelta)
process.TrackerSystematicMisalignments.skewDelta         = skewDelta
process.TrackerSystematicMisalignments.sagittaDelta      = sagittaDelta
process.TrackerSystematicMisalignments.modulatedLayerRotDelta      = math.radians(modulatedLayerRotDelta)

# output
process.PoolDBOutputService = cms.Service("PoolDBOutputService",
                                          process.CondDBSetup,
                                          toPut = cms.VPSet(
                                                            cms.PSet(
                                                                     record = cms.string('TrackerAlignmentRcd'),
                                                                     tag = cms.string(alignmenttag),
                                                            ),
                                                            cms.PSet(
                                                                     record = cms.string('TrackerAlignmentErrorExtendedRcd'),
                                                                     tag = cms.string('AlignmentErrorsExtended'),
                                                            ),
                                          ),
                                          connect = cms.string('sqlite_file:'+outputfilename),
)

process.p = cms.Path( process.TrackerSystematicMisalignments )
