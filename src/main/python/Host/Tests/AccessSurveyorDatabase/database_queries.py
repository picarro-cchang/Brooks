import numpy as np
import pyodbc

def getAnalyzerId(analyzer):
    
    # constructing and running query
    server = "b-eng-db01.picarro.int"
    database = "SurveyorEngineering"
    uid = "engineering"
    password = "aDs76WoiJn"
    connection = pyodbc.connect('DRIVER={SQL Server}; SERVER=%s; DATABASE=%s; UID=%s; PWD=%s' %
                            (server, database, uid, password))
    cursor = connection.cursor()
    
    analyzerId = None
    cursor.execute("""
        SELECT Id
            FROM [SurveyorEngineering].[dbo].[Analyzer]
            WHERE SerialNumber = '%s'
    """ % analyzer)
    for row in cursor:
        analyzerId = row[0]
    return analyzerId

def getSurveysForAnalyzer(analyzer,center,radius,num_points=20):
    
    angles = np.linspace(0.0,2*np.pi,num_points+1)[:-1]
    vectors = [cmath.rect(radius,angles[i]) for i in xrange(len(angles))]
    outline = [coordinatePlusDistance(center,vectors[i].real,vectors[i].imag)
              for i in xrange(len(vectors))]
    outline.append(outline[0])
    lat , lng = zip(*outline)
    outline = zip(lng,lat)
    
    analyzer_ID = getAnalyzerId(analyzer)
    
    server = "b-eng-db01.picarro.int"
    database = "SurveyorEngineering"
    uid = "engineering"
    password = "aDs76WoiJn"
    connection = pyodbc.connect('DRIVER={SQL Server}; SERVER=%s; DATABASE=%s; UID=%s; PWD=%s' %
                            (server, database, uid, password))
    cursor = connection.cursor()
    
    surveys = []
    start_epochs = []
    end_epochs = []
    cursor.execute("""
    
        declare @bounds geometry = geometry::STGeomFromText('POLYGON((%s))', 4326);
    
        SELECT DISTINCT Segment.SurveyId , Survey.StartEpoch, Survey.EndEpoch
        FROM     Segment INNER JOIN
                          Survey ON Segment.SurveyId = Survey.Id
        WHERE  (Segment.Shape.MakeValid().STIntersects(@bounds) = 1)
        AND   (Survey.AnalyzerId='%s')
        
    """ % (','.join([str(v[0])+' '+str(v[1]) for v in outline ]),analyzer_ID))
    for row in cursor:
        surveys.append(row[0])
        start_epochs.append(row[1])
        end_epochs.append(row[2])
        
    return surveys , start_epochs , end_epochs

 def getRelevantSurveyData(start_epoch,end_epoch,analyzer,center,radius,num_points):
    
    angles = np.linspace(0.0,2*np.pi,num_points+1)[:-1]
    vectors = [cmath.rect(radius,angles[i]) for i in xrange(len(angles))]
    outline = [coordinatePlusDistance(center,vectors[i].real,vectors[i].imag)
              for i in xrange(len(vectors))]
    outline.append(outline[0])
    lat , lng = zip(*outline)
    outline = zip(lng,lat)
    
    analyzer_ID = getAnalyzerId(analyzer)
    
    server = "b-eng-db01.picarro.int"
    database = "SurveyorEngineering"
    uid = "engineering"
    password = "aDs76WoiJn"
    connection = pyodbc.connect('DRIVER={SQL Server}; SERVER=%s; DATABASE=%s; UID=%s; PWD=%s' %
                            (server, database, uid, password))
    cursor = connection.cursor()
    
    min_data = {
    'EPOCH_TIME':[],
    'CH4': [],
    'GPS_ABS_LAT': [],
    'GPS_ABS_LONG': [],
    'CAR_VEL_N': [],
    'CAR_VEL_E': [],
    'WS_WIND_LAT': [],
    'WS_WIND_LON': [],
    'WIND_N': [],
    'WIND_E': [],
    'WIND_DIR_SDEV': [],
    }
    
    cursor.execute("""
    
        declare @bounds geometry = geometry::STGeomFromText('POLYGON((%s))', 4326);
    
        SELECT [EpochTime]
              ,[GpsLatitude]
              ,[GpsLongitude]
              ,[CarSpeedNorth]
              ,[CarSpeedEast]
              ,[WindSpeedNorth]
              ,[WindSpeedEast]
              ,[WindDirectionStdDev]
              ,[WindSpeedLateral]
              ,[WindSpeedLongitudinal]
              ,[CH4]
        FROM [SurveyorEngineering].[dbo].[Measurement]
        WHERE (EpochTime BETWEEN '%s' AND '%s')
        AND (AnalyzerId = '%s')
        AND (Shape.STIntersects(@bounds) = 1)
        AND (GpsFit=2)
        
    """ % (','.join([str(v[0])+' '+str(v[1]) for v in outline ]),str(start_epoch),str(end_epoch),analyzer_ID))
    
    for row in cursor:
        min_data['EPOCH_TIME'].append(row[0])
        min_data['GPS_ABS_LAT'].append(row[1])
        min_data['GPS_ABS_LONG'].append(row[2])
        min_data['CAR_VEL_N'].append(row[3])
        min_data['CAR_VEL_E'].append(row[4])
        min_data['WIND_N'].append(row[5])
        min_data['WIND_E'].append(row[6])
        min_data['WIND_DIR_SDEV'].append(row[7])
        min_data['WS_WIND_LAT'].append(row[8])
        min_data['WS_WIND_LON'].append(row[9])
        min_data['CH4'].append(row[10])
    for key in min_data.keys():
        min_data[key] = np.asarray(min_data[key])[::-1]
    min_data['CAR_SPEED'] = np.sqrt(min_data['CAR_VEL_N']**2+min_data['CAR_VEL_E']**2)
    
    return min_data

