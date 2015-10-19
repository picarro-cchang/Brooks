.. _expression_and_filter:

***************
Expression and Filter
***************

.. _expression:

Expression
=============================

Expression is a mathematical function that applies on the selected data and tranform the plot. 
Here is an expression example::

  y + CO2

In Expression field, 'x' is time-related data (x-axis data of the plot), and 'y' is data of selected variable (y-axis data of the plot). 
To call other variables in the selected data set, just type the variable names (e.g. CO2, CH4). 

.. _filter:

Filter
=============================

Filter is a mathematical expression that specifies data to include or exclude from plot(s). 
Here is a filter example::

  (CH4 < 5) & (CO2 < 10)

where CH4 and CO2 are both variable names in the selected data set. 

Below is a list logical operators defined in the filter field:

* &: AND 

* |: OR

* ~: NOT

* ^: XOR