﻿# Manage-Chia-Farm
This program helps chia farmers manage the thousands of plots within their farm and helps in the following areas:
  * Find and remove **non-plot files** --  In each of the farm folders, look for files that do not end with *.plot* 
    extension and bring that to the manager attention.  The manager is then prompted to delete all the offending 
    files to clear space for plots.
  * Find and remove  **duplicate plots** -- Search the farm for duplicate file names and report how many were found.  
    Manager is given the option to delete duplicates and maintain one copy to clear up space.
  * **Import plots** into farm -- This allows you to consolidate plots into new drives as you upgrade your drives or 
    move plots from plotters to farm.  This is one of my favorite utilities since it does the copying, renaming and 
    removing of files so that farming is not interrupted.   

> Script was tested with python 3.9 on Windows 10 


# 1. Installation

Pre-requisites 
* Python 3.9+
* Git

Open a terminal in windows and download the utility from Github.com 

`git clone https://github.com/aelfakih/Manage-Chia-Farm`

Change directory into Manage-Chia-Farm

`cd Manage-Chia-Farm`

Load required libraries using the following command

`pip install -r .\requirements.txt`

# 2. Configuration

Before being able to start using the utility, we need to configure it by editing 
the config.yaml.

Open the the utility configuraiton file and and enter the path to chia's config.yaml 
into the chia_config_file variable. (the next command is something that you might use. 
You can use your favorite editor)

`PS C:\Users\USERNAME\Manage-Chia-Farm> notepad.exe config.yaml`

Then edit the chia_config_file variable. The format is usually something like 
this (change the USERNAME to match your path):


```
# location of Chia's configuration file. It is used to navigate the plots directories
chia_config_file: C:\Users\USERNAME\.chia\mainnet\config\config.yaml
```


# 3. Usage
To run this program, execute the following command

`python manage-chia-farm.py`


# Example output

[[https://github.com/aelfakih/Manage-Chia-Farm/blob/master/captures/move_plots.png|alt=Moving Plots]]

# How to Support
XCH: xch13px92qjn4c8kzcdn8k02cvwpe6l97py3vzst8m3h2qnz7wxewmrscxck5d

# Common Issues

* When starting the utility you get errors about path not found

> FileNotFoundError: [WinError 3] The system cannot find the path specified: 'D:\\chia'

This occurs when there are invalid
