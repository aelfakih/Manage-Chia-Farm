# -*- mode: python ; coding: utf-8 -*-
# Manage-Chia-Farm
# Copyright Apache License Version 2.0
# Contact Adonis Elfakih https://github.com/aelfakih

# TO-DO
# read the plots_dirs from .chia config file
# in step 2/3 we may want to validate which between the two plots passes test (in this sprint, I asume both copies are valid)

# List the directories to explore
import pathlib

plot_dirs = ['E:\\farm003','D:\\farm004','F:\\farm002','G:\\farm001','H:\\farm005','I:\\farm006','J:\\farm007','L:\\farm008','K:\\farm011','M:\\farm012','P:\\farm009','O:\\farm010','N:\\farm013','Q:\\farm015','R:\\farm014']

# Import the modules we need
import os
import re
import sys
import os
import shutil

# initialize do not change
chia_farm = []
total_size_gb = 0
plotnames = []
plot_path={}
plot_count={}
plot_sizes=[]

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

if __name__ == '__main__':
    # Clear Screen to start ...
    clear = lambda: os.system('cls')
    clear()
    print('Manage-Chia-Farm | checks that plots are not duplicated, cleans junk files and reorganizes plots to maximize farming space')
    print('by Adonis Elfakih 2021, https://github.com/aelfakih/Manage-Chia-Farm\n')



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
print("* Scanning farm ... Found ", number_of_plots , "plots listed!")

### check for non plot files
print ("* [1/3] Checking for plots that don't have a '.plot' extension ... ",end="")
if  non_plot_list:
    number_of_files = len(non_plot_list)
    print("[NOK]")
    print(indent ("*", "WARNING! Found %s non-plot files in farm." % (number_of_files)))
    for file in non_plot_list:
        size_gb = round(os.path.getsize(file)/(2**30),2)
        total_size_gb += size_gb
        print(indent(">", "%s (%s GiB)" % (file,size_gb)))
    if yesno(indent("?","Do you want to DELETE NON-PLOT files and save %s GB of storage space?" % (total_size_gb))):
        for file in non_plot_list:
            if os.path.isfile(file):
                os.remove(file)
                print(indent("*", "Deleting:  %s" % file))
    else:
        print(indent("*","Skipping. No files deleted!"))
else:
    print ("[OK]")



# Load plot_ dictionaries from farm directories
for dir in plot_dirs:
    arr = os.listdir(dir)
    for plot in arr:
        plotnames.append(plot)
        if plot_path.get(plot):
            #print ("Duplicate %s %s %s" % (plot_path.get(plot),dir,plot))
            plot_path[plot] = "%s , %s" % (plot_path.get(plot),dir)
            plot_count[plot] = plot_count.get(plot) + 1
        else:
            plot_path[plot] = dir
            plot_count[plot] = 1



### check for non plot files
import collections
duplicate_plotnames = ([item for item, count in collections.Counter(plotnames).items() if count > 1])
print ("* [2/3] Checking for duplicate plot filenames ... ",end="")
if  duplicate_plotnames:
    number_of_files = len(duplicate_plotnames)
    print("[NOK]")
    print(indent ("*", "WARNING! Found %s plots with multiple copies" % (number_of_files)))
    for file in duplicate_plotnames:
        print(indent(">", "%s  (%s)" % (file,plot_path[file])))
    if yesno(indent("?","Do you want to DELETE DUPLICATE files?")):
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
        print(indent("*","Skipping. No files deleted!"))
else:
    print ("[OK]")

average_size = round(Average(plot_sizes),2)
print ("* [3/3] Checking for space in farms to maximize space usage (TBD) ... ")
print(indent("*", "Using Average plot size of %s GiB to fit plots in available farm space" % (average_size)))

for dir in plot_dirs:
    drive = pathlib.Path(dir).parts[0]
    total, used, free = shutil.disk_usage(drive)
    # convert to GiB
    free = free // (2**30)
    if free > average_size:
        #print ("Drive %s (%s): Total %s Used %s Free %s GiB" % (drive, dir, total // (2**30), used // (2**30), free ))
        mod = round(free/average_size)
        print(indent("*", "[TBD] %s has %s GiB free space, good enough for %s plot(s)" % (drive, free, mod)))
    else:
        print(indent("*", "Skipping %s not enough space for plots" % (drive)))


# Press the green button in the gutter to run the script.
# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
# See PyCharm help at https://www.jetbrains.com/help/pycharm/
