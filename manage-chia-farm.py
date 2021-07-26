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

from helpers import *
from PyInquirer import style_from_dict, Token, prompt, Separator
import logging

log_filename = 'log\\audit.log'
logging.basicConfig(filename=log_filename,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(filename)s %(funcName)s %(lineno)d %(levelname)s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p',
                    level=get_verbose_level())


""" 
initialize some of the variables needed in the program. Please do not change 
"""
menu_find_non_plots = "Find non-Plots"
menu_find_duplicates = "Find Duplicate Plots"
menu_import_plots = "Move Plots"
menu_verify_plots_and_directories = "Verify Plot Directories and Plots"
menu_show_farm_capacity = "Show Available Plot Storage Space"
menu_show_farm_usage = "Show Farm Bar Graph Usage "
menu_resolve_issues = "Resolve Issues Found"
menu_watch_and_replace = "Watch For NFTs and Replace existing OGs"

dynamic_menu_resolve_issues = ""

if __name__ == '__main__':
    style = get_pyinquirer_style ( )

    """ Check if the config.yaml exists, otherwise exit"""
    if not os.path.exists ( "config.yaml" ) :
        print("Error: config.yaml file not found. Please copy config.yaml.default and customize to your installation")
        exit()

    """ Check if the chia binary is defined, otherwise exit"""
    chia_binary = get_config ( 'config.yaml' ).get ( 'chia_binary' )
    if not os.path.exists ( chia_binary ) :
        print("Error: %s (chia_binary) is not found. Edit config.yaml" % (chia_binary))
        exit()




    """ Setup the screen """
    print_top_menu()
    if is_verbose():
        logging.info("Program: Started")

    initialize_me ( )


    loop=True
    while loop:

        do_show_farm_distribution()

        """ add menu options when errors are found """
        issues_found = do_check_for_issues ( )
        if issues_found > 0 :
            dynamic_menu_resolve_issues = "%s (%s)" % (menu_resolve_issues,issues_found)
            menu_options = [
                            Separator ("___________________ Issues _____________________\n") ,
                            dynamic_menu_resolve_issues ,
                            Separator ("__________ Farm Management (Live Scan) __________\n" ) ,
                            menu_verify_plots_and_directories ,
                            menu_watch_and_replace,
                            menu_import_plots ,
                            Separator ( "______________ Search (Live Scan) _____________\n"  ) ,
                            menu_find_non_plots ,
                            menu_find_duplicates ,
                            Separator ( "____________ Reporting (Database)_____________\n"  ) ,
                            menu_show_farm_capacity,
                            menu_show_farm_usage,
                            Separator ("________________________________________________\n" ) ,
                            "Done"
                            ]
        else :
            menu_options = [
                            Separator ("__________ Farm Management (Live Scan) __________\n" ) ,
                            menu_verify_plots_and_directories ,
                            menu_watch_and_replace,
                            menu_import_plots ,
                            Separator ("______________ Search (Live Scan) _____________\n" ) ,
                            menu_find_non_plots ,
                            menu_find_duplicates ,
                            Separator ( "____________ Reporting (Database)_____________\n"  ) ,
                            menu_show_farm_capacity,
                            menu_show_farm_usage ,
                            Separator ("________________________________________________\n" ) ,
                            "Done"
                            ]

        questions = [
            {
                'type' : 'list' ,
                'name' : 'do' ,
                'message' : 'Select an action' ,
                'choices' : menu_options ,

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
        elif answers['do'] == menu_verify_plots_and_directories:
            start_new_session()
            do_scan_farm()
        elif answers['do'] == dynamic_menu_resolve_issues:
            do_resolve_issues()
        elif answers['do'] == menu_show_farm_capacity:
            do_show_farm_capacity ( )
        elif answers['do'] == menu_show_farm_usage:
            do_show_farm_usage ( )
        elif answers['do'] == menu_watch_and_replace:
            do_watch_and_replace()
        elif answers['do'] == "Done":
            loop = False
            print("* Goodbye!")
            if is_verbose():
                logging.info("Program: Exit")

