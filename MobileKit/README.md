To run this code you will need some dependencies


sudo easy_install virtualenv
virtualenv venv
. venv/bin/activate
 pip install Flask

if you use venv you will need to make sure you add picarro pth to where the Host folder lives.  
  The Host folder is in a few of our repos and there will be more on this later. 


    touch /opt/picarro/investigator/venv/lib/python2.7/site-packages/picarro.pth

or

    touch /Library/Python/2.7/site-packages/picarro.pth

After you have the .pth in proper location depending on your environment be sure to add the line like so where Host lives.

  
    /opt/picarro/szesurveyor

To verify this has worked you should run python shell and be sure you can import the modules

    python
    >>> import Host.Common

    python AnalyzerServer/analyzerServer.py
    => maybe you're lucky enough for it to work :) 

Change these lines for the final path of the data directory
/opt/www/picarro/picarro_trunk/MobileKit/AnalyzerServer/analyzerServer.py:
57 # The following are split into a path and a filename with unix style wildcards.
58 # We search for the filename in the specified path and its subdirectories.
59: USERLOGFILES = '/opt/www/picarro/data/.dat'
60: PEAKFILES = '/opt/www/picarro/data/.peaks'
61: ANALYSISFILES = '/opt/www/picarro/data/.analysis'
62: SWATHFILES = '/opt/www/picarro/data/.swath'
63 MAX_DATA_POINTS = 500

    python AnalyzerServer/analyzerServer.py
    => maybe it works

http://epd-free.enthought.com/?Download=Download+EPD+Free+7.3-2

If you are on a mac make sure to go to settings, security, and then make it so you can download applications from anywhere.


You can use the following code to test that the install of numpy worked correctly as well as you having the Host.Common modules.

±  |master ✗| → ipython --pylab
Enthought Python Distribution (free version) -- www.enthought.com
(type 'upgrade' or see www.enthought.com/epd/upgrade to get the full EPD)

Python 2.7.3 |EPD_free 7.3-2 (32-bit)| (default, Apr 12 2012, 11:28:34) 
Type "copyright", "credits" or "license" for more information.

IPython 0.12.1 -- An enhanced Interactive Python.
?         -> Introduction and overview of IPython's features.
%quickref -> Quick reference.
help      -> Python's own help system.
object?   -> Details about 'object', use 'object??' for extra details.
x
Welcome to pylab, a matplotlib-based Python environment [backend: WXAgg].
For more information, type 'help(pylab)'.

In [1]: x = linspace(0,2*pi,1001)

In [2]: y = sin(x)

In [3]: plot(x,y)
Out[3]: [<matplotlib.lines.Line2D at 0x57a8430>]

In [4]: show()

In [5]: import Host.Common


# run the app
    python AnalyzerServer/analyzerServer.py

visit 

http://localhost:5000/public_url
visit http://localhost:5000/investigator_ben
