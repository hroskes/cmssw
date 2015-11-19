#=================================
#inputs
globaltag = '74X_dataRun2_Prompt_v4'    #Alignments and deformations are used unless overwritten.
                                        #  also APEs are copied from this GT (and other things are used internally, e.g. topology)
inputalignmentsqlitefile = None         #if None, uses the GT alignment
inputdeformationsqlitefile = None       #if None, uses the GT deformations
alignmenttag = 'Alignments'             #tag name for TrackerAlignmentRcd in the input file, also used for the output file
deformationtag = 'Deformations'         #tag name for TrackerSurfaceDeformationRcd in the input file, also used for the output file
runnumberIOV = 1                        #any run number in the iov that you want to start from (output iov is 1-infinity)

outputfilename = 'outputfile.db'


#misalignment amplitudes, -999 means no misalignment
#the commented numbers are the default magnitudes, which produce a maximum movement of around 600 microns
#see Alignment/TrackerAlignment/plugins/TrackerSystematicMisalignments.cc for definitions
#see also https://twiki.cern.ch/twiki/bin/viewauth/CMS/SystematicMisalignmentsofTracker
radialEpsilon     = -999. # 5e-4
telescopeEpsilon  = -999. # 5e-4
layerRotEpsilon   = -999. # 9.43e-6               #cm^-1
bowingEpsilon     = -999. # 6.77e-9               #cm^-2
zExpEpsilon       = -999. # 2.02e-4
twistEpsilon      = -999. # 2.04e-6               #cm^-1
ellipticalEpsilon = -999. # 5e-4
skewEpsilon       = -999. # 5.5e-2                #cm
sagittaEpsilon    = -999. # 5.0e-4

#phases for phi dependent misalignments
ellipticalDelta   = 0.
skewDelta         = 0.
sagittaDelta      = 0.

#deformation shifts, must be empty or have length 3 or 12
#the commented numbers are 50 microns for lengths, 0.5 mrad for angles
#  (for sensor width ~10cm this is also 50 micron max movement)
addDeformations = [
                   -999., #5e-3                    #sagittaX
                   -999., #5e-3                    #sagittaXY
                   -999., #5e-3                    #sagittaY
#rest of the parameters are for double sensors in TOB and TEC:
#  half of the difference between the two parts
                   -999., #5e-3                    #deltau
                   -999., #5e-3                    #deltav
                   -999., #5e-3                    #deltaw
                   -999., #5e-4                    #deltaalpha
                   -999., #5e-4                    #deltabeta
                   -999., #5e-4                    #deltagamma
                   -999., #5e-3                    #deltasagittaX
                   -999., #5e-3                    #deltasagittaXY
                   -999., #5e-3                    #deltasagittaY
#another parameter, ySplit, is in the deformation object.  It gives the place along y where the
#two sensors are split, and never changes.
                  ]
#=================================




import FWCore.ParameterSet.Config as cms

process = cms.Process("TrackerSystematicMisalignments")
process.load("FWCore.MessageService.MessageLogger_cfi")

process.load("Configuration.Geometry.GeometryRecoDB_cff")

process.load("CondCore.DBCommon.CondDBSetup_cfi")
process.source = cms.Source("EmptySource",
                            firstRun=cms.untracked.uint32(runnumberIOV),
)

process.maxEvents = cms.untracked.PSet(
    input = cms.untracked.int32(1)
)

# initial geom
# configure the database file - use survey one for default
process.load("Configuration.StandardSequences.FrontierConditions_GlobalTag_condDBv2_cff")
process.GlobalTag.globaltag=globaltag
if inputalignmentsqlitefile is not None:
    process.GlobalTag.toGet = cms.VPSet(
                                        cms.PSet(
                                                 record = cms.string('TrackerAlignmentRcd'),
                                                 tag = cms.string(alignmenttag),
                                                 connect = cms.untracked.string('sqlite_file:'+inputalignmentsqlitefile),
                                        ),
    )
if inputdeformationsqlitefile is not None:
    process.GlobalTag.toGet = cms.VPSet(
                                        cms.PSet(
                                                 record = cms.string('TrackerSurfaceDeformationRcd'),
                                                 tag = cms.string(deformationtag),
                                                 connect = cms.untracked.string('sqlite_file:'+inputdeformationsqlitefile),
                                        ),
    )


# input
process.load("Alignment.TrackerAlignment.TrackerSystematicMisalignments_cfi")
process.TrackerSystematicMisalignments.fromDBGeom = True

#uncomment one or more of these to apply the misalignment(s)

process.TrackerSystematicMisalignments.radialEpsilon     = radialEpsilon
process.TrackerSystematicMisalignments.telescopeEpsilon  = telescopeEpsilon
process.TrackerSystematicMisalignments.layerRotEpsilon   = layerRotEpsilon
process.TrackerSystematicMisalignments.bowingEpsilon     = bowingEpsilon
process.TrackerSystematicMisalignments.zExpEpsilon       = zExpEpsilon
process.TrackerSystematicMisalignments.twistEpsilon      = twistEpsilon
process.TrackerSystematicMisalignments.ellipticalEpsilon = ellipticalEpsilon
process.TrackerSystematicMisalignments.skewEpsilon       = skewEpsilon
process.TrackerSystematicMisalignments.sagittaEpsilon    = sagittaEpsilon

#misalignment phases
process.TrackerSystematicMisalignments.ellipticalDelta   = ellipticalDelta
process.TrackerSystematicMisalignments.skewDelta         = skewDelta
process.TrackerSystematicMisalignments.sagittaDelta      = sagittaDelta

#add constant deformation
process.TrackerSystematicMisalignments.addDeformations   = addDeformations

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
                                                            cms.PSet(
                                                                     record = cms.string('TrackerSurfaceDeformationRcd'),
                                                                     tag = cms.string(deformationtag),
                                                            ),
                                          ),
                                          connect = cms.string('sqlite_file:'+outputfilename),
)

process.p = cms.Path( process.TrackerSystematicMisalignments )
