import collections
from enum import Enum
from terminaltables import AsciiTable

class GasEnum(Enum):
    Air = 1
    CH4 = 2
    CO2 = 3
    CO = 4
    O2 = 5
    NH3 = 6
    H2O = 7

# ComponentGas
# Object to contain the details of one gas component in a mixture.
# For example if the reference gas is zero air, one component might be CO2
# and information about it, like concentration, would be stored in a
# ComponentGas object.
#
class ComponentGas(object):
    def __init__(self):
        self.gasName = ""           # Human readable name, free form
        self.gasType = ""           # GasEnum enum for defined gases
        self.gasConcPpm = 0.0       # Vendor reported gas conc in PPM
        self.gasAccPercent = 0.0    # Vendor reproted gas accuracy/uncertainty in %.
                                    # Usual vendor values are 0.5, 1, 2, 5 %
        return

    def setGasType(self, type):
        """
        Set the GasEnum enum.
        If type is a GasEnum enum confirm that it exists, throw an error if it doesn't.
        If the type is a string (molecule name), see if we can match to a known GasEnum enum.
        Throw an error if there is no match.
        :param type: Can be a GasEnum enum or a string.
        :return: Nothing
        """

        # See if type is a valid GasEnum enum.
        # If not, see if type is a string that matches one of the defined gases in GasEnum.
        if type in list(GasEnum):
            self.gasType = type
        else:
            for name, member in GasEnum.__members__.items():
                if type == name:
                    self.gasType = member

        if self.gasType is "":
            #print("Failed to assign gastype. %s is not a valid type." %type)
            raise AttributeError
            # exit(1)
        return

    def getGasType(self):
        return self.gasType

    def setGasConcPpm(self, conc):
        self.gasConcPpm = conc
        return

    def getGasConcPpm(self):
        return self.gasConcPpm

    def setGasAccPercent(self, acc):
        self.gasAccPercent = acc
        return

    def getGasAccPercent(self):
        return self.gasAccPercent

# ReferenceGas
# Represents a gas source that has one or more ComponentGas object.
# This object also contains information about the source such as
# the vendor name and serial number.
#
class ReferenceGas(object):
    def __init__(self, gasDict, key = ""):
        self.key = key          # Key (or section name like GAS0) in the ini file
        self.tankName = ""      # Human readable name like '2ppm CH4 in N2', free form
        self.tankVendor = ""    # Supplier
        self.tankSN = ""        # Tank serial number or some other unique identifier
        self.tankDesc = ""      # Free form field for any user input
        self.gasDict = gasDict  # Save the dict for writing changes back to disk
        self.zeroAir = "No"     # Zero Air needs special treatment in the analysis, use as a string, "Yes" or "No"

        # Store the component gases in the order that they appear in the task
        # manager ini file.  The order here sets the order that the gases appear in
        # the reference gas editor GUI.  It is assumed that the first component is
        # the molecule that we want to measure.
        self.components = collections.OrderedDict()    # Collection of GasComponent objects

        if "Name" in gasDict:
            self.tankName = gasDict["Name"]
        if "SN" in gasDict:
            self.tankSN = gasDict["SN"]
        if "Zero_Air" in gasDict:
            self.zeroAir = gasDict["Zero_Air"]

        # Loop through the list of component gases in this gas mix.
        # The concentration field is required but accuracy is optional.
        # If the list of accuracies is missing, we create a default version.
        # Components, Centrations, and Accuracy must have the same number
        # of elements.
        #
        component = []
        concentration = []
        uncertainty = []

        try:
            if isinstance(gasDict["Component"], list):
                component.extend(gasDict["Component"])
            else:
                component.append(gasDict["Component"])
        except KeyError as e:
            print("ReferenceGas.py - no defined component gases. Exception: %s" %e)
            exit(1)

        try:
            if isinstance(gasDict["Concentration"], list):
                list1 = [0.0 if (i < 0 or i > 1e6) else i for i in gasDict["Concentration"]]
                print("list:",list1)
                concentration.extend(gasDict["Concentration"])
            else:
                if float(gasDict["Concentration"]) >= 0 and float(gasDict["Concentration"]) <= 1e6:
                    concentration.append(gasDict["Concentration"])
                else:
                    concentration.append(0.0)
        except KeyError as e:
            print("ReferenceGas.py - no defined gas concentrations. Exception: %s" %e)
            exit(1)

        try:
            if isinstance(gasDict["Uncertainty"], list):
                uncertainty.extend(gasDict["Uncertainty"])
            else:
                uncertainty.append(gasDict["Uncertainty"])
        except KeyError as e:
            uncertainty = ["Unk"] * len(component)

        if not component  or not concentration:
            print("ReferenceGas.py - A gas component or concentration field is empty.")
            exit(1)
        if len(component) != len(concentration):
            print("ReferenceGas.py - The number of gas components and concentrations is not equal.")
            exit(1)

        for idx, elem in enumerate(component):
            cg = ComponentGas()
            cg.setGasType(component[idx])
            cg.setGasConcPpm(concentration[idx])
            # cg.setGasAccPpm(uncertainty[idx])
            cg.setGasAccPercent(uncertainty[idx])
            self.components[cg.getGasType()] = cg

        return

    def getGasConcPpm(self, gasEnum):
        return self.components[gasEnum].getGasConcPpm()

    # def getGasAccPpm(self, gasEnum):
    #     return self.components[gasEnum].getGasAccPpm()

    def getGasAccPercent(self, gasEnum):
        return self.components[gasEnum].getGasAccPercent()

    def get_reference_gas_for_qtable(self):
        """
        Create an ordered dict of the reference gas attributes.  The keys need
        to be human readable as these are passed to the reference gas editor GUI.
        The order is important so that the display order always matches the
        manual screen shots.
        :return:
        """
        d = collections.OrderedDict()
        d["Name"] = self.tankName
        d["SN"] = self.tankSN
        d["Desc"] = self.tankDesc
        d["Vendor"] = self.tankVendor
        d["Zero_Air"] = self.zeroAir
        for gas_enum, component_gas in self.components.items():
            d[gas_enum.name] = component_gas.getGasConcPpm()
            d[gas_enum.name + " acc."] = component_gas.getGasAccPercent()
        return d

    def getGasDetails(self):
        d = {} #collections.OrderedDict()
        d["Tank_Name"] = self.tankName
        d["Tank_Serial_Number"] = self.tankSN
        d["Tank_Description"] = self.tankDesc
        d["Tank_Vendor"] = self.tankVendor
        d["Zero_Air"] = self.zeroAir
        d["Gas"] = []
        for gas_enum, component_gas in self.components.items():
            d["Gas"].append([gas_enum.name, component_gas.getGasConcPpm(), component_gas.getGasAccPercent()])
        return d

    def getFormattedGasDetails(self, key):
        d = self.getGasDetails()
        table_data = []
        table_data.append(["Gas Cylinder Name", self.tankName])
        table_data.append(["Gas Cylinder Serial Number", self.tankSN])
        table_data.append(["Zero Air", self.zeroAir])
        for i, [gas_name, gas_conc, conc_acc] in enumerate(d["Gas"]):
            if i == 0:
                table_data.append(["Gas Composition", "[{0}] {1:10.3f} ppm +/- {2:<8}".format(gas_name, float(gas_conc), conc_acc)])
            else:
                table_data.append(["", "[{0}] {1:10.3f} ppm +/- {2:<8}".format(gas_name, float(gas_conc), conc_acc)])
        table = AsciiTable(table_data)
        table.title = key
        table.inner_heading_row_border = False
        return table.table + "\n"