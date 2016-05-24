
import numpy as np
import pyodbc

# constructing and running query
server = "b-eng-db01.picarro.int"
database = "SurveyorEngineering"
uid = "engineering"
password = "aDs76WoiJn"
connection = pyodbc.connect('DRIVER={SQL Server}; SERVER=%s; DATABASE=%s; UID=%s; PWD=%s' %
                        (server, database, uid, password))
cursor = connection.cursor()

cursor.execute("""
    SELECT Tag, StartEpoch, EndEpoch, AnalyzerId
        FROM [SurveyorEngineering].[dbo].[Survey]
""")
surveys = cursor.fetchall()
for survey in surveys:
    startEpoch = survey[1]
    endEpoch = survey[2]
    analyzerId = survey[3]
    cursor.execute("""
        SELECT EpochTime, CarSpeedNorth, CarSpeedEast, WindSpeedLongitudinal
            FROM [SurveyorEngineering].[dbo].[Measurement] WHERE
            EpochTime > %s AND EpochTime < %s AND AnalyzerId = '%s'
    """ % (startEpoch, endEpoch, analyzerId))
    maxSpeed = []
    for row in cursor:
        if row[1] is not None:
            carSpeed = abs(row[1]+1j*row[2])
            wsLon = row[3]
            maxSpeed.append(abs(carSpeed - wsLon))
    if maxSpeed:
        print "%s, %.2f" % (survey[0], max(maxSpeed))
    
