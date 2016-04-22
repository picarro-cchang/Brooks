#!/usr/bin/python
#
# EthanePipeline.py is an implementation of the subset of the Data Analytics pipeline that is relevant
#  to validating the surveyor ethane project
#
from numpy import ceil, log
import os
import pandas as pd
import traceback

from traitlets import (Bool, Dict, Float, Instance, Integer, List, Unicode)
from traitlets.config.application import Application

from Host.Pipeline.Blocks import Pipeline
from Host.Pipeline.PeaksBlocks import (AddDistanceBlock, BaselineFilterBlock, MinimumFilterBlock,
                                       PeakFilterBlock, SpaceScaleAnalyzerBlock)
from Host.Pipeline.UtilityBlocks import (AutoThresholdBlock,
                                         FrameFetcherBlock, InterpolatorBlock, JoinerBlock,
                                         LineCountBlock, PrinterBlock, ProcessStatusBlock)
from Host.Pipeline.EthaneBlocks import (EthaneClassifier, EthaneComputationBlock, EthaneDispositionBlock,
                                        JsonWriterBlock, VehicleExhaustClassifier)

class EthanePipeline(Pipeline):
    addDistanceBlock = Instance(AddDistanceBlock)
    baselineFilterBlock = Instance(BaselineFilterBlock)
    distanceInterpolatorBlock = Instance(InterpolatorBlock)
    ethaneComputationBlock = Instance(EthaneComputationBlock)
    ethaneDispositionBlock = Instance(EthaneDispositionBlock)
    frameFetcherBlock = Instance(FrameFetcherBlock)
    lineCountBlock = Instance(LineCountBlock)
    minimumFilterBlock = Instance(MinimumFilterBlock)
    peakAutoThresholdBlock = Instance(AutoThresholdBlock)
    peakFilterBlock = Instance(PeakFilterBlock)
    peakJoinerBlock = Instance(JoinerBlock)
    jsonWriterBlock = Instance(JsonWriterBlock)
    printerBlock = Instance(JsonWriterBlock)
    processStatusBlock = Instance(ProcessStatusBlock)
    spaceScaleAnalyzerBlock = Instance(SpaceScaleAnalyzerBlock)

    baseFilename = Unicode()
    dx = Float(1.0)  # Separation between points for distance interpolation
    # Parmeters for space-scale (peak) analysis
    factor = Float(1.1)         # Factor between adjacent scales
    sigmaMin = Float(2.0)       # Minimum half-width to consider for peak finding
    sigmaMax = Float(20.0)      # Maximum half-width to consider for peak finding
    # Parameters for peak filter
    maxWidth = Float(20.0)      # Maximum half-width to allow for peak filtering
    minAmpl = Float(0.035)      # Minimum amplitude for peak filtering
    # Parameters for high background (autothreshold) filtering
    autoThresh = Bool(True)     # Enable or disable autothreshold
    minimumFilterLength = Integer(51)   # Set distance range for minimum filter
    baselineFilterLength = Integer(201) # Set distance range for calculating background standard deviation
    autoThresholdOptions = Dict(default_value=dict(normWidthLo = 0.0, normWidthHi = 2.0, normAmplLo = 6.0, normAmplHi = 6.37))

    def __init__(self, **kwargs):
        super(EthanePipeline, self).__init__(**kwargs)

    def makeBlocks(self):
        self.frameFetcherBlock = FrameFetcherBlock()
        #self.printerBlock =  JsonWriterBlock(self.baseFilename + "_out.json")
        self.jsonWriterBlock = JsonWriterBlock(self.baseFilename + "_indications.json")
        self.lineCountBlock = LineCountBlock()
        self.processStatusBlock = ProcessStatusBlock(speciesList=[170])
        self.addDistanceBlock = AddDistanceBlock()

        distanceInterpolatorOptions = dict(linInterpKeys=['EPOCH_TIME', 'CAR_VEL_N', 'CAR_VEL_E',
                                                          'CAR_SPEED', 'WIND_N', 'WIND_E', 'WIND_DIR_SDEV',
                                                          'CH4', 'C2H6', 'C2H4', 'GPS_ABS_LAT', 'GPS_ABS_LONG',
                                                          'AnalyzerEthaneConcentrationUncertainty'],
                                           minInterpKeys=['GPS_FIT'],
                                           maxInterpKeys=['INST_STATUS', 'ValveMask', 'PATH_TYPE'])
        self.distanceInterpolatorBlock = InterpolatorBlock('DISTANCE', self.dx, **distanceInterpolatorOptions)

        t0 = 2 * (self.sigmaMin / self.factor) * (self.sigmaMin / self.factor)
        nlevels = int(ceil((log(2 * self.sigmaMax * self.sigmaMax) - log(t0)) / log(self.factor))) + 1
        spaceScaleOptions = dict(dx=self.dx, minAmpl=self.minAmpl, t_0=t0, nlevels=nlevels, tfactor=self.factor)
        self.spaceScaleAnalyzerBlock = SpaceScaleAnalyzerBlock(**spaceScaleOptions)


        self.ethaneComputationBlock = EthaneComputationBlock(interval=self.dx, config=self.config)
        self.ethaneDispositionBlock = EthaneDispositionBlock(config=self.config)

        self.minimumFilterBlock = MinimumFilterBlock('CH4', self.minimumFilterLength)
        self.baselineFilterBlock = BaselineFilterBlock('MIN_FILT_OUT', self.baselineFilterLength)
        self.peakJoinerBlock = JoinerBlock('DISTANCE', self.dx, maxLookback=1000, linInterpKeys=['BASELINE_FILT_OUT'])

        self.peakAutoThresholdBlock = AutoThresholdBlock(**self.autoThresholdOptions)
        self.peakFilterBlock = PeakFilterBlock(self.minAmpl, self.maxWidth)

    def linkBlocks(self):
        self.frameFetcherBlock.linkTo(self.processStatusBlock)
        self.processStatusBlock.linkTo(self.lineCountBlock)
        self.processStatusBlock.linkTo(self.addDistanceBlock)
        self.addDistanceBlock.linkTo(self.distanceInterpolatorBlock)
        self.distanceInterpolatorBlock.linkTo(self.spaceScaleAnalyzerBlock)
        #self.addDistanceBlock.linkTo(self.printerBlock)
        self.distanceInterpolatorBlock.linkTo(self.ethaneComputationBlock.inputs[0])
        self.spaceScaleAnalyzerBlock.linkTo(self.ethaneComputationBlock.inputs[1])
        self.ethaneComputationBlock.linkTo(self.ethaneDispositionBlock)

        self.distanceInterpolatorBlock.linkTo(self.minimumFilterBlock)
        self.minimumFilterBlock.linkTo(self.baselineFilterBlock)
        self.baselineFilterBlock.linkTo(self.peakJoinerBlock.inputs[0])
        self.ethaneDispositionBlock.linkTo(self.peakJoinerBlock.inputs[1])
        self.peakJoinerBlock.linkTo(self.peakAutoThresholdBlock)
        if self.autoThresh:
            self.peakAutoThresholdBlock.linkTo(self.peakFilterBlock)
        else:
            self.peakJoinerBlock.linkTo(self.peakFilterBlock)
        self.peakFilterBlock.linkTo(self.jsonWriterBlock)

