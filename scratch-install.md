# Install ldmx-sw and Its Dependencies in /export/scratch

### Why?
Having the ldmx-sw libraries installed in /local quickly overloads the filesystem when attempting 
to scale up the number of parallel jobs running. 
A medium-term solution is to install the software into /export/scratch on all of the machines 
that could be running batch for us.
After installing the dependencies and ldmx-sw onto one /export/scratch, we can mimic a shared
filesystem by manually copying over the installations to the worker nodes.

**The long-term solution is to actually have a container-runner installed on UMN computers.**

### Notes on Install Process

**Boost**
```
cd /local/cms/user/eichl008/boost/boost_1_72_0
./bootstrap.sh --prefix=/export/scratch/users/eichl008/ldmx-container/boost
./b2 install
```

**Python**
```
cd /local/cms/user/eichl008/python/Python-3.8.3
./configure.sh --enable-optimizations --with-ensurepip=install --prefix=/export/scratch/users/eichl008/ldmx-container/python
make -j4 install
export PYTHONHOME=/export/scratch/users/eichl008/ldmx-container/python
python3 -m pip install -U numpy
```

**CVMFS**
```
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
ldmx-env-source $XERCESDIR                      #xerces-c
ldmx-env-source $_cvmfs_dir/external/cmake/3.17.2 #cmake
ldmx-env-source $_cvmfs_dir/external/bz2lib/1.0.6 #bz2lib
ldmx-env-source $_cvmfs_dir/external/zlib/1.0     #zlib
ldmx-env-source $GCCDIR                         #gcc
```

**Geant4**

- (above) Need to source necessary cvmfs init.sh scripts before this one.

```
cd /local/cms/user/eichl008/geant4/geant4.10.02.p03_v0.3
rm -rf build
cmake \
    -DCMAKE_INSTALL_PREFIX=/export/scratch/users/eichl008/ldmx-container/geant4 \
    -DGEANT4_INSTALL_DATADIR=/hdfs/cms/user/eichl008/geant4/data \
    -DXERCESC_ROOT_DIR=$XERCESDIR \ 
    -DGEANT4_USE_GDML=ON \
    -DGEANT4_INSTALL_DATA=ON \
    -DGEANT4_USE_OPENGL_X11=ON \
    -DGEANT4_USE_SYSTEM_EXPAT=OFF \
    -DGEANT4_INSTALL_EXAMPLES=OFF \
    -B build
    -S .
cmake \
  --build build \
  --target install \
  -- -j3
```

**Root**

- (above) Need to source necessary cvmfs init.sh scripts before this one.
- Make sure the source at `root` is on the correct branch

```
cd /local/cms/user/eichl008/root/
rm -rf build
mkdir build
cd build
cmake \
    -DCMAKE_INSTALL_PREFIX=/export/scratch/users/eichl008/ldmx-container/root \
    -DPYTHON_EXECUTABLE=`which python3` \
    -DPYTHON_LIBS=$PYTHONHOME/lib \
    -Dgdml=ON \
    -Dxrootd=OFF \
    -Dvdt=OFF \
    -DCMAKE_CXX_STANDARD=17 \
    ../root
make install
```

