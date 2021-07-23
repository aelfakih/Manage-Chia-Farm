import subprocess
import pathlib
import os
import re
import sys
import shutil
import yaml
import collections
from tqdm import tqdm, trange
import logging
from PyInquirer import style_from_dict, Token, prompt, Separator

#####  Needs cleanup #####
def get_chia_farm_plots() :
    chia_farm = []
    plot_sizes =[]
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
                        plot_sizes.append ( round ( os.path.getsize ( filename ) / (2 ** 30) , 2 ) )
        else:
            logging.error("! %s, which is listed in chia's config.yaml file is not a valid directory" % (directory))
    # sort chia_farm
    chia_farm.sort ( )
    return chia_farm

def get_non_plots_in_farm( chia_farm ) :
    plot_list =[]

    # find files that have .plot extension
    p = re.compile ( ".*\.plot$" )

    # find symmetric difference.
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
    from database import do_changes_to_database
    from PyInquirer import prompt , Separator
    session_id = get_session_id()

    total_size_GiB = 0
    chia_farm = get_chia_farm_plots ( )
    """ [1] Find and remove NON-PLOTS """

    print ( "* Checking for non-plots files (without a '.plot' extension) ... " , end="" )

    """ Get the non plots in the farm """
    non_plot_list = get_non_plots_in_farm ( chia_farm )

    if non_plot_list :
        number_of_files = len ( non_plot_list )
        print ( "[NOK]" )
        print ( indent ( "*" , "WARNING! Found %s non-plot files in farm." % (number_of_files) ) )
        for file in non_plot_list :
            size_GiB = bytes_to_gib(os.path.getsize ( file ))
            total_size_GiB += size_GiB
            print ( indent ( ">" , "%s (%s GiB)" % (file , size_GiB) ) )
            do_changes_to_database (
                f"REPLACE INTO plots (name, path, drive, size, type, valid, scan_ukey) values ('{os.path.basename(file)}','{os.path.dirname(file)}\','{find_mount_point ( file )}','{size_GiB}','?','No','{session_id}')")


        """ Get feedback from farmer (default is do not delete) """
        questions = [
            {
                'type' : 'confirm' ,
                'message' : "Do you want to DELETE NON-PLOT files and save %s GB of storage space?" % (total_size_GiB) ,
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
    else :
        print ( "[OK] None found!" )
        if is_verbose ( ) :
            logging.info ( "No non-plots files found!" )

""" 
Find plots with the same name in the farm, 
so that we can prunce the farm and maintain 
only one copy
"""
def find_duplicate_plots() :
    from PyInquirer import prompt , Separator
    largest_capacity = 0

    print ( "* Checking for duplicate plot filenames ... " , end="" )

    """ Get the duplicate plotnames """
    duplicate_plotnames , plot_path = get_duplicte_plotnames ( get_plot_directories ( ) )

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
                print ( indent ( "*" , "Deleting [%s]" % (file_to_delete) ) )
                os.remove ( file_to_delete )
                if is_verbose ( ) :
                    logging.info ( "Deleting [%s]" % (file_to_delete) )
        else :
            print ( indent ( "*" , "Skipping. No files deleted!" ) )
    else :
        print ( "[OK] None found!" )
        if is_verbose ( ) :
            logging.info ( "No duplicate names files found!" )

def get_smallest_plot ( ):
    plot_dirs = get_plot_directories ( )
    min_storage_available = 9999999999
    average_size = 106300000
    counter = 0
    for dir in plot_dirs:
        drive = get_letter_drive ( dir )
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

    line_label = data[2][0]
    label_style = data[2][1] # Label Style: accepts: both, percent, count, none
    label_total = data[2][2] # Add Total: accepts: Yes, No


    segment_one_percent = 100 * segment_one_length / (segment_two_length + segment_one_length)
    segment_two_percent = 100 * segment_two_length / (segment_two_length + segment_one_length)
    total_segments = segment_two_length + segment_one_length

    segment_one_normalized = round ( (segment_one_length / (segment_one_length + segment_two_length)) * max_length )

    for i in range ( max_length ) :
        if i <= segment_one_normalized :
            sys.stdout.write (  get_colorama_fgcolor ( segment_one_color )+  u"\u2588" )
        if i > segment_one_normalized :
            sys.stdout.write ( get_colorama_fgcolor ( segment_two_color ) + u"\u2588" )
        sys.stdout.flush ( )


    #print Legend
    sys.stdout.write ( Fore.RESET )
    if label_total in "Yes":
        sys.stdout.write ( f" Total: {total_segments:.0f} >"  )
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
    if line_label:
        sys.stdout.write ( Fore.RESET + Back.RESET + f" : {line_label}" )
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
    print ( "* Scanning your farm! Found" , number_of_plots , "plots mounted to this machine!" )
    if is_verbose ( ) :
        logging.info ( "Found %s files in farm" % (number_of_plots) )

""" For a given path/file find the mount point"""
def find_mount_point(path):
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

"""
Check if the path we got is online. 
This case happens in windows where drives could get re-ordered after a reboot
"""
def is_plot_online(plot):
    # importing os.path module
    import os.path

    # Check whether the specified path is an existing directory or not
    isdir = os.path.isdir ( plot )

    return isdir

""" Retrun free space in GiB """
def get_free_space_GiB (dir):
    drive = pathlib.Path ( dir ).parts[0]
    total , used , free = shutil.disk_usage ( drive )
    # convert to GiB
    free = free // (2 ** 30)
    return free

""" Return True or False for verbose in config.yaml """
def is_verbose() :
    verbose = get_config ( 'config.yaml' ).get ( 'verbose' )
    if verbose == True:
        return True
    else:
        return False

def get_plot_directories():
    import yaml
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

def do_import_plots(style):
    import os , string
    from database import get_results_from_database
    from database import do_changes_to_database

    plots_to_import=[]
    import_action=[]
    total_size_GiB= 0
    from_drives =[]
    to_drives =[]

    free = 0
    used = 0
    action_keep = "Keep it"
    action_rename ="Keep and RENAME extension to 'IMPORTED'"
    action_delete ="Delete it"

    results = get_results_from_database ("""
    SELECT pd.drive as MOUNT, 
    (select count(*) from plots where drive = pd.drive and type = 'NFT') as NFT, 
    (select count(*) from plots where drive = pd.drive and type = 'OG') as OG ,
    pd.drive_free,
    pd.path
    FROM plot_directory as pd ;
    """)
    for line in results:
        drive = line[0]
        nft = line[1]
        og = line[2]
        free = round(line[3]/101.5)
        path = line[4]
        from_drives.append("[%s]  Contains %s NFTs, %s OGs" %  (drive,nft,og))
        if line[3] > 101.5 :
            to_drives.append("[%s]  Contains %s NFTs, %s OGs, and can accommodate %s k32 plots" %  (path,nft,og,free))

    # added an option for manual input
    from_drives.append ( ">> [Other] Location not listed in chia's plots directory" )
    from_drives.append ( ">> [Cancel]" )

    to_drives.append ( ">> [Cancel]" )


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
        return
    else:
        print("* Searching for .plot files in [%s] ..." % (import_from))

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
                    'message' : 'Which location you wanto to move plots TO?'

                }
            ]
            answers = prompt ( questions , style=style )
            import_to = answers['to'][answers['to'].find ( '[' ) + 1 :answers['to'].find ( ']' )]

            # exit if they to and form are the same
            if import_from == find_mount_point ( import_to ):
                print("! TO and FROM destinations are the same! Skipping")
                logging.info("The provided TO and FROM destinations are the same! Skipping import of plot.")
                return

            if import_to == "Cancel":
                return

            drive = pathlib.Path ( import_to ).parts[0]
            total , used , free = shutil.disk_usage ( drive )
            # convert to GiB
            free = bytes_to_gib(free)
            used = bytes_to_gib(used)
            total_size_GiB = round(total_size_GiB,0)

        if free < total_size_GiB:
            print ("** NOTICE! Some plots will be left behind due to free space available at destination.  (Plots %s GiB, Destination: %s GiB free)" % (total_size_GiB, free))
            print ("* You can move the remaining plots to a different destination later by re-running this utility. ")

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
                do_import_file_into_farm(plot,import_to, import_action)

                """ Reset the stats of the plot so that it is rescanned in new location"""
                do_changes_to_database("DELETE FROM plots WHERE name = '%s'" % (os.path.basename(plot)))

                """ delete size of originating plot directory"""
                do_changes_to_database ( "DELETE FROM plot_directory WHERE drive = '%s'" % (find_mount_point( plot )) )

                """ delete size of destination plot directory"""
                do_changes_to_database ( "DELETE FROM plot_directory WHERE drive = '%s'" % (find_mount_point ( import_to )) )

            # rescan farm after changes
            do_scan_farm ( )
        else :
            print ( "* No plots were moved from %s" % (import_from) )