def getSurveyMinData(start_epoch,end_epoch,analyzer,plot=False):
    
    analyzer_ID = getAnalyzerId(analyzer)
    
    server = "b-eng-db01.picarro.int"
    database = "SurveyorEngineering"
    uid = "engineering"
    password = "aDs76WoiJn"
    connection = pyodbc.connect('DRIVER={SQL Server}; SERVER=%s; DATABASE=%s; UID=%s; PWD=%s' %
                            (server, database, uid, password))
    cursor = connection.cursor()
    
    min_data = {
    'EPOCH_TIME':[],
    'CH4': [],
    'GPS_ABS_LAT': [],
    'GPS_ABS_LONG': [],
    'CAR_VEL_N': [],
    'CAR_VEL_E': [],
    'WS_WIND_LAT': [],
    'WS_WIND_LON': [],
    'WIND_N': [],
    'WIND_E': [],
    'WIND_DIR_SDEV': [],
    }
    
    cursor.execute("""
    
        SELECT [EpochTime]
              ,[GpsLatitude]
              ,[GpsLongitude]
              ,[CarSpeedNorth]
              ,[CarSpeedEast]
              ,[WindSpeedNorth]
              ,[WindSpeedEast]
              ,[WindDirectionStdDev]
              ,[WindSpeedLateral]
              ,[WindSpeedLongitudinal]
              ,[CH4]
        FROM [SurveyorEngineering].[dbo].[Measurement]
        WHERE (EpochTime BETWEEN '%s' AND '%s')
        AND (AnalyzerId = '%s')
        AND (GpsFit=2)
        
    """ % (str(start_epoch),str(end_epoch),analyzer_ID))
    
    for row in cursor:
        min_data['EPOCH_TIME'].append(row[0])
        min_data['GPS_ABS_LAT'].append(row[1])
        min_data['GPS_ABS_LONG'].append(row[2])
        min_data['CAR_VEL_N'].append(row[3])
        min_data['CAR_VEL_E'].append(row[4])
        min_data['WIND_N'].append(row[5])
        min_data['WIND_E'].append(row[6])
        min_data['WIND_DIR_SDEV'].append(row[7])
        min_data['WS_WIND_LAT'].append(row[8])
        min_data['WS_WIND_LON'].append(row[9])
        min_data['CH4'].append(row[10])
        
    for key in min_data.keys():
        a = np.asarray(min_data[key],dtype=np.float)
        is_nan = np.isnan(a)
        if np.any(is_nan):
            good = np.where(is_nan==False)[0]
            bad = np.where(is_nan==True)[0]
            i = np.arange(a.size,dtype=np.int)
            a[bad] = np.interp(i[bad],i[good],a[good])
        min_data[key] = a
        
    if plot:
        plt.figure()
        plt.plot(min_data['GPS_ABS_LONG'],min_data['GPS_ABS_LAT'])
        plt.show()
    
    min_data['CAR_SPEED'] = np.sqrt(min_data['CAR_VEL_N']**2+min_data['CAR_VEL_E']**2)
    
    lat1 = min_data['GPS_ABS_LAT'][:-1]
    lng1 = min_data['GPS_ABS_LONG'][:-1]
    lat2 = min_data['GPS_ABS_LAT'][1:]
    lng2 = min_data['GPS_ABS_LONG'][1:]
    dist = haversine_vectorized(lat1,lng1,lat2,lng2)
    dist = np.cumsum(dist)
    dist = np.insert(dist,0,0.0)
    min_data['DISTANCE'] = dist
    
    return min_data

def get_backtraj_data(analyzer,epoch_time,duration):
    
    epoch_times = []
    lats = []
    lngs = []
    car_vel_norths = []
    car_vel_easts = []
    wind_lats = []
    wind_lngs = []
    
    analyzer_ID = getAnalyzerId(analyzer)
    
    server = "b-eng-db01.picarro.int"
    database = "SurveyorEngineering"
    uid = "engineering"
    password = "aDs76WoiJn"
    connection = pyodbc.connect('DRIVER={SQL Server}; SERVER=%s; DATABASE=%s; UID=%s; PWD=%s' %
                            (server, database, uid, password))
    cursor = connection.cursor()
    
    cursor.execute("""
    
        SELECT [EpochTime]
              ,[GpsLatitude]
              ,[GpsLongitude]
              ,[CarSpeedNorth]
              ,[CarSpeedEast]
              ,[WindSpeedLateral]
              ,[WindSpeedLongitudinal]
        FROM [SurveyorEngineering].[dbo].[Measurement]
        WHERE (EpochTime BETWEEN '%s' AND '%s')
        AND (AnalyzerId = '%s')
        AND (GpsFit=2)
        
    """ % (str(epoch_time-duration),str(epoch_time),analyzer_ID))
    
    for row in cursor:
        epoch_times.append(row[0])
        lats.append(row[1])
        lngs.append(row[2])
        car_vel_norths.append(row[3])
        car_vel_easts.append(row[4])
        wind_lats.append(row[5])
        wind_lngs.append(row[6])
        
    return dict(epoch_time=np.asarray(epoch_times),latitude=np.asarray(lats),
                longitude=np.asarray(lngs),car_vel_n=np.asarray(car_vel_norths),
                car_vel_e=np.asarray(car_vel_easts),wind_lat=np.asarray(wind_lats),
                wind_lng=np.asarray(wind_lngs))
    
