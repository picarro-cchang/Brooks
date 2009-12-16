description = {}

description["200001"] = {"Title": """Dummy test for debugging""",\
"Descr":"This is a dummy test for debugging the report generation software." }

description["201001"] = {"Title": """Logic Board Laser 1 Laser Current Drive""",\
"Descr":"This steps the laser current for laser 1 and records the results." }

description["201002"] = {"Title": """Logic Board Laser 1 TEC Drive""",\
"Descr":"This steps the TEC current for laser 1 and records the results." }

description["201003"] = {"Title": """Logic Board Laser 1 thermistor test""",\
"Descr":"This steps the current through thermistor resistor for laser 1 and records the results." }

description["202001"] = {"Title": """Logic Board Laser 2 Laser Current Drive""",\
"Descr":"This steps the laser current for laser 2 and records the results." }

description["202002"] = {"Title": """Logic Board Laser 2 TEC Drive""",\
"Descr":"This steps the TEC current for laser 2 and records the results." }

description["202003"] = {"Title": """Logic Board Laser 2 thermistor test""",\
"Descr":"This steps the current through thermistor resistor for laser 2 and records the results." }

description["203001"] = {"Title": """Logic Board Laser 3 Laser Current Drive""",\
"Descr":"This steps the laser current for laser 3 and records the results." }

description["203002"] = {"Title": """Logic Board Laser 3 TEC Drive""",\
"Descr":"This steps the TEC current for laser 3 and records the results." }

description["203003"] = {"Title": """Logic Board Laser 3 thermistor test""",\
"Descr":"This steps the current through thermistor resistor for laser 3 and records the results." }

description["204001"] = {"Title": """Logic Board Laser 4 Laser Current Drive""",\
"Descr":"This steps the laser current for laser 4 and records the results." }

description["204002"] = {"Title": """Logic Board Laser 4 TEC Drive""",\
"Descr":"This steps the TEC current for laser 4 and records the results." }

description["204003"] = {"Title": """Logic Board Laser 4 thermistor test""",\
"Descr":"This steps the current through thermistor resistor for laser 4 and records the results." }

reportFilename = "report.txt"
htmlReportFilename = "report.html"

reportTemplate = """
G2000 integration test report
=============================
.. contents::
.. sectnum::

Instrument Summary
------------------

:Name: *Please fill in instrument details by editing report.txt*
"""
