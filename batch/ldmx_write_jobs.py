
class condor_submit_file() :
    """A wrapper for writing a condor submit file.
  
    Parameters
    ----------
    name : str
        Name of the condor_submit file to write
    executable : str
        Path to the executable that this file will be submitting
    nice : bool
        Is this cluster of jobs going to be nice?

    Attributes
    ----------
    _file : File
        file we are actually writing to
    header_template : str
        header string to show the hard-coded job parameters
    """
  
    header_template="""
executable          =  {executable}
universe            =  vanilla
requirements        =  Arch==\"X86_64\" && (Machine  !=  \"zebra01.spa.umn.edu\") && (Machine  !=  \"zebra02.spa.umn.edu\") && (Machine  !=  \"zebra03.spa.umn.edu\") && (Machine  !=  \"zebra04.spa.umn.edu\") && (Machine  !=  \"caffeine.spa.umn.edu\")
+CondorGroup        =  \"cmsfarm\"
nice_user           = {nice}
request_memory      =  4 Gb
on_exit_hold        = (ExitCode != 0)
"""

    def __init__(self,name,executable,nice) :
        self._file = open(name,'w')
        self._file.write(condor_submit_file.header_template.format(
          executable=os.path.realpath(executable),
          nice=str(nice))
          )

    def __del__(self) :
        """Close the file upon deletion"""
        self._file.close()

    def add(self,arguments,pause,test) :
        """Submit a job with the input arguments and pause.

        Parameters
        ----------
        arguments : str
            arguments to pass to executable for this job
        pause : int
            length of time in seconds to pause before next job can start
        test : bool
            if True, we will also connect a file to the std{out,err} of the job
        """

        if test :
          self._file.write('output = %s/$(Cluster)-$(Process).out\n'%(os.getcwd()))
          self._file.write('error  = %s/$(Cluster)-$(Process).out\n'%(os.getcwd()))

        self._file.write('arguments = %s\n'%arguments)
        self._file.write('next_job_start_delay = %d\n'%pause)
        self._file.write('queue\n')

import os,sys
import argparse

parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)

# required arg
parser.add_argument("job_list",type=str,help="Name of job list file that we should write to.")
parser.add_argument("-c","--config",required=True,type=str,help="Config script to run.")
parser.add_argument("-o","--out_dir",required=True,type=str,help="Directory to copy output to.")
environment = parser.add_mutually_exclusive_group(required=True)
environment.add_argument("--env_script",type=str,default=None,help="Environment script to run before running fire.")
environment.add_argument("--ldmx_version",type=str,default=None,help="LDMX Version to pick a pre-made environment script.")

# optional arg
parser.add_argument("--input_dir",default=None,type=str,help="Directory containing input files to run over.")
parser.add_argument("--num_jobs",type=int,default=None,help="Number of jobs to run (if not input directory given).")
parser.add_argument("--config_args",type=str,default='',help="Extra arguments to be passed to the configuration script.")
parser.add_argument("--start_job",type=int,default=0,help="Starting number to use when counting jobs (and run numbers)")

# rarely-used optional args
parser.add_argument("-t","--test",action='store_true',dest='test',help="Don't submit the job to the batch.")
parser.add_argument("--nonice",action='store_true',dest="nonice",help="Do not run this at nice priority.")
parser.add_argument("--run_script",type=str,help="Script to run jobs on worker nodes with.",default='%s/run_fire.sh'%os.path.dirname(os.path.realpath(__file__)))
parser.add_argument("--tmp_root",type=str,help="Directory to create any working directories inside of.",default='/export/scratch/user/%s/'%os.environ['USER'])
parser.add_argument("--sleep",type=int,help="Time in seconds to sleep before starting the next job.",default=60)

arg = parser.parse_args()

jobs = 0
if arg.input_dir is not None :
    full_input_dir = os.path.realpath(arg.input_dir)
    input_file_list = os.listdir(arg.input_dir)
    if arg.num_jobs is not None :
        jobs = min(arg.num_jobs,len(input_file_list))
    else :
        jobs = len(input_file_list)
elif arg.num_jobs is not None :
    jobs = arg.num_jobs
else :
    parser.error("Either an input directory of files or a number of jobs needs to be given.")

# make the output directory
full_out_dir_path = os.path.realpath(arg.out_dir)
if not os.path.exists(full_out_dir_path):
    os.makedirs(full_out_dir_path)

if not os.path.exists(full_out_dir_path):
    raise Exception('Unable to create output directory "%s"'%full_out_dir_path)

full_config_path = os.path.realpath(arg.config)
if not os.path.exists(full_config_path) :
    raise Exception('Config script "%s" does not exist.'%full_config_path)

if arg.env_script is not None :
    env_script = os.path.realpath(arg.env_script)
elif arg.ldmx_version is not None :
    env_script = "/local/cms/user/%s/ldmx/stable-installs/%s/setup.sh"%(os.environ['USER'],arg.ldmx_version)
else :
    parser.error('Either a full env script \'--env_script\' or a ldmx_version \'--ldmx_version\' must be specified.')

if not os.path.exists(env_script) :
    raise Exception('Environment script "%s" does not exist.'%env_script)

job_sub_file = condor_submit_file(arg.job_list,arg.run_script,not arg.nonice)
    
# This needs to match the correct order of the arguments in the run_fire.sh script
#   The input file and any extra config arguments are optional and come after the
#   three required arguments
arguments_template = arg.tmp_root+'/$(Cluster)-$(Process) {env_script} {config_script} {out_dir}'

for job in range(arg.start_job,arg.start_job+jobs) :
    arguments = arguments_template.format(
            env_script = env_script,
            config_script = full_config_path,
            out_dir = full_out_dir_path
            )

    if arg.input_dir is not None :
        arguments += ' %s/%s'%(full_input_dir,input_file_list[job-arg.start_job])

    arguments += ' --run_number %d %s'%(job,arg.config_args)

    job_sub_file.add(arguments,arg.sleep,arg.test)
#end loop over jobs
