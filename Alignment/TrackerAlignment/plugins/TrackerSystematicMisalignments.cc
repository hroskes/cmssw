#include "FWCore/Framework/interface/ESHandle.h"
#include "Geometry/Records/interface/IdealGeometryRecord.h"
#include "Geometry/TrackerGeometryBuilder/interface/TrackerGeomBuilderFromGeometricDet.h"

#include "Alignment/CommonAlignment/interface/SurveyDet.h"
#include "Alignment/TrackerAlignment/interface/AlignableTracker.h"

#include "CondFormats/Alignment/interface/Alignments.h"
#include "CondFormats/AlignmentRecord/interface/TrackerAlignmentRcd.h"
#include "CondFormats/Alignment/interface/AlignmentErrorsExtended.h"
#include "CondFormats/AlignmentRecord/interface/TrackerAlignmentErrorExtendedRcd.h"
#include "CondFormats/AlignmentRecord/interface/TrackerSurfaceDeformationRcd.h"

#include "FWCore/Framework/interface/EventSetup.h"
#include "FWCore/MessageLogger/interface/MessageLogger.h"
#include "FWCore/ParameterSet/interface/ParameterSet.h"

#include "DataFormats/DetId/interface/DetId.h"
#include "DataFormats/TrackerCommon/interface/TrackerTopology.h"
#include "Geometry/CommonTopologies/interface/TwoBowedSurfacesDeformation.h"
#include "Geometry/TrackerGeometryBuilder/interface/TrackerGeometry.h"
#include "Geometry/TrackingGeometryAligner/interface/GeometryAligner.h"
#include "CLHEP/Random/RandGauss.h"

#include "Alignment/TrackerAlignment/plugins/TrackerSystematicMisalignments.h"

#include "DataFormats/SiStripDetId/interface/SiStripDetId.h"  // for enums TID/TIB/etc.

// Database
#include "CondCore/DBOutputService/interface/PoolDBOutputService.h"
#include "FWCore/ServiceRegistry/interface/Service.h"

// -----------------------------------------------------------------
// 2010-05-20 Frank Meier
// Changed sign of z-correction, i.e. z-expansion is now an expansion
// made some variables constant, removed obviously dead code and comments

TrackerSystematicMisalignments::TrackerSystematicMisalignments(const edm::ParameterSet& cfg)
	: theAlignableTracker(0),
	  theParameterSet(cfg),
	  // use existing geometry
	  m_fromDBGeom(cfg.getUntrackedParameter< bool > ("fromDBGeom")),
	  // constants
	  //alignment weak modes
	  m_radialEpsilon(cfg.getUntrackedParameter< double > ("radialEpsilon")),
	  m_telescopeEpsilon(cfg.getUntrackedParameter< double > ("telescopeEpsilon")),
	  m_layerRotEpsilon(cfg.getUntrackedParameter< double > ("layerRotEpsilon")),
	  m_bowingEpsilon(cfg.getUntrackedParameter< double > ("bowingEpsilon")),
	  m_zExpEpsilon(cfg.getUntrackedParameter< double > ("zExpEpsilon")),
	  m_twistEpsilon(cfg.getUntrackedParameter< double > ("twistEpsilon")),
	  m_ellipticalEpsilon(cfg.getUntrackedParameter< double > ("ellipticalEpsilon")),
	  m_skewEpsilon(cfg.getUntrackedParameter< double > ("skewEpsilon")),
	  m_sagittaEpsilon(cfg.getUntrackedParameter< double > ("sagittaEpsilon")),

	  m_ellipticalDelta(cfg.getUntrackedParameter< double > ("ellipticalDelta")),
	  m_skewDelta(cfg.getUntrackedParameter< double > ("skewDelta")),
	  m_sagittaDelta(cfg.getUntrackedParameter< double > ("sagittaDelta")),
	  m_addDeformations(cfg.getUntrackedParameter< std::vector<double> > ("addDeformations"))
{
	if (m_radialEpsilon > -990.0){
		edm::LogWarning("MisalignedTracker") << "Applying radial ...";
	}
	if (m_telescopeEpsilon > -990.0){
		edm::LogWarning("MisalignedTracker") << "Applying telescope ...";
	}
	if (m_layerRotEpsilon > -990.0){
		edm::LogWarning("MisalignedTracker") << "Applying layer rotation ...";
	}
	if (m_bowingEpsilon > -990.0){
		edm::LogWarning("MisalignedTracker") << "Applying bowing ...";
	}
	if (m_zExpEpsilon > -990.0){
		edm::LogWarning("MisalignedTracker") << "Applying z-expansion ...";
	}
	if (m_twistEpsilon > -990.0){
		edm::LogWarning("MisalignedTracker") << "Applying twist ...";
	}
	if (m_ellipticalEpsilon > -990.0){
		edm::LogWarning("MisalignedTracker") << "Applying elliptical ...";
	}
	if (m_skewEpsilon > -990.0){
		edm::LogWarning("MisalignedTracker") << "Applying skew ...";
	}
	if (m_sagittaEpsilon > -990.0){
		edm::LogWarning("MisalignedTracker") << "Applying sagitta ...";
	}

	// get flag for suppression of blind movements
	suppressBlindMvmts = cfg.getUntrackedParameter< bool > ("suppressBlindMvmts");
	if (suppressBlindMvmts)
	{
		edm::LogWarning("MisalignedTracker") << "Blind movements suppressed (TIB/TOB in z, TID/TEC in r)";
	}

	// compatibility with old (weird) z convention
	oldMinusZconvention = cfg.getUntrackedParameter< bool > ("oldMinusZconvention");
	if (oldMinusZconvention)
	{
		edm::LogWarning("MisalignedTracker") << "Old z convention: dz --> -dz";
	}
	else
	{
		edm::LogWarning("MisalignedTracker") << "New z convention: dz --> dz";
	}

	if (m_addDeformations.size() > 0){
		if (m_addDeformations.size() != 3 && m_addDeformations.size() != 12){
			throw cms::Exception("BadSetup") << "addDeformations needs to have size 0, 3, or 12!";
		}
		edm::LogWarning("MisalignedTracker") << "Adding constant deformations ...";
	}

}