class EthanePipelineApp(Application):
    aliases = Dict(dict(config='EthanePipelineApp.config_file'))
    classes = List([EthaneComputationBlock, EthaneClassifier, VehicleExhaustClassifier])
    config_file = Unicode('', config=True, help="Name of configuration file")

    def initialize(self, argv=None):
        # These will go into the config file
        self.config.EthaneComputationBlock.methane_ethane_sdev_ratio = 0.2  # Ratio of methane conc. sdev to ethane conc. sdev
        self.config.EthaneComputationBlock.methane_ethylene_sdev_ratio = 0.09  # Ratio of methane conc. sdev to ethylene conc. sdev
        self.config.EthaneClassifier.nng_lower = 0.0  # Lower limit of ratio for not natural gas hypothesis
        self.config.EthaneClassifier.nng_upper = 0.1e-2  # Upper limit of ratio for not natural gas hypothesis
        self.config.EthaneClassifier.ng_lower = 2e-2  # Lower limit of ratio for natural gas hypothesis
        self.config.EthaneClassifier.ng_upper = 10e-2  # Upper limit of ratio for natural gas hypothesis
        self.config.EthaneClassifier.nng_prior = 0.27  # Prior probability of not natural gas hypothesis
        self.config.EthaneClassifier.thresh_confidence = 0.9  # Threshold confidence level for definite hypothesis
        self.config.EthaneClassifier.reg = 0.05  # Regularization parameter
        self.config.VehicleExhaustClassifier.ve_ethylene_sdev_factor = 2.0  # Ethylene standard deviation factor for vehicle exhaust
        self.config.VehicleExhaustClassifier.ve_ethylene_lower = 0.15  # Ethylene lower level for vehicle exhaust
        self.config.VehicleExhaustClassifier.ve_ethane_sdev_factor = 0.0  # Ethane standard deviation factor for vehicle exhaust
        self.config.VehicleExhaustClassifier.ve_ethane_upper = 2.0  # Ethane upper level for vehicle exhaust
        self.parse_command_line(argv)
        if self.config_file:
            self.load_config_file(self.config_file)

    def start(self):
        filenamesToProcess = [
            #r"C:\Research\Ethane\MenloCaptures\SurveyExport_find5peaks_RFADS2003_07-04-2016-03-09-56_F_Standard.dat",
            #r"C:\Research\Ethane\MenloCaptures\SurveyExport_menlo-ana2002-1_RFADS2002_06-04-2016-18-48-18_A_Standard.dat",
            r"C:\Research\Ethane\MenloCaptures\SurveyExport_Isotopic Test_RFADS2002_04-04-2016-19-51-18_A_Standard.dat",
            #r"C:\Research\Ethane\SantaClara2\SurveyExport_santa clara 318_RFADS2047_18-03-2016-21-09-43_A_Standard.dat",
            #r"X:\For Max\Cases for Sze Mar29\Mission B2 Bodily\FEDS2037-Feb3-02-MissionB2-20160203-233502Z-DataLog_User_Minimal.dat",
            #r"X:\For Max\Cases for Sze Mar29\Mission B2 Bodily\SurveyExport_Ethane Mis B2 Bodily_RFADS2037_31-01-2016-07-55-05_F_Standard.dat",
            #r"X:\For Max\Cases for Sze Mar29\Mission B2 Bodily\SurveyExport_EthaneMisB2_RFADS2037_02-02-2016-04-34-52_F_Standard.dat",
            #r"X:\For Max\Cases for Sze Mar29\Mission B2 Bodily\SurveyExport_EthaneMissionB2S1_RFADS2037_30-12-2015-03-40-28_E_Standard.dat",
            #r"X:\For Max\Cases for Sze Mar29\Mission B2 Bodily\SurveyExport_EthaneMissionB2S2_RFADS2037_30-12-2015-04-55-31_E_Standard.dat",
            #r"X:\For Max\Cases for Sze Mar29\Mission B2 Bodily\SurveyExport_EthaneMissionB2S3_RFADS2037_30-12-2015-06-02-02_E_Standard.dat",
            #r"X:\For Max\Cases for Sze Mar29\Mission B2 Bodily\SurveyExport_Ethane_Mission_B2_2_RFADS2037_19-12-2015-04-38-01_E_Standard.dat",
            #r"X:\For Max\Cases for Sze Mar29\Mission B2 Bodily\SurveyExport_Ethane_Mission_B_1_RFADS2037_19-12-2015-03-49-14_E_Standard.dat"
        ]
        for inputFilename in filenamesToProcess:
            baseFilename = os.path.splitext(inputFilename)[0]
            dataFrame = pd.read_table(inputFilename, delim_whitespace=True, na_values=['NAN'])
            try:
                pipeline = EthanePipeline(baseFilename=baseFilename, config=self.config)
                pipeline.makeBlocks()
                pipeline.linkBlocks()
                pipeline.frameFetcherBlock.post(dataFrame)
                pipeline.frameFetcherBlock.complete()
                while not pipeline.waitCompletion(0.5):
                    pass
            except:
                print traceback.format_exc()

if __name__ == "__main__":
    app = EthanePipelineApp()
    app.initialize()
    app.start()

