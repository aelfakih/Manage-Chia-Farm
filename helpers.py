import pathlib
import os
import re
import sys
import shutil
import yaml
from tqdm import tqdm, trange
import logging
from database import *
from PyInquirer import style_from_dict, Token, prompt, Separator
import sqlite3 as sql


def db_connect() :
    db = sql.connect ( 'db\chia-farm-stats.db' )
    return db

# cleanup the cli output to avoid confusion when cleaning space
def indent(symbol,string):
    tab = '    '
    space = ' '
    sentence = tab + symbol + space + string
    return(sentence)

# Python program to get average of a list
def Average(lst):
	return sum(lst) / len(lst)

""" For a given pathm find the mount points"""
def find_mount_point(path):
    path = os.path.abspath(path)
    while not os.path.ismount(path):
        path = os.path.dirname(path)
    return path


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
    import os
    import yaml
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Unable to find the config.yaml file. Expected location: {file_path}")
    f = open(file_path, 'r')
    config = yaml.load(stream=f, Loader=yaml.Loader)
    f.close()
    return config

#################### Helpers ####################

def get_mount_point(dir) :
    drive = pathlib.Path ( dir ).parts[0]
    return drive


"""
Check if the path we got is online. 
This case happens in windows where drives could get re-ordered
"""
def is_plot_online(plot):
    # importing os.path module
    import os.path

    # Check whether the
    # specified path is an
    # existing directory or not
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
    plots_to_import=[]
    import_action=[]
    drive_size={}
    total_size_gb= 0
    available_drives =[]
    free = 0
    used = 0
    action_keep = "Keep it"
    action_rename ="Keep and RENAME extension to 'IMPORTED'"
    action_delete ="Delete it"

    #available_drives = ['%s:' % d for d in string.ascii_uppercase if os.path.exists ( '%s:' % d )]
    for drive in ['%s:' % d for d in string.ascii_uppercase if os.path.exists ( '%s:' % d )]:
        total , used , free = shutil.disk_usage ( drive )
        # convert to GiB
        free = free // (2 ** 30)
        #print( "%s (%s) GiB Free" %  (drive,free) )
        available_drives.append("|%s| Free (%s) GiB" %  (drive,free))

    questions = [
        {
            'type' : 'list' ,
            'name' : 'from' ,
            'choices': available_drives,
            'message' : 'Which Drive to you want to import FROM?'

        }
    ]
    answers = prompt ( questions , style=style )
    pattern = "\|(.*?)\|"
    import_from = re.search ( pattern , answers['from'] ).group ( 1 )


    print("* Searching for .plot files in [%s] ..." % (import_from))

    """ Walk the drive looking for .plot files """
    for root , dirs , files in os.walk ( import_from ) :
        for file in files :
            if file.endswith ( ".plot" ) :
                filename = root + '\\' + file
                plots_to_import.append ( filename )
                size_gb = round ( os.path.getsize ( filename ) / (2 ** 30) , 2 )
                total_size_gb += size_gb
                print (">" , "%s (%s GiB)" % (filename , size_gb) )

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
                'type' : 'input' ,
                'name' : 'to' ,
                'message' : 'Which location you wanto to move plots TO?'

            }
        ]
        answers = prompt ( questions , style=style )
        import_to = answers['to']

        drive = pathlib.Path ( import_to ).parts[0]
        total , used , free = shutil.disk_usage ( drive )
        # convert to GiB
        free = free // (2 ** 30)
        used = used // (2 ** 30)
        total_size_gb = round(total_size_gb,0)

    if free < total_size_gb:
        print ("** NOTICE! Some plots will be left behind due to free space available at destination.  (Plots %s GiB, Destination: %s GiB free)" % (total_size_gb, free))
        print ("* You can move the remaining plots to a different destination later by re-runinng this utility. ")

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
    #input_file = 'Q:\\plot-k32-2021-06-22-17-26-8713aa7b1b639ef1b071e1dde2efd86ef12bc592c66f70f9d5c7683a140f3ab6.plot'
    dest = destination_folder + '\\' + basename + '.tmp'
    f_size = os.stat ( src ).st_size
    buff = 10485760  # 1024**2 * 10 = 10M

    disk_label = pathlib.Path ( destination_folder ).parts[0]
    dest_total , dest_used , dest_free = shutil.disk_usage ( disk_label )

    if dest_free < f_size:
        logging.info ("* Skipping: not enough space available on %s " % (disk_label))
        print("* Skipped not enough space at destination")
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


                print ( f'Done! Copied {f_size} bytes.' )


