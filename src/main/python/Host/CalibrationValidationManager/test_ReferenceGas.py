import unittest
from StringIO import StringIO
from pprint import pprint
from Host.Common.configobj import ConfigObj
from ReferenceGas import GasEnum, ComponentGas, ReferenceGas

class TestReferenceGas(unittest.TestCase):

    def setUp(self):
        pass

    def test_component_init(self):
        cg = ComponentGas()
        self.assertIsInstance(cg, ComponentGas)

    def test_component_gas_setGetGasType(self):
        # Test to set/get a valid gas enum type
        for gasVarName, gasEnum in GasEnum.__members__.items():
            cg = ComponentGas()
            cg.setGasType(gasEnum)
            self.assertEqual(cg.getGasType(), gasEnum)
        # Test if we can set the gas enum type with a properly
        # formatted name, e.g. "CH4" is converted to GasEnum.CH4
        for gasVarName, gasEnum in GasEnum.__members__.items():
            cg = ComponentGas()
            cg.setGasType(gasVarName)
            self.assertEqual(cg.getGasType(), gasEnum)
        # Test if a bad input name raises and exception
        for gasVarName, gasEnum in GasEnum.__members__.items():
            cg = ComponentGas()
            with self.assertRaises(AttributeError):
                cg.setGasType(gasVarName + "_")

    def test_reference_gas_init(self):
        co = ConfigObj("./task_manager.ini")
        rg = ReferenceGas(co["GASES"]["GAS0"])
        self.assertIsInstance(rg, ReferenceGas)

    def test_reference_gas_getGasConcPpm(self):
        co = ConfigObj("./task_manager.ini")
        rg = ReferenceGas(co["GASES"]["GAS0"])
        input_conc = co["GASES"]["GAS0"]["Concentration"][0]
        output_conc = rg.getGasConcPpm(GasEnum.CH4)
        self.assertEqual(input_conc, output_conc)

if __name__ == '__main__':
    unittest.main()

