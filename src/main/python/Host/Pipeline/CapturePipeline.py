#!/usr/bin/python
#
# CapturePipeline.py is an implementation of the pipeline for analyzing isotopic capture mode
#
import os
import pandas as pd
import traceback

from traitlets import (Bool, Dict, Float, Instance, Integer, List, Unicode)
from traitlets.config.application import Application

from Host.Pipeline.Blocks import Pipeline
from Host.Pipeline.PeaksBlocks import (AddDistanceBlock)
from Host.Pipeline.UtilityBlocks import (FrameFetcherBlock, LineCountBlock, PrinterBlock, ProcessStatusBlock)
from Host.Pipeline.CaptureBlocks import (CaptureAnalyzerBlock, )
from Host.Pipeline.EthaneBlocks import (EthaneClassifier, JsonWriterBlock)


class CapturePipeline(Pipeline):
    addDistanceBlock = Instance(AddDistanceBlock)
    captureAnalyzerBlock = Instance(CaptureAnalyzerBlock)
    frameFetcherBlock = Instance(FrameFetcherBlock)
    lineCountBlock = Instance(LineCountBlock)
    jsonWriterBlock = Instance(JsonWriterBlock)
    printerBlock = Instance(PrinterBlock)
    processStatusBlock = Instance(ProcessStatusBlock)

    baseFilename = Unicode()

    def __init__(self, **kwargs):
        super(CapturePipeline, self).__init__(**kwargs)

    def makeBlocks(self):
        self.frameFetcherBlock = FrameFetcherBlock()
        self.jsonWriterBlock = JsonWriterBlock(self.baseFilename + "_analysis.json")
        self.lineCountBlock = LineCountBlock()
        self.processStatusBlock = ProcessStatusBlock(speciesList=[25, 150, 170])
        self.addDistanceBlock = AddDistanceBlock()
        self.captureAnalyzerBlock = CaptureAnalyzerBlock(config=self.config)

    def linkBlocks(self):
        self.frameFetcherBlock.linkTo(self.processStatusBlock)
        self.processStatusBlock.linkTo(self.lineCountBlock)
        self.processStatusBlock.linkTo(self.addDistanceBlock)
        self.addDistanceBlock.linkTo(self.captureAnalyzerBlock)
        self.captureAnalyzerBlock.linkTo(self.jsonWriterBlock)

class CapturePipelineApp(Application):
    aliases = Dict(dict(config='AnalysisPipelineApp.config_file'))
    classes = List([CaptureAnalyzerBlock, EthaneClassifier])
    config_file = Unicode('', config=True, help="Name of configuration file")

    def initialize(self, argv=None):
        self.config.CaptureAnalyzerBlock.captureType = "Isotopic"            # Type of capture mode to use
        self.config.CaptureAnalyzerBlock.methane_ethane_sdev_ratio = 0.2     # Ratio of methane conc. sdev to ethane conc. sdev
        self.config.CaptureAnalyzerBlock.methane_ethylene_sdev_ratio = 0.09  # Ratio of methane conc. sdev to ethylene conc. sdev
        self.config.EthaneClassifier.nng_lower = 0.0  # Lower limit of ratio for not natural gas hypothesis
        self.config.EthaneClassifier.nng_upper = 0.1e-2  # Upper limit of ratio for not natural gas hypothesis
        self.config.EthaneClassifier.ng_lower = 2e-2  # Lower limit of ratio for natural gas hypothesis
        self.config.EthaneClassifier.ng_upper = 10e-2  # Upper limit of ratio for natural gas hypothesis
        self.config.EthaneClassifier.nng_prior = 0.27  # Prior probability of not natural gas hypothesis
        self.config.EthaneClassifier.thresh_confidence = 0.9  # Threshold confidence level for definite hypothesis
        self.config.EthaneClassifier.reg = 0.05  # Regularization parameter
        self.parse_command_line(argv)
        if self.config_file:
            self.load_config_file(self.config_file)

    def start(self):
        filenamesToProcess = [
            #r"C:\Research\DE1347\SurveyExport_rd trace iso multi-2_FEDS2015-PGE_13-11-2015-22-12-21_C_Standard.dat",
            #r"C:\Research\Ethane\PulseReplays\250_20_sample_and_hold_with_transitions\RFADS2021-250-35-20160212-171822Z-DataLog_User_Minimal.dat",
            r"C:\Research\Ethane\PulseReplays\250_20_sample_and_hold_with_transitions\RFADS2021-250-20-20160212-065557Z-DataLog_User_Minimal.dat",
            r"C:\Research\Ethane\PulseReplays\LargeAmplitudePulses\RFADS2037-20160217-001904Z-DataLog_User_Minimal.dat"
        ]
        for inputFilename in filenamesToProcess:
            baseFilename = os.path.splitext(inputFilename)[0]
            dataFrame = pd.read_table(inputFilename, delim_whitespace=True, na_values=['NAN'])
            if "C2H6" in dataFrame.columns.values.tolist():             # Heuristic to find type of capture mode to use
                self.config.CaptureAnalyzerBlock.captureType = "Ethane"
            else:
                self.config.CaptureAnalyzerBlock.captureType = "Isotopic"
            try:
                pipeline = CapturePipeline(baseFilename=baseFilename, config=self.config)
                pipeline.makeBlocks()
                pipeline.linkBlocks()
                pipeline.frameFetcherBlock.post(dataFrame)
                pipeline.frameFetcherBlock.complete()
                while not pipeline.waitCompletion(0.5):
                    pass
            except:
                print traceback.format_exc()

if __name__ == "__main__":
    app = CapturePipelineApp()
    app.initialize()
    app.start()