""" 
Import a file to farm takes as an argument the full plot filename with path
and the destination folder location.  The method copies the file into
a .tmp file and show the progress on the screen.  Once the file has been completelty
copied, it changes the name to it from .tmp to .plot so that it is included by
chia.
"""
def do_import_file_into_farm(src, destination_folder, action):
    import shutil , os , sys, time
    from tqdm import tqdm
    basename = os.path.basename ( src )
    dest = destination_folder + '\\' + basename + '.tmp'
    f_size = os.stat ( src ).st_size
    buff = 10485760  # 1024**2 * 10 = 10M

    disk_label = pathlib.Path ( destination_folder ).parts[0]
    dest_total , dest_used , dest_free = shutil.disk_usage ( disk_label )

    if dest_free < f_size:
        logging.info (f"* Copying was skipped for lack of available space at {disk_label} ")
        print(f"! Copying was skipped for lack of available space at {disk_label}")
    else:
        num_chunks = f_size // buff + 1
        if is_verbose ( ) :
            logging.info ( "Copying %s as %s" % (src , dest) )
        with open ( src , 'rb' ) as src_f , open ( dest , 'wb' ) as dest_f :
            try :
                for i in tqdm ( range ( num_chunks ) ) :
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
        print ( "* Checking plot directory %s: " % (dir), end="" )

        if os.path.isdir(dir):
            mount_point = find_mount_point(dir)
            mount_total , mount_used , mount_free = shutil.disk_usage ( mount_point )
            mount_total = bytes_to_gib(mount_total)
            mount_used = bytes_to_gib(mount_used)
            mount_free = bytes_to_gib(mount_free)
            print(" Directory: Valid |",end="")
            do_changes_to_database( "REPLACE INTO plot_directory (path, drive, drive_size, drive_used, drive_free, valid, scan_ukey) values ('%s','%s','%s','%s','%s','%s','%s')" % (dir , mount_point , mount_total, mount_used,mount_free, "Yes",session_id))
            """ Check if the plots defined in the chia config file are online"""
            if not is_plot_online(dir):
                logging.error("%s plot is offline" % (dir))
                print (" Online: No |",end="")
            else:
                print (" Online: Yes |",end="")
                arr = os.listdir ( dir )
                plots_at_location = len(arr)
                print ( " # plots %s | Scanning Plots..." % (plots_at_location))
                with tqdm ( total=plots_at_location ) as pbar :
                    for plot in arr :
                        pbar.update ( 1 )
                        scanned = 0
                        indirectory=0
                        if (plot not in ignore_these) :
                            data = get_results_from_database(f"SELECT (select count(*) from plots where name= '{plot}') as scanned, (select count(*) from plots where name= '{plot}' and path='{dir}') as indirectory FROM plots where name ='{plot}'")
                            for line in data:
                                scanned = line[0]
                                indirectory = line[1]

                            if not scanned and not indirectory :
                                filename = dir + '\\' + plot
                                plot_size = bytes_to_gib( os.path.getsize ( filename ))
                                logging.info ( "Checking %s:" % (plot) )
                                logging.info ( " Size: %s |" % (plot_size) )

                                found = "Found 1 valid plots"
                                is_nft = "Pool public key: None"
                                output = []
                                chia_binary = get_chia_binary ( )
                                if os.path.exists ( chia_binary ) and plot.endswith ( ".plot" ) :
                                    output = subprocess.getoutput ( '%s plots check -g %s' % (chia_binary , plot) )
                                    # if it is a valid plot, find out if it is NFT or OG
                                    if found in output :
                                        logging.info ( f"{plot} Plot Valid: Yes" )
                                        valid = "Yes"

                                        if is_nft in output :
                                            logging.info ( f"{plot} Plot Type: NFT" )
                                            type = "NFT"
                                        else :
                                            logging.info ( f"{plot} Plot Type: OG" )
                                            type = "OG"

                                    else :
                                        logging.info ( f"{plot} Plot Valid: No" )
                                        logging.info ( f"{plot} Plot Type: Not Applicable" )
                                        valid = "No"
                                        type = "NA"


                                    do_changes_to_database("REPLACE INTO plots (name, path, drive, size, type, valid, scan_ukey) values ('%s','%s','%s','%s','%s','%s','%s')" % (
                                        plot , dir , mount_point , plot_size , type , valid,session_id))

                                else :
                                    logging.error ( "Chia binary was not found, please check config.yaml setting **" )

                            else :
                                logging.info ( "Plot %s has been previously scanned!" % (plot) )
                                if not indirectory:
                                    do_changes_to_database (f"UPDATE plots SET path='{dir}', drive='{mount_point}', scan_ukey='{session_id}' WHERE name='{plot}'")
                                    logging.info(f"Updated {plot} locaiton to {dir} in DB")


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
            logging.info(f"DELETE FROM plot_directory WHERE path = '{path}'")
            do_changes_to_database(f"DELETE FROM plot_directory WHERE path = '{path}'")

    """
    Let us scan the database and check that the files are still there,
    otherwise remove entry
    """
    data = get_results_from_database(f"SELECT id,name,path FROM plots WHERE scan_ukey IS NULL")
    if len(data) > 0:
        print ("* Scanning farm for deleted or moved files...")
        for record in data:
            id = record[0]
            filename= record[2] + "\\" + record[1]
            if not os.path.exists(filename):
                logging.info(f"! {filename} not found! removing from plots database")
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
                logging.info(f"! {filename} not found! removing from plots database")
                print(f"DELETE FROM plots WHERE name = '{record[1]}'")
                do_changes_to_database ( f"DELETE FROM plots WHERE name = '{record[1]}'" )
            else:
                do_changes_to_database(f"UPDATE plots SET scan_ukey = '{session_id}' WHERE id = {id}")


