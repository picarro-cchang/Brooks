# Test suite for the swath processor

import unittest

import Host.Common.SwathProcessor as sp

class TestSwathProcessor(unittest.TestCase):
    # Check the ltqnorm function
    # This should return for a probability p, the threshold z such that the probability that a unit normally distributed random variable
    #  is less than p is z
    def test_ltqnorm_1(self):
        self.assertRaises(ValueError,sp.ltqnorm,1.1)
        self.assertRaises(ValueError,sp.ltqnorm,-1.1)
        self.assertAlmostEqual(sp.ltqnorm(0.5),0.0)
    def test_ltqnorm_2(self):
        self.assertAlmostEqual(sp.ltqnorm(0.84134),1.0,delta=0.001)
        self.assertAlmostEqual(sp.ltqnorm(0.9772498),2.0,delta=0.001)
        self.assertAlmostEqual(sp.ltqnorm(0.9986501),3.0,delta=0.001)
        self.assertAlmostEqual(sp.ltqnorm(1.0-0.84134),-1.0,delta=0.001)
        self.assertAlmostEqual(sp.ltqnorm(1.0-0.9772498),-2.0,delta=0.001)
        self.assertAlmostEqual(sp.ltqnorm(1.0-0.9986501),-3.0,delta=0.001)
    pass
    

if __name__ == '__main__':
    unittest.main()
