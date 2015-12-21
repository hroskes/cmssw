CMSSW_7_4_16_Legacy
===================

This branch is intended for tracker-alignment work that still needs to be done in a 74X release cycle.
Here we collect all the commits of higher cycles that are not yet or will never be backported to a 74X release.


Usage
-----
Please add any commits you think are important to have also in 74X to this branch, and *add a note below* so that other know about the changes.
Feel free to tag the current version of this branch with a meaningful tag name before you add any changes if you feel your changes add significant modifications.


Features in addition to CMSSW_7_4_16
------------------------------------

### Remove obsolete cms* scripts for eos file operations
This corresponds to PRs [#12795](https://github.com/cms-sw/cmssw/pull/12795/commits)
and [#11830](https://github.com/cms-sw/cmssw/pull/11830/commits)

Replaces cms* scripts for eos file system operations by appropriate eos commands.

### Zmumu validation update
Originally in PR [#11197](https://github.com/cms-sw/cmssw/pull/11197/commits), rebased in [#11830](https://github.com/cms-sw/cmssw/pull/11830/commits)

Updates to fitting and plotting code

### Bugfixes
This corresponds to PR [#12526](https://github.com/cms-sw/cmssw/pull/12526)

Fixes in the systematic misalignment tool, offline validation, and 3D geometry comparison

### Faster surface deformation plots
This corresponds to PR [#11024](https://github.com/cms-sw/cmssw/pull/11024)
