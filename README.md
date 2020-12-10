# ldmx-sw at UMN

This repository is focused on helping LDMX collaborators use ldmx-sw at UMN.

Currently, UMN does *not* have a container running program installed, so we still have to construct the dependencies from `cvmfs`.

This has been done in the `ldmx-env.sh` bash script.

## Quick Start

- Setup Environment: `source ldmx-env.sh`
  - **This assumes that `ldmx-sw` is downloaded alongside this repository.**
- Configure the Build: `cd ldmx-sw; mkdir build; cd build; ldmxcmake`
- Make and Install: `make -j4 install`
- Run: `fire config.py`

For a more detailed explanation, look at the [Getting Started Guide](getting_started.md).
