#!/usr/bin/python
#
# EthaneAggregation.py implements aggregation of indications using exclusion radius
#
import json
from numpy import argsort, asarray, cos, median, pi
from traitlets import (Dict, Float, Instance, List, Unicode)
from traitlets.config.application import Application
from traitlets.config.configurable import Configurable
from Host.Pipeline.EthaneBlocks import EthaneClassifier, VehicleExhaustClassifier
from Host.Pipeline.GroupSources import CompositeVerdict, SourceAggregator

DTR = pi/180.0
EARTH_RADIUS = 6371000

class EthaneAggregation(Configurable):
    amplitude_key = Unicode("AMPLITUDE")
    disposition_key = Unicode("VERDICT")
    latitude_key = Unicode("GPS_ABS_LAT")
    longitude_key = Unicode("GPS_ABS_LONG")
    ethane_ratio_key = Unicode("ETHANE_RATIO")
    ethane_ratio_sdev_key = Unicode("ETHANE_RATIO_SDEV")
    passed_threshold_key = Unicode("PASSED_THRESHOLD")
    agg_ethane_ratio_key = Unicode("AGG_ETHANE_RATIO")
    agg_ethane_ratio_sdev_key = Unicode("AGG_ETHANE_RATIO_SDEV")
    agg_disposition_key = Unicode("AGG_VERDICT")
    agg_confidence_key = Unicode("AGG_CONFIDENCE")

    ethane_classifier = Instance(EthaneClassifier)
    source_aggregator = Instance(SourceAggregator, allow_none=True)
    composite_verdict = Instance(CompositeVerdict, allow_none=True)

    exclusion_radius = Float()
    indications = List(Dict())

    def __init__(self, **kwargs):
        super(EthaneAggregation, self).__init__(**kwargs)
        self.ethane_classifier = EthaneClassifier(config=self.config)

    def process(self):
        # Sort the indications in decreasing order of amplitude
        sorted_indications = sorted(self.indications, key=lambda k: k[self.amplitude_key], reverse=True)
        # Active indications are ones which can be aggregated and are candidates for being the representative
        #  of a group of indications within an exclusion radius
        lat_array = []
        lng_array = []
        for rank, indication in enumerate(sorted_indications):
            indication["ACTIVE"] = bool(indication[self.passed_threshold_key]) and \
                (indication[self.disposition_key] != "VEHICLE_EXHAUST")
            indication["RANK"] = rank
            indication["GROUP_RANKS"] = []
            lat_array.append(indication[self.latitude_key])
            lng_array.append(indication[self.longitude_key])
        #
        lat_array = asarray(lat_array)
        lng_array = asarray(lng_array)
        # Get median latitude for estimating distance scale via spherical earth approximation
        med_lat = median(lat_array)
        mpd_lat = DTR * EARTH_RADIUS            # Meters per degree of latitude
        mpd_lng = mpd_lat * cos(DTR * med_lat)  # Meters per degree of longitude

        # Order by longitude to find nearest neighbors
        perm = argsort(lng_array)
        for i, (lat, lng) in enumerate(zip(lat_array, lng_array)):
            # Go though active sources in order of decreasing amplitude
            if not sorted_indications[i]["ACTIVE"]:
                if sorted_indications[i][self.disposition_key] == "VEHICLE_EXHAUST":
                    sorted_indications[i][self.agg_disposition_key] = "VEHICLE_EXHAUST"
                elif not sorted_indications[i][self.passed_threshold_key]:
                    sorted_indications[i][self.agg_disposition_key] = "BELOW_THRESHOLD"
                else:
                    sorted_indications[i][self.agg_disposition_key] = "EXCLUDED"
                continue
            # Find other indications within the exclusion radius
            elow = 0
            ehigh = 0
            # If longitudes differ by more than delta_lng, we are outside the exclusion radius
            delta_lng = self.exclusion_radius / mpd_lng
            # Note that lng_array[perm[e]] is in order of increasing longitude as e is incremented
            # We find elow and ehigh so that when e is in [elow,ehigh), lng_array[perm[e]] is
            #  possibly within the exclusion radius of the point (lng,lat)
            while elow < len(perm) and lng_array[perm[elow]] < lng - delta_lng:
                elow += 1
            while ehigh < len(perm) and lng_array[perm[ehigh]] <= lng + delta_lng:
                ehigh += 1
            # Now go through candidates between elow and ehigh and use both latitude and longitude
            #  to find indications which are actually in the exclusion radius
            for e in range(elow, ehigh):
                j = int(perm[e])
                if (j < i) or not sorted_indications[j]["ACTIVE"]:
                    continue  # Exclude inactive peaks and peaks of larger amplitude than the indication of interest
                assert lng - delta_lng <= lng_array[j] < lng + delta_lng
                dx = mpd_lng * (lng - lng_array[j])
                dy = mpd_lat * (lat - lat_array[j])
                if 0 < dx * dx + dy * dy <= self.exclusion_radius ** 2:
                    # An indication "j" in the exclusion radius around indication "i" is added to the group
                    # belonging to indication i, and is no longer a candidate for being a representative.
                    # Note that sources which are classified as vehicle exhaust are excluded from joining any groups
                    if sorted_indications[j][self.disposition_key] != "VEHICLE_EXHAUST":
                        sorted_indications[i]["GROUP_RANKS"].append(j)
                        sorted_indications[j]["ACTIVE"] = False

            # Having elected the representative "i" at the center of a group, we calculate the group statistics
            #  (ethane ratio and standard deviation) from all the group members
            ethane_ratios = [sorted_indications[i][self.ethane_ratio_key]]
            ethane_ratio_sdevs = [sorted_indications[i][self.ethane_ratio_sdev_key]]
            for j in sorted_indications[i]["GROUP_RANKS"]:
                ethane_ratios.append(sorted_indications[j][self.ethane_ratio_key])
                ethane_ratio_sdevs.append(sorted_indications[j][self.ethane_ratio_sdev_key])
            self.source_aggregator = SourceAggregator(
                measurements=asarray(ethane_ratios),
                uncertainties=asarray(ethane_ratio_sdevs),
                max_sources=4,
                prior_prob_factor_per_source=0.2,
                source_range=0.5
            )
            hypotheses = self.source_aggregator.aggregate()
            assignment_result = self.source_aggregator.get_assignment(hypotheses[0])
            self.composite_verdict = CompositeVerdict()
            for group in assignment_result["groups"]:
                verdict, confidence = self.ethane_classifier.verdict(
                    ethane_ratio=group["mean"],
                    ethane_ratio_sdev=group["uncertainty"]
                )
                self.composite_verdict.add_result(verdict, group["mean"], group["uncertainty"], confidence)

            # Store the aggregated result
            sorted_indications[i][self.agg_ethane_ratio_key] = self.composite_verdict.ethane_ratio
            sorted_indications[i][self.agg_ethane_ratio_sdev_key] = self.composite_verdict.ethane_ratio_sdev
            disposition, confidence = self.composite_verdict.state, self.composite_verdict.confidence
            sorted_indications[i][self.agg_disposition_key] = disposition
            sorted_indications[i][self.agg_confidence_key] = confidence
        return sorted_indications

