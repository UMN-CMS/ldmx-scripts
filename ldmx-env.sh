#!/bin/bash

# SUGGESTION:
#   Put the following command in your .bashrc file to make setting up
#   the ldmx environment easier
#   alias ldmxenv='source <path-to-this-file>/ldmx-env.sh'

# get the directory of this script
export LDMX_ENV_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# This is the full path to the directory containing ldmx-sw
export LDMXBASE="/local/cms/user/$USER/ldmx"

# installation prefix for ldmx-sw
export LDMX_INSTALL_PREFIX="$LDMXBASE/ldmx-sw/install"

### Helpful Aliases and Bash Functions
# cmake script required to be done before make to build ldmx-sw
# WARNING: must be in $LDMXBASE/ldmx-sw/build directory when you run cmake
#   if you run it outside of build directory and it completes, 
#   you will need to git reset and git clean to remove
#   the build files that are mixed with the source files
function ldmxcmake {
  (set -x; cmake -DCMAKE_INSTALL_PREFIX=$LDMX_INSTALL_PREFIX -DBOOST_ROOT=$BOOSTDIR "$@" ../;)
}

function ldmxana-cmake {
  (set -x; cmake -DBOOST_ROOT=$BOOSTDIR -DLDMXSW_INSTALL_PREFIX=$LDMX_INSTALL_PREFIX "$@" ../;)
}

# prepends fire with valgrind to check for memory leaks
alias ldmx-val='valgrind --tool=memcheck --leak-check=yes --suppressions=$ROOTSYS/etc/root/valgrind-root.supp --log-file=memcheck.log fire'

# skips directories that aren't modules
#   now run 'grepmodules <pattern>' in ldmx-sw/ to search for a <pattern> in the module source files
alias grepmodules='grep --exclude-dir=build --exclude-dir=docs --exclude-dir=install --exclude-dir=.git -rHn'

# total remake command
# nuclear option
#   deletes ldmx install
#   goes to build directory, completely deletes old build, 
#   re-executes cmake and make, returns to prior directory
ldmxremake() {
  rm -rf $LDMX_INSTALL_PREFIX &&
  cd $LDMXBASE/ldmx-sw/build &&
  rm -r * &&
  ldmxcmake &&
  make install -j8 &&
  cd -
}

# helpful alias for making a stable installation
alias ldmx-make-stable='bash $LDMX_ENV_DIR/batch/make_stable.sh'

# helpful alias for writing batch job lists
alias ldmx-write-jobs='python $LDMX_ENV_DIR/batch/ldmx_write_jobs.py'

### The rest is believed to be the same for all umn users
# It is a hassle to change the gcc version because all of the other
# libraries could change versions. This means when we want to change
# the gcc version, you must go through the cvmfs directory tree and
# input the versions of these other libraries that we need. There is
# almost certainly an intelligent bash script that could do this for
# us, but I am not writing one write now.
# You also need to touch these library directories so that they
# appear when cmake looks for them.

## bash variables needed by cmake
# /local/cms installations of geant4 and root
TMP_ROOT="/local/cms/user/eichl008/install-test"
G4_VERSION_10_2_gcc821_cxx17="geant4.10.02.p03_v0.3-gcc821-cxx17"
G4_VERSION_10_2_gcc821="geant4.10.02.p03_v0.3-gcc821"
G4_VERSION_10_5_gcc821="geant4.10.05.p01-gcc821" 
export G4DIR="$TMP_ROOT/local/cms/other/geant4/$G4_VERSION_10_2_gcc821"
ROOT_VERSION_6_16_gcc821_cxx17="6.16.00-gcc821-cxx17"
ROOT_VERSION_6_16_gcc821="6.16.00-gcc821"
ROOT_VERSION_6_20_gcc821_cxx17="6.20.00-gcc821-cxx17"
ROOTDIR="$TMP_ROOT/local/cms/other/root/$ROOT_VERSION_6_20_gcc821_cxx17"
export BOOSTDIR="/local/cms/user/eichl008/boost/install"
export PYTHONHOME="/local/cms/user/eichl008/python/install"

# location of cms shared libraries
# use this to specifiy which gcc should be used in compilation
CVMFSDIR="/cvmfs/cms.cern.ch/slc7_amd64_gcc820"
export XERCESDIR="$CVMFSDIR/external/xerces-c/3.1.3"
export GCCDIR="$CVMFSDIR/external/gcc/8.2.0"

## Initialize libraries/programs from cvmfs and /local/cms
# all of these init scripts add their library paths to LD_LIBRARY_PATH
source $XERCESDIR/etc/profile.d/init.sh                         #xerces-c
source $CVMFSDIR/external/cmake/3.17.2/etc/profile.d/init.sh    #cmake
source $CVMFSDIR/external/bz2lib/1.0.6/etc/profile.d/init.sh    #bz2lib
source $CVMFSDIR/external/zlib/1.0/etc/profile.d/init.sh        #zlib
source $GCCDIR/etc/profile.d/init.sh                            #gcc
source $ROOTDIR/bin/thisroot.sh                                 #root 
source $G4DIR/bin/geant4.sh                                     #geant4

# add libraries to cmake/make search path for linking
export LD_LIBRARY_PATH=$LDMX_INSTALL_PREFIX/lib:$LDMX_INSTALL_PREFIX/external/onnxruntime-linux-x64-1.2.0/lib:$BOOSTDIR/lib:$PYTHONHOME/lib:$LD_LIBRARY_PATH

# add ldmx python scripts to python search path
export PYTHONPATH=$PYTHONHOME/lib/python3:$LDMX_INSTALL_PREFIX/python:$PYTHONPATH

# add ldmx executables to system search path
export PATH=$PYTHONHOME/bin:$LDMX_INSTALL_PREFIX/bin:$PATH

