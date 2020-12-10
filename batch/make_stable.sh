#!/bin/bash

set -ex

###############################################################################
# Create a Stable Install for Batch from the Current Build
#   Inputs:
#     - Name of Install to Make, optional
#   Assumptions:
#     - ldmx-sw source code is the way you want it
#     - ldmx-sw source code is at /local/cms/user/$USER/ldmx/ldmx-sw
###############################################################################

_curr_dir=$PWD
_dir_of_make_stable="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# let's go to the ldmx-sw of the user running this script
if ! cd /local/cms/user/$USER/ldmx/ldmx-sw
then
  echo "This script assumes the ldmx-sw source is at '/local/cms/user/$USER/ldmx/ldmx-sw'."
  exit 100
fi

_install_name="$1"
if [ -z $_install_name ]
then
  _install_name=$(git rev-parse --abbrev-ref HEAD)
  if [ "$_install_name" = "HEAD" ]
  then
    # detached head state - tag?
    _install_name=$(git tag --points-at HEAD)
    if [ -z $_install_name ]
    then
      # detached head and no tag
      echo "You are in detached head state without a tag name. You need to name this stable install manually."
      exit 101
    fi
  fi
fi

_build_dir=build-$_install_name

_stable_installs_dir=/local/cms/user/$USER/ldmx/stable-installs
mkdir -p $_stable_installs_dir

_install_dir=$_stable_installs_dir/$_install_name

if ! mkdir $_build_dir
then
  # cleanup old build directory
  rm -r $_build_dir
  mkdir $_build_dir
fi
cd $_build_dir

if ! source $_dir_of_make_stable/../ldmx-env.sh
then
  echo "I can't locate the environment setup script!"
  exit 102
fi

cmake \
  -DCMAKE_INSTALL_PREFIX=$_install_dir \
  -DBOOST_ROOT=$BOOSTDIR \
  ..

make -j6 install

# copy over a setup script substituting in the install directory
sed "s+export LDMX_INSTALL_PREFIX.*$+export LDMX_INSTALL_PREFIX=\"$_install_dir\"+" \
  $_dir_of_make_stable/../ldmx-env.sh \
  > $_install_dir/setup.sh

# return
cd $_curr_dir
