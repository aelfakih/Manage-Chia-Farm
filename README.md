# Manage-Chia-Farm
## Features

This program helps chia farmers manage the thousands of plots within their farm, and supports the following
features:
  * **Menu-driven design**, allows farmer to navigate through available options and minimize errors due to
    manual data entry.
    
    ![Main Menu](https://github.com/aelfakih/Manage-Chia-Farm/blob/master/captures/main_menu.png?raw=true)
    

  * **Show Available Space**: This function scans the database and reports the available number of plots
    that can be stored in the plot directory (assumes k32 plot size 101.5 GiB.
    
    ![Main Menu](https://github.com/aelfakih/Manage-Chia-Farm/blob/master/captures/show_available_space.png?raw=true)

  * **Show Used Space**: This function scans the database and reports how the space is being used. It lists all the
    mount points and show total size, how much it is used and free reported in GiB.
    
    ![Main Menu](https://github.com/aelfakih/Manage-Chia-Farm/blob/master/captures/show_used_space.png?raw=true)
    

  * **Resolve Issues Found**: This scans the data found during the *Verify Plot Directories and Plots* and
  give farmer the option to fix chia configuration file, and remove invalid plots.  (By default this option is
  not visible in menu option, until an issue is detected after a farm/plots scan)
  * **Find non-plots**: Search in each of the farm folders, look for files that do not end with *.plot* 
  extension and prompt manager to delete the files to clear space.
  * **Find duplicate plots**: Search the farm for duplicate file names and prompt manager to delete duplicates 
  and maintain one copy to clear up space (it has logic to remove duplicates with minimal impact on 
  compactness of farm).
  * **Verify Plot Directories and Plots** This is an **exhaustive and slow process** to test and verify all the 
    plots in the farm and learn about your farm to make management easier for larger farms.  Data collected is 
    saved in a sqlite db called chia-farm-stats.db which is stored locally. The program:
    * Checks that **directory plots are online** so that farmer can take action.
    * **Verifies plots are valid** for the installed chia instance.
    * **Classifies the plots as NFT or OG**.
    * Saves location and size  
  * **Move plots**: Allows farmer to select source location from list and search for plots to move.  It also helps 
    farmer in understanding how much available at destination.
    This function allows the consolidation of plots into a location as you upgrade your drives or 
    move plots from plotters to farm.  Source files can be:
    * Kept at source location.
    * Renamed (have an .imported extenstion)
    *  or deleted.
    NOTE that if you ctrl-C out of manage-chia-farm while executing a move plot command, it will apply the selected 
    action on source file -- if you do not want to lose any plots, always use the *imported* option then manually 
    delete the source files)    

> Script was tested with python 3.9 on Windows 10 

## Supported Volume mounts

manage-chia-farm can detect these types of drive mounts and return space statistics:
* **Letter mounted drives** (i.e. D:\, E:\)
* **Folder mounted drives**  In windows you can mount iscsi and usb drives as directories such
  as *c:\mnt\drive1* this allows the user not be limited to D-Z drive naming.
* **Network drives** (i.e. //server/mount_point)  NAS mounted drives (NFS, Samba, etc..) can be recognized 
  an scanned for plots.

![Three mount styles](https://github.com/aelfakih/Manage-Chia-Farm/blob/master/captures/drive_mount_styles.png?raw=true)


# Upgrading from previous versions

If you installed the project as described below, you can get the latest code changes by 
executing the following command in the Manage-Chia-Farm directory

`git pull origin master`


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
the config.yaml.  Copy the default config.yaml

`cd Manage-Chia-Farm`

`copy config.yaml.default config.yaml`

Open the configuration file and enter the path to chia's config.yaml 
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
## Import Plots into Farm
Running the Import plots option (also as stand alone ) you can move file created in madmax plotter into your 
farm by using this utility.  This is what the utility does:
1. After you select the DRIVE to import from, the program looks for .plot files and displays them as a confirmation
1. If you agree to move them, it asks for destination and asks you if you want to delete the source files 
   after copying or mark them as imported
1. Based on your preferences, it will then copy the file from source to destination location 
   (while adding a .tmp extension) so that chia does not try to open it.
1. When it is done copying, it will remove the .tmp file and (delete or rename source)

In the following example you can see that I was importing the plots from **J: drive**, which were
freshly plotted with madmax, into the farm to folder **e:\AquaBird** .  I elected to keep the source 
files as .imported (which I manually deleted after the import completed) 

![Import Plots into Farm](https://github.com/aelfakih/Manage-Chia-Farm/blob/master/captures/move_plots.png?raw=true)

## Verify Plot Directories and Plots
 
This option take a long time to run since it will execute the chia client to verify the validity of the plot.
The data from the scan is stored in a local sqlite database called **chia-farm-stats.db** and you can browse it
using any sqlite capable application. Try (https://sqlitebrowser.org/)

![Verify Plot Directories and Plots](https://github.com/aelfakih/Manage-Chia-Farm/blob/master/captures/verify_plot_directories_and_plots.png?raw=true)

The database will be used in future updates to quickly find information about any plot in your farm and improve
the overall speed of managing a large chia farm.


# How to Support

If you enjoy this program and want to part with some Mojos, feel free to send it to 

XCH: xch12gp5cmdwlrpdpvza8ttvjeu5ml76ytn7v94ujwzpwwvff6n6h3lsgxn65h

