.. _user_guide:

***************
User's Guide
***************

.. figure:: _static/main_menu.jpg
    
**Main menu of DatViewer**

* :ref:`file_menu`

* :ref:`time_series_plot`

* :ref:`correlation_plot`

.. _file_menu: 
  
File Menu
============================

Open H5
---------------
Open a Picarro data file (HDF5 format) for data analysis and visualization. After opening the data file, you may create new :ref:`time_series_plot`.

Load Config
---------------
Load a configuration file (ini format) to restore parameters of workplace. See :ref:`save_configuration` for details.

Unpack Zip File
----------------

Unpack zip file and concatenate all H5 files inside into a single H5 file. See :ref:`concatenate_file` for details.

.. _concatenate_file:

Concatenate H5 Files
---------------------

Concatenate H5 files and zip archives of H5 files into into a single H5 file. 
After selecting path of data files, DatViewer will automatically search a H5 file in the zip/folder
and look for all available variables in the H5 file. All these available variables are listed in the left panel, 
and users can use ">>" button to put variables to the right panel for concatenation.

.. image:: _static/save_variables.jpg

**Large dataset**: see :ref:`huge_files`.

**See also:**

.. toctree::
   :maxdepth: 1
   
   define_time_range.rst

.. _DAT_H5:

Convert DAT to H5
-----------------------
Convert data file from DAT to HDF5 format. Details about these two formats are described below:

**DAT format:**
DAT files accepted by DatViewer store tabular data (numbers and text) in plain text.
 
* Each line of the file is a data record. Each record consists of one or more fields, separated by whitespaces. 

* The first line of data file indicates column names.

* There must be a field "EPOCH_TIME" storing acquisition epoch time (expressed as seconds since Jan 1, 1970) of the data. Otherwise the first and
  second fields must be "DATE" and "TIME". The "DATE" field must have the format "mm/dd/yyyy" or "yyyy-mm-dd", 
  and the "TIME" field must have the format "HH:MM:SS(.sss)" where (.sss) means optional fraction of seconds.

**HDF5 format:**
HDF5 is a data model, library, and file format for storing and managing data. Please visit `The HDF5 Home Page <https://www.hdfgroup.org/HDF5/>`_
When converting DAT to HDF5 format, DatViewer creates a table named "results" to contain data. 

Convert H5 to DAT
-----------------------
Convert data file from HDF5 to DAT format. See :ref:`DAT_H5` for details about these two formats.

.. note:: When converting H5 to DAT format, each column has a fixed width of 26 characters. So if column headings are too long (more than 25 chars),
          DatViewer will convert or truncate them. For example, column name "fineLaserCurrent_1_controlOn" will be replaced by "fineLaserCurr_1_ctrlOn".

.. _time_series_plot:

Time Series Plot
============================

.. image:: _static/time_series_plot.jpg

**See also:**

.. toctree::
   :maxdepth: 1
   
   time_series_plot_menu.rst
   canvas.rst

Data set name and Var name
------------------------------------
A HDF5 file can store one or more tables. Each of these table is called a **Data set**.
A table can contain one or more columns. Each column is called a variable (**Var**).

.. _Expression:

Expression
-----------------------

*Expression* is a mathematical function that applies on the selected data and transforms the plot. 
Here is an example of expression::

  y + CO2

Here *y* is the data of selected variable (y-axis data of the plot) and *CO2* is the data of CO2 column in selected table.
So this expression transforms the plot to be summation of selected variable and CO2 data.

.. note:: All variables in the selected dataset can be used in the *Expression* field. 
          Besides, *x* and *y* are defined as short-cuts for x-axis and y-axis data of the plot, correspondingly.
          
.. note:: *Expression* field is applied after :ref:`Filter` but before :ref:`Average`.
          
Autoscale Y
-----------------------
When this option is selected, DatViewer will autoscale on *y* axis to make sure all data within the range of *x* axis
is displayed.

.. _Average:

Average
----------------------------
When *Do average* button is clicked, moving average is calculated on the data with subset size specified in the field *N average*.

.. note:: Averaging is performed after application of :ref:`Filter` and :ref:`Expression` fields.

Mean, Std dev, and Peak to peak
------------------------------------
Mean, Std dev (Standard deviation) and peak to peak are all statistical information of data in the current view. 

.. _Filter:

Filter
----------------------

*Filter* is a mathematical expression that specifies data to include or exclude from plot(s). 
Here is an example of filter::

  (CH4 < 5) & (CO2 < 10)

where CH4 and CO2 are both variable names in the selected data set. 
So this filter removes all rows with CH4 >= 5 or CO2 >= 10 from dataset.

.. note:: All variables in the selected dataset can be used in the *Filter* field. 

.. note:: *Filter* field is applied before :ref:`Expression` field.

Available logical operators in the *Filter* field:  ``&`` (AND), ``|`` (OR), ``~`` (NOT) and ``^`` (XOR). 

.. _correlation_plot:

Correlation/XY Plot
============================

.. image:: _static/correlation_plot.jpg

.. seealso::  * For details about plot canvas, see :ref:`plotting_canvas`

              * For details about *File* menu, see :ref:`save_configuration`

.. _analysis_menus_correlation:

Analysis menu
----------------------------

.. image:: _static/analysis_menus_correlation_plot.jpg

.. toctree::
   :maxdepth: 1
   
   fitting.rst   

* Integration: calculate area under the curve using the composite trapezoidal rule.

* Statistics: calculate mean, standard deviation and peak to peak for data in the current view.