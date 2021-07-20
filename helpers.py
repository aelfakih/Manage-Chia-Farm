import subprocess
import pathlib
import os
import re
import sys
import shutil
import yaml
from tqdm import tqdm, trange
import logging
from PyInquirer import style_from_dict, Token, prompt, Separator


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
        free = bytes_to_gib(free)
        used = bytes_to_gib(used)
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
    from database import get_results_from_database
    plots_to_import=[]
    import_action=[]
    drive_size={}
    total_size_gb= 0
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
                    filename = root + '\\' + file
                    plots_to_import.append ( filename )
                    size_gb = bytes_to_gib ( os.path.getsize ( filename ))
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
                return

            if import_to == "Cancel":
                return

            drive = pathlib.Path ( import_to ).parts[0]
            total , used , free = shutil.disk_usage ( drive )
            # convert to GiB
            free = bytes_to_gib(free)
            used = bytes_to_gib(used)
            total_size_gb = round(total_size_gb,0)

        if free < total_size_gb:
            print ("** NOTICE! Some plots will be left behind due to free space available at destination.  (Plots %s GiB, Destination: %s GiB free)" % (total_size_gb, free))
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

    chia_farm = []
    plot_sizes =[]
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
                            #data = get_results_from_database ( "SELECT id FROM plots WHERE name = '%s' and path='%s'" % (plot,dir) )
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
                                is_og = "Pool public key: None"
                                output = []
                                chia_binary = get_chia_binary ( )
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

                                    do_changes_to_database("REPLACE INTO plots (name, path, drive, size, type, valid, scan_ukey) values ('%s','%s','%s','%s','%s','%s','%s')" % (
                                        plot , dir , mount_point , plot_size , type , valid,session_id))

                                else :
                                    logging.error ( "Chia binary was not found, please check config.yaml setting **" )

                            else :
                                logging.info ( "Plot %s has been previously scanned!" % (plot) )
                                if not indirectory:
                                    do_changes_to_database (
                                        "REPLACE INTO plots (name, path, drive, scan_ukey) values ('%s','%s','%s','%s')" % (
                                            plot , dir , mount_point , session_id) )
                                    print(f"* Not in directory {plot} {dir} {mount_point}")


                        # Commit your changes in the database
                        #db.commit ( )
        else:
            ## TO DO , ask if you want to fix chia config file
            print ( " Directory: In-Valid |" , end="" )
            logging.error("! %s, which is listed in chia's config.yaml file is not a valid directory" % (dir))
            do_changes_to_database("REPLACE INTO plot_directory (path, drive, drive_size, drive_used, drive_free, valid,scan_ukey) values ('%s','%s','%s','%s','%s','%s','%s')" % (dir , "" , 0, 0,0, "No",session_id))

    # Commit your changes in the database
    #db.commit ( )
    # Closing the connection
    #db.close ( )


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

    """ Check fir invalid plots"""
    data = get_results_from_database("SELECT * FROM plots WHERE valid = 'No'")
    invalid_plots =0
    if len ( data ) > 0 :
        for line in data:
            path = line[2]
            file = line[1]
            filename = path + file
            if os.path.isfile(filename):
                invalid_plots += 1
            else:
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
                filename = path + file
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

    """ Check for invalid plots"""
    data = get_results_from_database("SELECT count(*), type FROM plots WHERE valid = 'Yes' GROUP BY type")
    for line in data:
        if line[1] == 'NFT':
            nft = line[0]
        else:
            og = line[0]

    #print (data, nft, og)

    from termgraph import termgraph as tg
    from collections import defaultdict
    C = tg.AVAILABLE_COLORS

    if (nft == 0) and (og == 0):
        print("* Please run the 'Verify Plot Directories and Plots' to scan the farm for NFTs, OGs and Validate plots...")
    else:
        nft_pct = (nft/(nft+og)) * 100
        og_pct = (og/(nft+og)) * 100

        tg.chart (
            colors=[C["green"] , C["yellow"]] ,
            data=[[nft , og]] ,
            args=defaultdict (
                bool ,
                {
                    "stacked" : True ,
                    "custom_tick": u"\u2588",
                    "width" : 40 ,
                    "format" : "{:<5.2f}" ,
                    "no_labels" : True ,
                    "suffix" : f" (NFT:{nft} ({nft_pct:.0f}%), OG:{og} ({og_pct:.0f}%))"
                } ,
            ) ,
            labels=[""] ,
        )


def do_show_farm_capacity():
    from termgraph import termgraph as tg
    from collections import defaultdict
    from database import get_results_from_database
    color = tg.AVAILABLE_COLORS
    labels=[]
    used=[]
    free=[]

    print("* Farm capacity in (plots)")
    """ Check for invalid plots"""
    data = get_results_from_database("SELECT * FROM plot_directory WHERE valid = 'Yes'")
    if data:
        for line in data:
            path = line[1]

            # if the free space is greater than an average k32 (101.5 GiB) plot then show availability
            if line[5] > 101.5:
                free.append(round(line[5]/101.5))
                used.append(line[4])
                labels.append(path.ljust(25))


        #print(labels,free)
        colors = [color["green"]]
        suffix ="available plot space(s)"
        tprint ( False, labels , free , colors, suffix, format="{:<5.0f}" )
    else:
        print ("* Please run the 'Verify Plot Directories and Plots' to scan the farm for NFTs, OGs and Validate plots..." )


def do_show_farm_usage():
    from termgraph import termgraph as tg
    from collections import defaultdict
    from database import get_results_from_database
    color = tg.AVAILABLE_COLORS

    print("* Farm capacity in (plots)")
    """ Check for invalid plots"""
    data = get_results_from_database("SELECT * FROM plot_directory WHERE valid = 'Yes'")
    for line in data:
        path = line[1]
        used = line[4]
        free = line[5]


        tg.chart (
            colors=[color["magenta"] , color["green"]] ,
            data=[[used , free]] ,
            args=defaultdict (
                bool ,
                {
                    "stacked" : True ,
                    "custom_tick" : u"\u2588" ,
                    "width" : 60 ,
                    "format" : "{:.0f}" ,
                    "no_labels" : False ,
                    "suffix" : f" GiB Total | Used {used:.1f} GiB | Free {free:.1f} GiB"
                } ,
            ) ,
            labels=[path.ljust(25)] ,
        )


#    print(labels,used)
#    colors = [color["magenta"],color["yellow"]]
#    suffix =" GiB used"
#    tprint ( True, labels , used , colors, suffix, format="{:<3.2f}" )


def tprint(stacked,labels, values, colors, suffix, **kwargs):
    from termgraph.termgraph import chart

    args = {
        "stacked": stacked,
        "width": 60,
        "no_labels": False,
        "custom_tick" : u"\u2588" ,
        "format": "{:<6.2f}",
        "suffix": suffix,
        "vertical": False,
        "histogram": False,
        "no_values": False,
    }
    args.update(kwargs)
    data = [[x] for x in values]
    chart(colors=colors, data=data, args=args, labels=labels)


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
