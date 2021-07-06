import pathlib
import os
import re
import sys
import shutil
import yaml

# cleanup the cli output to avoid confusion when cleaning space
def indent(symbol,string):
    tab = '    '
    space = ' '
    sentence = tab + symbol + space + string
    return(sentence)

# check for y/n answers
def yesno(question):
    """Simple Yes/No Function."""
    prompt = "%s (y/n): " % (question)
    ans = input(prompt).strip().lower()
    if ans not in ['y', 'n']:
        print(indent("*",f'{ans} is an invalid reponse, please try again...'))
        return yesno(question)
    if ans == 'y':
        return True
    return False

# Python program to get average of a list
def Average(lst):
	return sum(lst) / len(lst)




# defrag logic
def defrag_plots(plot_dirs, average_size):
    min_storage_available = 9999999999
    max_storage_available = 0

    counter = 0
    for dir in plot_dirs:
        drive = pathlib.Path(dir).parts[0]
        total, used, free = shutil.disk_usage(drive)
        # convert to GiB
        free = free // (2**30)
        used = used // (2**30)
        calculated_num_of_plots = round(used / average_size)
        if free > average_size:
            counter += 1
            mod = round(free/average_size)
            print(indent(">", "%s has %s GiB free, good enough for %s plot(s)" % (dir, free, mod)))
            #print (indent("*","Drive %s (%s): Total %s GiB Used %s GiB Free %s GiB (~%s plots)" % (drive, dir, total // (2**30), used, free , calculated_num_of_plots)))
            # find the smallest plot available
            if free < min_storage_available:
                min_storage_available = free
                min_storage_drive = drive
                max_plots_to_fit = mod
            # find the largest plot available
            if (free > max_storage_available) and (mod <= max_plots_to_fit) :
                max_storage_available = free
                max_storage_drive = drive

    return [counter-2,min_storage_drive,max_storage_drive,max_plots_to_fit]


def get_config(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Unable to find the config.yaml file. Expected location: {file_path}")
    f = open(file_path, 'r')
    config = yaml.load(stream=f, Loader=yaml.Loader)
    f.close()
    return config

def get_chia_location(config):
    return config.get('chia_config_file')

