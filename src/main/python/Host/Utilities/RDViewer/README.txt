    RDViewer Notes

    Author: Tracy Walder
    Last updated: 3/7/2014


This code was added in response to issue #699: Migrate Debug Utilities submitted by Alex F.

This addresses the third application in the list, RD Residuals with Averaging, in this folder:
    "S:\CRDS\R&D projects\Picarro Stewards\Debug Utilities\RD Residuals\viewRdWaveforms_with_average.py"

I renamed the awkward Python source filename as RDViewer.py. There was a second Python source file in that folder, which is older
and from which the longer name was derived.

Since this currently uses the enthought libraries, we cannot build it as an executable. The file from which it was derived
used a local copy of CmdFIFO, SharedTypes, and interface.py but viewRdWaveforms_with_average.py needs this modification
so it can be run on any analyzer.


History:

3/7/2014: Committed the original sources, along with the various other files (omitting viewRdWaveforms.py as it is old
          source). Fixed the line endings for FigureInteraction.py and Ringdown Viewer Install.txt
          with a hex editor before checking in due to a git warning (replaced 0A -> 0D0A). Also they won't appear on a
          single line in Notepad (git warning leads me to believe will never be right in my own folder). Perhaps these
          files were last edited on a Mac?









