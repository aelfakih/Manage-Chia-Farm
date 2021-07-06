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
import inquirer
from helpers import *
from pprint import pprint
import collections
from PyInquirer import prompt, Separator
from PyInquirer import style_from_dict, Token, prompt, Separator
import logging
import sqlite3 as sql



logging.basicConfig(filename='log\\audit.log', encoding='utf-8',
                    format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.INFO)
""" 
initialize some of the variables needed in the program. Please do not change 
"""

plot_path = {}
plot_count = {}
plot_sizes = []
evacuate_drives = []
defrag_plan = []
verbose = get_config('config.yaml').get('verbose')
menu_find_non_plots = "Find non-Plots"
menu_find_duplicates = "Find Duplicate Plots"
menu_import_plots = "Import Plots into Farm"
menu_evacuate_drives = "Evacuate Drives"

def get_drives_to_evacuate():
    config = get_config ( 'config.yaml' ).get ( 'evacuate_drives' )
    if config:
        if verbose:
            logging.info ( "The following paths are marked for evacuation %s" % (config) )
        return config
    else:
        if verbose:
            logging.info ( "No drives marked for evacuation in config.yaml" )
        return []


def get_chia_farm_plots() :
    chia_farm = []
    plot_dirs = get_plot_directories()
    """ Scan through the farm to build chia_farm (database) """
    for directory in plot_dirs :
        arr = os.listdir( directory )
        for plot in arr :
            filename = directory + '\\' + plot
            chia_farm.append ( filename )
            plot_sizes.append ( round ( os.path.getsize ( filename ) / (2 ** 30) , 2 ) )
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

def load_farm_stats_to_db ():
    verbose = get_config ( 'config.yaml' ).get ( 'verbose' )
    import sqlite3 as sql
    db = sql.connect ( 'sinoda.db' )
    # Creating a cursor object using the cursor() method
    c = db.cursor ( )
    from datetime import datetime
    time = datetime.now ( ).strftime ( "%B %d, %Y %I:%M%p" )
    plot_dirs = get_plot_directories()
    farm=[]
    for dir in plot_dirs :
        drive = pathlib.Path ( dir ).parts[0]
        path = pathlib.Path ( dir ).parts[1]
        farm.append([path, drive, time])
        SQLQ = "INSERT INTO farm (path, drive, updatedatetime) values ('%s','%s','%s')" % (path,drive,time)
        c.execute ( SQLQ)
        if verbose:
            logging.info(SQLQ)

    # Commit your changes in the database
    db.commit()
    print ( "Records inserted........" )
    # Closing the connection
    db.close ( )







def get_plot_directories():
    config = get_config(get_chia_location(get_config('config.yaml')))
    return config.get('harvester').get('plot_directories')

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
    for dir in plot_dirs :
        arr = os.listdir ( dir )
        for plot in arr :
            plotnames.append ( plot )
            if plot_path.get ( plot ) :
                # print ("Duplicate %s %s %s" % (plot_path.get(plot),dir,plot))
                plot_path[plot] = "%s , %s" % (plot_path.get ( plot ) , dir)
                plot_count[plot] = plot_count.get ( plot ) + 1
            else :
                plot_path[plot] = dir
                plot_count[plot] = 1
    duplicate_plotnames = ([item for item , count in collections.Counter ( plotnames ).items ( ) if count > 1])
    return duplicate_plotnames

def find_non_plots() :
    #from PyInquirer import prompt , Separator
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
                        if verbose: logging.info ( "Deleting:  %s" % file )
            else :
                print ( indent ( "*" , "Skipping. No files deleted!" ) )
        else :
            print ( "[OK] None found!" )
            if verbose: logging.info ( "No non-plots files found!" )
    else :
        if verbose: logging.info( "Skipped checking for non-plots as configured in config.yaml" )

