from collections import deque
import json
from mock import call, MagicMock
import numpy as np
from numpy import arctan, arctan2, asarray, cos, pi, sin, sqrt, tan
import os
import sys
import tempfile
from traitlets.config import Config
import traceback
import unittest
from Host.Pipeline.EthaneAggregation import EthaneAggregation

def distVincenty(lat1, lon1, lat2, lon2):
    # WGS-84 ellipsiod. lat and lon in DEGREES
    a = 6378137
    b = 6356752.3142
    f = 1/298.257223563
    toRad = pi/180.0
    L = (lon2-lon1)*toRad
    U1 = arctan((1-f) * tan(lat1*toRad))
    U2 = arctan((1-f) * tan(lat2*toRad))
    sinU1 = sin(U1)
    cosU1 = cos(U1)
    sinU2 = sin(U2)
    cosU2 = cos(U2)

    Lambda = L
    iterLimit = 100
    for _ in range(iterLimit):
        sinLambda = sin(Lambda)
        cosLambda = cos(Lambda)
        sinSigma = sqrt((cosU2*sinLambda) * (cosU2*sinLambda) +
                        (cosU1*sinU2-sinU1*cosU2*cosLambda) * (cosU1*sinU2-sinU1*cosU2*cosLambda))
        if sinSigma == 0:
            return 0  # co-incident points
        cosSigma = sinU1*sinU2 + cosU1*cosU2*cosLambda
        sigma = arctan2(sinSigma, cosSigma)
        sinAlpha = cosU1 * cosU2 * sinLambda / sinSigma
        cosSqAlpha = 1 - sinAlpha*sinAlpha
        if cosSqAlpha == 0:
            cos2SigmaM = 0
        else:
            cos2SigmaM = cosSigma - 2*sinU1*sinU2/cosSqAlpha
        C = f/16*cosSqAlpha*(4+f*(4-3*cosSqAlpha))
        lambdaP = Lambda
        Lambda = L + (1-C) * f * sinAlpha * \
          (sigma + C*sinSigma*(cos2SigmaM+C*cosSigma*(-1+2*cos2SigmaM*cos2SigmaM)))
        if abs(Lambda-lambdaP) <= 1.e-12: break
    else:
        raise ValueError("Failed to converge")

    uSq = cosSqAlpha * (a*a - b*b) / (b*b)
    A = 1 + uSq/16384*(4096+uSq*(-768+uSq*(320-175*uSq)))
    B = uSq/1024 * (256+uSq*(-128+uSq*(74-47*uSq)))
    deltaSigma = B*sinSigma*(cos2SigmaM+B/4*(cosSigma*(-1+2*cos2SigmaM*cos2SigmaM)-
                                            B/6*cos2SigmaM*(-3+4*sinSigma*sinSigma)*(-3+4*cos2SigmaM*cos2SigmaM)))
    return b*A*(sigma-deltaSigma)

class EthaneAggregationTest(unittest.TestCase):
    exclusion_radius = 20
    @classmethod
    def setUpClass(cls):
        myconfig = Config()
        myconfig.EthaneClassifier.nng_lower = 0.0
        myconfig.EthaneClassifier.nng_upper = 0.1e-2
        myconfig.EthaneClassifier.ng_lower = 2.0e-2
        myconfig.EthaneClassifier.ng_upper = 10.0e-2
        myconfig.EthaneClassifier.nng_prior = 0.27
        myconfig.EthaneClassifier.thresh_confidence = 0.9
        myconfig.EthaneClassifier.reg = 0.05
        with file('aggregation_input.json', "rb") as jp:
            indications = json.load(jp)
        ea = EthaneAggregation(indications=indications, exclusion_radius=cls.exclusion_radius, config=myconfig)
        sorted_indications = ea.process()
        with file('aggregation_output.json', "wb") as jp:
            json.dump(sorted_indications, jp, indent=2, sort_keys=True)

    def setUp(self):
        with file('aggregation_output.json', "rb") as jp:
            self.indications = json.load(jp)

    def test_ignore_below_threshold(self):
        for indication in self.indications:
            if not indication["PASSED_THRESHOLD"]:
                self.assertFalse(indication["ACTIVE"])

    def test_vehicle_exhaust_inactive(self):
        for indication in self.indications:
            if indication["VERDICT"] == "VEHICLE_EXHAUST":
                self.assertFalse(indication["ACTIVE"])

    def test_amplitude_within_group(self):
        for indication in self.indications:
            if indication["ACTIVE"]:
                for member in indication["GROUP_RANKS"]:
                    self.assertLessEqual(self.indications[member]["AMPLITUDE"], indication["AMPLITUDE"])

    def test_distances_within_group(self):
        for indication in self.indications:
            if indication["ACTIVE"]:
                for member in indication["GROUP_RANKS"]:
                    self.assertLessEqual(distVincenty(indication["GPS_ABS_LAT"],
                                                      indication["GPS_ABS_LONG"],
                                                      self.indications[member]["GPS_ABS_LAT"],
                                                      self.indications[member]["GPS_ABS_LONG"]), self.exclusion_radius)

    def test_distances_between_representatives(self):
        lat_list = []
        lng_list = []
        for indication in self.indications:
            if indication["ACTIVE"]:
                lat_list.append(indication["GPS_ABS_LAT"])
                lng_list.append(indication["GPS_ABS_LONG"])
        # Check representatives are further apart than exclusion radius
        for i, (lat1, lng1) in enumerate(zip(lat_list, lng_list)):
            for (lat2, lng2) in zip(lat_list[:i], lng_list[:i]):
                self.assertGreater(distVincenty(lat1, lng1, lat2, lng2), self.exclusion_radius)

    def test_membership_in_groups(self):
        group_members = []
        for indication in self.indications:
            if indication["ACTIVE"]:
                group_members.extend(indication["GROUP_RANKS"])
        group_members = set(group_members)
        for indication in self.indications:
            if indication["ACTIVE"]:
                self.assertNotIn(indication["RANK"], group_members)
            else:
                if (indication["VERDICT"] == "VEHICLE_EXHAUST") or not indication["PASSED_THRESHOLD"]:
                    self.assertNotIn(indication["RANK"], group_members)
                else:
                    self.assertIn(indication["RANK"], group_members)

    def test_aggregation_arithmetic(self):
        for indication in self.indications:
            if indication["ACTIVE"]:
                ethane_ratio = [indication["ETHANE_RATIO"]]
                ethane_ratio_sdev = [indication["ETHANE_RATIO_SDEV"]]
                for member in indication["GROUP_RANKS"]:
                    ethane_ratio.append(self.indications[member]["ETHANE_RATIO"])
                    ethane_ratio_sdev.append(self.indications[member]["ETHANE_RATIO_SDEV"])
                ethane_ratio = asarray(ethane_ratio)
                ethane_ratio_sdev = asarray(ethane_ratio_sdev)
                agg_ethane_ratio_sdev = sum(ethane_ratio_sdev ** (-2)) ** (-0.5)
                agg_ethane_ratio = sum(ethane_ratio * ethane_ratio_sdev ** (-2)) / sum(ethane_ratio_sdev ** (-2))
                self.assertAlmostEqual(agg_ethane_ratio, indication["AGG_ETHANE_RATIO"])
                self.assertAlmostEqual(agg_ethane_ratio_sdev, indication["AGG_ETHANE_RATIO_SDEV"])

    def test_all_have_agg_dispositions(self):
        for indication in self.indications:
            self.assertIn("AGG_VERDICT", indication)

if __name__ == "__main__":
    unittest.main()