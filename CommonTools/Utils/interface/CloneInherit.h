//The idea for this code is taken from Jonathan Boccara's blog
//https://www.fluentcpp.com/2017/09/12/how-to-return-a-smart-pointer-and-use-covariance/
//with some adjustments to match CMSSW conventions

//The point is described at length there, but the general idea is that we want each
//derived class to be cloneable and give a pointer of the correct type.
//If you call clone on a pointer to the base class which points to the derived class:
//  std::unique_ptr<Base> base(new Derived());
//  base->clone();
//You get a unique_ptr<Base>, but it points to a Derived and what it points to can be cast.

//See
//  Alignment/CommonAlignment/interface/AlignmentUserVariables.h                 (example Base)
//  Alignment/HIPAlignmentAlgorithm/interface/HIPUserVariables.h                 (example Derived)
//  Alignment/CommonAlignmentParametrization/src/RigidBodyAlignmentParameters.cc (where clone is called)

#include <memory>

template <typename Derived, typename Base> class CloneInherit : public Base {
public:
  std::unique_ptr<Derived> clone() const {
    return std::unique_ptr<Derived>(static_cast<Derived*>(this->cloneImpl()));
  }
 
private:
  virtual CloneInherit *cloneImpl() const override {
    return new Derived(*static_cast<const Derived*>(this));
  }
};
