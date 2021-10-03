import subprocess
import pathlib
import os
import re
import sys
import shutil
import collections
import logging
from PyInquirer import style_from_dict, Token, prompt

#####  Needs cleanup #####
def get_chia_farm_plots() :
    chia_farm = []
    plot_dirs = get_plot_directories()
    ignore_these = ["$RECYCLE.BIN","System Volume Information"]

    """ Scan through the farm to build chia_farm (database) """
    for directory in plot_dirs :
        if os.path.isdir (directory):
            arr = os.listdir( directory )
            for plot in arr :
                if plot not in ignore_these:
                    filename = directory + '\\' + plot
                    if os.path.isfile(filename):
                        chia_farm.append ( filename )
        else:
            if is_verbose ( ) :
                logging.error("%s, which is listed in chia's config.yaml file is not a valid directory" % (directory))
    # sort chia_farm
    return chia_farm

def get_non_plots_in_farm( chia_farm ) :
    """
    Return list of items that DO NOT end with .plot
    """
    import logging
    plot_list =[]

    # find files that have .plot extension
    pattern =".*\.plot$"

    ignore_extensions = get_extenstions_to_ignore ( )
    if ignore_extensions:
        print ("! Ignoring files ending with ", end="")
        for extension in ignore_extensions :
            print (f" [{extension}] ", end="")
            pattern = f"{pattern}|.*\{extension}$"

    print (" as defined in config.yaml")
    logging.debug(f"Returning list of plots that DO NO match this regex pattern {pattern}")
    p = re.compile ( pattern )

    # find symmetric difference.
    plot_list = list ( filter ( p.match , chia_farm ) )



    # find symmetric difference.
    non_plot_list = set ( plot_list ).symmetric_difference ( chia_farm )
    return non_plot_list