void TrackerSystematicMisalignments::beginJob()
{

}


void TrackerSystematicMisalignments::analyze(const edm::Event& event, const edm::EventSetup& setup){

	//Retrieve tracker topology from geometry
	edm::ESHandle<TrackerTopology> tTopoHandle;
	setup.get<IdealGeometryRecord>().get(tTopoHandle);
	const TrackerTopology* const tTopo = tTopoHandle.product();

	edm::ESHandle<GeometricDet>  geom;
	setup.get<IdealGeometryRecord>().get(geom);
	TrackerGeometry* tracker = TrackerGeomBuilderFromGeometricDet().build(&*geom, theParameterSet);

	//take geometry from DB or randomly generate geometry
	if (m_fromDBGeom){
		//build the tracker
		edm::ESHandle<Alignments> alignments;
		edm::ESHandle<AlignmentErrorsExtended> alignmentErrors;
		edm::ESHandle<AlignmentSurfaceDeformations> deformations;

		setup.get<TrackerAlignmentRcd>().get(alignments);
		setup.get<TrackerAlignmentErrorExtendedRcd>().get(alignmentErrors);
		setup.get<TrackerSurfaceDeformationRcd>().get(deformations);

		//apply the latest alignments
		GeometryAligner aligner;
		aligner.applyAlignments<TrackerGeometry>( &(*tracker), &(*alignments), &(*alignmentErrors), AlignTransform() );
		aligner.attachSurfaceDeformations<TrackerGeometry>( &(*tracker), &(*deformations) );
	}

	applySystematicDeformation( &(*tracker), tTopo );
	theAlignableTracker = new AlignableTracker(&(*tracker), tTopo);
	applySystematicMisalignment( &(*theAlignableTracker) );

	// -------------- writing out to alignment record --------------
	Alignments* myAlignments = theAlignableTracker->alignments() ;
	AlignmentErrorsExtended* myAlignmentErrorsExtended = theAlignableTracker->alignmentErrors() ;
	AlignmentSurfaceDeformations* mySurfaceDeformations = theAlignableTracker->surfaceDeformations() ;

	// Store alignment[Error]s to DB
	edm::Service<cond::service::PoolDBOutputService> poolDbService;
	std::string theAlignRecordName  = "TrackerAlignmentRcd";
	std::string theErrorRecordName  = "TrackerAlignmentErrorExtendedRcd";
	std::string theDeformRecordName = "TrackerSurfaceDeformationRcd";

	// Call service
	if( !poolDbService.isAvailable() ) // Die if not available
		throw cms::Exception("NotAvailable") << "PoolDBOutputService not available";

	poolDbService->writeOne<Alignments>(&(*myAlignments), poolDbService->beginOfTime(), theAlignRecordName);
	poolDbService->writeOne<AlignmentErrorsExtended>(&(*myAlignmentErrorsExtended), poolDbService->beginOfTime(), theErrorRecordName);
	poolDbService->writeOne<AlignmentSurfaceDeformations>(&(*mySurfaceDeformations), poolDbService->beginOfTime(), theDeformRecordName);
}

