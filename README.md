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

Running the Import plots option (also as stand alone ) you can move file created in madmax plotter into your 
farm by using this utility.  This is what the utility does:
1. After you select the DRIVE to import from, the program looks for .plot files and displays them as a confirmation
1. If you agree to move them, it asks for destination and asks you if you want to delete the source files 
   after copying or mark them as imported
1. Based on your preferences, it will then copy the file from source to destination location 
   (while adding a .tmp extension) so that chia does not try to open it.
1. When it is done copying, it will remove the .tmp file and (delete or rename source)

![Moving Plots](https://github.com/aelfakih/Manage-Chia-Farm/blob/master/captures/move_plots.png?raw=true)

# How to Support

If you enjoy this program and want to part with some Mojos, feel free to send it to 

XCH: xch12gp5cmdwlrpdpvza8ttvjeu5ml76ytn7v94ujwzpwwvff6n6h3lsgxn65h

