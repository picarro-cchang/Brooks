
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
