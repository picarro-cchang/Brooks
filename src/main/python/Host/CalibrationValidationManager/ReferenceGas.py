from enum import Enum
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
        self.gasName = ""       # Human readable name, free form
        self.gasType = ""       # GasEnum enum for defined gases
        self.gasConcPpm = 0.0   # Vendor reported gas conc in PPM
        self.gasAccPpm = 0.0    # Vendor reproted gas accuracy/uncertainty in PPM
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

    def setGasAccPpm(self, acc):
        self.gasAccPpm = acc
        return

    def getGasAccPpm(self):
        return self.gasAccPpm

# ReferenceGas
# Represents a gas source that has one or more ComponentGas object.
# This object also contains information about the source such as
# the vendor name and serial number.
#
class ReferenceGas(object):
    def __init__(self, gasDict):
        # print("initializing Reference Gas", gasDict)
        self.tankName = ""      # Human readable name like '2ppm CH4 in N2', free form
        self.tankVendor = ""    # Supplier
        self.tankSN = ""        # Tank serial number or some other unique identifier
        self.tankDesc = ""      # Free form field for any user input
        self.components = {}    # Collection of GasComponent objects

        if "Name" in gasDict:
            self.tankName = gasDict["Name"]
        if "SN" in gasDict:
            self.tankSN = gasDict["SN"]

        # Loop through the list of component gases in this gas mix.
        # The concentration field is required but accuracy is optional.
        # If the list of accuracies is missing, we create a default version.
        # Components, Centrations, and Accuracy must have the same number
        # of elements.
        #
        component = []
        concentration = []
        accuracy = []

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
                concentration.extend(gasDict["Concentration"])
            else:
                concentration.append(gasDict["Concentration"])
        except KeyError as e:
            print("ReferenceGas.py - no defined gas concentrations. Exception: %s" %e)
            exit(1)

        try:
            if isinstance(gasDict["Accuracy"], list):
                accuracy.extend(gasDict["Accuracy"])
            else:
                accuracy.append(gasDict["Accuracy"])
        except KeyError as e:
            accuracy = ["UNK"] * len(component)

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
            cg.setGasAccPpm(accuracy[idx])
            self.components[cg.getGasType()] = cg

        return

    def getGasConcPpm(self, gasEnum):
        return self.components[gasEnum].getGasConcPpm()

    def getGasAccPpm(self, gasEnum):
        return self.components[gasEnum].getGasAccPpm()

