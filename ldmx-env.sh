#!/bin/bash

# SUGGESTION:
#   Put the following command in your .bashrc file to make setting up
#   the ldmx environment easier
#   alias ldmx-env='source <path-to-this-file>/ldmx-env.sh'

# get the directory of this script
export LDMX_ENV_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &>/dev/null && pwd )"

# This is the full path to the directory containing ldmx-sw
export LDMX_BASE="$( cd "${LDMX_ENV_DIR}/../" &>/dev/null && pwd)"

# installation prefix for ldmx-sw
export LDMX_INSTALL_PREFIX="$LDMX_BASE/ldmx-sw/install"

### Helpful Aliases and Bash Functions
# cmake command required to be done before make to build ldmx-sw
# WARNING: must be in $LDMX_BASE/ldmx-sw/build directory when you run cmake
#   if you run it outside of build directory and it completes, 
#   you will need to git reset and git clean to remove
#   the build files that are mixed with the source files
function ldmx-cmake {
  (set -x; cmake -DCMAKE_INSTALL_PREFIX=$LDMX_INSTALL_PREFIX -DBOOST_ROOT=$BOOSTDIR "$@" ../;)
}

function ldmx-ana-cmake {
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
ldmx-remake() {
  rm -rf $LDMX_INSTALL_PREFIX &&
  cd $LDMX_BASE/ldmx-sw/build &&
  rm -r * &&
  ldmxcmake &&
  make install -j8 &&
  cd -
}

# setup the condor batch environemtn
alias ldmx-condor-env='source $LDMX_ENV_DIR/batch/condor_env.sh'

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
ROOT_VERSION_6_22_gcc821_cxx17="6.22.00-gcc821-cxx17"
ROOTDIR="$TMP_ROOT/local/cms/other/root/$ROOT_VERSION_6_22_gcc821_cxx17"
export BOOSTDIR="/local/cms/user/eichl008/boost/install"

# Using the bash variable 'PYTHONHOME' gives a hint to look
#   here for Python to cmake, so this helps simplify our
#   cmake commands.
export PYTHONHOME="/local/cms/user/eichl008/python/install"

# location of cms shared libraries
# use this to specifiy which gcc should be used in compilation
CVMFSDIR="/cvmfs/cms.cern.ch/slc7_amd64_gcc820"
export XERCESDIR="$CVMFSDIR/external/xerces-c/3.1.3"
export GCCDIR="$CVMFSDIR/external/gcc/8.2.0"

# sometimes our computers are disconnected from cvmfs
#   so we need to check if we found the necessary source files
_we_good="YES"

# Setup the input package
#   if the path contains 'cvmfs', then we assume we are given
#     a path to cvmfs package and source the corresponding init.sh
#   otherwise, source the input
ldmx-env-source() {
  _file_to_source="$1"
  if [[ "$1" == *"cvmfs"* ]]
  then
    _file_to_source=$1/etc/profile.d/init.sh
  fi

  if ! source $_file_to_source
  then
    _we_good="$_file_to_source"
  fi
}

## Initialize libraries/programs from cvmfs and /local/cms
# all of these init scripts add their library paths to LD_LIBRARY_PATH
ldmx-env-source $XERCESDIR                      #xerces-c
ldmx-env-source $CVMFSDIR/external/cmake/3.17.2 #cmake
ldmx-env-source $CVMFSDIR/external/bz2lib/1.0.6 #bz2lib
ldmx-env-source $CVMFSDIR/external/zlib/1.0     #zlib
ldmx-env-source $GCCDIR                         #gcc
ldmx-env-source $ROOTDIR/bin/thisroot.sh        #root 
ldmx-env-source $G4DIR/bin/geant4.sh            #geant4

if [ $_we_good != "YES" ]
then
  echo "Could not source '$_we_good'! (Most likely cvmfs has been disconnected.)"
  return 1
fi

# Make the directory passed to this funtion
#   another directory that could be loaded by a program at runtime
#
# Adds <input-dir>/lib to LD_LIBRARY_PATH and <input-dir>/bin to PATH
ldmx-env-load-lib() {
  export LD_LIBRARY_PATH="$1"/lib:$LD_LIBRARY_PATH
  export PATH="$1"/bin:$PATH
}

# add libraries to cmake/make search path for linking
ldmx-env-load-lib $PYTHONHOME
ldmx-env-load-lib $BOOSTDIR
ldmx-env-load-lib $LDMX_INSTALL_PREFIX
ldmx-env-load-lib $LDMX_INSTALL_PREFIX/external/onnxruntime-linux-x64-1.2.0

# Load the python module passed to this function
#   when running a python program
#
# Adds <input-dir> to PYTHONPATH
ldmx-env-load-module() {
  export PYTHONPATH="$1":$PYTHONPATH
}

# add ldmx python scripts to python search path
ldmx-env-load-module $PYTHONHOME/lib/python3
ldmx-env-load-module $LDMX_INSTALL_PREFIX/python

