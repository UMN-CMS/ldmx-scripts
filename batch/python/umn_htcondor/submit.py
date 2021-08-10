"""Specializations of the HTCondor Python API for use at UMN

Here we define some helpful funcitons you can run from within the python3 interpreter to submit and manage the jobs.
"""

import htcondor #HTCondor Python API
import classad  #HTCondor internal data structure
import getpass  #Gets current user name
import os # for path joining and directory listing
import shutil # for copying files
import sys # for exiting after check failure
import json # for dumping objects to log file
from umn_htcondor import utility 

class JobInstructions(htcondor.Submit) :
    """Specialization of htcondor.Submit that has some helper functions for us.

    Parameters
    ----------
    executable_path : str
        Path to the executable to run fire
    output_dir : str
        Path to the directory to copy output files to
        If relative, pre-pend with your hdfs directory.
    singularity_img : str
        Path to the img to run for each job
    config : str
        Path to configuration script to give to fire
        The config is copied to the detail directory and run from there to maintain stability.
    input_arg_name : str, optional
        String to give the config script before the input files/run_number
        Default is empty string.
    extra_config_args : str, optional
        Extra arguments to supply to the config script on the command line
        Default is empty string (no extra args)

    Attributes
    ----------
    __full_out_dir_path : str
        Full path to output directory
    __full_detail_dir_path : str
        Full path to directory to store details of this run
    __items_to_loop_over : list[dict]
        List of dictionaries defining the variables condor should loop over when submitting the jobs
    __cluster_id : int
        ID number for cluster these job instructions were submitted as (0 if not submitted yet)

    Warnings
    --------
    Currently, we are limited to running ~100 jobs simultaneously
    so that we don't overload the /local/ filesystem. There are 16 slots
    on each scorpion so that means we should limit ourselves to 5-6 scorpions.
    """

    def __init__(self,
        executable_path, output_dir, singularity_img, config,
        input_arg_name = '', extra_config_args = '', program = 'fire') :

        self.__cluster_id = 0
        self.__full_out_dir_path = utility.full_dir(output_dir)

        if 'hdfs' not in self.__full_out_dir_path :
            if not JobInstructions._warn('You are writing output files to a directory that is *not* in {utility.hdfs_dir()}.','continue anyway') :
                raise Exception('Not using HDFS!')

        self.__full_detail_dir_path = utility.full_dir(os.path.join(self.__full_out_dir_path, 'detail'))

        utility.check_exists(singularity_img)

        full_run_script = utility.full_file(executable_path)
        shutil.copy2(full_run_script, os.path.join(self.__full_detail_dir_path,'run.sh'))

        # log directory inside of detail directory
        log_dir = utility.full_dir(os.path.join(self.__full_detail_dir_path,'logs'))

        super().__init__({
            'universe' : 'vanilla',
            # The +CondorGroup (I believe) is telling Condor to include this job submission
            #   under the accounting for the 'cmsfarm' group
            '+CondorGroup' : classad.quote('cmsfarm'),
            # This line keeps any jobs in a 'hold' state return a failure exit status
            #   If you are developing a new executable (run script), this might need to be removed
            #   until you get your exit statuses defined properly
            'on_exit_hold' : classad.Attribute('ExitCode') != 0,
            # This line passes the ExitCode from the application as the hold subcode
            'on_exit_hold_subcode' : classad.Attribute('ExitCode'),
            # And we explain that the hold was because run_fire failed
            'on_exit_hold_reason' : classad.quote('run.sh returned non-zero exit code (stored in HoldReasonSubCode)'),
            # This line tells condor whether we should be 'nice' or not.
            #   Niceness is a way for condor to help determine how 'urgent' this job is
            #   Please default to alwasy being nice
            'nice_user' : True,
            # Now our job specific information
            #   'executable' is required by condor and that variable name cannot be changed
            #   the other variable names are ours and can be changed and used in the rest of this file
            # We will be having bash read a script to run our program
            'executable' : '/usr/bin/bash', 
            # Don't try to transfer executable (assume bash is installed on all target nodes)
            'transfer_executable' : False,
            # Tell condor that it should transfer files that it controls
            'should_transfer_files' : 'YES',
            # Copy the output files when the job exits
            'when_to_transfer_output' : 'ON_EXIT',
            # Our job ID is just a combination of the cluster and process IDs
            #   we add some zero-padding to the process id so everything is nice and aligned :)
            'our_job_id' : '$(Cluster)_$INT(Process,%04d)',
            # stdout and stderr are the same file
            'output' : f'{log_dir}/$(our_job_id).out',
            'error'  : '$(output)',
            # Condor log file
            'log' : f'{log_dir}/$(our_job_id).log',
            # Pass the username through the environment, so the bash script can use $USER
            'environment' : classad.quote(f'USER={getpass.getuser()} LDMX_BASE={os.environ["LDMX_BASE"]}'),
            # Just some helpful variables to clean up the long arguments line
            'output_dir' : self.__full_out_dir_path,
            'run_script' : '$(output_dir)/detail/run.sh',
            'singularity_img' : singularity_img
          })

        # we deduce the arguments to the run script by whether a configuration script was provided
        if config is None :
            # assume the container has the program and script inside it
            self['arguments'] = f'$(run_script) $(our_job_id) $(singularity_img) $(output_dir) {extra_config_args} {input_arg_name}'
        else:
            # the config script is copied to the output directory for persistency
            #   and so that the jobs have a stable version
            full_config_path = utility.full_file(config)
            shutil.copy2(full_config_path, os.path.join(self.__full_detail_dir_path,'script.py'))
            self['conf_script'] = '$(output_dir)/detail/script.py'
            # need to provide program and script
            self['arguments'] = f'$(run_script) $(our_job_id) $(singularity_img) $(output_dir) {program} $(conf_script) {extra_config_args} {input_arg_name}'

        self['requirements'] = utility.dont_use_machine('caffeine')
        for m in ['zebra01','zebra02','zebra03','zebra04'] :
            self.ban_machine(m)            

        self.__items_to_loop_over = None

    def memory(self,max_mem_str) :
        """Set the max memory requested for these jobs

        See Also
        --------
        https://htcondor.readthedocs.io/en/latest/man-pages/condor_submit.html#submit-description-file-commands
        for what the allowed strings are
        """

        self['request_memory'] = max_mem_str

    def disk(self, max_disk_str) :
        """Set the maximum amount of disk space requested for these jobs

        See Also
        --------
        https://htcondor.readthedocs.io/en/latest/man-pages/condor_submit.html#submit-description-file-commands
        for what the allowed strings are
        """

        self['request_disk'] = max_disk_str

    def nice(self,be_nice) :
        """Set the nice-ness of these jobs

        You should almost always be nice.
        Every user of HTCondor has two "levels": nice and not-nice.

        Parameters
        ----------
        be_nice : bool
            True if we should be nice
        """

        self['nice_user'] = bool(be_nice)

    def priority(self, prio = 1) :
        """Set the priority for this job relative to your other jobs.

        The default priority for your jobs is zero, higher priority
        integers will mean condor will have those jobs run before the
        jobs with lower priority.

        Again, this priority integer is only within your own set of jobs.
        HTCondor and the administrators completely handle priority between
        different users.
        
        Parameters
        ----------
        prio : int, optional
            priority integer specifying how important the job is
        """

        self['priority'] = prio

    def ban_machine(self,m) :
        """Don't allow the jobs to run on the input machine.

        We assume that there is already at least one
        requirement defined, so the first requirement
        will need to be defined in the constructor.
        """

        self['requirements'] = classad.ExprTree(self['requirements']).and_(utility.dont_use_machine(m))

    def use_machine(self,m) :
        """Specifically request that the jobs run on the input machine.

        We assume that the other requires should be logical or'd with
        this requirement so that multiple calls to this function specify
        a list of machine to use.
        """

        self['requirements'] = classad.ExprTree(self['requirements']).or_(utility.use_machine(m))

    def sleep(self,time) :
        """Sleep for the input number of seconds between starting jobs.

        It is helpful to have some lag time so that transferring large files
        or reading from executable files can happen without overloading
        the filesystem. 
        
        This generally doesn't need to be very long, only a few seconds.
        """
        self['next_job_start_delay'] = time

    def periodic_release(self) :
        """Tell this HTCondor to release all jobs that returned specific exit codes

        The run_fire.sh script that runs the jobs returns a failure status of 99 when the worker node
        it is assigned to is not connected to hdfs and/or cvmfs (both of which are required for our jobs).
        This is helpful for trying to get jobs that failed this way back into the submission queue.
        
        If a machine is not reconnected to hdfs/cvmfs automatically, you may with to ban it.

        Other exit codes from run fire correspond to failure modes that aren't our fault,
        and simply require us to re-submit. These other failure modes aren't really well understood,
        but they seem to only affect our jobs for a small number of randomly distributed jobs.

        Exit Code | Description of Failure Mode
        ----------|----------------------------
        99        | hdfs or cvmfs is not mounted on worker node (before running)
        100       | Can't create or enter working directory (probably not enough space on worker node)
        117       | Output directory can't be seen on worker node (probably disconnected from hdfs during running)
        118       | Output file failed to cp to destination or copy of file did not match original

        See Also
        --------
        ban_machine : Banning machines before submitting jobs
        manage.ban_machine : Banning machines while they are idle/held
        """

        # The hold reason code is 3 when we told condor to hold the job on exit
        # We told condor to hold if run_fire.sh exits with a non-zero exit code
        held_by_us = (classad.Attribute('HoldReasonCode') == 3)

        # We have told condor to save the exit code of run_fire.sh in HoldReasonSubCode
        exit_code = classad.Attribute('HoldReasonSubCode')

        self['periodic_release'] = held_by_us.and_((exit_code == 99).or_(exit_code == 100).or_(exit_code == 117).or_(exit_code == 118))

    def run_over(self, add_args, items) :
        """Lowest-level access to setting the items that we should loop over.

        Parameters
        ----------
        add_args : str
            Argument string to add to 'arguments' parameter
        items : list[dict]
            List of dictionary "items" that will be looped over for the jobs
        """

        self['arguments'] += add_args
        self.__items_to_loop_over = items

    def run_over_input_dirs(self, input_dirs, num_files_per_job, recursive = True) :
        """Have the config script run over num_files_per_job files taken from input_dirs, generating jobs
        until all of the files in input_dirs are included.

        Parameters
        ----------
        input_dirs : list of str
            List of input directories, files, or file listings to run over
        num_files_per_job : int
            Number of files for each job to have (maximum, could be less)
        recursive : bool
            True if we should recursively search for root and list files in the supplied directories
        """

        if self.__items_to_loop_over is not None :
            raise Exception('Already defined how these jobs should run.')

        def smart_recursive_input(file_or_dir) :
            """Recursively add the full path to the file or files in the input directory"""
            full_list = []
            if isinstance(file_or_dir,list) :
                for entry in file_or_dir :
                    full_list.extend(smart_recursive_input(entry))
            elif os.path.isfile(file_or_dir) and file_or_dir.endswith('.root') :
                full_list.append(os.path.realpath(file_or_dir))
            elif os.path.isfile(file_or_dir) and file_or_dir.endswith('.list') :
                with open(file_or_dir) as listing :
                    file_listing = listing.readlines()
        
                full_list.extend(smart_recursive_input([f.strip() for f in file_listing]))
            elif os.path.isdir(utility.full_dir(file_or_dir)) :
                d = utility.full_dir(file_or_dir)
                full_list.extend(smart_recursive_input([os.path.join(d,f) for f in os.listdir(d)]))
            else :
                print(f"'{file_or_dir}' is not a ROOT file, a directory, or a list of files. Skipping.")
            #file or directory
            return full_list

        if recursive :
            input_file_list = smart_recursive_input(input_dirs)
        else :
            input_file_list = []
            for d in [utility.full_dir(d) for d in input_dirs] :
                input_file_list.extend([os.path.realpath(os.path.join(d,f)) for f in os.listdir(d)])
    
        # we need to define a list of dictionaries that htcondor submission will loop over
        #   we partition the list of input files into space separate lists of maximum length arg.files_per_job
        def partition(l, n) :
            chunks = []
            for i in range(0,len(l),n):
                space_sep = ''
                for p in l[i:i+n] :
                    space_sep += f'{p} '
                #loop over sub list
                chunks.append(space_sep) 
            #loop over full list
            return chunks
        #end def of partition
        
        self.run_over(' $(input_files)', [{'input_files' : i} for i in partition(input_file_list, num_files_per_job)])

    def run_refill(self) :
        """Get missing run numbers from output directory and submit those.

        We determine the run numbers to submit by looking through the output directory
        for any run numbers that are missing between the minimum and maximum run number.

        Run numbers are determined from the file names.
        The file names must match the following form:

            <other-parameters>_run_<run-number>.root

        For example

            my_fancy_sample_run_0420.root

        would produce a run number of '420', while

            my_fancy_sample_run0420.root

        would just be skipped and

            my_fancy_sample_0420_run.root

        would cause the python to error-out.
        """

        if self.__items_to_loop_over is not None :
            raise Exception('Already defined how these jobs should run.')

        runs = []
        for f in os.listdir(self.__full_out_dir_path) :
            parameters = f[:-5].split('_')
            if 'run' in parameters :
                runs.append(int(parameters[parameters.index('run')+1]))
            #end if run is in parameter list
        #end loop over directory

        if len(runs) == 0 :
            raise Exception('No run numbers listed in output directory. Cant refill!')

        runs.sort()

        self.run_over(' $(run_number)',[{'run_number':str(r)} for r in range(runs[0],runs[-1]+1) if r not in runs])

    def run_numbers(self, start, number):
        """Run over iterated run numbers

        We simply determine the run numbers by counting up from start
        until we have a reached number of jobs.

        Parameters
        ----------
        start : int
            First run number to start on
        number : int
            Number of jobs to submit
        """

        if self.__items_to_loop_over is not None :
            raise Exception('Already defined how these jobs should run.')

        self.run_over(' $(run_number)',[{'run_number' : str(r)} for r in range(start, start+number)])

    def _pause_before(next_thing) :
        """Pause before the next thing and allow the user the option to exit the script."""
        answer = input('[Q/q+Enter] to quit or [Enter] to '+next_thing+'... ')
        return (not answer.capitalize().startswith('Q'))

    def _warn(msg, next_thing) :
        """Print a warning message and ask for confirmation before proceding to next thing."""
        print(f' WARN {msg}') 
        return JobInstructions.__pause_before(next_thing)

    def __str__(self) :
        """Return a printed version of this object using htcondor.Submit.__str__"""
        return super().__str__()

    def _check(self) :
        """Print configuration to screen and pause for confirmation."""

        print(self)
        if not JobInstructions._pause_before('see Queue-ing list') : return False
        print(self.__items_to_loop_over)
        return True

    def _log_submission(self, f) :
        """Log the job configurations to the input file (assumed open)

        Parameters
        ----------
        f : file
            Open file to write our full submission log to
        """

        f.write("== Condor Configuration ==\n")
        print(self, file=f)
        f.write("\n== Run Script ==\n")
        with open(self.__full_detail_dir_path+'/run.sh') as rs :
            f.write(rs.read())
        if os.path.isfile(self.__full_detail_dir_path+'/script.py') :
            f.write("\n== Config Script ==\n")
            with open(self.__full_detail_dir_path+'/script.py') as conf :
                f.write(conf.read())
        f.write("\n== List of Items ==\n")
        f.write(json.dumps(self.__items_to_loop_over,indent=1))

    def submit(self) :
        """Actually submit the job instructions to the batch system."""
        schedd = htcondor.Schedd()
        with schedd.transaction() as txn :
            submit_result = self.queue_with_itemdata(txn, itemdata=iter(self.__items_to_loop_over))
            self.__cluster_id = submit_result.cluster()
            print(f'Submitted to Cluster {self.__cluster_id}')

        with open(f'{self.__full_detail_dir_path}/submit.{self.__cluster_id}.log','w') as log :
            self._log_submission(log)

    def submit_interactive(self) :
        """Submit to the batch system while checking with the user along the way"""

        if not self._check() : return
        if not JobInstructions._pause_before('submit') : return

        self.submit()

        if JobInstructions._pause_before('watch jobs') :
            from umn_htcondor import manage
            manage.watch_q()
    
