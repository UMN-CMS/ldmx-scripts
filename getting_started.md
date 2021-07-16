# Getting Started Guide

This guide is meant to help new users get started using ldmx-sw at UMN.
Here, we assume that the new user already has a UMN computing account and can access CMS group workspace `/local/cms/`, specifically, you have a directory that you own at `/local/cms/user/<your-username>`.

If you do not have a directory at `/local/cms/user/`, you can create one (assuming you have the correct permissions).

```
cd /local/cms/user/
mkdir $USER
cd $USER
```

`USER` is a bash variable that stores your username. Putting a `$` in front of a bash variable makes it return its value.

Now that we have your own directory set up in the CMS group workspace, we can get started.

## Getting this Repo

First, lets get this repository into our workspace so that we can use the scripts that are here.
I `clone` this repository into the directory `umn-specific` in order to isolate it from other LDMX repositories that contain scripts.

```
cd /local/cms/user/$USER
mkdir ldmx
cd ldmx
git clone git@github.com:UMN-CMS/ldmx-scripts.git umn-specific
```

This assumes you have [SSH Key Access](https://docs.github.com/en/free-pro-team@latest/github/authenticating-to-github/connecting-to-github-with-ssh) 
setup for your GitHub account. Look to the link to set this up.

## Helpful Command

In order to help ldmx-sw compile and run, we have to setup the computing environment.
The script `ldmx-env.sh` in this repository is intended to do this setup of the environment. 
It is helpful to create whats called a "bash alias" in order to make the running of this script easier.

The file `~/.bashrc` is run everytime you log into a UMN computer, so we are going to define our "bash alias" there.

```
echo "# source ldmx environment setup script" >> ~/.bashrc
echo "alias ldmx-env='source /local/cms/user/$USER/ldmx/ldmx-scripts/ldmx-env.sh; unalias ldmx-env'" >> ~/.bashrc
```

Now, you can run `ldmx-env` to setup the computing environment.

## Getting ldmx-sw

Now we are ready to start working with ldmx-sw.

```
cd /local/cms/user/$USER/ldmx
git clone --recursive git@github.com:LDMX-Software/ldmx-sw.git
```

The `--recursive` option is very important because ldmx-sw consists of several different `git` modules.

## Configuring the ldmx-sw Build

Before we can compile ldmx-sw, we need to configure the build so that the compiler "knows" where the various dependencies are. 
The environment setup script defines a bash function that runs this configuring command with the necessary options for you. 
In order to keep the source code for ldmx-sw clean, it is preferred to have a separate directory for the build files.

```
ldmx-env
cd ldmx-sw
mkdir build
cd build
ldmx cmake ..
```

## Building and Installing

Now that the build is configured, we can compile and install.

```
ldmx make -j4 install
```

The `-j4` option tells the program `make` to use `4` cores during the compilation. 
This helps speed up the build, but may hide any compilation errrors that could pop up during the compiling!

## Running

ldmx-sw compiles a program called `fire` which runs our simulation and reconstruction software over a series of "events". 
`fire` is configured by passing it a python script. The details of how to run `fire` and 
what should go in the configuration script are more general and can be found [on the ldmx-software documentation site](https://ldmx-software.github.io/docs/). 
For now, we can simply test our installation by running one of the test scripts that come with ldmx-sw.

```
cd .. #move out of the ldmx-sw/build directory into ldmx-sw
ldmx fire SimCore/test/basic.py
```

