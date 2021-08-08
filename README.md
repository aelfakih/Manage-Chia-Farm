# Manage-Chia-Farm
### Manage your Chia farm like a Pro! 
> **NOTE:** Manage-Chia-Farm(MCF) was developed and tested with Python 3.9 on Windows 10 


![Main Menu](https://github.com/aelfakih/Manage-Chia-Farm/blob/master/captures/mcf-demo.gif?raw=true)

# Why Manage-Chia-Farm?

While chia provides farmers with the ability to validate plots and to detect duplicates, the GUI only provides 
an error message and does allow farmers ways to remedy the issues, or to intelligently decide which is the
best option to take, so that the farm maximizes its compactness.  MCF aims to bridge that gap by providing the
tools to analyze what plots are valid, invalid, which files are sitting in the plot directories eating up space
that can be deleted.  Give farmers the flexibility to exclude which file extensions to ignore from the analysis.

When Chia started, many farmers started creating plots that were commonly referred to as 
Old-Gangster (OG)s plots, which were used for Solo farming, those were upgraded to NFT plots as 
of Version 1.2.0 and could be used for Pool farming.  As of version 1.4 of MCF farmers can point the
application at a source location, and it would then import the incoming plots over existing OGs
one-file-at-a-time.

MCF is designed to run in the terminal on purpose, to make it more interoperable and to require less
dependencies.  I hope you enjoy using it, and feel free to reach out if you encounter a bug that you would
like me to look at.

-- Adonis

# 1. Features

Manage-Chia-Farm (MCF) is a **menu-driven-program**, which allows farmers to move, migrate, overwrite, verify and
manage OG and NFT plots with a chia farm.  It speeds up the process of managing a farm and minimizes errors 
due to manual data entry.

MCF is designed to handle the management of thousands of plots in chia farms and supports the following features:

![Main Menu](https://github.com/aelfakih/Manage-Chia-Farm/blob/master/captures/main_menu.png?raw=true)

## 1.1 Farm Management
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
  * **Overwrite OG Plots**: Allow farmers to automatically overwrite OGs when importing NFTs into farm 
    without having to search for them or move them aroundm.  This is an important feature for farmers 
    that have OG plots and are migrating into an all NFT plot configuration.
 * **Resolve Issues Found**: This scans the data found during the *Verify Plot Directories and Plots* and
  give farmer the option to fix chia configuration file, and remove invalid plots.  (By default this option is
  not visible in menu option, until an issue is detected after a farm/plots scan)
## 1.2 Search
 * **Find non-plots**: Search in each of the farm folders, look for files that do not end with *.plot* 
  extension and prompt manager to delete the files to clear space.
  * **Find duplicate plots**: Search the farm for duplicate file names and prompt manager to delete duplicates 
  and maintain one copy to clear up space (it has logic to remove duplicates with minimal impact on 
  compactness of farm).

## 1.3 Reporting
  * **Show Available Space**: This function scans the database and reports the available number of plots
    that can be stored in mounted plot directories (assumes k32 plot size 101.5 GiB)
    
  * **Show Farm bar Graph Usage**: This function scans the database and reports how the space is being used. 
    It lists all the mount points and shows total size, how much it is used and free reported size in GiB.
    
![Show Available Space](https://github.com/aelfakih/Manage-Chia-Farm/blob/master/captures/show_available_space.png?raw=true)

![Show Used Space](https://github.com/aelfakih/Manage-Chia-Farm/blob/master/captures/show_used_space.png?raw=true)

## 1.4 Multiple Volume Mount Support

MCF detects these types of drive mounts and returns space statistics:
* **Letter mounted drives** (i.e. D:\, E:\)
* **Folder mounted drives**  In windows you can mount iscsi and usb drives as directories such
  as *c:\mnt\drive1* this allows the user not be limited to D-Z drive naming.
* **Network drives** (i.e. //server/mount_point)  NAS mounted drives (NFS, Samba, etc..) can be recognized 
  an scanned for plots.

![Three mount styles](https://github.com/aelfakih/Manage-Chia-Farm/blob/master/captures/drive_mount_styles.png?raw=true)


# 2. Installation (Git)

Pre-requisites 
* Python 3.9+
* Git

Open a terminal in windows and download the utility from Github.com 

`git clone https://github.com/aelfakih/Manage-Chia-Farm`

Change directory into Manage-Chia-Farm

`cd Manage-Chia-Farm`

Load required libraries using the following command

`pip install -r .\requirements.txt`

## 2.1 Upgrading from previous versions (Git)

If you installed the project as described below, you can get the latest code changes by 
executing the following command in the Manage-Chia-Farm directory

`git pull origin master`

# 3. Configuration

Before being able to start using the utility, we need to configure it by editing 
the config.yaml.  Copy the default config.yaml

`cd Manage-Chia-Farm`

`copy config.yaml.default config.yaml`

Open the configuration file and enter the path to chia's config.yaml 
into the chia_config_file variable. (the next command is something that you might use. 
You can use your favorite editor)

`PS C:\Users\USERNAME\Manage-Chia-Farm> notepad.exe config.yaml`

### chia_config_file
Edit the chia_config_file variable. The format is usually something like 
this (change the USERNAME to match your path):

```buildoutcfg
# location of Chia's configuration file. It is used to navigate the plots directories
chia_config_file: C:\Users\USERNAME\.chia\mainnet\config\config.yaml
```
### chia_binary
Edit the chia_binary variable. The format is usually something like 
this (change the USERNAME and VERSION to match your path):

```buildoutcfg
# location of chia executable, used when importing plots to verify that they belong to this farm
chia_binary: C:\Users\USERNAME\AppData\Local\chia-blockchain\app-VERSION\resources\app.asar.unpacked\daemon\chia.exe
```
### verbose
You can control the amount of logging needed for your setup. To turn logging on, set *verbose* to True
to control the amount of reporting collected you can set *verbose_level* to ERROR, INFO or DEBUG, where 
ERROR shows the least amount of messages (ctitical to funcionality) and DEBUG shows the most, so you
can see what the application is doing and verify expected behaviour.

```buildoutcfg
# when verbose is true, the program ouputs extra information into log\audit.log
verbose: false
```

### verbose_level

```
# what level of logging do you want to show, by default it is ERROR
# Available options are ERROR, INFO, DEBUG
verbose_level: ERROR
```

### database_location  (Optional)

Store the SQLite database at a different location than the default ".\db\" 

```buildoutcfg
# Where do you want to store the database.  If not defined, it is stored in local directory "db"
# database_location: db
database_location: C:\path\to\database\
```

### ignore_extensions  (Optional)

Ignore specific file extensions when executing the **Find non-plots**, so that
you can keep files that you want to keep in farm.  Good examples are *.plot.tmp* files if running
MCF on a plotter machine and you do not want to accidentaly delete the .tmp files

```buildoutcfg
# Ignore the following file extensions when looking for non-plots for deletion
# NOTE! all extensions MUST start with a (.) dot. for example .txt , .plot.tmp
ignore_extensions:
 - .plot.tmp
```



# 4. Usage
To run this program, execute the following command

`python manage-chia-farm.py`


# Example Output
## Import Plots into Farm
![Import Plots into Farm](https://github.com/aelfakih/Manage-Chia-Farm/blob/master/captures/move_plots.png?raw=true)

## Verify Plot Directories and Plots
![Verify Plot Directories and Plots](https://github.com/aelfakih/Manage-Chia-Farm/blob/master/captures/verify_plot_directories_and_plots.png?raw=true)


# How to Support

If you enjoy this program and want to part with some Mojos, feel free to send it to 

XCH: xch12gp5cmdwlrpdpvza8ttvjeu5ml76ytn7v94ujwzpwwvff6n6h3lsgxn65h

# Windows 10 Tips and Tricks

## Labeling Drives

Avoid serializing your drives from 1 to N. Instead, encapsulate them inside the serialized number of the 
JBOD.  Consider you have 20 JBODs and each one holds 10 drives. Instead of labeling them 1-20, label them
BOX1-1..BOX11-10
..
BOX20-1..BOX20-20

This approach, makes it easier to connect what you see happening on MCF or other system error messages. 

## Mounting Drives 

While the first instincts is to mount drives using letters on Windows, you soon will run out of drive letters
and windows will from time to time switch the letter it assigns drives, which may affect farmers that use
subdirectory structures (another hint DO NOT use subdirectories yo do not need them).

So create a directory structure in the root directory (I use "/mnt") specifically designed to mount drives, and it 
would mirror the drive labels.

![Labeling an Mounting Drives](https://github.com/aelfakih/Manage-Chia-Farm/blob/master/captures/labeling_and_mounting.png?raw=true)

