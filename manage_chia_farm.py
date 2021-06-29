# -*- mode: python ; coding: utf-8 -*-
# Manage-Chia-Farm
# Copyright Apache License Version 2.0
# Contact Adonis Elfakih https://github.com/aelfakih

# Features kanban is available on https://github.com/aelfakih/Manage-Chia-Farm/projects

import pathlib
import os
import re
import sys
import shutil
import yaml


# initialize do not change
chia_farm = []
total_size_gb = 0
plotnames = []
plot_path={}
plot_count={}
plot_sizes=[]
evacuate_drives=[]
defrag_plan=[]

from functions import *

if __name__ == '__main__':
    # Clear Screen to start ...
    clear = lambda: os.system('cls')
    clear()
    print('Manage-Chia-Farm | checks that plots are not duplicated, cleans junk files and reorganizes plots to maximize farming space')
    print('by Adonis Elfakih 2021, https://github.com/aelfakih/Manage-Chia-Farm\n')

# Get the location of the chia config.yaml
filename = 'config.yaml'
config = get_config(filename)
filename = get_chia_location(config=config)

#get the plot_directories
chia_config = get_config(filename)
plot_dirs = get_plot_directories(chia_config)

# Load chia_farm from farm directories
for dir in plot_dirs:
    arr = os.listdir(dir)
    for plot in arr:
        filename = dir + '\\' + plot
        chia_farm.append(filename)
        plot_sizes.append(round(os.path.getsize(filename) / (2**30), 2))


#sort chia_farm
chia_farm.sort()

# find files that have .plot extension
p = re.compile(".*\.plot$")
plot_list = list(filter(p.match,chia_farm))

# find symmetric difference.
non_plot_list = set(plot_list).symmetric_difference(chia_farm)
number_of_plots = len(chia_farm)
print("* Scanning your farm! Found", number_of_plots , "plots listed!")

# decide how verbose we should be
verbose = get_config('config.yaml').get('verbose')

#### CLEAN FOR NON-PLOTS #####
if get_config('config.yaml').get('check_for_non_plots'):
    ### check for non plot files
    print("* Checking for non-plots files (without a '.plot' extension) ... ", end="")
    if non_plot_list:
        number_of_files = len(non_plot_list)
        print("[NOK]")
        print(indent("*", "WARNING! Found %s non-plot files in farm." % (number_of_files)))
        for file in non_plot_list:
            size_gb = round(os.path.getsize(file) / (2 ** 30), 2)
            total_size_gb += size_gb
            print(indent(">", "%s (%s GiB)" % (file, size_gb)))
        if yesno(
                indent("?", "Do you want to DELETE NON-PLOT files and save %s GB of storage space?" % (total_size_gb))):
            for file in non_plot_list:
                if os.path.isfile(file):
                    os.remove(file)
                    print(indent("*", "Deleting:  %s" % file))
        else:
            print(indent("*", "Skipping. No files deleted!"))
    else:
        print("[OK]")
else:
    if verbose: print("* Skipped checking for non-plots as configured in config.yaml")

#### CLEAN FOR DUPLICATES ####
if get_config('config.yaml').get('check_duplicates_plots'):
    # Load plot_ dictionaries from farm directories
    for dir in plot_dirs:
        arr = os.listdir(dir)
        for plot in arr:
            plotnames.append(plot)
            if plot_path.get(plot):
                # print ("Duplicate %s %s %s" % (plot_path.get(plot),dir,plot))
                plot_path[plot] = "%s , %s" % (plot_path.get(plot), dir)
                plot_count[plot] = plot_count.get(plot) + 1
            else:
                plot_path[plot] = dir
                plot_count[plot] = 1

    ### check for non plot files
    import collections

    duplicate_plotnames = ([item for item, count in collections.Counter(plotnames).items() if count > 1])
    print("* Checking for duplicate plot filenames ... ", end="")
    if duplicate_plotnames:
        number_of_files = len(duplicate_plotnames)
        print("[NOK]")
        print(indent("*", "WARNING! Found %s plots with multiple copies" % (number_of_files)))
        for file in duplicate_plotnames:
            print(indent(">", "%s  (%s)" % (file, plot_path[file])))
        if yesno(indent("?", "Do you want to DELETE DUPLICATE files?")):
            for file in duplicate_plotnames:
                plot_locations = plot_path[file].split(",")
                count = 0
                for dir in plot_locations:
                    file_to_delete = dir.strip() + '\\' + file
                    if count == 0:
                        count += 1
                        print(indent("*", "Keeping [%s]" % (file_to_delete)))
                    else:
                        print(indent("*", "Deleting [%s]" % (file_to_delete)))
                        os.remove(file_to_delete)
        else:
            print(indent("*", "Skipping. No files deleted!"))
    else:
        print("[OK]")
else:
    if verbose: print("* Skipped checking for duplicate plot filenames per config.yaml")

#### DEFRAGMENT FARM ####
evacuate_drives = get_config('config.yaml').get('evacuate_drives')

if evacuate_drives:
    if verbose: print("* Will evacuate %s" % (evacuate_drives))

average_size = round(Average(plot_sizes),2)
print ("* Checking for space on drives farms to maximize space usage (defragment)... ")

if verbose:
    print(indent("*", "Using Average plot size of %s GiB to fit plots in available farm space" % (average_size)))

# loop while defrag
#iterate = len(plot_dirs)
#while (iterate > 0) and (get_config('config.yaml').get('defragment_the_farm')):
#    iterate, to_plot, from_plot, plots_to_move = defrag_plots(dir)
#    print("%s %s %s %s" % (iterate, to_plot, from_plot, plots_to_move))

#print("MIN %s %s" % (min_storage_drive, min_storage_available))
#print("MAX %s %s" % (max_storage_drive, max_storage_available))
#print(defrag_plan)


# Press the green button in the gutter to run the script.
# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
# See PyCharm help at https://www.jetbrains.com/help/pycharm/