def get_plots_in_list( list ) :
    # find files that have .plot extension
    p = re.compile ( ".*\.plot$" )
    plot_list = list ( filter ( p.match , list ) )
    return plot_list

def bytes_to_gib(number) :
    number = number // (2 ** 30)
    return number

def do_scan_farm():
    from tqdm import tqdm , trange
    chia_farm = []
    plot_sizes =[]
    ignore_these = ["$RECYCLE.BIN","System Volume Information"]
    db = db_connect ( )
    c = db.cursor ( )

    print ( "Scanning Chia farm..." )
    plot_dirs = get_plot_directories ( )

    if is_verbose() :
        logging.info ( "Scanning Chia farm..." )

    for dir in plot_dirs :
        print ( "* Checking plot directory %s: " % (dir), end="" )

        if os.path.isdir(dir):
            mount_point = find_mount_point(dir)
            mount_total , mount_used , mount_free = shutil.disk_usage ( drive )
            mount_total = bytes_to_gib(mount_total)
            mount_used = bytes_to_gib(mount_used)
            mount_free = bytes_to_gib(mount_free)
            print(" Directory: Valid |",end="")
            SQLQ = "REPLACE INTO plot_directory (path, drive, drive_size, drive_used, drive_free, valid) values ('%s','%s','%s','%s','%s','%s')" % (dir , mount_point , mount_total, mount_used,mount_free, "Yes")
            c.execute ( SQLQ )
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
                        if plot not in ignore_these :
                            c.execute ( "SELECT id FROM plots WHERE name = '%s' and path='%s'" % (plot,dir) )
                            data = c.fetchall ( )
                            if len ( data ) == 0 :
                                filename = dir + '\\' + plot
                                plot_size = round ( os.path.getsize ( filename ) / (2 ** 30) , 2 )
                                logging.info ( "Checking %s:" % (plot) )
                                logging.info ( " Size: %s |" % (plot_size) )

                                import subprocess
                                found = "Found 1 valid plots"
                                is_og = "Pool public key: None"
                                output = []
                                chia_binary = get_config ( 'config.yaml' ).get ( 'chia_binary' )
                                if os.path.exists ( chia_binary ) :
                                    output = subprocess.getoutput ( '%s plots check -g %s' % (chia_binary , plot) )
                                    if found in output :
                                        logging.info ( "Plot Valid: Yes" )
                                        valid = "Yes"
                                    else :
                                        logging.info ( " Plot Valid: No" )
                                        valid = "No"

                                    if is_og in output :
                                        logging.info ( " Plot Type: NFT" )
                                        type = "NFT"
                                    else :
                                        logging.info ( " Plot Type: OG" )
                                        type = "OG"

                                    SQLQ = "REPLACE INTO plots (name, path, drive, size, type, valid) values ('%s','%s','%s','%s','%s','%s')" % (
                                        plot , dir , mount_point , plot_size , type , valid)
                                    c.execute ( SQLQ )

                                else :
                                    logging.error ( "Chia binary was not found, please check config.yaml setting **" )

                            else :
                                logging.info ( "Plot %s has been previously scanned!" % (plot) )
                        # Commit your changes in the database
                        db.commit ( )
        else:
            ## TO DO , ask if you want to fix chia config file
            print ( " Directory: In-Valid |" , end="" )
            logging.error("! %s, which is listed in chia's config.yaml file is not a valid directory" % (dir))
            SQLQ = "REPLACE INTO plot_directory (path, drive, drive_size, drive_used, drive_free, valid) values ('%s','%s','%s','%s','%s','%s')" % (dir , mount_point , 0, 0,0, "No")
            c.execute ( SQLQ )

    # Commit your changes in the database
    db.commit ( )
    # Closing the connection
    db.close ( )