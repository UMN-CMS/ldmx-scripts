#!/bin/bash

###############################################################################
# ldmx-setup-deps.sh
#   Bash source script meant to connect up the dependencies needed to build
#   and run ldmx-sw.
#
# It is a hassle to change the gcc version because all of the other
# libraries could change versions. This means when we want to change
# the gcc version, you must go through the cvmfs directory tree and
# input the versions of these other libraries that we need. There is
# almost certainly an intelligent bash script that could do this for
# us, but I am not writing one write now.
# You also need to touch these library directories so that they
# appear when cmake looks for them.
#
#   Assumptions:
#     - LDMX_INSTALL_PREFIX is defined to be the install path of ldmx-sw
###############################################################################

export G4DIR="/local/cms/user/eichl008/geant4/geant4.10.02.p03_v0.3/install"
_root_dir="/local/cms/user/eichl008/root/6.22.06/install"
_boost_dir="/local/cms/user/eichl008/boost/install"

# Using the bash variable 'PYTHONHOME' gives a hint to look
#   here for Python to cmake, so this helps simplify our
#   cmake commands.
export PYTHONHOME="/local/cms/user/eichl008/python/install"

# location of cms shared libraries
# use this to specifiy which gcc should be used in compilation
_cvmfs_dir="/cvmfs/cms.cern.ch/slc7_amd64_gcc820"
export XERCESDIR="$_cvmfs_dir/external/xerces-c/3.1.3"
export GCCDIR="$_cvmfs_dir/external/gcc/8.2.0"

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
ldmx-env-source $XERCESDIR                        #xerces-c
ldmx-env-source $_cvmfs_dir/external/cmake/3.17.2 #cmake
ldmx-env-source $_cvmfs_dir/external/bz2lib/1.0.6 #bz2lib
ldmx-env-source $_cvmfs_dir/external/zlib/1.0     #zlib
ldmx-env-source $GCCDIR                           #gcc
ldmx-env-source $_root_dir/bin/thisroot.sh        #root 
ldmx-env-source $G4DIR/bin/geant4.sh              #geant4

if [ $_we_good != "YES" ]
then
  echo "Could not source '$_we_good'! (Most likely cvmfs has been disconnected.)"
  return 3
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
ldmx-env-load-lib $_boost_dir
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

