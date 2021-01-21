# Install ldmx-sw and Its Dependencies in /export/scratch

Here we mimic using a container.
Our "container" only works if worker node has the same OS, connection to cvmfs, and
we unpack the container in the exact same file-system location.
I have chosen `/export/scratch/users/eichl008/ldmx-container` as the "root" container directory
because the different machines have different `/export/scratch` mounts so we don't overload
the filesystem _and_ I have access to write onto all of these scratch mounts.

### Why?
Having the ldmx-sw libraries installed in /local quickly overloads the filesystem when attempting 
to scale up the number of parallel jobs running. 
A medium-term solution is to install the software into /export/scratch on all of the machines 
that could be running batch for us.
After installing the dependencies and ldmx-sw onto one /export/scratch, we can mimic a shared
filesystem by manually copying over the installations to the worker nodes.

**The long-term solution is to actually have a container-runner installed on UMN computers.**

### Notes on Install Process

Before starting any of the builds below, make sure that the external
dependencies are connected by sourcing our new environment script.
This should be done in a new terminal so that the environment is not
contaminated by the other environment setup script.
```
source container/container_env.sh
```

**Boost**
```
cd /local/cms/user/eichl008/boost/boost_1_72_0
./bootstrap.sh --prefix=$LDMX_CONTAINER_DIR/boost
./b2 install
```

**Python**
```
cd /local/cms/user/eichl008/python/Python-3.8.3
./configure.sh \
  --enable-shared \
  --enable-optimizations \
  --with-ensurepip=install \
  --prefix=$LDMX_CONTAINER_DIR/python
make -j4 install
python3 -m pip install -U numpy
```

**Geant4**

- We put the large data files onto `/hdfs` because those files are read-only and can be shared across several Geant4 versions

```
cd /local/cms/user/eichl008/geant4/geant4.10.02.p03_v0.3
rm -rf build
cmake \
    -DCMAKE_INSTALL_PREFIX=$LDMX_CONTAINER_DIR/geant4 \
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
  -- -j4
```

**Root**

```
cd /local/cms/user/eichl008/root/
cmake \
    -DCMAKE_INSTALL_PREFIX=/export/scratch/users/eichl008/ldmx-container/root \
    -DPYTHON_EXECUTABLE=`which python3` \
    -DPYTHON_LIBS=$PYTHONHOME/lib \
    -Dgdml=ON \
    -Dxrootd=OFF \
    -Dvdt=OFF \
    -DCMAKE_CXX_STANDARD=17 \
    -S root-6-22-08 \
    -B root-6-22-08-build
cmake \
  --build root-6-22-08-build \
  --target install \
  -- -j4
```

**ldmx-sw**
 
```
cd ldmx-sw
rm -rf scratch-build
mkdir scratch-build
cd scratch-build
cmake -DCMAKE_INSTALL_PREFIX=$LDMX_CONTAINER_DIR/ldmx-sw/ ..
make -j4 install
```

**ldmx-analysis**

```
cd ldmx-analysis
rm -rf scratch-build
mkdir scratch-build
cd scratch-build
cmake -DLDMXSW_INSTALL_PREFIX=$LDMX_INSTALL_PREFIX ..
make -j4 install
```

### Deployment

After doing all of the installation steps above and then testing to make sure ldmx-sw still works, 
we can deploy this "container" to the worker nodes by copying the scratch directory to them.
The "copying" of the "container" directory is done in a somewhat round-about way so that
we can avoid re-compiling this in the future if the scratch directory is cleaned.
Additionally, we can save space on the worker nodes by only including the files we need for running 
(`lib` s, `bin` s, the detector description, batch setup and running scripts, 
and root/ldmx-sw includes for ROOT dictionaries).

The first step is packing the container into an archive for persistency.
```
cd /hdfs/cms/user/eichl008/ldmx/containers
ldmx-container-pack {detailed-name-specifying-versions.tar}
```

Then we can unpack this archive on one of the worker nodes for testing.
```
ldmx-container-deploy {container.tar} scorpion1
ldmx-container-test scorpion1 {config-you-want-to-run.py} {config-args}
```

If that goes well, then we can deploy it to all of the worker nodes
and start submitting batch jobs. Deploying takes a long time because
we have to unpack all of the dependencies on each of the worker nodes.
```
ldmx-container-deploy {container.tar} scorpion{1..48}
```

**Warnings**
- This takes up a lot of space on the scratch directory (~1.5G of the 10G).
- This does not allow for more than one version of ldmx-sw to be running at once.
- This can be easily broken by routine cleaning of the scratch directories.

Hopefully, updating the container ldmx-sw will mean only having to re-install ldmx-sw, 
re-make the archive, and then force unpack it, but we shall see.
