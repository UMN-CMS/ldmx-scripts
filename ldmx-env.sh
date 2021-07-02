#!/bin/bash

# SUGGESTION:
#   Put the following command in your .bashrc file to make setting up
#   the ldmx environment easier
#   alias ldmx-env='source <path-to-this-file>/ldmx-env.sh; unalias ldmx-env'

# get the directory of this script
export LDMX_ENV_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &>/dev/null && pwd )"

# use the larger export scratch for temp working
export TMPDIR=/export/scratch/users/$USER
mkdir -p $TMPDIR

# This is the full path to the directory containing ldmx-sw on local
_base="$( cd "${LDMX_ENV_DIR}/../" &>/dev/null && pwd)"

# Check for /export/scratch copy for working on interactive node
_interactive_base="/export/scratch/users/$USER/ldmx"
if [[ -d ${_interactive_base}/ldmx-sw ]]; then
  _base="${_interactive_base}"
fi

# define cache location
export SINGULARITY_CACHEDIR=$_base/.singularity

# Setup container environment
if ! source $_base/ldmx-sw/scripts/ldmx-env.sh -b $_base $@; then
  echo "ERROR from container setup script."
  return 1
fi

# We also use a python and ROOT install outside of the container

# Custom Python has the HTCondor API installed
export PYTHONHOME="/local/cms/user/eichl008/python/install"
export LD_LIBRARY_PATH=$PYTHONHOME/lib:$LD_LIBRARY_PATH
export PATH=$PYTHONHOME/bin:$PATH
export PYTHONPATH=$PYTHONHOME/lib/python3:$PYTHONPATH

# try to import root when opening pyroot interactive
alias pyroot='python3 -i -c "import ROOT"'

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

# newer version of ROOT is closer to what's inside the container
source /local/cms/user/eichl008/root/6.22.06/install/bin/thisroot.sh
# location of cms shared libraries
_cvmfs_dir="/cvmfs/cms.cern.ch/slc7_amd64_gcc820"
ldmx-env-source $_cvmfs_dir/external/bz2lib/1.0.6 #bz2lib
ldmx-env-source $_cvmfs_dir/external/zlib/1.0  #zlib
ldmx-env-source $_cvmfs_dir/external/gcc/8.2.0 #gcc

# Other helpful aliases and functions below

# prepends fire with valgrind to check for memory leaks
alias ldmx-val='valgrind --tool=memcheck --leak-check=yes --suppressions=$ROOTSYS/etc/root/valgrind-root.supp --log-file=memcheck.log fire'

# skips directories that aren't modules
#   now run 'grepmodules <pattern>' in ldmx-sw/ to search for a <pattern> in the module source files
alias grepmodules='grep --exclude-dir=build --exclude-dir=docs --exclude-dir=install --exclude-dir=.git -rHn'

# setup the condor batch environemtn
alias ldmx-condor-env='source $LDMX_ENV_DIR/batch/condor_env.sh; unalias ldmx-condor-env'

# remove all the files listed in install_manifest.txt
alias ldmx-clean-install='xargs rm < install_manifest.txt'

# A safe copy where we make sure that the copy succeeded
safe-cp() {
  local _file="$1"
  local _dest_dir="$2"
  echo -n "$_file..."
  if cp -t $_dest_dir $_file; then
    sync
    if cmp -s $_dest_dir/$_file $_file; then
      echo "success!"
      return 0
    else
      echo "failed on cmp"
      #remove non-matching destination file
      rm $_dest_dir/$_file
    fi
  else
    echo "failed on cp"
    #remove failed copy (if it exists)
    # sometimes cp leaves a partially copied file behind
    if [[ -f $_dest_dir/$_file ]]; then
      rm $_dest_dir/$_file;
    fi
  fi
  return 1
}

# Safely move a file, making sure the copy succeeded
safe-mv() {
  local _file="$1"
  local _dest_dir="$2"
  if safe-cp $_file $_dest_dir; then
    rm $_file
  fi
}
