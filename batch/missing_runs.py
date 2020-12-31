#!/bin/env python3

def list_runs(file_listing) :
    """List the run numbers of the input file list."""

    runs = []
    for f in file_listing :
        parameters = f[:-5].split('_') #remove '.root' and split by underscore
        if 'run' in parameters :
            #run number is parameter after name 'run'
            runs.append(int(parameters[parameters.index('run')+1]))
        #end if run is in parameter list
    #end loop over files

    return runs

def missing(sorted_number_list) :
    return [m for m in range(sorted_number_list[0],sorted_number_list[-1]+1) if m not in sorted_number_list]


if __name__ == '__main__' :
    
    import sys, os

    files = []
    for arg in sys.argv[1:] :
        if os.path.isdir(arg) :
            files.extend(os.listdir(arg))
        elif os.path.isfile(arg) :
            files.append(arg)
        else :
            print('%s is not a file or directory.'%arg)

    runs = list_runs(files)
    runs.sort()
    miss = missing(runs)

    # print each on a new line
    for m in miss :
        print(m)
