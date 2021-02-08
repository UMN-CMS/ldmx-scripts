# Bare Metal Build

By "bare metal", I simply mean that we are *not* inside of the container.

The bare metail build here at UMN depends mostly on CVMFS which is already used heavily and mainted by the CMS group here at UMN.
This document is focused on how this bare metal build was constructed so that 
we can hopefully make it easier to update the ldmx-sw environment here in the future.

**Note**: I am expecting this bare metal build to be a stop-gap solution while we wait for singularity to be installed on our cluster.

## Current Environment

The current environment for building and running ldmx-sw is setup mainly through the `ldmx-setup-deps.sh` script.
This script does the two main activities for making sure our environment is setup properly.

1. Source initialization scripts for various dependencies.
2. Manually add directories to `PATH` (for executables), `LD_LIBRARY_PATH` (for dynamically loaded libraries), and `PYTHONPATH` (for python modules).

In that script, you can see all of the details on how to construct the environment.
Here, I will offer some explanation on how to setup the dependencies correctly so that script can work properly.

## CVMFS

[Cern Virtual Machine File System](https://cernvm.cern.ch/fs/) is a scalable method for distributing software packages.
The CMS experiment relies heavily on it to distribute their software CMS-SW.

Essentially, what we need to know about it are two things.

1. CVMFS is a cache-based system. This means a lot of files and directories in `/cvmfs/` will not appear unless *specifically* requested by the user.
2. CVMFS is read-only. This means if we cant find something we need there, we will have to build it ourselves.

CVMFS is organized into a hierarchy where the first level is based on the operating system and GCC version the user wishes to use.
ldmx-sw uses C++17 (min gcc ~5?) and our cluster is CentOS 7 (equivalent to `slc7`), so we will choose to look for our dependencies
in `/cvmfs/cms.cern.ch/slc7_amd64_gcc820/`. For the rest of this document, this directory is called `<cvfms_dir>`.
Because the rest of the dependencies depend on the version of GCC we use, changing the GCC version is a huge hassle.
For this reason, the most recent version of GCC available on CVMFS was chosen even though it is more advanced than required.

Each of the software packages installed on CVMFS can be initialized by the script
```
<software-dir>/etc/profile.d/init.sh
```
where `<software-dir>` is the root directory of the installation of that package.

We are able to some of our base required libraries on `/cvmfs/`, so I list them here.

- GCC : The C/C++ compiler.
  - `<cvmfs_dir>/external/gcc/8.2.0`
  - We define this directory as `GCCDIR` and `export` it because that helps `cmake` find this version.
- bz2lib : compression library used with ROOT
  - `<cvmfs_dir>/external/bz2lib/1.0.6`
- zlib : compression library used with ROOT
  - `<cvmfs_dir>/external/zlib/1.0`
- Xerces-C : XML Parser Geant4 uses to parse GDML files
  - `<cvmfs_dir>/external/xerces-c/3.1.3`
  - We define this directory as `XERCESDIR` and `export` it because that helps `cmake` find this version.
- cmake : Tool to configure a build so that dependencies are correctly organized and linked
  - `<cvmfs_dir>/external/cmake/3.17.2`

Since we want to compile ldmx-sw with these libraries, the rest of the dependencies 
also need to be compiled and linked to these libraries.

## Custom Dependencies

The larger dependencies of ldmx-sw have some specific requirements,
so we need to build them ourselves.

**Remember**: We need to make sure these dependencies are compiled and linked to the packages we are using from CVMFS.
This can be done by commenting out the custom dependencies that havent been built yet in `ldmx-setup-deps.sh` and sourcing
that script.

I have put all of these custom dependencies in my `/local/` directory:
```
/local/cms/user/eichl008
```
For the rest of this document, this directory will be called `<local>`.

ROOT needs to be built with our specific installation of Python, so we will build Python first.

### Python

0. Go and make a place for it `cd <local>; mkdir python; cd python`
1. Download the Python source `wget https://www.python.org/ftp/python/3.8.3/Python-3.8.3.tgz`
2. Unpack the source code `tar xzvf Python-3.8.3.tgz`
3. Go into the source code `cd Python-3.8.3`
4. Configure the build
   - `--enable-shared` is required because we will be linking to a C++ program.
   - `--enable-optimizations` just allows it to be good amount faster but takes longer to compile.
   - `--with-ensurepip=install` makes sure this Python has its own `pip` so we can install packages
   - `--prefix` defines where the installation should go
```
./configure.sh \
  --enable-shared \
  --enable-optimizations \
  --with-ensurepip=install \
  --prefix=<local>/python/install
```
5. Build and Install `make -j4 install`
6. Install `numpy` (required for PyROOT) and `htcondor` (for batch submission)
```
cd ../install
./bin/python3 -m pip install -U numpy htcondor
```

### Boost

0. Go and make a place for it `cd <local>; mkdir boost; cd boost`
1. Download the source `wget https://sourceforge.net/projects/boost/files/boost/1.72.0/boost_1_72_0.tar.gz/download`
2. Unpack the source and go into it `tar xzvf boost_1_72_0.tar.gz; cd boost_1_72_0`
3. Configure the build
```
./bootstrap.sh --prefix=<local>/boost/install
```
4. Build and Install `./b2 install`

### Geant4

0. Go and make a place for it `cd <local>; mkdir geant4; cd geant4`
1. Download the source specific to ldmx `git clone -b LDMX.10.2.3_v0.4 https://github.com/LDMX-Software/geant4.git`
2. Configure the build
   - We want Geant4 to install any necessary data (`-DGEANT4_INSTALL_DATA=ON`) but we put all data (no matter the Geant4 version)
     into a shared directory (`-DGEANT4_INSTALL_DATADIR=/hdfs/cms/user/eichl008/geant4/data`) so 
     we dont waste time downloading data we already have.
   - We need to point Geant4 directly to Xerces-C (`-DXERCESC_ROOT_DIR=$XERCESDIR`).
   - We can somewhat lighten the Geant4 installation by not installing examples. This option is not present in all Geant4 versions.
   - We install Geant4 into a directory named after the version we pulled the source for.
     This is done because there will inevitably be a time when we are thinking of upgrading Geant4.
```
cmake \
  -DGEANT4_INSTALL_DATA=ON \
  -DGEANT4_USE_GDML=ON \
  -DGEANT4_INSTALL_EXAMPLES=OFF \
  -DXERCESC_ROOT_DIR=$XERCESDIR \
  -DCMAKE_INSTALL_PREFIX=LDMX.10.2.3_v0.4 \
  -DGEANT4_INSTALL_DATADIR=/hdfs/cms/user/eichl008/geant4/data \
  -B geant4/build \
  -S geant4
```
3. Build and Install
```
cmake \
  --build geant4/build \
  --target install \
  -- -j4
```

### ROOT

This dependency is the most finicky, so dont be surprised if you run into difficulties.

0. Go and make a place for it `cd <local>; mkdir root; cd root`
1. Download the source into a matching version directory `mkdir 6.22.06; cd 6.22.06; wget https://root.cern/download/root_v6.22.06.source.tar.gz`
2. Unpack the source into its own directory `mkdir source; tar xzvf root_v6.22.06.source.tar.gz -C source`
3. Configure the build
   - We need to point this ROOT build to our custom Python that was built earlier.
     This is where we would need to re-source `ldmx-setup-deps.sh`, but this time with everything (but ROOT) un-commented.
   - We want this ROOT build to be lighter `-Dminimal=ON`, but we still need PyROOT `-Dpyroot=ON`.
   - ldmx-sw requires that ROOT is built with C++17 `-DCMAKE_CXX_STANDARD=17`
```
cmake \
    -DCMAKE_INSTALL_PREFIX=install \
    -DPYTHON_EXECUTABLE=`which python3` \
    -DPYTHON_LIBS=$PYTHONHOME/lib \
    -Dminimal=ON \
    -Dpyroot=ON \
    -DCMAKE_CXX_STANDARD=17 \
    -S source \
    -B build
```
4. Build and Install
```
cmake --build build --target install -- -j4
```