void TrackerSystematicMisalignments::applySystematicMisalignment(Alignable* ali)
{

	const align::Alignables& comp = ali->components();
	unsigned int nComp = comp.size();
	//move then do for lower level object
	//for issue of det vs detunit
	bool usecomps = true;
	if ((ali->alignableObjectId()==2)&&(nComp>=1)) usecomps = false;
	for (unsigned int i = 0; i < nComp; ++i){
		if (usecomps) applySystematicMisalignment(comp[i]);
	}

	// if suppression of blind mvmts: check if subdet is blind to a certain mode
	bool blindToZ(false), blindToR(false);
	if (suppressBlindMvmts)
	{
		const int subdetid = ali->geomDetId().subdetId();
		switch(subdetid)
		{
			// TIB/TON blind to z
			case SiStripDetId::TIB:
			case SiStripDetId::TOB:
				blindToZ = true;
				break;
			// TID/TEC blind to R
			case SiStripDetId::TID:
			case SiStripDetId::TEC:
				blindToR = true;
				break;
			default:
				break;
		}
	}

	const int level = ali->alignableObjectId();
	if ((level == 1)||(level == 2)){
		const align::PositionType gP = ali->globalPosition();
		const align::GlobalVector gVec = findSystematicMis( gP, blindToZ, blindToR);
		ali->move( gVec );
	}
}

align::GlobalVector TrackerSystematicMisalignments::findSystematicMis( const align::PositionType& globalPos, const bool blindToZ, const bool blindToR ){
//align::GlobalVector TrackerSystematicMisalignments::findSystematicMis( align::PositionType globalPos ){
	// calculates shift for the current alignable
	// all corrections are calculated w.r.t. the original geometry
	double deltaX = 0.0;
	double deltaY = 0.0;
	double deltaZ = 0.0;
	const double oldX = globalPos.x();
	const double oldY = globalPos.y();
	const double oldZ = globalPos.z();
	const double oldPhi = globalPos.phi();
	const double oldR = sqrt(globalPos.x()*globalPos.x() + globalPos.y()*globalPos.y());

	if (m_radialEpsilon > -990.0 && !blindToR){
		deltaX += m_radialEpsilon*oldX;
		deltaY += m_radialEpsilon*oldY;
	}
	if (m_telescopeEpsilon > -990.0 && !blindToZ){
		deltaZ += m_telescopeEpsilon*oldR;
	}
	if (m_layerRotEpsilon > -990.0){
		// The following number was chosen such that the Layer Rotation systematic
		// misalignment would not cause an overall rotation of the tracker.
		const double Roffset = 57.0;
		const double xP = oldR*cos(oldPhi+m_layerRotEpsilon*(oldR-Roffset));
		const double yP = oldR*sin(oldPhi+m_layerRotEpsilon*(oldR-Roffset));
		deltaX += (xP - oldX);
		deltaY += (yP - oldY);
	}
	if (m_bowingEpsilon > -990.0 && !blindToR){
		const double trackeredgePlusZ=271.846;
		const double bowfactor=m_bowingEpsilon*(trackeredgePlusZ*trackeredgePlusZ-oldZ*oldZ);
		deltaX += oldX*bowfactor;
		deltaY += oldY*bowfactor;
	}
	if (m_zExpEpsilon > -990.0 && !blindToZ){
		deltaZ += oldZ*m_zExpEpsilon;
	}
	if (m_twistEpsilon > -990.0){
		const double xP = oldR*cos(oldPhi+m_twistEpsilon*oldZ);
		const double yP = oldR*sin(oldPhi+m_twistEpsilon*oldZ);
		deltaX += (xP - oldX);
		deltaY += (yP - oldY);
	}
	if (m_ellipticalEpsilon > -990.0 && !blindToR){
		deltaX += oldX*m_ellipticalEpsilon*cos(2.0*oldPhi + m_ellipticalDelta);
		deltaY += oldY*m_ellipticalEpsilon*cos(2.0*oldPhi + m_ellipticalDelta);
	}
	if (m_skewEpsilon > -990.0 && !blindToZ){
		deltaZ += m_skewEpsilon*cos(oldPhi + m_skewDelta);
	}
	if (m_sagittaEpsilon > -990.0){
		// deltaX += oldX/fabs(oldX)*m_sagittaEpsilon; // old one...
		deltaX += oldR*m_sagittaEpsilon*sin(m_sagittaDelta);
		deltaY += oldR*m_sagittaEpsilon*cos(m_sagittaDelta);    //Delta y is cos so that delta=0 reflects the old behavior
	}

	// Compatibility with old version <= 1.5
	if (oldMinusZconvention) deltaZ = -deltaZ;

	align::GlobalVector gV( deltaX, deltaY, deltaZ );
	return gV;
}

