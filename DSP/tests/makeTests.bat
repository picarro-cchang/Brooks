rem gcc -o testRdFitting.exe -I../inc -I../autogen testRdFitting.c ../common/rdFitting.c ../common/CuTest.c
gcc -o testSpectCntrl.exe -DTESTING -I../inc -I../registerTest -I../tests -I../autogen ../common/fpga.c testSpectCntrl.c testHarness.c ../registerTest/spectrumCntrl.c ../common/CuTest.c
