.. _plotting_canvas:

***************
Canvas
***************

.. _mouse_events:

Mouse motion and figure transform
==================================

* Left click and drag: **Zoom in** into the selected area of the plot.

* Left click and drag with SHIFT key down: **Pan** the plot  

* Left click and drag with CTRL key down: **Zoom out** from the plot

* Left click and drag with ALT key down: **Stretch** the plot

* Right click: Pop up righ-key menu

.. _right_key_menu:

Right-key menu
==================================

.. image:: _static/right_key_menu.jpg

Export Image
----------------------

Export the current plot as a JPEG/PNG/PDF file.

Export Data in Current View
----------------------------------

Export only Datetime and the selected variable in current view to a HDF5/CSV file.

Export All Data in Current Time Range
-----------------------------------------

Export all available columns of selected dataset in current time range to a HDF5 file.
See :ref:`concatenate_files_timerange` for an example of use case.

.. _image_editor:

Edit Plot Properties
--------------------------

.. image:: _static/image_editor.jpg

* **Title**: title of the plot.

* **Line**: line pattern of the plot. If *None* is selected, data points will plotted without connecting lines.

* **Marker**: marker of data points. If *None* is selected, data points will not be shown.

* **Min** and **Max**: minimum and maximum of data range for the axis.

* **x[0]**: set the earliest time of dataset as the minimum of x-axis.

* **Time zone**: time zone selected for Datetime variables. This defaults to the local time zone.

* **Label**: label of the axis.

Statistics
---------------------------

Calculate mean, standard deviation and peak to peak for data in the current view.