SurfaceDeformationFactory::Type
TrackerSystematicMisalignments::getDeformationType(const GeomDetUnit *geomDetUnit, const TrackerTopology* const tTopo){
       if (
              geomDetUnit->subDetector() == GeomDetEnumerators::PixelBarrel
           || geomDetUnit->subDetector() == GeomDetEnumerators::PixelEndcap
           || geomDetUnit->subDetector() == GeomDetEnumerators::TIB
           || geomDetUnit->subDetector() == GeomDetEnumerators::TID
       )
               return SurfaceDeformationFactory::kBowedSurface;
       else if (geomDetUnit->subDetector() == GeomDetEnumerators::TOB)
               return SurfaceDeformationFactory::kTwoBowedSurfaces;
       else if (geomDetUnit->subDetector() == GeomDetEnumerators::TEC)
       {
               if (tTopo->tecRing(geomDetUnit->geographicalId()) <= 4)
                       return SurfaceDeformationFactory::kBowedSurface;
               else
                       return SurfaceDeformationFactory::kTwoBowedSurfaces;
       }
       else
               throw cms::Exception("GeometryError")
               << "[TrackerSystematicMisalignments] Error, tried to get reference for non-tracker subdet " << geomDetUnit->subDetector();
               return SurfaceDeformationFactory::kBowedSurface;
}

void TrackerSystematicMisalignments::applySystematicDeformation(TrackerGeometry* geometry, const TrackerTopology* const tTopo){
//the structure of this function is copied from Alignment/OfflineValidation/plugins/TrackerGeometryIntoNtuples.cc
	AlignmentSurfaceDeformations *newDeformations = new AlignmentSurfaceDeformations();
	auto const & detUnits =  geometry->detUnits();
	for (auto iunit = detUnits.begin(); iunit != detUnits.end(); ++iunit) {
		auto geomDetUnit = *iunit;
		const SurfaceDeformation *oldDeformation = geomDetUnit->surfaceDeformation();

		std::vector<double> oldparams = oldDeformation->parameters();
		std::vector<double> addparams(12, 0);
		for (unsigned int i = 0; i < m_addDeformations.size(); i++){  //already checked in the constructor that m_addDeformations.size() = 0, 3, or 12
			addparams[i] += m_addDeformations[i];
		}
		//can also add other values (e.g. position-dependent) to addparams

		if (oldDeformation) {
			SurfaceDeformationFactory::Type type = getDeformationType(geomDetUnit, tTopo);
			std::vector<double> newparams;
			switch (type) {
				case SurfaceDeformationFactory::kBowedSurface:
					for (int i = 0; i < 3; i++)
						newparams.push_back(oldparams[i] + addparams[i]);
					break;
				case SurfaceDeformationFactory::kTwoBowedSurfaces:
				{
					for (int i = 0; i < 12; i++)
						newparams.push_back(oldparams[i] + addparams[i]);
					const TwoBowedSurfacesDeformation *oldTwoBowedDeformation = dynamic_cast<const TwoBowedSurfacesDeformation*>(oldDeformation);
					if (!oldTwoBowedDeformation)
						throw cms::Exception("GeometryError")
						<< "[TrackerSystematicMisalignments] " << geomDetUnit->geographicalId().rawId()
						<< " has the wrong kind of deformations!" << oldparams.size();
					newparams.push_back(oldDeformation->parameters()[oldTwoBowedDeformation->k_ySplit()]);
					break;
				}
				default:
					throw cms::Exception("GeometryError") << "[TrackerSystematicMisalignments] "
					<< geomDetUnit->geographicalId().rawId() << " has an unknown kind of deformation "
					<< "with " << oldparams.size() << " parameters";
			}
			newDeformations->add(geomDetUnit->geographicalId(), type, newparams);
		}
		else
			edm::LogWarning("MisalignedTracker")
			<< "GeomDetUnit " << geomDetUnit->geographicalId().rawId() << " has no surface deformations!  Can't add to it.";
	}

	GeometryAligner aligner;
	aligner.attachSurfaceDeformations<TrackerGeometry>( &(*geometry), newDeformations );
}

// Plug in to framework

#include "FWCore/Framework/interface/MakerMacros.h"

DEFINE_FWK_MODULE(TrackerSystematicMisalignments);
