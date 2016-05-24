.. WLMstation documentation master file

Welcome to WLMstation's documentation!
=======================================

The purpose of this program is to help building wavelength monitor (WLM), a key component of Picarro 
cavity ring down spectroscopy (CRDS) analyzers. The old WLM station software was written in Visual Basic. 
Due to the obsolete Visual Basic language and some other driver issues, the old program cannot run on new computers with latest Windows operating systems.
We have made the following changes to update the WLM build station:

* Rewrite the software using Python so it can run properly on new computers. 

* Replace old digital multi-meters with a high-speed digital-to-analogue converter (DAC) for fast data acquisition.

* Use a G2000 system as light source to enable fast scan on wave number. 

New WLMstation software discards many functionalities of old program that are not used any more and focuses on the following tasks:

* Monitor laser power.

* Monitor transmittance and reflectance of the etalon.

* Scan laser wave number and calculate ratio of transmittance and reflectance.

Table of Contents:

.. toctree::
   :maxdepth: 2
   
   getting_started.rst
   user_guide.rst