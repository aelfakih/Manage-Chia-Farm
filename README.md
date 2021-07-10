# Manage-Chia-Farm
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


# Installation

Pre-requisites 
* Python 3.9+
* Git

Open a terminal in windows and download the utility from Github.com 

`git clone https://github.com/aelfakih/Manage-Chia-Farm`

Change directory into Manage-Chia-Farm

`cd Manage-Chia-Farm`

Load required libraries using the following command

`pip install -r .\requirements.txt`

# Configuration

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


# Usage
To run this program, execute the following command

`python manage-chia-farm.py`


# Example output
> Manage-Chia-Farm | checks that plots are not duplicated, cleans junk files and reorganizes plots to maximize farming space
by Adonis Elfakih 2021, https://github.com/aelfakih/Manage-Chia-Farm
>
>* Scanning farm ... Found  447 plots listed!
>* [1/3] Checking for plots that don't have a '.plot' extension ... [OK]
>* [2/3] Checking for duplicate plot filenames ... [OK]
>* [3/3] Checking for space in farms to maximize space usage (TBD) ...
>    * Using Average plot size of 101.36 GiB to fit plots in available farm space
>    * Skipping E:\ not enough space for plots
>    * [TBD] D:\ has 1460 GiB free space, good enough for 14 plot(s)
>    * Skipping F:\ not enough space for plots
>    * Skipping G:\ not enough space for plots
>    * [TBD] H:\ has 154 GiB free space, good enough for 2 plot(s)
>    * [TBD] I:\ has 255 GiB free space, good enough for 3 plot(s)
>    * Skipping J:\ not enough space for plots
>    * Skipping L:\ not enough space for plots
>    * [TBD] K:\ has 120 GiB free space, good enough for 1 plot(s)
>    * Skipping M:\ not enough space for plots
>    * Skipping P:\ not enough space for plots
>    * [TBD] O:\ has 120 GiB free space, good enough for 1 plot(s)
>    * Skipping N:\ not enough space for plots
>    * [TBD] Q:\ has 6126 GiB free space, good enough for 60 plot(s)
>    * [TBD] R:\ has 221 GiB free space, good enough for 2 plot(s)

# How to Support
XCH: xch13px92qjn4c8kzcdn8k02cvwpe6l97py3vzst8m3h2qnz7wxewmrscxck5d

# Common Issues

* When starting the utility you get errors about path not found

> FileNotFoundError: [WinError 3] The system cannot find the path specified: 'D:\\chia'

This occurs when there are invalid
