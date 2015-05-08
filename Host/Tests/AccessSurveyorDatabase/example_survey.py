
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

# Get table names
cursor.execute("""
    SELECT DISTINCT TABLE_NAME
        FROM [SurveyorEngineering].INFORMATION_SCHEMA.COLUMNS
""")
print "\nTables Available"
for row in cursor:
    print row


# Get analyzer table column names
cursor.execute("""
    SELECT COLUMN_NAME
        FROM [SurveyorEngineering].INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'Analyzer'
""")

print "\nAnalyzer table columns"
for row in cursor:
    print row

# Get analyzer names and Id
cursor.execute("""
    SELECT SerialNumber, Id
        FROM [SurveyorEngineering].[dbo].[Analyzer]
""")

print "\nAnalyzers in database"
for row in cursor:
    print row

# Get measurement table column names
print "\nMeasurement table columns"
cursor.execute("""
    SELECT COLUMN_NAME
        FROM [SurveyorEngineering].INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'Measurement'
""")

for row in cursor:
    print row
    
# Get survey table column names
print "\nSurvey table columns"
cursor.execute("""
    SELECT COLUMN_NAME
        FROM [SurveyorEngineering].INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'Survey'
""")

for row in cursor:
    print row
        
# Get surveys
print "\nSurveys"
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
    
