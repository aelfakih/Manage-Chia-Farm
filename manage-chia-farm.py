"""
A program to manage chia farms and maximize the used of space available to the farmer.
You can download the latest from https://github.com/aelfakih/Manage-Chia-Farm

Copyright 2021 Adonis Elfakih

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

try:
    from io import UnsupportedOperation as IOUnsupportedOperation
except ImportError:
    class IOUnsupportedOperation(Exception):
        """A dummy exception to take the place of Python 3's
        ``io.UnsupportedOperation`` in Python 2"""

import pathlib
import os
import re
import sys
import shutil
import yaml
from database import *
from helpers import *
import collections
from PyInquirer import style_from_dict, Token, prompt, Separator
import logging



logging.basicConfig(filename='log\\audit.log', encoding='utf-8',
                    format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.INFO)
""" 
initialize some of the variables needed in the program. Please do not change 
"""

menu_find_non_plots = "Find non-Plots"
menu_find_duplicates = "Find Duplicate Plots"
menu_import_plots = "Import Plots into Farm"
menu_evacuate_drives = "Evacuate Drives"

def get_drives_to_evacuate():
    print("Work in Progress!")

def get_chia_farm_plots() :
    chia_farm = []
    plot_sizes =[]
    plot_dirs = get_plot_directories()
    """ Scan through the farm to build chia_farm (database) """
    for directory in plot_dirs :
        if os.path.isdir (directory):
            arr = os.listdir( directory )
            for plot in arr :
                filename = directory + '\\' + plot
                chia_farm.append ( filename )
                plot_sizes.append ( round ( os.path.getsize ( filename ) / (2 ** 30) , 2 ) )
        else:
            logging.error("! %s, which is listed in chia's config.yaml file is not a valid directory" % (directory))
    # sort chia_farm
    chia_farm.sort ( )
    return chia_farm

def get_average_plot_sizes( plot_dirs ) :
    """ Scan through the farm to build chia_farm (database) """
    for directory in plot_dirs :
        arr = os.listdir ( directory )
        for plot in arr :
            filename = directory + '\\' + plot
            plot_sizes.append ( round ( os.path.getsize ( filename ) / (2 ** 30) , 2 ) )
    return plot_sizes

def scan_plot_directories ():

    plot_dirs = get_plot_directories ( )

    if is_verbose() :
        logging.info ( "Loading chia plot paths into DB" )

    for dir in plot_dirs :
        drive = pathlib.Path ( dir ).parts[0]
        """ Check if the plots defined in the chia config file are online"""
        if not is_plot_online(drive):
            logging.error("%s plot is offline" % (dir))
            print ("! %s plot is Offline!" % (dir))
        else:
            save_plot_directory ( dir )



def get_non_plots_in_farm( chia_farm ) :
    # find files that have .plot extension
    p = re.compile ( ".*\.plot$" )
    plot_list = list ( filter ( p.match , chia_farm ) )
    # find symmetric difference.
    non_plot_list = set ( plot_list ).symmetric_difference ( chia_farm )
    return non_plot_list

def get_duplicte_plotnames(plot_dirs) :
    # Load plot_ dictionaries from farm directories
    duplicate_plotnames=[]
    plotnames=[]
    plot_path={}
    plot_count={}
    ignore_these = ["$RECYCLE.BIN","System Volume Information"]
    for dir in plot_dirs :
        if os.path.isdir ( dir ) :
            arr = os.listdir ( dir )
            for plot in arr :
                """ Skip Windows recycle and volume files"""
                if plot not in ignore_these:
                    plotnames.append ( plot )
                    if plot_path.get ( plot ) :
                        # print ("Duplicate %s %s %s" % (plot_path.get(plot),dir,plot))
                        plot_path[plot] = "%s , %s" % (plot_path.get ( plot ) , dir)
                        plot_count[plot] = plot_count.get ( plot ) + 1
                        plot_count[plot] = plot_count.get ( plot ) + 1
                    else :
                        plot_path[plot] = dir
                        plot_count[plot] = 1
    duplicate_plotnames = ([item for item , count in collections.Counter ( plotnames ).items ( ) if count > 1])
    return duplicate_plotnames, plot_path

def find_non_plots() :
    from PyInquirer import prompt , Separator
    total_size_gb = 0
    chia_farm = get_chia_farm_plots ( )
    """ [1] Find and remove NON-PLOTS """
    if get_config ( 'config.yaml' ).get ( 'check_for_non_plots' ) :

        print("* Checking for non-plots files (without a '.plot' extension) ... ", end="")

        """ Get the non plots in the farm """
        non_plot_list = get_non_plots_in_farm ( chia_farm )

        if non_plot_list :
            number_of_files = len ( non_plot_list )
            print ( "[NOK]" )
            print ( indent ( "*" , "WARNING! Found %s non-plot files in farm." % (number_of_files) ) )
            for file in non_plot_list :
                size_gb = round ( os.path.getsize ( file ) / (2 ** 30) , 2 )
                total_size_gb += size_gb
                print ( indent ( ">" , "%s (%s GiB)" % (file , size_gb) ) )

            """ Get feedback from farmer (default is do not delete) """
            questions = [
                {
                    'type' : 'confirm' ,
                    'message' : "Do you want to DELETE NON-PLOT files and save %s GB of storage space?" % ( total_size_gb) ,
                    'name' : 'delete_non_plots' ,
                    'default' : False ,
                }
            ]
            answers = prompt ( questions )
            if answers['delete_non_plots'] :
                for file in non_plot_list :
                    if os.path.isfile ( file ) :
                        os.remove ( file )
                        print ( indent ( "*" , "Deleting:  %s" % file ) )
                        if is_verbose():
                            logging.info ( "Deleting:  %s" % file )
            else :
                print ( indent ( "*" , "Skipping. No files deleted!" ) )
        else :
            print ( "[OK] None found!" )
            if is_verbose():
                logging.info ( "No non-plots files found!" )
    else :
        if is_verbose():
            logging.info( "Skipped checking for non-plots as configured in config.yaml" )

""" 
Find plots with the same name in the farm, 
so that we can prunce the farm and maintain 
only one copy
"""
def find_duplicate_plots() :
    from PyInquirer import prompt , Separator
    # if this is enabled in config then proceed
    if get_config ( 'config.yaml' ).get ( 'check_duplicates_plots' ) :
        print ( "* Checking for duplicate plot filenames ... " , end="" )

        """ Get the duplicate plotnames """
        duplicate_plotnames, plot_path = get_duplicte_plotnames ( get_plot_directories() )

        if duplicate_plotnames :
            number_of_files = len ( duplicate_plotnames )
            print ( "[NOK]" )
            print ( indent ( "*" , "WARNING! Found %s plots with multiple copies" % (number_of_files) ) )
            for file in duplicate_plotnames :
                print ( indent ( ">" , "%s  (%s)" % (file , plot_path[file]) ) )

            """ Get feedback from farmer (default is do not delete) """
            questions = [
                {
                    'type' : 'confirm' ,
                    'message' : "Do you want to DELETE DUPLICATE files?",
                    'name' : 'delete_duplicates' ,
                    'default' : False ,
                }
            ]
            answers = prompt ( questions )
            if answers['delete_duplicates'] :
                for file in duplicate_plotnames :
                    plot_locations = plot_path[file].split ( "," )
                    count = 0
                    for dir in plot_locations :
                        file_to_delete = dir.strip ( ) + '\\' + file
                        if count == 0 :
                            count += 1
                            print ( indent ( "*" , "Keeping [%s]" % (file_to_delete) ) )
                        else :
                            print ( indent ( "*" , "Deleting [%s]" % (file_to_delete) ) )
                            ###os.remove(file_to_delete)
                            if is_verbose() :
                                logging.info ("Deleting [%s]" % (file_to_delete) )
            else :
                print ( indent ( "*" , "Skipping. No files deleted!" ) )
        else :
            print ( "[OK] None found!" )
            if is_verbose() :
                logging.info ( "No duplicate names files found!" )
    else :
        if is_verbose() :
            logging.info( "Skipped checking for duplicate plot filenames per config.yaml" )

def evacuate_plots() :
    plot_dirs = get_plot_directories ( )
    """ Evacuate drives """
    evacuate_drives = get_config ( 'config.yaml' ).get ( 'evacuate_drives' )
    if evacuate_drives :
        if is_verbose():
            logging.info( "Will evacuate %s" % (evacuate_drives) )
    average_size = round ( Average ( get_average_plot_sizes( plot_dirs ) ) , 2 )
    print ( "* Checking for space on drives farms to maximize space usage (defragment)... " )
    if is_verbose() :
        logging.info( "Using Average plot size of %s GiB to fit plots in available farm space" % (average_size) )
    # loop while defrag
    iterate = len ( plot_dirs )
    while (iterate > 0) and (get_config ( 'config.yaml' ).get ( 'defragment_the_farm' )) :
        plot_dirs = get_plot_directories ( )
        iterate , to_plot , from_plot , plots_to_move = defrag_plots ( plot_dirs , average_size )
        print ( "%s From: %s >> %s ( %s plots)" % (iterate , from_plot , to_plot , plots_to_move) )

def print_top_menu() :
    # Clear Screen to start ...
    clear = lambda : os.system ( 'cls' )
    clear ( )
    print (
        'Manage-Chia-Farm | checks that plots are not duplicated, cleans junk files and reorganizes plots to maximize farming space' )
    print ( 'by Adonis Elfakih 2021, https://github.com/aelfakih/Manage-Chia-Farm\n' )




def get_smallest_plot ( ):
    plot_dirs = get_plot_directories ( )
    min_storage_available = 9999999999
    average_size = round ( Average ( get_average_plot_sizes ( plot_dirs ) ) , 2 )
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
            if is_verbose():
                logging.info("%s has %s GiB free, good enough for %s plot(s)" % (dir, free, mod))
            # find the smallest plot available
            if free < min_storage_available:
                min_storage_available = free
                min_storage_drive = dir
                max_plots_to_fit = mod
    if is_verbose():
        logging.info("Choosing %s to store a max of %s plots" % (min_storage_drive, max_plots_to_fit))
    return min_storage_drive, max_plots_to_fit

def get_destination_capacity ( dir ):
    plot_dirs = get_plot_directories ( )
    min_storage_available = 9999999999
    max_plots_to_fit = min_storage_drive = 0
    average_size = 106300000
    counter = 0

    drive = pathlib.Path ( dir ).parts[0]
    total , used , free = shutil.disk_usage ( drive )
    # convert to GiB
    free = free // (2 ** 30)
    used = used // (2 ** 30)
    calculated_num_of_plots = round ( used / average_size )
    print(drive, total, used, free, calculated_num_of_plots)
    if free > average_size :
        counter += 1
        mod = round ( free / average_size )
        if is_verbose ( ) :
            logging.info ( "%s has %s GiB free, good enough for %s plot(s)" % (dir , free , mod) )
        # find the smallest plot available
        if free < min_storage_available :
            min_storage_available = free
            min_storage_drive = dir
            max_plots_to_fit = mod

    if is_verbose():
        logging.info("Choosing %s to store a max of %s plots" % (min_storage_drive, max_plots_to_fit))
    return min_storage_drive, max_plots_to_fit






def initialize_me() :

    """ Set Up the SQLite database """
    initialize_database ( )

    """ Scan the Chia Plot Directories """
    scan_plot_directories ( )
    """ Get the plots that the Chia farm is farming """
    plot_dirs = get_plot_directories ( )
    if is_verbose ( ) :
        logging.info ( "Scanning the following plot directories: %s" % (plot_dirs) )
    """ Get the plots available in the farm """
    chia_farm = get_chia_farm_plots ( )
    number_of_plots = len ( chia_farm )
    print ( "* Scanning your farm! Found" , number_of_plots , "plots listed!\n" )
    if is_verbose ( ) :
        logging.info ( "Found %s files in farm" % (number_of_plots) )




if __name__ == '__main__':

    print_top_menu()
    if is_verbose():
        logging.info("Program: Started")



    """
    Set the stage so we can monitor and analyze farm
    """
    initialize_me ( )

    style = get_pyinquirer_style ( )

    loop=True
    while loop:

        questions = [
            {
                'type' : 'list' ,
                'name' : 'do' ,
                'message' : 'Select a farm management action' ,
                'choices' : [menu_find_non_plots , menu_find_duplicates , menu_import_plots , Separator(), "Done"] ,

            }
        ]
        answers = prompt ( questions , style=style )
        if is_verbose() :
            logging.info ( "Menu: %s" % (menu_find_non_plots) )

        if answers['do'] == menu_find_non_plots:
            find_non_plots ( )
        elif answers['do'] == menu_find_duplicates :
            find_duplicate_plots ( )
        elif answers['do'] == menu_import_plots:
            do_import_plots(style)
        elif answers['do'] == menu_evacuate_drives:
            get_drives_to_evacuate()
        elif answers['do'] == "Done":
            loop = False
            print("* Goodbye!")
            if is_verbose():
                logging.info("Program: Exit")

