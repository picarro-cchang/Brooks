function d = readHdf5(fname)
% Reads in an HDF5 formatted file specified by 'fname'
tempFile = 'tempFile.mat';
system(['hdf5ToMat.py ' fname ' ' tempFile]);
d = load(tempFile);