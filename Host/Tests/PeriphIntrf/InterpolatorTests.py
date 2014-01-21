"""
Copyright 2014 Picarro Inc.
"""

from Host.PeriphIntrf.Interpolators import Interpolators


class TestInterpolators(object):

    def testLinear(self):
        assert Interpolators.linear([0.0, 1.0], [0.0, 1.0], 0.5) == 0.5
        assert Interpolators.linear([1.0, 4.0], [1.0, 2.0], 1.5) == 2.5

    def testMax(self):
        assert Interpolators.max([0.0, 0.0], [0.0, 1.0], 0.5) == 0.0
        assert Interpolators.max([0.0, 1.0], [0.0, 1.0], 0.5) == 1.0
        assert Interpolators.max([1.0, 0.0], [0.0, 1.0], 0.5) == 1.0
        assert Interpolators.max([1.0, 1.0], [0.0, 1.0], 0.5) == 1.0

    def testBitwiseOr(self):
        assert Interpolators.bitwiseOr([0x0F, 0xF0], [0.0, 1.0], 0.5) == 255.0
        assert Interpolators.bitwiseOr([0x00, 0x00], [0.0, 1.0], 0.5) == 0.0
