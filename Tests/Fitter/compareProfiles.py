# Compare Galatry function evaluation routines

from Host.Fitter.fitterCore import voigt, voigt0, galatry, galatry0
import numpy as np

x = np.linspace(-10,10,2001)

for y in 100*np.random.rand(100):
    print "y = ",y
    ve = abs(voigt(x,y)-np.real(voigt0(x,y))).max() 
    if ve > 1e-6:
        print "At y =",y, "Voigt error is: ", ve
    for z in 100*np.random.rand(100):
        ge = abs(galatry(x,y,z)-galatry0(x,y,z)).max()
        if ge > 1e-6:
            print "At y =",y," z =",z," Galatry error is ",ge
            