def get_chia_binary() :
    chia_binary = get_config ( 'config.yaml' ).get ( 'chia_binary' )
    return chia_binary

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
                logging.info(f"! File:{filename} is not a valid entry in Database! Deleteing it form id # {line[0]}")
                do_changes_to_database("DELETE FROM plots WHERE ID = %s" % (line[0]))
        logging.error ("Found %s invalid plots in farm" % (issues))
    issues += invalid_plots
    return issues

def do_resolve_issues():
    from database import get_results_from_database
    from database import do_changes_to_database

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
            print ( "* Deleting invalid files plot files..." )
            for line in data :
                path = line[2]
                file = line[1]
                filename = path + "\\" + file
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
        print("* Please run the 'Verify Plot Directories and Plots' to scan the farm for NFTs, OGs and Validate plots...")
    else:
        data=[[nft,"GREEN","NFT"],[og,"YELLOW","OG"],["","both","Yes"]]
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

    """ Check for invalid plots"""
    data = get_results_from_database("SELECT * FROM plot_directory WHERE valid = 'Yes'")
    for line in data:
        path = line[1]
        used = line[4]
        free = line[5]
        pct_used = (used / (used + free)) * 100
        if free < 100.5:
            drive_full = "[FULL]"
        else:
            drive_full = f"[{round(free/101.5)} Plots]"

        data=[[used,"RED","Used"],
              [free,"GREEN","Free"],
              [path.ljust(25) + drive_full,"percent","Yes"]]
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

