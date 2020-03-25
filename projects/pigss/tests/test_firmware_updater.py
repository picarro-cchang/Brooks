import utilities.firmware_updater as firmware_updater
from unittest.mock import Mock, patch, MagicMock
import os
os.environ["QT_QPA_PLATFORM"] = "offscreen"  # allows to run unittests headless
from qtpy import QtCore


fake_hardware_meta = {"Serial_Devices": {
    "/dev/ttyACM0": {
        "Driver": "NumatoDriver",
        "Path": "/dev/ttyACM0",
        "Baudrate": 19200,
        "Numato_ID": 0,
        "RPC_Port": 33030
    },
    "/dev/ttyUSB0": {
        "Driver": "AlicatDriver",
        "Path": "/dev/ttyUSB0",
        "Baudrate": 19200,
        "RPC_Port": 33020
    },
    "/dev/ttyUSB1": {
        "Driver": "PigletDriver",
        "Bank_ID": 1,
        "Topaz_A_SN": "104",
        "Topaz_B_SN": "105",
        "Manifold_SN": "A157UT4W",
        "Manifold_FW": "1.1.9",
        "Whitfield_SN": "SN8",
        "Path": "/dev/ttyUSB1",
        "Baudrate": 230400,
        "RPC_Port": 33040
    },
    "/dev/ttyUSB2": {
        "Driver": "PigletDriver",
        "Bank_ID": 2,
        "Topaz_A_SN": "104",
        "Topaz_B_SN": "105",
        "Manifold_SN": "A157UT4W",
        "Manifold_FW": "1.1.999",
        "Whitfield_SN": "SN8987",
        "Path": "/dev/ttyUSB2",
        "Baudrate": 230400,
        "RPC_Port": 33041
    }
}
}


def set_up(qtbot):
    window = firmware_updater.FirmwareUpdateWidget()
    qtbot.addWidget(window, before_close_func=window.about_to_close)
    window.show()
    qtbot.waitForWindowShown(window)
    return window, qtbot


@patch('utilities.firmware_updater.check_for_piggs_core_status', new=MagicMock(return_value=True))
def test_pigss_services_status_active(qtbot):
    """
        Test to check correct label
    """
    window, qtbot = set_up(qtbot)
    qtbot.wait(10)
    assert window.dynamic_piggs_core_status_label.text() == "ACTIVE"


@patch('utilities.firmware_updater.check_for_piggs_core_status', new=MagicMock(return_value=False))
def test_pigss_services_status_not_active(qtbot):
    """
        Test to check correct label
    """
    window, qtbot = set_up(qtbot)
    qtbot.wait(10)
    assert window.dynamic_piggs_core_status_label.text() == "NOT ACTIVE"


@patch('utilities.firmware_updater.check_for_piggs_core_status', new=MagicMock(return_value=False))
def test_scan(qtbot):
    """
        Test to check that after scanning for hardware 
        utility will create appropriate amount of widgets
    """
    fake_serialmapper_to_returned = MagicMock()
    serialmapper = MagicMock(return_value=fake_serialmapper_to_returned)

    fake_serialmapper_to_returned.get_usb_serial_devices = Mock(return_value=fake_hardware_meta)
    with patch('back_end.madmapper.usb.serialmapper.SerialMapper', new=serialmapper):
        window, qtbot = set_up(qtbot)
        qtbot.wait(10)
        qtbot.mouseClick(window.btn_scan_for_hardware, QtCore.Qt.LeftButton)
        qtbot.wait(2000)
        assert (len(window.piggles_widgets) == 2)

        qtbot.mouseClick(window.btn_scan_for_hardware, QtCore.Qt.LeftButton)
        qtbot.wait(2000)
        assert (len(window.piggles_widgets) == 2)