def get_duplicte_plotnames(plot_dirs) :
    """
    In the plot_dirs list, look for duplicates and return them
    the duplicate names (no path) with a list that shows the
    locations where they repeat

    example:

    plot-1234567.plot, ["c:\path1","m:\path20"]
    """

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
    import logging
    """
    Method scans the chia farm for NON-PLOTS and prompts farmer to delete them.
    NON-PLOTS are files that do not end in .plot
    * it does not need DB to scan, the scan is made live
    * it does save data found into database
    """
    from database import do_changes_to_database
    from PyInquirer import prompt , Separator
    session_id = get_session_id()

    total_size_GiB = 0
    chia_farm = get_chia_farm_plots ( )

    print ("* ----------------------------------------------------------------------")
    print ("* Checking for non-plots files (files that DO NOT END in .plot)... ")
    print ("* ----------------------------------------------------------------------")
    if is_verbose ( ) :
        logging.info ( f"Looking for non-plot files" )

    """ Get the non plots in the farm """
    non_plot_list = get_non_plots_in_farm ( chia_farm )

    if non_plot_list :
        number_of_files = len ( non_plot_list )
        print ( indent ( "*" , "WARNING! Found %s non-plot files in farm." % (number_of_files) ) )
        for file in non_plot_list :
            size_GiB = bytes_to_gib(os.path.getsize ( file ))
            total_size_GiB += size_GiB
            print ( indent ( ">" , "%s (%s GiB)" % (file , size_GiB) ) )
            if is_verbose ( ) :
                logging.info(f"NON-PLOT file detected: {file} Size: {size_GiB} GiB")
            do_changes_to_database (
                f"REPLACE INTO plots (name, path, drive, size, type, valid, scan_ukey) values ('{os.path.basename(file)}','{os.path.dirname(file)}\','{find_mount_point ( file )}','{size_GiB}','?','No','{session_id}')")


        """ Get feedback from farmer (default is do not delete) """
        questions = [
            {
                'type' : 'confirm' ,
                'message' : "Do you want to DELETE NON-PLOT files and save %s GiB of storage space?" % (total_size_GiB) ,
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
                    if is_verbose ( ) :
                        logging.info ( "Deleting:  %s" % file )
        else :
            print ( indent ( "*" , "Skipping. No files deleted!" ) )
            if is_verbose ( ) :
                logging.info("No Files Were Deleted")
    else :
        if is_verbose ( ) :
            logging.info ( "No non-plots files found!" )

def find_duplicate_plots() :
    """
    Find plots with the same name in the farm,
    so that we can prunce the farm and maintain
    only one copy
    """
    from PyInquirer import prompt
    largest_capacity = 0

    print ("* ----------------------------------------------------------------------")
    print ( "* Checking for duplicate plot filenames ... ")
    print ("* ----------------------------------------------------------------------")
    if is_verbose ( ) : logging.info("Looking for duplicate plots")

    """ Get the duplicate plotnames """
    duplicate_plotnames , plot_path = get_duplicte_plotnames ( get_plot_directories ( ) )

    if duplicate_plotnames :
        number_of_files = len ( duplicate_plotnames )
        print ( indent ( "*" , "WARNING! Found %s plots with multiple copies" % (number_of_files) ) )
        for file in duplicate_plotnames :
            print ( indent ( ">" , "%s  found in (%s)" % (file , plot_path[file]) ) )
            if is_verbose ( ) :
                logging.info ( f"{file} found in {plot_path[file]}" )

        """ Get feedback from farmer (default is do not delete) """
        questions = [
            {
                'type' : 'confirm' ,
                'message' : "Do you want to DELETE DUPLICATE files?" ,
                'name' : 'delete_duplicates' ,
                'default' : False ,
            }
        ]
        answers = prompt ( questions )
        if answers['delete_duplicates'] :
            for file in duplicate_plotnames :
                plot_locations = plot_path[file].split ( "," )
                count = 0
                """ Remove the file where there is a LOT of free space (so we keep the farm plots consolidated) """
                for dir in plot_locations :
                    size = get_free_space_GiB ( dir.strip ( ) )
                    if size > largest_capacity :
                        largest_capacity = size
                        remove_from_drive = dir

                file_to_delete = remove_from_drive.strip ( ) + '\\' + file

                if os.path.exists ( file_to_delete ) :
                    print ( indent ( "*" , "Deleting [%s]" % (file_to_delete) ) )
                    if is_verbose ( ) :
                        logging.info ( "Deleting [%s]" % (file_to_delete) )
                    os.remove ( file_to_delete )
                    if is_verbose ( ) :
                        logging.info ( "Deleting [%s]" % (file_to_delete) )

            do_scan_farm ( )
        else :
            print ( indent ( "*" , "Skipping. No files deleted!" ) )
            if is_verbose ( ) :
                logging.info ( "Skipping. No files deleted!" )
    else :
        if is_verbose ( ) :
            logging.info ( "No duplicate names files found!" )



def get_smallest_plot ( ):
    plot_dirs = get_plot_directories ( )
    min_storage_available = 9999999999
    average_size = 106300000
    counter = 0
    for dir in plot_dirs:
        drive = find_mount_point ( dir )
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

#################### Helpers ####################
def get_colorama_fgcolor(color) :
    from colorama import Fore , Back , Style
    if color in "BLACK" :
        return Fore.BLACK
    if color in "GREEN" :
        return Fore.GREEN
    if color in "RED" :
        return Fore.RED
    if color in "YELLOW" :
        return Fore.YELLOW
    if color in "BLUE" :
        return Fore.BLUE
    if color in "MAGENTA" :
        return Fore.MAGENTA
    if color in "CYAN" :
        return Fore.CYAN
    if color in "WHITE" :
        return Fore.WHITE

def get_colorama_bgcolor(color) :
    from colorama import Fore , Back , Style
    if color in "BLACK" :
        return Back.BLACK
    if color in "GREEN" :
        return Back.GREEN
    if color in "RED" :
        return Back.RED
    if color in "YELLOW" :
        return Back.YELLOW
    if color in "BLUE" :
        return Back.BLUE
    if color in "MAGENTA" :
        return Back.MAGENTA
    if color in "CYAN" :
        return Back.CYAN
    if color in "WHITE" :
        return Back.WHITE


def stacked_bar_chart(data , max_length) :
    from colorama import Fore , Back , Style
    from colorama import init
    init ( )

    segment_one_length = data[0][0]
    segment_one_color = data[0][1]
    segment_one_label = data[0][2]

    segment_two_length = data[1][0]
    segment_two_color = data[1][1]
    segment_two_label = data[1][2]

    bar_chart_prefix = data[2][0]
    label_style = data[2][1] # Label Style: accepts: both, percent, count, none
    label_total = data[2][2] # Add Total: accepts: Yes, No
    bar_chart_suffix = data[2][3]


    segment_one_percent = 100 * segment_one_length / (segment_two_length + segment_one_length)
    segment_two_percent = 100 * segment_two_length / (segment_two_length + segment_one_length)
    total_segments = segment_two_length + segment_one_length

    segment_one_normalized = round ( (segment_one_length / (segment_one_length + segment_two_length)) * max_length )

    if bar_chart_prefix:
        sys.stdout.write ( Fore.RESET + Back.RESET + f"{bar_chart_prefix} |" )

    for i in range ( max_length ) :
        if i <= segment_one_normalized :
            sys.stdout.write (  get_colorama_fgcolor ( segment_one_color )+  u"\u2588" )
        if i > segment_one_normalized :
            sys.stdout.write ( get_colorama_fgcolor ( segment_two_color ) + u"\u2588" )
        sys.stdout.flush ( )


    #print Legend
    sys.stdout.write ( Fore.RESET )
    if label_total in "Yes":
        sys.stdout.write ( f" Total: {total_segments:5.0f} >"  )
    sys.stdout.write ( Fore.RESET +  " : " )
    sys.stdout.write (  Fore.RESET + get_colorama_bgcolor ( segment_one_color )+  f"{segment_one_label}" )
    if label_style in "both" or label_style in "count":
        sys.stdout.write (  Fore.RESET + Back.RESET +  f" {segment_one_length}" )
    if label_style in "both" or label_style in "percent" :
        sys.stdout.write (  Fore.RESET + Back.RESET +  f" {segment_one_percent:3.0f}%" )

    sys.stdout.write ( Fore.RESET +  " : " )
    sys.stdout.write (  Fore.RESET + get_colorama_bgcolor ( segment_two_color )+  f"{segment_two_label}" )
    if label_style in "both" or label_style in "count":
        sys.stdout.write ( Fore.RESET + Back.RESET + f" {segment_two_length}" )
    if label_style in "both" or label_style in "percent" :
        sys.stdout.write ( Fore.RESET + Back.RESET + f" {segment_two_percent:3.0f}%" )
    if bar_chart_suffix:
        sys.stdout.write ( Fore.RESET + Back.RESET + f" : {bar_chart_suffix}" )
    print ( Style.RESET_ALL )

def print_top_menu() :
    # Clear Screen to start ...
    clear = lambda : os.system ( 'cls' )
    clear ( )
    print (
        'Manage-Chia-Farm | Manage your Chia farm like a Pro' )
    print ( 'by Adonis Elfakih 2021, https://github.com/aelfakih/Manage-Chia-Farm\n' )

def initialize_me() :
    from database import initialize_database

    """ Set Up the SQLite database """
    initialize_database ( )

    """ Get the plots that the Chia farm is farming """
    plot_dirs = get_plot_directories ( )
    if is_verbose ( ) :
        logging.info ( "Scanning the following plot directories: %s" % (plot_dirs) )
    """ Get the plots available in the farm """
    chia_farm = get_chia_farm_plots ( )
    number_of_plots = len ( chia_farm )
    print ( "* Scanning your farm! Found" , number_of_plots , "plots mounted onto this machine!" )
    if is_verbose ( ) :
        logging.info ( "Found %s files in farm" % (number_of_plots) )

def find_mount_point(path):
    """
    For a given path/file find the mount point
    """
    path = os.path.abspath(path)
    while not os.path.ismount(path):
        path = os.path.dirname(path)
    return path

def get_config(file_path):
    import os
    import yaml
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Unable to find the config.yaml file. Expected location: {file_path}")
    f = open(file_path, 'r')
    config = yaml.load(stream=f, Loader=yaml.Loader)
    f.close()
    return config

def is_plot_online(plot):
    """
    Check if the path we got is online.
    This case happens in windows where drives could get re-ordered after a reboot
    """

    # importing os.path module
    import os.path

    # Check whether the specified path is an existing directory or not
    isdir = os.path.isdir ( plot )

    return isdir

def get_free_space_GiB (dir):
    """
    Return free space in GiB
    """
    drive = pathlib.Path ( dir ).parts[0]
    total , used , free = shutil.disk_usage ( drive )
    # convert to GiB
    free = free // (2 ** 30)
    return free

def is_verbose() :
    """
    Return True or False for verbose in config.yaml
    """
    verbose = get_config ( 'config.yaml' ).get ( 'verbose' )
    if verbose == True:
        return True
    else:
        return False

def get_verbose_level() :
    import logging
    """
    Return the level of logging, ERROR by default
    """
    verbose = get_config ( 'config.yaml' ).get ( 'verbose_level' )
    if verbose:
        if verbose in "ERROR":
            return logging.ERROR
        elif verbose in "INFO":
            return logging.INFO
        elif verbose in "DEBUG":
            return  logging.DEBUG
        else:
            return logging.ERROR
    else:
        return logging.ERROR

def get_plot_directories():
    config = get_config(get_config('config.yaml').get('chia_config_file'))
    return config.get('harvester').get('plot_directories')

def get_pyinquirer_style() :
    style = style_from_dict ( {
        Token.Separator : '#eab676' ,
        Token.QuestionMark : '#ffffff bold' ,
        Token.Selected : '#eab676' ,  # default
        Token.Pointer : '#eab676 bold' ,
        Token.Instruction : '' ,  # default
        Token.Answer : '#eab676 bold' ,
        Token.Question : '' ,
    } )
    return style

def print_spaces(input,length):
    x = ' '
    word =""
    i = 0
    count=length-len(input)
    while i <= count :
        word = word + x
        i += 1
    return word

def do_import_plots(style):
    import os , string
    from database import get_results_from_database
    from database import do_changes_to_database

    plots_to_import=[]
    import_action=[]
    total_size_GiB= 0
    from_drives =[]
    to_drives =[]


    # get the list of plot directories to ignore (i.e. do not want to add any more plots to)
    do_no_import_into_this_plot_directory = get_config ( 'config.yaml' ).get ( 'do_no_import_into_this_plot_directory' )
    WhereStatement=""
    if len(do_no_import_into_this_plot_directory) > 0:
        JoinedString = ",".join("'{0}'".format(elem) for elem in do_no_import_into_this_plot_directory)
        WhereStatment = "WHERE path NOT IN (%s)" %JoinedString


    free = 0
    used = 0
    action_keep = "Keep it"
    action_rename ="Keep and RENAME extension to 'IMPORTED'"
    action_delete ="Delete it"

    if is_verbose ( ) :
        logging.info("Getting list of potential source and destination locations")

    results = get_results_from_database ("""
    SELECT DISTINCT(pd.path), 
    (select count(*) from plots where drive = pd.drive and type = 'NFT') as NFT, 
    (select count(*) from plots where drive = pd.drive and type = 'OG') as OG ,
    pd.drive_free,
    pd.path
    FROM plot_directory as pd 
    %s
    order by 
    pd.path;
    """
    %WhereStatment)

    for line in results:
        drive = line[0]
        nft = line[1]
        og = line[2]
        accomodates = round(line[3]/101.5)
        path = line[4]
        if os.path.exists(drive):
            total , used , free = shutil.disk_usage ( find_mount_point ( drive ) )
            # convert to GiB
            free = bytes_to_gib ( free )
            total = bytes_to_gib ( total )
            from_drives.append(f'[{drive}]{print_spaces(drive,25)}| {nft:3.0f} NFTs, {og:3.0f} OGs | {free:5.0f}/{total:5.0f} ({free/total*100:5.2f})% GiB Free  |  ')
            if is_verbose ( ) :
                logging.info ( f'[{drive}]{print_spaces(drive,25)}| {nft:3.0f} NFTs, {og:3.0f} OGs | {free:5.0f}/{total:5.0f} ({free/total*100:5.2f})% GiB Free  |  ' )

            if line[3] > 101.5 :
                to_drives.append(f"[{drive}]{print_spaces(drive,25)}| {nft:3.0f} NFTs, {og:3.0f} OGs | Can accommodate {accomodates} k32 plots")

    from_drives.sort()
    to_drives.sort()
    # added an option for manual input
    from_drives.append ( f"[Other]{print_spaces('other',25)}| Location NOT listed in chia's plots directory" )
    from_drives.append ( "[Cancel]" )

    to_drives.append ( "[Cancel]" )


    questions = [
        {
            'type' : 'list' ,
            'name' : 'from' ,
            'choices': from_drives,
            'message' : 'Select SOURCE location to search for plots that you want to MOVE INTO farm?'

        }
    ]
    answers = prompt ( questions , style=style )
    import_from = answers['from'][answers['from'].find('[')+1:answers['from'].find(']')]

    if import_from == "Other":
        questions = [
            {
                'type' : 'input' ,
                'name' : 'from' ,
                'message' : 'Please enter SOURCE location'

            }
        ]
        answers = prompt ( questions , style=style )
        import_from = answers['from']

    if import_from == "Cancel":
        if is_verbose ( ) :
            logging.info ( f'Cancelled  ' )
        return
    else:
        print("* Searching for .plot files in [%s] ..." % (import_from))
        if is_verbose ( ) :
            logging.info ( f"Searching for .plot files in [%s] ..." % (import_from) )

        """ Walk the drive looking for .plot files """
        for root , dirs , files in os.walk ( import_from ) :
            for file in files :
                if file.endswith ( ".plot" ) :
                    type="Unverified"
                    data = get_results_from_database(f"SELECT type FROM plots WHERE name ='{file}'")
                    if len(data) > 0:
                        for line in data:
                            type = line[0]
                    filename = root + '\\' + file
                    plots_to_import.append ( filename )
                    size_GiB = bytes_to_gib ( os.path.getsize ( filename ))
                    total_size_GiB += size_GiB
                    print (f"> {filename} ({size_GiB} GiB)  (Format: {type})")
                    if is_verbose ( ) :
                        logging.info ( f"{filename} ({size_GiB} GiB)  (Format: {type})")

        questions = [
            {
                'type' : 'confirm' ,
                'name' : 'import' ,
                'message' : 'Do you want to import these files?' ,
                'default' : False

            }
        ]
        answers = prompt ( questions , style=style )
        import_decision = answers['import']

        if import_decision == True :
            questions = [
                {
                    'type' : 'list' ,
                    'name' : 'to' ,
                    'choices' : to_drives ,
                    'message' : 'Which location you want to move plots TO?'

                }
            ]
            answers = prompt ( questions , style=style )
            import_to = answers['to'][answers['to'].find ( '[' ) + 1 :answers['to'].find ( ']' )]

            # exit if the to and form are the same
            if import_from == find_mount_point ( import_to ):
                print("! TO and FROM destinations are the same! Skipping")
                if is_verbose ( ) :
                    logging.info("The provided TO and FROM destinations are the same! Skipping import of plot.")
                return

            if import_to == "Cancel":
                return

            mount_point = find_mount_point ( import_to )
            total , used , free = shutil.disk_usage ( mount_point )
            # convert to GiB
            free = bytes_to_gib(free)
            total_size_GiB = round(total_size_GiB,0)

        if free < total_size_GiB:
            print ( "!---------------------------------------------------------------------------------")
            print ( "! NOTICE! Some plots will be left behind due to lack of free space at destination.")
            print (f"! (Total incoming plot(s) size {total_size_GiB} GiB, Available destination space: {free} GiB) at {mount_point}")
            print ( "! You can move the remaining plots to a different destination later by re-running this utility. ")
            print ( "!---------------------------------------------------------------------------------")

        if import_decision == True :
            questions = [
                {
                    'type' : 'list' ,
                    'name' : 'delete' ,
                    'choices': [action_keep, action_rename, action_delete],
                    'message' : 'After the import is complete, what do you want to do with SOURCE plot?'

                }
            ]
            answers = prompt ( questions , style=style )
            action = answers['delete']

            if action == action_keep:
                import_action = "keep"
            elif action == action_rename:
                import_action = "rename"
            elif action == action_delete:
                import_action = "delete"

        if (plots_to_import) and (import_decision == True) and (import_to):
            for plot in plots_to_import :
                print ( "* Copying %s to %s" % (plot , import_to) )
                if do_import_file_into_farm(plot,import_to, import_action):
                    # Reset the stats of the plot so that it is rescanned in new location
                    do_changes_to_database("DELETE FROM plots WHERE name = '%s'" % (os.path.basename(plot)))
                    # delete size of originating plot directory
                    do_changes_to_database ( "DELETE FROM plot_directory WHERE drive = '%s'" % (find_mount_point( plot )) )
                    # delete size of destination plot directory
                    do_changes_to_database ( "DELETE FROM plot_directory WHERE drive = '%s'" % (find_mount_point ( import_to )) )
                    # rescan farm after changes
                    do_scan_farm ( )

        else :
            print ( "* No plots were moved from %s" % (import_from) )
def do_menu_overwrite_og_plots(style):
    import os , string
    from database import get_results_from_database
    from database import do_changes_to_database

    plots_to_import=[]
    total_size_GiB= 0
    confirm_decision = False

    free = 0
    used = 0
    action_keep = "Keep it"
    action_rename ="Keep and RENAME extension to 'IMPORTED'"
    action_delete ="Delete it"

    if is_verbose ( ) :
        logging.info("Getting list of NFT source locations")

    from_drives = get_list_nft_source_locations ( )
    questions = [
        {
            'type' : 'list' ,
            'name' : 'from' ,
            'choices': from_drives,
            'message' : 'Select NFT SOURCE location'

        }
    ]
    answers = prompt ( questions , style=style )
    import_from = answers['from'][answers['from'].find('[')+1:answers['from'].find(']')]
    if import_from == "Other":
        questions = [
            {
                'type' : 'input' ,
                'name' : 'from' ,
                'message' : 'Please enter SOURCE location'

            }
        ]
        answers = prompt ( questions , style=style )
        import_from = answers['from']
    if import_from == "Cancel":
        if is_verbose ( ) :
            logging.info ( f'Cancelled  ' )
        return
    else:
        if is_verbose ( ):logging.info ( f"Searching for .plot files in [{import_from}] ...")
        print(f"* Searching for .plot files in [{import_from}] ...")
        plots_to_import, nfts = get_plots_to_import ( import_from )
        questions = [
            {
                'type' : 'confirm' ,
                'name' : 'import' ,
                'message' : f'Do you want to import these {nfts} files?' ,
                'default' : False
            }
        ]
        answers = prompt ( questions , style=style )
        import_decision = answers['import']
        if import_decision == True :
            data = get_results_from_database ( f"SELECT COUNT(*) FROM plots WHERE type = 'OG'" )
            for line in data :
                ogs = line[0]
            if nfts > ogs:
                print (f"* You do not have enough OG space in your farm. You are importing {nfts} NFTs and there are {ogs} OGs in your farm.")
                logging.info(f"* You do not have enough OG space in your farm. You are importing {nfts} NFTs and there are {ogs} OGs in your farm.")
            questions = [
                {
                    'type' : 'confirm' ,
                    'name' : 'import' ,
                    'message' : f'ARE YOU SURE THAT YOU WANT TO OVERWRITE {nfts} of {ogs} OGS WITH NFTS?' ,
                    'default' : False

                }
            ]
            answers = prompt ( questions , style=style )
            confirm_decision = answers['import']
        else:
            print ("* Skipping!")

        if (plots_to_import) and (confirm_decision == True) and (import_decision == True):
            for plot in plots_to_import:
                print (f"for plot={plot}")
                data = get_results_from_database(f"SELECT name,path FROM plots WHERE TYPE = 'OG' LIMIT 1")
                if len(data) > 0:
                    for line in data :
                        name = line[0]
                        path = line[1]
                        filename = path+'\\'+name

                print ( f"find OG filename={filename}" )
                if os.path.exists ( filename ) :
                    print ( f"* Removing OG FILE {filename}" )
                    os.remove ( filename )
                    print ( f"* DELETING DATABASE ENTRY FOR {filename}" )
                    do_changes_to_database ( f"DELETE FROM plots WHERE name = '{name}'" )
                    logging.info ( f"Replacing OG plot {filename}" )
                    logging.info ( f"Deleting Database file and data base entry for {filename} type:OG" )
                    print ( f"* CHECKING SPACE BEFORE COPYING {plot}" )
                    # Double Check if there is space before copying
                    total , used , free = shutil.disk_usage ( find_mount_point ( path ) )
                    # convert to GiB
                    if bytes_to_gib ( free ) >= 101.5 :
                         print ( "* Copying %s to %s" % (plot , path) )
                         logging.info ( f"Copying NFT plot {plot} into OG's location at {path}" )
                         if do_import_file_into_farm ( plot , path , get_default_action_after_replacing_ogs() ):
                             # Reset the stats of the plot so that it is rescanned in new location
                             do_changes_to_database (f"DELETE FROM plots WHERE name = '{os.path.basename ( plot )}'")
                             # delete size of originating plot directory
                             do_changes_to_database ("DELETE FROM plot_directory WHERE drive = '%s'" % (find_mount_point ( plot )) )
                             # delete size of destination plot directory
                             do_changes_to_database ("DELETE FROM plot_directory WHERE drive = '%s'" % (find_mount_point ( path )) )
                    # rescan farm after changes
                    do_scan_farm ( )
                else:
                    print(f"{filename} not found!")

        else :
            print ( "* No plots were moved from %s" % (import_from) )


def get_plots_to_import(import_from) :
    from database import get_results_from_database

    plots_to_import=[]
    total_size_GiB=0

    """ Walk the drive looking for .plot files """
    nfts = 0
    for root , dirs , files in os.walk ( import_from ) :
        for file in files :
            if file.endswith ( ".plot" ) :
                type = "Unverified"
                data = get_results_from_database ( f"SELECT type FROM plots WHERE name ='{file}'" )
                if len ( data ) > 0 :
                    for line in data :
                        type = line[0]
                filename = root + '\\' + file
                plots_to_import.append ( filename )
                size_GiB = bytes_to_gib ( os.path.getsize ( filename ) )
                total_size_GiB += size_GiB
                print ( f"> {filename} ({size_GiB} GiB)  (Format: {type})" )
                nfts += 1
                if is_verbose ( ) :
                    logging.info ( f"{filename} ({size_GiB} GiB)  (Format: {type})" )

    return plots_to_import, nfts


def get_list_nft_source_locations() :
    from database import  get_results_from_database
    from_drives=[]

    results = get_results_from_database ( """
    SELECT pd.drive as MOUNT, 
    (select count(*) from plots where drive = pd.drive and type = 'NFT') as NFT, 
    (select count(*) from plots where drive = pd.drive and type = 'OG') as OG ,
    pd.drive_free,
    pd.path
    FROM plot_directory as pd ;
    """ )
    for line in results :
        drive = line[0]
        nft = line[1]
        og = line[2]
        if os.path.exists ( drive ) :
            total , used , free = shutil.disk_usage ( drive )
            # convert to GiB
            free = bytes_to_gib ( free )
            total = bytes_to_gib ( total )
            if nft > 1 :
                from_drives.append (
                    f'[{drive}]{print_spaces ( drive , 25 )}| {nft:3.0f} NFTs, {og:3.0f} OGs | {free:5.0f}/{total:5.0f} ({free / total * 100:5.2f})% GiB Free  |  ' )
                if is_verbose ( ) :
                    logging.info (
                        f'[{drive}]{print_spaces ( drive , 25 )}| {nft:3.0f} NFTs, {og:3.0f} OGs | {free:5.0f}/{total:5.0f} ({free / total * 100:5.2f})% GiB Free  |  ' )
    from_drives.sort ( )
    # added an option for manual input
    from_drives.append ( f"[Other]{print_spaces ( 'other' , 25 )}| Location NOT listed in chia's plots directory" )
    from_drives.append ( "[Cancel]" )
    return from_drives


def do_import_file_into_farm(src, destination_folder, action):
    """
    Import a file to farm takes as an argument the full plot filename with path
    and the destination folder location.  The method copies the file into
    a .tmp file and show the progress on the screen.  Once the file has been completelty
    copied, it changes the name to it from .tmp to .plot so that it is included by
    chia.
    """
    import shutil , os , sys, time
    from tqdm import tqdm
    basename = os.path.basename ( src )
    dest = destination_folder + '\\' + basename + '.tmp'
    f_size = os.stat ( src ).st_size
    buff = 10485760  # 1024**2 * 10 = 10M
    # Find the usage around the mount point
    disk_label = find_mount_point(destination_folder)
    dest_total , dest_used , dest_free = shutil.disk_usage ( disk_label )

    if dest_free < f_size:
        if is_verbose ( ) :
            logging.info (f"Copying was skipped for lack of available space at {disk_label} ")
        print(f"! Copying was skipped for lack of available space at {disk_label}")
        return False
    else:
        num_chunks = f_size // buff + 1
        if is_verbose ( ) :
            logging.info ( "Copying %s as %s" % (src , dest) )
        with open ( src , 'rb' ) as src_f , open ( dest , 'wb' ) as dest_f :
            try :
                for i in tqdm ( range ( num_chunks ) , bar_format='{desc:<5.5}{percentage:3.0f}%|{bar:60}{r_bar}' ) :
                    chunk = src_f.read ( buff )
                    dest_f.write ( chunk )
            except IOError as e :
                print ( e )
            finally :
                # give them the proper names (dest == remove .tmp , src == add .to_be_deleted)
                dest_f.close ( )
                src_f.close ( )
                live = destination_folder + '\\' + basename
                done = src + '.imported'
                os.rename ( dest , live )  # make the plot live
                if is_verbose ( ) :
                    logging.info ( "[DESTINATION] Renaming %s to %s" % (dest , live) )

                if action == "rename":
                    os.rename ( src , done )  # stop source from being reimported
                    if is_verbose ( ) :
                        logging.info ( "[SOURCE] Renamed %s to %s" % (src , done) )
                elif action =="delete":
                    os.remove(src)
                    if is_verbose ( ) :
                        logging.info ( "[SOURCE] Deleted %s" % (src) )


                print ( f'Done! Copied {bytes_to_gib(f_size)} GiB' )
    return True

def get_plots_in_list( list ) :
    # find files that have .plot extension
    p = re.compile ( ".*\.plot$" )
    plot_list = list ( filter ( p.match , list ) )
    return plot_list

def bytes_to_gib(number) :
    number = number // (2 ** 30)
    return number

def do_scan_farm():
    from database import do_changes_to_database
    from database import get_results_from_database
    from tqdm import tqdm , trange

    ignore_these = ["$RECYCLE.BIN","System Volume Information"]
    session_id = get_session_id()

    print ( "Scanning Chia farm..." )
    plot_dirs = get_plot_directories ( )

    if is_verbose() :
        logging.info ( "Scanning Chia farm..." )

    for dir in plot_dirs :

        if os.path.isdir(dir):
            mount_point = find_mount_point(dir)
            mount_total , mount_used , mount_free = shutil.disk_usage ( mount_point )
            mount_total = bytes_to_gib(mount_total)
            mount_used = bytes_to_gib(mount_used)
            mount_free = bytes_to_gib(mount_free)
            logging.debug(f"Path {dir} is valid Valid")
            do_changes_to_database( "REPLACE INTO plot_directory (path, drive, drive_size, drive_used, drive_free, valid, scan_ukey) values ('%s','%s','%s','%s','%s','%s','%s')" % (dir , mount_point , mount_total, mount_used,mount_free, "Yes",session_id))
            """ Check if the plots defined in the chia config file are online"""
            if not is_plot_online(dir):
                logging.error("%s plot is offline" % (dir))
            else:
                logging.debug (f" Plot {dir}is online")
                arr = os.listdir ( dir )
                plots_at_location = len(arr)
                """ If there are files to scan, start loop """
                if plots_at_location > 0:
                    logging.debug ( " %s plots found. " % (plots_at_location) )
                    with tqdm ( total=plots_at_location , bar_format='{desc:<25}{percentage:<3.0f}%|{bar:60}{r_bar}' ) as pbar :
                        for plot in arr :
                            pbar.update ( 1 )
                            pbar.set_description ( "%s " % (dir) )
                            scanned = 0
                            indirectory=0
                            if (plot not in ignore_these) :
                                data = get_results_from_database(f"SELECT (select count(*) from plots where name= '{plot}') as scanned, (select count(*) from plots where name= '{plot}' and path='{dir}') as indirectory FROM plots where name ='{plot}' order by path")
                                logging.debug ( f"DATA = {data}" )
                                for line in data:
                                    scanned = line[0]
                                    indirectory = line[1]
                                    logging.debug(f"DATA = {data}")

                                if not scanned and not indirectory :
                                    filename = dir + '\\' + plot
                                    plot_size = bytes_to_gib( os.path.getsize ( filename ))
                                    if is_verbose ( ) :
                                        logging.info ( "Checking %s:" % (plot) )
                                        logging.info ( "Size: %s |" % (plot_size) )

                                    found = "Found 1 valid plots"
                                    is_nft = "Pool public key: None"
                                    output = []
                                    chia_binary = get_chia_binary ( )
                                    if chia_binary:
                                        if os.path.exists ( chia_binary ) and plot.endswith ( ".plot" ) :
                                            output = subprocess.getoutput ( '%s plots check -g %s' % (chia_binary , plot) )
                                            # if it is a valid plot, find out if it is NFT or OG
                                            if found in output :
                                                if is_verbose ( ) :
                                                    logging.info ( f"{plot} Plot Valid: Yes" )
                                                valid = "Yes"

                                                if is_nft in output :
                                                    if is_verbose ( ) :
                                                        logging.info ( f"{plot} Plot Type: NFT" )
                                                    type = "NFT"
                                                else :
                                                    if is_verbose ( ) :
                                                        logging.info ( f"{plot} Plot Type: OG" )
                                                    type = "OG"

                                            else :
                                                if is_verbose ( ) :
                                                    logging.info ( f"{plot} Plot Valid: No" )
                                                    logging.info ( f"{plot} Plot Type: Not Applicable" )
                                                valid = "No"
                                                type = "NA"


                                            do_changes_to_database("REPLACE INTO plots (name, path, drive, size, type, valid, scan_ukey) values ('%s','%s','%s','%s','%s','%s','%s')" % (
                                                plot , dir , mount_point , plot_size , type , valid,session_id))
                                    else :
                                        logging.error ( "Chia binary was not found, please check config.yaml setting **" )

                                else :
                                    if is_verbose ( ) :
                                        logging.info ( "Plot %s has been previously scanned!" % (plot) )
                                    if not indirectory:
                                        do_changes_to_database (f"UPDATE plots SET path='{dir}', drive='{mount_point}', scan_ukey='{session_id}' WHERE name='{plot}'")
                                        if is_verbose ( ) :
                                            logging.info(f"Updated {plot} locaiton to {dir} in DB")
                else:
                    print ( " %s plots found | Skipping!" % (plots_at_location) )


        else:
            print ( " Directory: In-Valid |" , end="" )
            logging.error("! %s, which is listed in chia's config.yaml file is not a valid directory" % (dir))
            do_changes_to_database("REPLACE INTO plot_directory (path, drive, drive_size, drive_used, drive_free, valid,scan_ukey) values ('%s','%s','%s','%s','%s','%s','%s')" % (dir , "" , 0, 0,0, "No",session_id))

    """
    After the scan, let us do some garbage collection of 
    records left behind from plots that are not longer attached to farm
    """
    data = get_results_from_database(f"SELECT path FROM plot_directory WHERE scan_ukey != '{session_id}'")
    if len(data) > 0:
        print("! Detected plot directories in database but not in Chia's config.yaml file")
        print("* Cleaning up the plot directories and associated plot names from database")
        for record in data:
            path = record[0]
            if is_verbose ( ) :
                logging.info(f"DELETE FROM plot_directory WHERE path = '{path}'")
            do_changes_to_database(f"DELETE FROM plot_directory WHERE path = '{path}'")

    """
    Let us scan the database and check that the files are still there,
    otherwise remove entry
    """
    data = get_results_from_database(f"SELECT id,name,path FROM plots")
    if len(data) > 0:
        print ("* Scanning farm for deleted or moved files...")
        for record in data:
            id = record[0]
            filename= record[2] + "\\" + record[1]
            if not os.path.exists(filename):
                if is_verbose ( ) :
                    logging.info(f"{filename} not found! removing from plots database")
                    logging.info(f"DELETE FROM plots WHERE name = '{record[1]}'")
                do_changes_to_database ( f"DELETE FROM plots WHERE name = '{record[1]}'" )
            else:
                do_changes_to_database(f"UPDATE plots SET scan_ukey = '{session_id}' WHERE id = {id}")

    data = get_results_from_database(f"SELECT id,name,path FROM plots WHERE scan_ukey != '{session_id}'")
    if len(data) > 0:
        print ("* Scanning farm for deleted or moved files...")
        for record in data:
            id = record[0]
            filename= record[2] + "\\" + record[1]
            if not os.path.exists(filename):
                if is_verbose ( ) :
                    logging.info(f"{filename} not found! removing from plots database")
                    logging.info(f"DELETE FROM plots WHERE name = '{record[1]}'")
                do_changes_to_database ( f"DELETE FROM plots WHERE name = '{record[1]}'" )
            else:
                do_changes_to_database(f"UPDATE plots SET scan_ukey = '{session_id}' WHERE id = {id}")

def get_chia_binary() :
    import logging
    chia_binary = get_config ( 'config.yaml' ).get ( 'chia_binary' )
    if not chia_binary:
        logging.error("chia_binary variable was not found in config.yaml, please configure and restart application")
        exit()
    logging.debug(f"* chia_binary location: {chia_binary}")
    return chia_binary

def get_sync_plot_dirs_with_forks() :
    import logging

    sync_plot_directory_with_locally_install_forks = get_config ( 'config.yaml' ).get ( 'sync_plot_directory_with_locally_install_forks' )

    if not sync_plot_directory_with_locally_install_forks:
        sync_plot_directory_with_locally_install_forks = False

    logging.debug(f"* sync_plot_directory_with_locally_install_forks is set to {sync_plot_directory_with_locally_install_forks}")
    return sync_plot_directory_with_locally_install_forks


def get_default_action_after_replacing_ogs() :
    import logging
    """
    Farmers can automatically overwrite OGS with NFTS that which are found at a specified locations.
    This method, tells the calling method what to do with the plot after it has been imported.
    the default is rename, which is appending the word "imported" to the end of the filename
    """
    default_action_after_replacing_ogs = get_config ( 'config.yaml' ).get ( 'default_action_after_replacing_ogs' )

    if not default_action_after_replacing_ogs:
        default_action_after_replacing_ogs = "rename"

    logging.debug(f"* Default Action After Replacing OGS is Set to {default_action_after_replacing_ogs}")
    return default_action_after_replacing_ogs


def get_extenstions_to_ignore() :
    ignore_extensions = get_config ( 'config.yaml' ).get ( 'ignore_extensions' )
    if not ignore_extensions:
        logging.info("ignore_extensions variable was not found in config.yaml")
        return False
    return ignore_extensions




def do_check_for_issues():
    from database import get_results_from_database
    from database import do_changes_to_database

    issues = 0

    """ Check for invalid plots"""
    data = get_results_from_database("SELECT * FROM plot_directory WHERE valid = 'No'")
    if len ( data ) > 0 :
        logging.error ("Found %s invalid plot-directory definitions in chia's config.yaml file" % (len ( data )))
        issues += len(data)

    """ Check for invalid plots"""
    data = get_results_from_database("SELECT * FROM plots WHERE valid = 'No'")
    invalid_plots =0
    if len ( data ) > 0 :
        for line in data:
            path = line[2]
            file = line[1]
            filename = path + "\\" + file
            if os.path.isfile(filename):
                invalid_plots += 1
            else:
                if is_verbose ( ) :
                    logging.info(f"File:{filename} is not a valid entry in Database! Deleteing it form id # {line[0]}")
                do_changes_to_database("DELETE FROM plots WHERE ID = %s" % (line[0]))
        if is_verbose():
            logging.info ("No invalid plots found in farm")
    issues += invalid_plots
    return issues

def do_resolve_issues():
    from database import get_results_from_database
    from database import do_changes_to_database
    from tqdm import tqdm
    import logging

    issues = 0
    style = get_pyinquirer_style ( )

    """ Check for invalid plots"""
    data = get_results_from_database("SELECT * FROM plot_directory WHERE valid = 'No'")
    if len ( data ) > 0 :
        print ("* Plot-directory definitions in chia's config.yaml (%s issue found)" % (len ( data )))

        for line in data:
            print ("> %s is NOT a valid plot directory" % (line[1]))

        questions = [
            {
                'type' : 'confirm' ,
                'name' : 'do' ,
                'message' : 'Do you want to remove entries from your chia\'s configuration?' ,
                'default' : False ,

            }
        ]
        answers = prompt ( questions , style=style )
        if answers['do']:
            print ("* Updating chia plot configuration to remove invalid directories...")
            chia_binary = get_chia_binary ( )
            for line in data :
                path = line[1]
                output = subprocess.getoutput ( '%s plots remove -d %s' % (chia_binary , path) )
                do_changes_to_database("DELETE FROM plot_directory WHERE ID = %s" % (line[0]))
        else:
            print ( "* No changes made to chia configuration" )

    """ Check fir invalid plots"""
    data = get_results_from_database("SELECT * FROM plots WHERE valid = 'No'")
    if len ( data ) > 0 :
        print ("* Invalid plots found in farm (%s)" % (len ( data )))

        for line in data:
            print ( "> %s\%s is NOT a valid chia plot file" % (line[2],line[1]) )

        questions = [
            {
                'type' : 'confirm' ,
                'name' : 'do' ,
                'message' : 'Do you want to DELETE these files?' ,
                'default' : False ,

            }
        ]
        answers = prompt ( questions , style=style )
        if answers['do'] :
            print ( "* Deleting invalid plot ..." )
            for i in tqdm ( range ( len ( data ) ) , bar_format='{desc:<5.5}{percentage:3.0f}%|{bar:60}{r_bar}' ) :
                for line in data :
                    path = line[2]
                    file = line[1]
                    filename = path + "\\" + file
                    if filename in get_extenstions_to_ignore():
                        ignore = True
                    else:
                        ignore = False

                    if not ignore:
                        os.remove ( filename )
                        do_changes_to_database("DELETE FROM plots WHERE ID = %s" % (line[0]))
                        # reset the plot_directory_stats for the removed files
                        do_changes_to_database (
                            "DELETE FROM plot_directory WHERE drive = '%s'" % (find_mount_point ( filename )) )
        else :
            print ( "* No changes made to chia configuration" )

    # rescan farm after changes
    do_scan_farm ( )

def do_show_farm_distribution():
    from database import get_results_from_database
    og=0
    nft=0

    print("*--------------------------------------------------------------")
    print("* Farm Plot Type Distribution")
    print("*--------------------------------------------------------------")

    """ Check for invalid plots"""
    data = get_results_from_database("SELECT count(*), type FROM plots WHERE valid = 'Yes' GROUP BY type")
    for line in data:
        if line[1] == 'NFT':
            nft = line[0]
        else:
            og = line[0]

    if (nft == 0) and (og == 0):
        print("* No NFT or OG plots found!")
        if is_verbose ( ) :
            logging.info("No NFT or OG plots found!")
        print("* Please run the 'Verify Plot Directories and Plots' to scan the farm for NFTs, OGs and Validate plots...")
    else:
        data=[[nft,"GREEN","NFT"],
              [og,"YELLOW","OG"],
              ["Your Farm Distribution","both","Yes",""]]
        stacked_bar_chart ( data , 40 )

def do_show_farm_capacity():
    from database import get_results_from_database
    labels=[]
    used=[]
    free=[]

    print("* ----------------------------------------------------------------------")
    print("* Farm Capacity:")
    print("* Plot Directory            | Capacity (# plots) ")
    print("* ----------------------------------------------------------------------")
    """ Check for invalid plots"""
    data = get_results_from_database("SELECT * FROM plot_directory WHERE valid = 'Yes'")
    if data:
        for line in data:
            path = line[1]

            # if the free space is greater than an average k32 (101.5 GiB) plot then show availability
            if line[5] > 101.5:
                print(f"> {path.ljust ( 25 )} | Space for [{round(line[5]/101.5):3.0f}] k32 plots available")
    else:
        print ("* Please run the 'Verify Plot Directories and Plots' to scan the farm for NFTs, OGs and Validate plots..." )

def do_show_farm_usage():
    from database import get_results_from_database

    print("* ----------------------------------------------------------------------")
    print("* Farm Usage:")
    print("* Bar Graph (Usage)                 | Total GiB > Legend : Plot Directory [Capacity]")
    print("* ----------------------------------------------------------------------")

    # SELECT
    # pd.drive as MOUNT ,
    # (select count( *)
    # from plots where
    # drive = pd.drive and type = 'NFT') as NFT ,
    # (select count( *)
    # from plots where
    # drive = pd.drive and type = 'OG') as OG ,
    # pd.drive_free ,
    # pd.path
    # FROM
    # plot_directory as pd;




    """ Check for invalid plots"""
    data = get_results_from_database(
        """
        SELECT pd.path, 
        pd.drive_used, 
        pd.drive_free, 
        (select count( *) from plots where drive = pd.drive and type = 'NFT') as NFT,
        (select count( *) from plots where drive = pd.drive and type = 'OG') as OG 
        FROM plot_directory as pd WHERE valid = 'Yes'
        """
        )
    for line in data:
        path = line[0]
        used = line[1]
        free = line[2]
        nft_count = line[3]
        og_count = line[4]
        pct_used = (used / (used + free)) * 100
        if free < 100.5:
            drive_full = f"[Drive Full - {nft_count:>3.0f} NFTs/{og_count:>3.0f} OGs]"
        else:
            drive_full = f"[{round(free/101.5)} K32 Spots - {nft_count:>3.0f} NFTs/{og_count:>3.0f} OGs]"

        data=[[used,"RED","Used"],
              [free,"GREEN","Free"],
              [path.ljust(25) ,"percent","Yes", drive_full]]
        stacked_bar_chart ( data , 40 )

def start_new_session():
    import uuid
    from database import do_changes_to_database
    session_id = uuid.uuid4 ( )
    do_changes_to_database ("DELETE FROM farm_scan")
    do_changes_to_database ("INSERT INTO farm_scan (initiated_by, scan_ukey) values ('','%s')" % (session_id) )
    return

def get_session_id():
    from database import get_results_from_database
    data = get_results_from_database ( "SELECT scan_ukey FROM farm_scan ;" )
    return data[0][0]

def save_config(filename,config_data):
    import yaml
    tempfile = filename + str(os.getpid())
    with open(tempfile, "w") as f:
        yaml.safe_dump(config_data, f)
    shutil.move(tempfile, filename)


def load_config(filename):
    import yaml
    if not os.path.isfile(filename):
        print(f"can't find {filename}")
    r = yaml.safe_load(open(filename, "r"))
    return r


def do_sync_chia_forks ():
    import logging
    print ( "* Synchronizing Chia's Plot Directories with the following chia forks..." )
    logging.info("* Looking for chia forks to sync directory plots with")
    # Load the Chia Config file
    chia_data = load_config(get_config ( 'config.yaml' ).get ( 'chia_config_file' ))
    # lets loop through the known chia forks
    chia_forks=get_config ( 'config.yaml' ).get ( 'chia_forks' )
    # Loaded the chia forks in the config files
    logging.info(f"* found the following forks defined in config file {chia_forks}")
    for fork_name in chia_forks:
        fork_config_file = fork_name + "\mainnet\config\config.yaml"
        if os.path.exists(fork_config_file):
            print(f"* {fork_name}")
            logging.debug(f"Fork name: {fork_name}...")
            fork_data = load_config(fork_config_file)
            for item in fork_data['harvester']['plot_directories']:
                fork_data['harvester']['plot_directories'].remove ( item )
            # Add Chia's plot directory
            for item in chia_data['harvester']['plot_directories']:
                fork_data['harvester']['plot_directories'].append(item)

            save_config(fork_config_file,fork_data)




#################### NOT ready to be used  ###################
# cleanup the cli output to avoid confusion when cleaning space
def indent(symbol,string):
    tab = '    '
    space = ' '
    sentence = tab + symbol + space + string
    return(sentence)


""" TBD defrag logic to compact (not used yet)"""
def defrag_plots(plot_dirs, average_size):
    min_storage_available = 9999999999
    max_storage_available = 0

    counter = 0
    for dir in plot_dirs:
        drive = pathlib.Path(dir).parts[0]
        total, used, free = shutil.disk_usage(drive)
        # convert to GiB
        free = bytes_to_gib(free)
        used = bytes_to_gib(used)
        calculated_num_of_plots = round(used / average_size)
        if free > average_size:
            counter += 1
            mod = round(free/average_size)
            print(indent(">", "%s has %s GiB free, good enough for %s plot(s)" % (dir, free, mod)))
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

