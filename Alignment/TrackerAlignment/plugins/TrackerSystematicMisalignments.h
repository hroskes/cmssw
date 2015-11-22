#ifndef Alignment_TrackerAlignment_TrackerSystematicMisalignments_h
#define Alignment_TrackerAlignment_TrackerSystematicMisalignments_h

/** \class TrackerSystematicMisalignments
 *
 *  Class to misaligned tracker from DB.
 *
 *  $Date: 2012/06/13 09:24:50 $
 *  $Revision: 1.5 $
 *  \author Chung Khim Lae
 */
// user include files

#include "CondFormats/Alignment/interface/Definitions.h"
#include "FWCore/Framework/interface/ESHandle.h"
#include "FWCore/Framework/interface/EDAnalyzer.h"
#include "TFile.h"

class AlignableSurface;
class Alignments;

namespace edm {
  class ParameterSet;
}

class TrackerSystematicMisalignments:
public edm::EDAnalyzer
{
public:

	TrackerSystematicMisalignments(const edm::ParameterSet&);
	~TrackerSystematicMisalignments();

	/// Read ideal tracker geometry from DB
	virtual void beginJob();

	virtual void analyze(const edm::Event&, const edm::EventSetup&);

private:

	void applySystematicMisalignment( Alignable* );
	const std::pair<const align::GlobalVector, const align::RotationType>
		findSystematicMis( const align::PositionType&, const bool blindToZ, const bool blindToR );
	void applySystematicDeformation(Alignable *ali);
	AlignableTracker* theAlignableTracker;

	const edm::ParameterSet theParameterSet;

	// configurables needed for the systematic misalignment
	bool m_fromDBGeom;

	double m_radialEpsilon;
	double m_telescopeEpsilon;
	double m_layerRotEpsilon;
	double m_bowingEpsilon;
	double m_zExpEpsilon;
	double m_twistEpsilon;
	double m_ellipticalEpsilon;
	double m_skewEpsilon;
	double m_sagittaEpsilon;

	//misalignment phases
	double m_ellipticalDelta;
	double m_skewDelta;
	double m_sagittaDelta;

	std::vector<double> m_addDeformations;

	std::string m_geometryComparisonRootFilename;
	TFile *m_geometryComparisonRootFile;
	std::map<int, std::pair<align::GlobalVector, align::RotationType> > m_movementsFromRootFile;

	// flag to steer suppression of blind movements
	bool suppressBlindMvmts;

	// flag for old z behaviour, version <= 1.5
	bool oldMinusZconvention;
};

#endif
