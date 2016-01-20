.. _getting_started:

******************
Getting Started
******************

DatViewer is easy to use. If you want to plot data, go to *File* menu and select *Open H5 File*
to load data file. Then go to *New* menu to create a new Time Series Plot window, which is the main playground of the dataset. 
Please read the task list below for instructions on specific task:

**Task Groups**

* :ref:`general_plotting`

* :ref:`date_time`

* :ref:`file_operation`

.. _general_plotting:

General Data Plotting
===========================

Plot one variable versus another
----------------------------------------
This is called *Correlation Plot* in DatViewer. In the Time Series Plot window, go to *Analysis* menu
and select *Correlation Plot*. A dialog will pop up asking you to specify the x and y variables for the 
plot. After that your desired plot will be shown in a separate XY Plot window.

The XY Plot window provides some useful tools for analyzing the data, such as linear fitting and polynomial fitting.
See :ref:`correlation_plot` for details.

Plot difference of two variables (or other transformations on dataset)
--------------------------------------------------------------------------
Assume that you have two columns "CH4" and "CO2" and you would like to plot the difference of these two variables.
To do so, make sure that the data file is loaded and the correct dataset is selected in the Time Series Plot window.
Then simply enter formula ``CH4 - CO2`` into the :ref:`expression` field, and difference of CH4 and CO2 will be plotted in the corresponding canvas. 
Basically you can use all variables in the selected dataset by typing the variable name. 
You can even use mathematical functions such as *exp*, *sin*, and *abs* in your formula.
The :ref:`expression` field supports python scripting for data process and analysis. 

Plot variables in certain conditions (filtering)
-----------------------------------------------------
Use the :ref:`filter` field to remove unwanted data points or select data in certain conditions. 
For example, your dataset has a column called "CH4" and you would like to get a plot for CH4 concentration lower than 10.
To this end, simply enter formula ``CH4 < 10`` into the :ref:`filter` field. You can filter data based on a combination of criteria. 
For example, to see a plot for ValveMask equal to 2 and CH4 concentration lower than 10, enter formula ``(CH4 < 10) & (ValveMask == 2)``.

Display data point without connecting lines (or customizing other features of figure)
---------------------------------------------------------------------------------------------
Right click on the plot canvas and select :ref:`image_editor` in the pop-up menu. This will open up a dialog for customizing the figure.
Many figure features can be changed in this dialog, for example, marker, line pattern, title, range of x- and y-axes, etc. 

.. _date_time:

Date and Time
==========================

Change time zone
----------------------
By default, your local time zone is used for all plots. However, you can change time zone by
right clicking on the plot canvas and then selecting :ref:`image_editor` in the pop-up menu. 
In the *Image Editor* dialog, choose your desired time zone from the drop-down list. 


Display x-axis as elapsed time since the starting point of dataset (or any time point)
---------------------------------------------------------------------------------------
In the Time Series Plot window, go to *View* menu and then select *x-Axis in Minute*. 
This will change the x-axis data to elapsed minutes since the earliest point in the plot, 
so the x axis in the new plot starts from 0. Likewise, selecting *x-Axis in Hour* will change the x-axis data to 
elapsed hours since the earliest point in the plot. To display x-axis as elapsed time since a specific time, 
right click on the plot canvas and select :ref:`image_editor`. Then specify the desired time origin 
in the *Min* field of *x-Axis*. If you would like to use the starting point of dataset as the time origin,
click button *x[0]* next to the *Min* field, which automatically enter the earliest time of dataset into *Min*.

.. _file_operation:

File Concatenation and Format Conversion
==========================================

.. _concatenate_files_timerange:

Concatenate data files in a specific time range
-------------------------------------------------------
Go to :ref:`file_menu` and click *Concatenate H5 Files*. After selecting the target folder, a *Select Variables* dialog will open up. 
Then click button *Define date range* to specify time range for file concatenation. Be caution on the following things about time range:

#.  Picarro data file is named with the creation time, and DatViewer uses file name to determine whether or not the data file is within the 
    specified time range. If the file name has ever been changed, don't use specify time range. Instead, try concatenating all files first and then 
    use method in the item below to save data in specific time range.

#.  DatViewer does NOT concatenate data files exactly within the specified time range. Usually, the resulting dataset 
    has a wider time range than the user specification. To accurately define the time range, load the concatenated dataset in DatViewer
    and make a time series plot for any variable. Then open right-key menu in canvas and select :ref:`image_editor`. Define time range for x-axis in 
    the *Image Editor* dialog. After that, open right-key menu in canvas again and select *Export All Data in Current Time Range*. 
    This will save all data exactly within the specified time range into a file.
    
.. seealso::  :ref:`define_time_range`

.. _huge_files:

Concatenate huge volume of data files
----------------------------------------------------------
If you would like to concatenate data files of several hundreds of MB or even larger, tick *Large dataset* checkbox in the *Select Variables* dialog.
For normal file concatenation, DatViewer loads data into memory and sort dataset with time before writing into a file. This can easily 
cause memory error if large volume of data files are concatenated. By selecting the *Large dataset* option, DatViewer writes data directly into hard disk so as to 
save memory space. This way DatViewer can handle very large dataset without causing memory error. 

However, since data is written directly into hard disk without sorting, the resulting dataset may not be in chronological order.
To make sure the correct chronological order of dataset, data files need to be saved in directory trees named by date and time, and data files need
to be named with creation time (just like data files in Private Log). This way DatViewer can write files to hard disk in the correct chronological order.