
def welcome_text(gasName, gasConcs):
    g0, g1, g2 = gasConcs
    str = "<h1><center>Welcome to the {0} Surrogate Gas Validation Tool</center></h1>".format(gasName)
    str += """<p>The Picarro Surrogate Gas Validation Tool guides users through one of three Validation Procedures that 
    use zero air and/or the appropriate surrogate gas as a stable proxy for the target species. 
    Instrument Validation requires the following supplies:<p>
    <ul>
        <li>Up to four cylinders of input gases:</li>
            <ul>
            <li>1 Gas Validation: 1 {0} standard cylinder</li>
            <li>2 Gas Span Validation: One cylinder of zero air and one or two {0} standard cylinders</li>
            <li>3 or 4 Gas Linear Regression Validation: One cylinder of zero air and two or three {0} standard cylinders (Recommended concentrations: {1} ppm, {2} ppm, {3} ppm)</li>
            </ul>
        <li>Up to four regulators (one for each cylinder being used). Each regulator should be capable of accurately delivering 2-3 psig (0.1-0.2 bar) of line pressure.</li>
        <li>Sufficient tubing to connect the regulator(s) to the instrument. We recommend using &frac14;" OD PTFE or PFA tubing.</li>
        <li>Suitable adjustable or fixed wrenches for making gas-line connections.</li>
    </ul>
    To create input options, select Show Editors below and enter the requested information for each cylinder used. <p>
    After cylinder details are entered, select Validation Type and the input source for each of the four available Tasks.
    Any of the four Tasks may be skipped by selecting SKIP. When Validation Type and Task Sequence is confirmed, select Start Run below to proceed with the Validation Procedure.
    """.format(gasName, g0, g1, g2)
    return str

def editor_instructions(gasName):
    str = "<h1><center>Editor Instructions</center></h1>"

    str += """
    Instrument validation requires up to four cylinders of input gases:
    <ul>
        <li>Gas Validation: 1 {0} standard cylinder</li>
        <li>Gas Span Validation: One cylinder of zero air and one or two {0} standard cylinders</li>
        <li>3 or 4 Gas Linear Regression Validation: One cylinder of zero air and two or three {0} standard cylinders (Recommended concentrations: Xppm, XXppm, XXXppm)</li>
    </ul>
    Use the Reference Gas Editor to enter the following information from each cylinder's Certificate of Accuracy:
    <ul>
        <li>Name: assign an identifier to the cylinder (e.g. 'Zero Air')</li>
        <li>SN: vendor-issued identifier for the cylinder (e.g. item number, lot number, etc.)</li>
        <li>Zero_Air: If the cylinder contains zero air, select between 'Ultra Zero' and 'Standard Zero', otherwise, select 'No'</li>
        <li>{0} ppm: Enter the concentration listed on the cylinder's Certificate in ppm</li>
        <li>{0} acc: Select the accuracy listed on the cylinder from the drop-down menu</li>
        </ul>
    After cylinder details are entered, click on Save to store the cylinder information. In the Task Editor, 
    select Validation Type and the input source for each of the four available Tasks. Any of the four Tasks may be 
    skipped by selecting 'Skip'. When Validation Type and Task Sequence are configured, click on Save in the Task 
    Editor to confirm the changes. Select Start Run below to proceed with the Validation Procedure. 
    """.format(gasName)
    return str

def equilibrating_text(gasName):
    str = """
    <br><br><br><center>
    Waiting for {0} to equilibrate before measuring...
    </center>
    """.format(gasName)
    return str

def measuring_text(gasName):
    str = "<br><br><br><center>Measuring {0}...".format(gasName)
    return str

def pre_task_instructions(gasSource):
    str = """
    <br><br><br><center>
    Attach a regulator to the source "{}" with the output pressure set to zero. Open the cylinder valve 
    and adjust the output line pressure to 2-3psig (0.1-0.2 bar).
    After connecting the gas line to the instrument, click NEXT below.
    </center>
    """.format(gasSource)
    return str

def post_task_instructions():
    str = "<br><br><br><center>Close the valve on the gas source and disconnect the line from the analyzer. Click NEXT to proceed..</center>"
    return str

def job_complete_text():
    str = """
    <br><br><br><center>Validation Procedure Completed<br><br>
    Select VIEW REPORT to view the results of the Validation Procedure.<br><br>
    To save a copy on an external drive, select DOWNLOAD REPORT.<br><br>
    To run another Validation Procedure, select the appropriate procedure and tasks in the Task Editor and select START RUN.
    </center>
    """
    return str