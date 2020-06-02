import ctypes

data_bytes = (ctypes.c_byte * 65536)()

for i in xrange(len(data_bytes)):
    data_bytes[i] = i & 0xFF

with open("lattice.bit", "wb") as op:
    op.write(data_bytes)
