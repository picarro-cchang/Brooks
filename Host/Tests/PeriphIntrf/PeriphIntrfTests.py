"""
Copyright 2014 Picarro Inc.
"""

from __future__ import with_statement

import sys
from os import path

import pytest
import mock

from Host.PeriphIntrf import PeriphIntrf
from Host.PeriphIntrf import Errors

sys.path.append(path.join(path.dirname(__file__), '..'))
from Helpers import BroadcastSink


class TestPeriphIntrf(object):
    
    def setup_method(self, m):
        self.broadcaster = BroadcastSink.BroadcastSink()

    def teardown_method(self, m):
        self.broadcaster = None

    @mock.patch.object(PeriphIntrf.PeriphIntrf, 'connect')
    @mock.patch.object(PeriphIntrf.PeriphIntrf, 'getFromSocket')
    @mock.patch.object(PeriphIntrf.PeriphIntrf, 'selectAllDataByTime')
    def testLinearInterpolationSinglePortSingleLabel(self, selectAllDataByTime, getFromSocket, connect):
        selectAllDataByTime.return_value = [
            # PORT0
            [[0.0, 1.0], [
                # TEST1
                [0.0, 1.0]]]
        ]

        pi = PeriphIntrf.PeriphIntrf(path.join(path.dirname(__file__), 'data', 'linearSingleConfigSingleLabel.ini'),
                                     self.broadcaster)

        assert pi.dataInterpolators == [{'TEST1' : 'linear'}]

        ret = pi.getDataByTime(0.5, ['TEST1'])
        assert ret is not None
        assert len(ret) == 1
        assert ret[0] == 0.5

    @mock.patch.object(PeriphIntrf.PeriphIntrf, 'connect')
    @mock.patch.object(PeriphIntrf.PeriphIntrf, 'getFromSocket')
    @mock.patch.object(PeriphIntrf.PeriphIntrf, 'selectAllDataByTime')
    def testLinearInterpolationSinglePortMultiLabel(self, selectAllDataByTime, getFromSocket, connect):
        selectAllDataByTime.return_value = [
            # PORT0
            [[1.0, 2.0], [
                # TEST1
                [1.0, 2.0],
                # TEST2
                [1.0, 4.0]
            ]]
        ]

        pi = PeriphIntrf.PeriphIntrf(path.join(path.dirname(__file__), 'data', 'linearSingleConfigMultiLabel.ini'),
                                     self.broadcaster)

        assert pi.dataInterpolators == [{'TEST1' : 'linear', 'TEST2' : 'linear'}]

        ret = pi.getDataByTime(1.5, ['TEST1', 'TEST2'])
        assert ret is not None
        assert len(ret) == 2
        assert ret[0] == 1.5
        assert ret[1] == 2.5

    @mock.patch.object(PeriphIntrf.PeriphIntrf, 'connect')
    @mock.patch.object(PeriphIntrf.PeriphIntrf, 'getFromSocket')
    @mock.patch.object(PeriphIntrf.PeriphIntrf, 'selectAllDataByTime')
    def testMaxInterpolationSinglePortSingleLabel(self, selectAllDataByTime, getFromSocket, connect):
        selectAllDataByTime.return_value = [
            # PORT0
            [[0.0, 1.0], [
                # TEST1
                [0.0, 1.0]]]
        ]

        pi = PeriphIntrf.PeriphIntrf(path.join(path.dirname(__file__), 'data', 'maxSingleConfigSingleLabel.ini'),
                                     self.broadcaster)

        assert pi.dataInterpolators == [{'TEST1' : 'max'}]

        ret = pi.getDataByTime(0.5, ['TEST1'])
        assert ret is not None
        assert len(ret) == 1
        assert ret[0] == 1.0

    @mock.patch.object(PeriphIntrf.PeriphIntrf, 'connect')
    @mock.patch.object(PeriphIntrf.PeriphIntrf, 'getFromSocket')
    @mock.patch.object(PeriphIntrf.PeriphIntrf, 'selectAllDataByTime')
    def testMaxInterpolationSinglePortMultiLabel(self, selectAllDataByTime, getFromSocket, connect):
        selectAllDataByTime.return_value = [
            # PORT0
            [[0.0, 1.0], [
                # TEST1
                [0.0, 1.0],
                # TEST2
                [0.0, 0.0]]]
        ]

        pi = PeriphIntrf.PeriphIntrf(path.join(path.dirname(__file__), 'data', 'maxSingleConfigMultiLabel.ini'),
                                     self.broadcaster)

        assert pi.dataInterpolators == [{'TEST1' : 'max', 'TEST2' : 'max'}]

        ret = pi.getDataByTime(0.5, ['TEST1', 'TEST2'])
        assert ret is not None
        assert len(ret) == 2
        assert ret[0] == 1.0
        assert ret[1] == 0.0

    @mock.patch.object(PeriphIntrf.PeriphIntrf, 'connect')
    @mock.patch.object(PeriphIntrf.PeriphIntrf, 'getFromSocket')
    @mock.patch.object(PeriphIntrf.PeriphIntrf, 'selectAllDataByTime')
    def testMaxInterpolationSinglePortMultiLabel(self, selectAllDataByTime, getFromSocket, connect):
        selectAllDataByTime.return_value = [
            # PORT0
            [[0.0, 1.0], [
                # TEST1
                [0.0, 1.0],
                # TEST2
                [1.0, 2.0]]]
        ]

        pi = PeriphIntrf.PeriphIntrf(path.join(path.dirname(__file__), 'data', 'mixedSingleConfigMultiLabel.ini'),
                                     self.broadcaster)

        assert pi.dataInterpolators == [{'TEST1' : 'max', 'TEST2' : 'linear'}]

        ret = pi.getDataByTime(0.5, ['TEST1', 'TEST2'])
        assert ret is not None
        assert len(ret) == 2
        assert ret[0] == 1.0
        assert ret[1] == 1.5

    @mock.patch.object(PeriphIntrf.PeriphIntrf, 'connect')
    @mock.patch.object(PeriphIntrf.PeriphIntrf, 'getFromSocket')
    def testNotEnoughInterpolators(self, getFromSocket, connect):
        with pytest.raises(Errors.InterpolationListIncomplete):
            pi = PeriphIntrf.PeriphIntrf(path.join(path.dirname(__file__), 'data', 'notEnoughInterpolators.ini'),
                                         self.broadcaster)

    @mock.patch.object(PeriphIntrf.PeriphIntrf, 'connect')
    @mock.patch.object(PeriphIntrf.PeriphIntrf, 'getFromSocket')
    def testUnknownInterpolator(self, getFromSocket, connect):
        with pytest.raises(Errors.InterpolationTypeUnknown):
            pi = PeriphIntrf.PeriphIntrf(path.join(path.dirname(__file__), 'data', 'unknownInterpolator.ini'),
                                         self.broadcaster)

    @mock.patch.object(PeriphIntrf.PeriphIntrf, 'connect')
    @mock.patch.object(PeriphIntrf.PeriphIntrf, 'getFromSocket')
    @mock.patch.object(PeriphIntrf.PeriphIntrf, 'selectAllDataByTime')
    def testBitwiseOrInterpolationSinglePortMultiLabel(self, selectAllDataByTime, getFromSocket, connect):
        selectAllDataByTime.return_value = [
            # PORT0
            [[0.0, 1.0], [
                # TEST1
                [1.0, 2.0],
                # TEST2
                [4.0, 8.0]]]
        ]

        pi = PeriphIntrf.PeriphIntrf(path.join(path.dirname(__file__), 'data', 'bitwiseOrSingleConfigMultiLabel.ini'),
                                     self.broadcaster)

        assert pi.dataInterpolators == [{'TEST1' : 'bitwiseOr', 'TEST2' : 'bitwiseOr'}]

        ret = pi.getDataByTime(0.5, ['TEST1', 'TEST2'])
        assert ret is not None
        assert len(ret) == 2
        assert ret[0] == 3.0
        assert ret[1] == 12.0


    

        
        