""" 
Find plots with the same name in the farm, 
so that we can prunce the farm and maintain 
only one copy
"""
def find_duplicate_plots() :
    # if this is enabled in config then proceed
    if get_config ( 'config.yaml' ).get ( 'check_duplicates_plots' ) :
        print ( "* Checking for duplicate plot filenames ... " , end="" )

        """ Get the duplicate plotnames """
        duplicate_plotnames = get_duplicte_plotnames ( get_plot_directories() )

        if duplicate_plotnames :
            number_of_files = len ( duplicate_plotnames )
            print ( "[NOK]" )
            print ( indent ( "*" , "WARNING! Found %s plots with multiple copies" % (number_of_files) ) )
            for file in duplicate_plotnames :
                print ( indent ( ">" , "%s  (%s)" % (file , plot_path[file]) ) )

            """ Get feedback from farmer (default is do not delete) """
            questions = [
                inquirer.Confirm ( 'delete_duplicates' ,
                                   message="Do you want to DELETE DUPLICATE files?" , default=False )
            ]
            answers = inquirer.prompt ( questions )
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
                            os.remove(file_to_delete)
                            if verbose :
                                logging.info ("Deleting [%s]" % (file_to_delete) )
            else :
                print ( indent ( "*" , "Skipping. No files deleted!" ) )
        else :
            print ( "[OK] None found!" )
            if verbose :
                logging.info ( "No duplicate names files found!" )
    else :
        if verbose :
            logging.info( "Skipped checking for duplicate plot filenames per config.yaml" )

def evacuate_plots() :
    plot_dirs = get_plot_directories ( )
    """ Evacuate drives """
    evacuate_drives = get_config ( 'config.yaml' ).get ( 'evacuate_drives' )
    if evacuate_drives :
        if verbose:
            logging.info( "Will evacuate %s" % (evacuate_drives) )
    average_size = round ( Average ( get_average_plot_sizes( plot_dirs ) ) , 2 )
    print ( "* Checking for space on drives farms to maximize space usage (defragment)... " )
    if verbose :
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

""" 
Import a file to farm takes as an argument the full plot filename with path
and the destination folder location.  The method copies the file into
a .tmp file and show the progress on the screen.  Once the file has been completelty
copied, it changes the name to it from .tmp to .plot so that it is included by
chia.
"""
def import_file_into_farm(src, destination_folder):
    verbose = get_config ( 'config.yaml' ).get ( 'verbose' )
    import shutil , os , sys, time
    from tqdm import tqdm
    basename = os.path.basename ( src )
    #input_file = 'Q:\\plot-k32-2021-06-22-17-26-8713aa7b1b639ef1b071e1dde2efd86ef12bc592c66f70f9d5c7683a140f3ab6.plot'
    dest = destination_folder + '\\' + basename + '.tmp'
    f_size = os.stat ( src ).st_size
    buff = 10485760  # 1024**2 * 10 = 10M

    num_chunks = f_size // buff + 1
    if verbose:
        logging.info("Copying as %s" % (src, dest))
    with open ( src , 'rb' ) as src_f , open ( dest , 'wb' ) as dest_f :
        try :
            for i in tqdm ( range ( num_chunks ) ) :
                chunk = src_f.read ( buff )
                dest_f.write ( chunk )
        except IOError as e :
            print ( e )
        finally :
            # give them the proper names (dest == remove .tmp , src == add .to_be_deleted)
            dest_f.close()
            src_f.close()
            live = destination_folder + '\\' + basename
            done = src + '.to_be_deleted'
            os.rename(dest,live) # make the plot live
            if verbose:
                logging.info("[DESTINATION] Renaming %s to %s" % (dest, live))
            os.rename(src,done) # stop source from being reimported
            if verbose:
                logging.info("[SOURCE] Renaming %s to %s" % (src,done))
            print ( f'Done! Copied {f_size} bytes.' )



def get_smallest_plot ( ):
    verbose = get_config ( 'config.yaml' ).get ( 'verbose' )
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
            if verbose: logging.info("%s has %s GiB free, good enough for %s plot(s)" % (dir, free, mod))
            # find the smallest plot available
            if free < min_storage_available:
                min_storage_available = free
                min_storage_drive = dir
                max_plots_to_fit = mod
    if verbose:
        logging.info("Choosing %s to store a max of %s plots" % (min_storage_drive, max_plots_to_fit))
    return min_storage_drive, max_plots_to_fit

