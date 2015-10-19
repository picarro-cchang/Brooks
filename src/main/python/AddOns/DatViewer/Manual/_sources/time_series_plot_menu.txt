.. _menus_time_series_plot:

***************************
Menus of Time Series Plot
***************************

.. image:: _static/menus_time_series_plot.jpg

.. _file_menu_time:

File menu
=============================

.. _save_configuration:

Save configuration
------------------------

Save figure properties, expression, filter and other settings into a configuration file 
so that they can be loaded easily in the future. Properties to be saved can be specified in 
the Figure Capture panel.

.. image:: _static/feature_capture.jpg

* If all features are selected, loading configuration file will reproduce the workplace.

* If Data file is not captured, loading configuration file will apply all other parameters to data file in the memory.

* If X (Y) range is not captured,  figures will be auto scaled on x (y) axis.

.. _analysis_menu_time:

Analysis menu
=============================

.. _correlation_plot_menu:

Correlation plot
-----------------------------

Plot y-axis data in one frame versus that in the other. Enable when two or more frames exist in the current window. 
See :ref:`correlation_plot` for details.

.. _view_menu_time:

View menu
=============================

* x-Axis in DateTime: x-axis data is shown in the datetime format

* x-Axis in Minute: x-axis data is in unit of minute. 

* x-Axis in Hour: x-axis data is in unit of hour.

When switching from DateTime to Minute/Hour, x-axis data is substracted by the earliest point shown in the panel, 
and then converted to desired unit. 
