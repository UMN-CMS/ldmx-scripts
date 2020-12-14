"""Writing jobs for ldmx Condor batch submission

This python script is intended to be used with the running script 'run_fire.sh' in
this current directory.
"""

import os,sys
import argparse

parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)

# required arg
parser.add_argument("sub_file_name",type=str,help="Name of submission file that we should write to.")
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
parser.add_argument("-t","--test",action='store_true',dest='test',help="Attach terminal output of worker nodes to files for later viewing. ONLY GOOD FOR DEBUGGING. This will overload the filesystem if you use it on large batches.")
parser.add_argument("--nonice",action='store_true',dest="nonice",help="Do not run this at nice priority.")
parser.add_argument("--run_script",type=str,help="Script to run jobs on worker nodes with.",default='%s/run_fire.sh'%os.path.dirname(os.path.realpath(__file__)))
parser.add_argument("--scratch_root",type=str,help="Directory to create any working directories inside of.",default='/export/scratch/user/%s'%os.environ['USER'])
parser.add_argument("--sleep",type=int,help="Time in seconds to sleep before starting the next job.",default=60)

arg = parser.parse_args()

jobs = 0
if arg.input_dir is not None :
    full_input_dir = os.path.realpath(arg.input_dir)
    input_file_list = [ os.path.join(full_input_dir,f) for f in os.listdir(arg.input_dir) ]
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

sub_file_template="""# Condor Submission File
# Header for Jobs, defines global variables for use in this condor submission
#   anything defined here will be defined for the rest of this submission file
#   they can be re-defined and then the new value would be used for any later 'queue' commands

# These variables are general condor variables that are helpful for us
universe     = vanilla
requirements = Arch==\"X86_64\" && (Machine  !=  \"zebra01.spa.umn.edu\") && (Machine  !=  \"zebra02.spa.umn.edu\") && (Machine  !=  \"zebra03.spa.umn.edu\") && (Machine  !=  \"zebra04.spa.umn.edu\") && (Machine  !=  \"caffeine.spa.umn.edu\")
+CondorGroup = \"cmsfarm\"

# How much memory does this job require?
#   This is somewhat hard to determine since one does not normally track memory usage of one's programs.
#   4 Gb of RAM is a high upper limit, so this probably mean that less jobs will run in parallel, BUT
#   it helps make sure no jobs slow down due to low amount of available memory.
request_memory = 4 Gb

# This line keeps any jobs in a 'hold' state return a failure exit status
#   If you are developing a new executable (run script), this might need to be removed
#   until you get your exit statuses defined properly
on_exit_hold = (ExitCode != 0)

# This line tells condor whether we should be 'nice' or not.
#   Niceness is a way for condor to help determine how 'urgent' this job is
#   Please default to alwasy being nice
nice_user = {nice}

# Now our job specific information
#   'executable' is required by condor and that variable name cannot be changed
#   the other variable names are ours and can be changed and used in the rest of this file
executable    = {executable}
env_script    = {env_script}
scratch_root  = {scratch_root}
config_script = {config}
output_dir    = {out_dir}

# This is the number of seconds to pause between starting jobs
#   It is helpful to have some lag time so that transferring large files can happen
#   without overloading the file system
next_job_start_delay = {sleep}

# We will be using a run_number in the argument list, so we define it here
#   as a special variable that is a shift away from the Process ID.
#   Process is a condor defined variable that starts at 0 and increments up for each
#   job submitted. Here we use it to define sequential run numbers.
run_number_calculation = $(Process) + {start_job}
run_number = $INT(run_number_calculation)

# Finally, we define the arguments to the executable we defined earlier
#   Notice that we can use the variables we have defined earlier in this argument list
#   Condor will make the substitutions before starting the job
arguments = {arguments}
{terminal_output}
# Submit the Jobs
#   Now we actually submit the jobs.
#   The 'queue' command can do several things and this is where Condor handles the variables defined about it.
#   Look at the Condor documentation for all the details about how to write a helpful 'queue' command.
{queue_command}
"""

# This needs to match the correct order of the arguments in the run_fire.sh script
#   The input file and any extra config arguments are optional and come after the
#   three required arguments
arguments = '$(scratch_root)/$(Cluster)-$(Process) $(env_script) $(config_script) $(output_dir)'

if arg.input_dir is not None :
    arguments += ' $(input_file)'

arguments += ' --run_number $(run_number) ' + arg.config_args

queue_command = ''
if arg.input_dir is not None :
    if jobs != len(input_file_list) :
        # need special listing
        #  -> construct list of input files and run numbers
        queue_command += 'queue input_file from (\n'
        for run in range(jobs) :
            queue_command += '\t%s\n'%(input_file_list[run])
        queue_command += ')\n'
    else :
        # submitting the whole directory
        queue_command += 'queue input_file matching files %s/*\n'%(full_input_dir)
else :
    # submitting a range of run numbers
    queue_command += 'queue %d \n'%(jobs)

terminal_output = """
# Print any terminal messages that come up during the job to the file below
output = $(output_dir)/$(Cluster)-$(Process).out
error  = $(output_dir)/$(Cluster)-$(Process).out
"""

if not arg.test :
    terminal_output = ""

with open(arg.sub_file_name,'w') as submission_file :
    submission_file.write(sub_file_template.format(
          executable=os.path.realpath(arg.run_script),
          nice=str(not arg.nonice),
          env_script = env_script,
          scratch_root = arg.scratch_root,
          config = full_config_path,
          out_dir = full_out_dir_path,
          start_job = arg.start_job,
          sleep = arg.sleep,
          arguments = arguments,
          terminal_output = terminal_output,
          queue_command = queue_command
          ))