def import_plots(style):
    plots_to_import=[]
    found = 0
    delta = 1
    import os , string
    available_drives = ['%s:' % d for d in string.ascii_uppercase if os.path.exists ( '%s:' % d )]
    questions = [
        {
            'type' : 'list' ,
            'name' : 'from' ,
            'message' : 'Which Drive to you want to import from?' ,
            'choices' : available_drives ,

        }
    ]
    answers = prompt ( questions , style=style )
    print("* Searching for .plot files in [%s] ..." % (answers['from']))

    while delta > 0:
        """ Walk the drive looking for .plot files """
        for root , dirs , files in os.walk ( answers['from'] ) :
            for file in files :
                if file.endswith ( ".plot" ) :
                    filename = root + '\\' + file
                    plots_to_import.append(filename)
                    print ( "> %s" % (filename ) )


        # check the file is not available already in farm.  If it is, ask to mar it as duplicate
        # find the drives that have the smallest number of available slots to copy over
        # copy to the available drive/folder
        if plots_to_import:
            target , count = get_smallest_plot()
            found = len ( plots_to_import )
            delta = found - count
            if verbose:
                logging.info("We can copy %s files from %s to %s " % (count,answers['from'],target))
            i = 0
            for plot in plots_to_import :
                if (i < count) and (plot):
                    print ("* Copying %s to %s" % (plot, target))
                    import_file_into_farm(plot,target)
                    i += 1  # how many files to copy
                else:
                    break
        else:
            print("* No importable plots were found in %s" % (answers['from']))
            delta = 0


    # """ Run the check """
    # import subprocess
    # chia_binary = get_config ( 'config.yaml' ).get ( 'chia_binary' )
    # if chia_binary :
    #     for plot in plots_to_import:
    #         args = ["plots","check","-g",plot]
    #         execute = [chia_binary]
    #         execute.extend(args)
    #         cmd = "%s plots check -g %s" % (chia_binary,plot)
    #         print ( "* Running %s to veridy plots" % (cmd) )
    #         result = subprocess.run(execute,stdout=subprocess.PIPE)
    #         print(result.stdout)




if __name__ == '__main__':

    print_top_menu()
    if verbose:
        logging.info("Program: Started")

    """ Define the Database connection """
    db = sql.connect ( "sinoda.db" )

    with db :
            db.execute ( """
             CREATE TABLE if not exists plots (
                 id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                 name TEXT,
                 path TEXT,
                 drive TEXT,
                 size FLOAT,
                 last);
                 """ )
            db.execute ( """
             CREATE TABLE if not exists farm (
                 id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                 path TEXT,
                 drive TEXT,
                 updatedatetime text DEFAULT (strftime('%Y-%m-%d %H:%M:%S:%s','now', 'localtime')));
                 """ )

    load_farm_stats_to_db()

    """ Get the plots that the Chia farm is farming """
    plot_dirs = get_plot_directories()

    if verbose:
        logging.info("Scanning the following plot directories: %s" % (plot_dirs))

    """ Get the plots available in the farm """
    chia_farm = get_chia_farm_plots (  )
    number_of_plots = len(chia_farm)
    print("* Scanning your farm! Found", number_of_plots , "plots listed!\n")
    if verbose:
        logging.info ( "Found %s files in farm" % (number_of_plots) )


    style = style_from_dict({
        Token.Separator: '#eab676',
        Token.QuestionMark: '#ffffff bold',
        Token.Selected: '#eab676',  # default
        Token.Pointer: '#eab676 bold',
        Token.Instruction: '',  # default
        Token.Answer: '#eab676 bold',
        Token.Question: '',
    })
    loop=True
    while loop:

        questions = [
            {
                'type' : 'list' ,
                'name' : 'do' ,
                'message' : 'Select a farm management action' ,
                'choices' : [menu_find_non_plots , menu_find_duplicates , menu_evacuate_drives, menu_import_plots , Separator(), "Done"] ,

            }
        ]
        answers = prompt ( questions , style=style )
        if verbose :
            logging.info ( "Menu: %s" % (menu_find_non_plots) )

        if answers['do'] == menu_find_non_plots:
            find_non_plots ( )
        elif answers['do'] == menu_find_duplicates :
            find_duplicate_plots ( )
        elif answers['do'] == menu_import_plots:
            import_plots( style )
        elif answers['do'] == menu_evacuate_drives:
            get_drives_to_evacuate()
        elif answers['do'] == "Done":
            loop = False
            print("* Goodbye!")
            if verbose:
                logging.info("Program: Exit")