@patch('utilities.firmware_updater.check_for_piggs_core_status', new=MagicMock(return_value=False))
def test_bank_id_flush(qtbot):
    """
        Test flushing down the bank id for the piglet
    """
    fake_serialmapper_to_returned = MagicMock()
    serialmapper = MagicMock(return_value=fake_serialmapper_to_returned)
    fake_serialmapper_to_returned.get_usb_serial_devices = Mock(return_value=fake_hardware_meta)

    fake_piglet_driver_to_be_returned = MagicMock()
    fake_piglet_driver = MagicMock(return_value=fake_piglet_driver_to_be_returned)
    with patch('back_end.madmapper.usb.serialmapper.SerialMapper', new=serialmapper):
        with patch('back_end.piglet.piglet_driver.PigletBareDriver', new=fake_piglet_driver):
            window, qtbot = set_up(qtbot)
            qtbot.wait(10)
            qtbot.mouseClick(window.btn_scan_for_hardware, QtCore.Qt.LeftButton)

            def wait_until_piggles_widgets_loaded():
                assert (len(window.piggles_widgets) == 2)
            qtbot.waitUntil(wait_until_piggles_widgets_loaded, timeout=2000)
            PigletWidget = window.piggles_widgets[0]

            PigletWidget.bank_id_cb.setCurrentText("2")

            qtbot.mouseClick(PigletWidget.btn_bank_id_flush, QtCore.Qt.LeftButton)
            qtbot.wait(1000)
            fake_piglet_driver_to_be_returned.set_slot_id.assert_called_with(2)


@patch('utilities.firmware_updater.check_for_piggs_core_status', new=MagicMock(return_value=False))
def test_flashing_firmware(qtbot):
    """
        Test to flashing firmware
    """
    fake_serialmapper_to_returned = MagicMock()
    serialmapper = MagicMock(return_value=fake_serialmapper_to_returned)
    fake_serialmapper_to_returned.get_usb_serial_devices = Mock(return_value=fake_hardware_meta)

    with patch('back_end.madmapper.usb.serialmapper.SerialMapper', new=serialmapper):
        window, qtbot = set_up(qtbot)
        qtbot.wait(10)
        qtbot.mouseClick(window.btn_scan_for_hardware, QtCore.Qt.LeftButton)

        def wait_until_piggles_widgets_loaded():
            assert (len(window.piggles_widgets) == 2)
        qtbot.waitUntil(wait_until_piggles_widgets_loaded, timeout=2000)
        PigletWidget = window.piggles_widgets[0]

        fake_fw_file_path = "/fake/file/path.hex"
        PigletWidget.fw_file_path = fake_fw_file_path

        fake_subprocess = MagicMock()
        with patch('subprocess.call', new=fake_subprocess):
            PigletWidget.on_btn_fw_flash_click()
            qtbot.wait(10)
            fake_subprocess.assert_called()


def test_check_for_pigss_status(qtbot):
    """
        Test detecting pigss process running or not
    """
    assert not firmware_updater.check_for_piggs_core_status()

    with patch('utilities.firmware_updater.process_triggers', new=[""]):
        assert firmware_updater.check_for_piggs_core_status()


def test_qthreads():
    """
        Test qthreads properly executed
    """
    parent = MagicMock()
    fake_serialmapper_to_returned = MagicMock()
    serialmapper = MagicMock(return_value=fake_serialmapper_to_returned)

    fake_serialmapper_to_returned.get_usb_serial_devices = Mock(return_value=fake_hardware_meta)
    with patch('back_end.madmapper.usb.serialmapper.SerialMapper', new=serialmapper):

        thread = firmware_updater.ScanHardwareThread(parent)
        thread.run()
        fake_serialmapper_to_returned.get_usb_serial_devices.assert_called()

        fake_subprocess = MagicMock()
        with patch('subprocess.call', new=fake_subprocess):
            thread = firmware_updater.FlashTheFirmwareThread(parent,
                                                             fake_hardware_meta["Serial_Devices"]["/dev/ttyUSB1"],
                                                             "/fake/file/path.hex")
            thread.run()
            fake_subprocess.assert_called()

        fake_piglet_driver_to_be_returned = MagicMock()
        fake_piglet_driver = MagicMock(return_value=fake_piglet_driver_to_be_returned)
        with patch('back_end.piglet.piglet_driver.PigletBareDriver', new=fake_piglet_driver):
            thread = firmware_updater.FlushBankIDThread(parent,
                                                        fake_hardware_meta["Serial_Devices"]["/dev/ttyUSB1"],
                                                        "8")
            thread.run()
            fake_piglet_driver_to_be_returned.set_slot_id.assert_called_with(8)
