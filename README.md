# Manage-Chia-Farm
This program helps chia farmers manage the thousands of plots within their farm and helps in the following three areas:
  * Scans farm for non-plot files and allows you to delete them 
  * Scan the farm for duplicates and allows you to easily keep one version and clear up space.
  * (Coming up later) Move plots within farm to maximize space usage and clear up space to add more plots

> Script was tested with python 3.9 on Windows 10 

# Usage
1. Open main.py and edit the *plot_dirs* variable to include a list of the plot
directories you want to manage.  Once you have finish making your changes, you are ready to scan your farm..
 
1. run **python main.py**


# Example output
> MaximizeChiaSpace | checks that plots are not duplicated, cleans junk files and reorganizes plots to maximize farming space
by Adonis Elfakih 2021, https://github.com/aelfakih
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