class EthaneAggregationApp(Application):
    aliases = Dict(dict(config='EthaneAggregationApp.config_file'))
    classes = List([EthaneClassifier, VehicleExhaustClassifier])
    config_file = Unicode('', config=True, help="Name of configuration file")

    def initialize(self, argv=None):
        # These will go into the config file
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
        self.config.VehicleExhaustClassifier.ve_ethane_upper = 10.0  # Ethane upper level for vehicle exhaust
        self.parse_command_line(argv)
        if self.config_file:
            self.load_config_file(self.config_file)

    def start(self):
        filenamesToProcess = [
            #r"C:\Research\Ethane\Flint\SurveyExport_hotel_RFADS2021_13-03-2016-21-02-13_C_Manual_indications.json"
            r"C:\Research\Ethane\SantaClara\SurveyExport_EthaneSC_AS1_RFADS2037_20-12-2015-02-42-19_E_Standard_indications.json",
            r"C:\Research\Ethane\SantaClara\SurveyExport_EthaneSC_AS2_RFADS2037_18-12-2015-05-13-02_E_Standard_indications.json",
            r"C:\Research\Ethane\SantaClara\SurveyExport_EthaneSC_AS2_RFADS2037_20-12-2015-04-39-08_E_Standard_indications.json",
            r"C:\Research\Ethane\SantaClara\SurveyExport_Ethane_Mission_A_1_RFADS2037_19-12-2015-05-44-32_E_Standard_indications.json",
            r"C:\Research\Ethane\SantaClara\SurveyExport_SantaClaraA_RFADS2037_03-01-2016-04-38-39_E_Standard_indications.json",
            r"C:\Research\Ethane\SantaClara\SurveyExport_SantaClaraA_RFADS2037_03-01-2016-07-36-48_E_Standard_indications.json",
            r"C:\Research\Ethane\SantaClara\SurveyExport_sc_A_1_RFADS2037_04-01-2016-04-45-01_E_Standard_indications.json",
            r"C:\Research\Ethane\SantaClara\SurveyExport_sc_A_1_RFADS2037_23-12-2015-02-30-05_D_Standard_indications.json",
            r"C:\Research\Ethane\SantaClara\SurveyExport_SC_A_1_RFADS2037_29-12-2015-03-16-14_F_Standard_indications.json",
            r"C:\Research\Ethane\SantaClara\SurveyExport_sc_A_2_RFADS2037_04-01-2016-06-11-29_E_Standard_indications.json",
            r"C:\Research\Ethane\SantaClara\SurveyExport_sc_A_2_RFADS2037_23-12-2015-04-20-11_D_Standard_indications.json",
            r"C:\Research\Ethane\SantaClara\SurveyExport_SC_A_2_RFADS2037_29-12-2015-04-48-01_F_Standard_indications.json"
        ]
        # Get the indications into a list of dictionaries
        indications = []
        for inputFilename in filenamesToProcess:
            with open(inputFilename, "rb") as jp:
                indications.extend(json.load(jp))
        ea = EthaneAggregation(indications=indications, exclusion_radius=20, config=self.config)
        sorted_indications = ea.process()
        with file('aggregation_output.json', "wb") as jp:
            json.dump(sorted_indications, jp, indent=2, sort_keys=True)

if __name__ == "__main__":
    app = EthaneAggregationApp()
    app.initialize()
    app.start()

