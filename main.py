from flask import Flask
import json
import MySQLdb
import time
from geopy.distance import vincenty
from email import email

app = Flask(__name__)
app.config['DEBUG'] = True

# Note: We don't need to call run() since our application is embedded within
# the App Engine WSGI application server.

@app.route('/')
def hello():
    str_invite = "<html> <body> Welcome to the smartbin project! <br> Use the following links for traversing the smartbin data. <br>"
    str_invite = str_invite + "a. Display bins per city /smartbins/'city' <br>"
    str_invite = str_invite + "b. Display bins per city per area /smartbins/'city'/'area' <br>"
    str_invite = str_invite + "c. Display fill levels of all bins /smartbins/filllevels/ <br>"
    str_invite = str_invite + "d. Display fill levels of bins per city /smartbins/filllevels/'city' <br>"
    str_invite = str_invite + "e. Display fill levels of bins per city per area /smartbins/filllevels/'city'/'area' <br>"
    str_invite = str_invite + "f. Display routes to bins at an area /smartbins/routes/filllevel/'city'/'area'/'cLat'/'cLong' <br>"
    str_invite = str_invite + "g. Display fill levels for analysis /smartbins/analyze/filllevels <br>"
    str_invite = str_invite + "h. Display fill levels for analysis per city /smartbins/analyze/filllevels/'city' <br>"
    str_invite = str_invite + "i. Display fill levels for analysis per city per area /smartbins/analyze/filllevels/'city'/'area' </body> </html> \n"
    return str_invite

@app.route("/smartbins/<city>")
def jsonencodeBinsAtCity(city):
    smartBins = getFillLevelOfBinsAtCity(city)
    json_str = json.dumps(smartBins, indent=5)
    return json_str

@app.route("/smartbins/<city>/<area>")
def jsonencodeBinsAtCityArea(city,area):
    smartBins = getFillLevelOfBinsAtAreaCity(area, city)
    json_str = json.dumps (smartBins, indent=5)
    return json_str

@app.route("/smartbins/filllevels/")
def jsonencodeGetFillLevels():   
    smartBins = getFillLevelOfAllBins()
    json_str = json.dumps(smartBins, indent=5)
    return json_str

@app.route("/smartbins/filllevels/<city>")
def jsonencodeGetFillLevelsCity(city):   
    smartBins = getFillLevelOfBinsAtCity(city)
    json_str = json.dumps(smartBins, indent=5)
    return json_str

@app.route("/smartbins/filllevels/<city>/<area>")
def jsonencodeGetFillLevelsCityArea(city, area):   
    smartBins = getFillLevelOfBinsAtAreaCity(area, city)
    json_str = json.dumps (smartBins, indent=5)
    return json_str

@app.route("/smartbins/routes/filllevel/<city>/<area>/<cLat>/<cLong>")
def jsonencodeGetRouteCityArea(city,area,cLat,cLong):   
    smartBins = getOriginDestWaypointsForBins(city, area, cLat, cLong, 'High')
    json_str = json.dumps(smartBins, indent=5)
    return json_str

@app.route("/smartbins/analyze/filllevels")
def jsonencodeGetFillLevelsForAnalysis():
    smartBins = getFillLevelsForAnalyse()
    json_str = json.dumps(smartBins, indent=5)
    return json_str   
  
@app.route("/smartbins/analyze/filllevels/<city>")
def jsonencodeGetFillLevelsForAnalysisPerCity(city):
    smartBins = getFillLevelsForAnalysePerCity(city)
    json_str = json.dumps(smartBins, indent=5)
    return json_str   

@app.route("/smartbins/analyze/filllevels/<city>/<area>")
def jsonencodeGetFillLevelsForAnalysisPerCityPerArea(city,area):
    smartBins = getFillLevelsForAnalysePerCityPerArea(city, area)
    json_str = json.dumps(smartBins, indent=5)
    return json_str   

@app.route("/smartbins/user/<userId>/<password>")
def jsonencodeGetUserInfo(userId, password):
    userInfo = getUserInfo(userId, password)
    json_str = json.dumps(userInfo, indent=5)
    return json_str

@app.route("/smartbins/user/post/<userId>/<password>/<phone>/<email>")
def jsonencodeSetUserInfo(userId, password, phone, email):
    error = insertUserInfo(userId, password, phone, email)
    json_str = json.dumps(error, indent =5)
    return json_str

@app.errorhandler(404)
def page_not_found(e):
    output = {}
    json_str = json.dumps(output, indent=5)
    return json_str

"""
************************************************************************************************************
The code for database handling
************************************************************************************************************
"""
def connectBinDb():
    """
    This function establishes a connection with the database
    
    Args:
        None
    
    Returns:
        The database handle
    
    """
    #hostname = "/cloudsql/smartbin-1097:smartbinproject"
    #username = "root"
    #password = ""
    #dbName = "smartbin_db1"
    
    db = MySQLdb.connect(unix_socket='/cloudsql/smartbin-1097:smartbinproject',user='root',passwd='password',db='smartbin_db1',charset='utf8')
    
    return db

def closeBinDb(db):
    """
    This function closes the connection with the database
    
    Args:
        None
    
    Returns:
        None
    """
    
    db.close()

def getFillLevelsForAnalyse():
    """
    This function returns fill levels of all bins in the database for generating reports and further analysis.
    
    Args:
        None
    
    Returns:
        A dictionary with details of all smart bins
        
    Sample output:
    {
     "8": {
          "city": "Bengaluru", 
          "Area": "Hongasandra", 
          "Address": "Ozone Manay Tech Park", 
          "Longitude": 77.637527, 
          "Activity": [
               {
                    "October": [
                         {
                              "TimeStamp": "7-October-2015 20:10", 
                              "FillLevel": 16.0
                         }, 
                         {
                              "TimeStamp": "7-October-2015 20:29", 
                              "FillLevel": 23.0
                         }, 
                         {
                              "TimeStamp": "18-October-2015 10:9", 
                              "FillLevel": 36.0
                         }, 
                         {
                              "TimeStamp": "18-October-2015 10:12", 
                              "FillLevel": 49.0
                         }, 
                         {
                              "TimeStamp": "18-October-2015 10:15", 
                              "FillLevel": 51.0
                         }, 
                         {
                              "TimeStamp": "18-October-2015 11:22", 
                              "FillLevel": 72.0
                         }
                    ]
               }
          ], 
          "Latitude": 12.891341
      }
     }
    """
    
    SmartBins = {}
    months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
    
    # Establish connection with database
    db = connectBinDb()
    
    # prepare a cursor object using cursor() method
    cursor = db.cursor()
    
    # Execute the query to retrieve Highly filled bins at (area, city)
    sqlQuery = "select s.Longitude,s.Latitude,s.Address,a.AreaName,c.Name,f.filllevel,f.TimeStamp,s.BinId from smartbin s inner join smartbinfilllevel f  on f.BinId = s.BinId inner Join area a on a.areaId = s.AreaId inner Join city c on c.CityId = a.cityId"

    try:
        cursor.execute(sqlQuery);
        results = cursor.fetchall();
    except:
        print "Error: Unable to fetch data"
    
    for row in results:
        longitude = row[0]
        latitude = row[1]
        address = row[2]
        areaName = row[3]
        cityName = row[4]
        fillLevel = row[5]
        timeStamp = row[6]
        binId = row[7]
        
        activity = []
        record = {}
        done = 0
        
        timeStampFmt = time.strptime(str(timeStamp), "%Y-%m-%d %H:%M:%S")          
        timeEntry = str(timeStampFmt.tm_mday)+"-"+str(months[timeStampFmt.tm_mon-1])+"-"+str(timeStampFmt.tm_year)+" "+str(timeStampFmt.tm_hour)+":"+str(timeStampFmt.tm_min)
        
        if (SmartBins.has_key(binId)):
            activity = SmartBins[binId]['Activity']
            for i in range(len(activity)):
                record = activity[i]
                if (record.has_key(months[timeStampFmt.tm_mon-1])):
                    monthEntry =  record[months[timeStampFmt.tm_mon-1]]
                    entry = {"FillLevel":fillLevel,"TimeStamp":timeEntry}
                    monthEntry.append(entry)
                    done = 1
            if (done == 0):
                entry = {months[timeStampFmt.tm_mon-1]:[{"FillLevel":fillLevel,"TimeStamp":timeEntry}]}
                activity.append(entry)     
        else:
            SmartBins[binId] = {"Latitude":latitude, "Longitude":longitude,"Address":address,"Area":areaName,"city":cityName,'Activity':[{months[timeStampFmt.tm_mon-1]:[{"FillLevel":fillLevel,"TimeStamp":timeEntry}]}]}
            
    # disconnect from server
    closeBinDb(db)
       
    return SmartBins

def getFillLevelsForAnalysePerCity(city):
    """
    This function returns fill levels of all bins at 'city' in the database for generating reports and further analysis.
    
    Args:
        city(string)
    
    Returns:
        A dictionary with details of all smart bins at 'city'
        
    Sample output:
{
     "Bins": [
          {
               "city": "bengaluru", 
               "October": {
                    "week1": 41.8, 
                    "week3": 37.666666666666664, 
                    "week2": 13.0, 
                    "week4": 43.125
               }, 
               "Area": "bommanahalli", 
               "September": {
                    "week1": 0, 
                    "week3": 0, 
                    "week2": 0, 
                    "week4": 35.166666666666664
               }, 
               "Longitude": 77.623541, 
               "Address": "Golden Heritage Apartments", 
               "Latitude": 12.910673, 
               "id": 1
          }, 
          {
               "city": "bengaluru", 
               "October": {
                    "week1": 37.0, 
                    "week3": 41.0, 
                    "week2": 24.333333333333332, 
                    "week4": 45.625
               }, 
               "Area": "bommanahalli", 
               "September": {
                    "week1": 0, 
                    "week3": 0, 
                    "week2": 0, 
                    "week4": 33.5
               }, 
               "Longitude": 77.630748, 
               "Address": "Oxford Dental College", 
               "Latitude": 12.901162, 
               "id": 2
          }
        ]
    }
    """
    SmartBins = {}
    months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
    
    # Establish connection with database
    db = connectBinDb()
    
    # prepare a cursor object using cursor() method
    cursor = db.cursor()
    
    # Execute the query to retrieve Highly filled bins at (area, city)
    sqlQuery = "select s.Longitude,s.Latitude,s.Address,a.AreaName,c.Name,f.filllevel,f.TimeStamp,s.BinId from smartbin s inner join smartbinfilllevel f  on f.BinId = s.BinId inner Join area a on a.areaId = s.AreaId inner Join city c on c.CityId = a.cityId where c.Name = '"+city.lower()+"'"

    try:
        cursor.execute(sqlQuery);
        results = cursor.fetchall();
    except:
        print "Error: Unable to fetch data"
    
    for row in results:
        longitude = row[0]
        latitude = row[1]
        address = row[2]
        areaName = row[3]
        cityName = row[4]
        fillLevel = row[5]
        timeStamp = row[6]
        binId = row[7]
        
        activity = []
        record = {}
        done = 0
        
        timeStampFmt = time.strptime(str(timeStamp), "%Y-%m-%d %H:%M:%S")          
        #timeEntry = str(timeStampFmt.tm_mday)+"-"+str(months[timeStampFmt.tm_mon-1])

        if (SmartBins.has_key(binId)):
            if (SmartBins[binId].has_key(months[timeStampFmt.tm_mon-1])):                 
                if (int(timeStampFmt.tm_mday / 7) == 0):
                    SmartBins[binId][months[timeStampFmt.tm_mon-1]]['week1'].append(fillLevel)
                elif (int(timeStampFmt.tm_mday / 7) == 1):
                    SmartBins[binId][months[timeStampFmt.tm_mon-1]]['week2'].append(fillLevel)
                elif (int(timeStampFmt.tm_mday / 7) == 2):
                    SmartBins[binId][months[timeStampFmt.tm_mon-1]]['week3'].append(fillLevel)
                else:
                    SmartBins[binId][months[timeStampFmt.tm_mon-1]]['week4'].append(fillLevel)
            else:
                week1=[]
                week2=[]
                week3=[]
                week4=[]
                if (int(timeStampFmt.tm_mday / 7) == 0):
                    week1.append(fillLevel)
                elif (int(timeStampFmt.tm_mday / 7) == 1):
                    week2.append(fillLevel)
                elif (int(timeStampFmt.tm_mday / 7) == 2):
                    week3.append(fillLevel)
                else:
                    week4.append(fillLevel)
                   
                entry = {months[timeStampFmt.tm_mon-1]:{"week1": week1, "week2": week2, "week3":week3, "week4":week4}}
                SmartBins[binId].update(entry)
        else:
            week1=[]
            week2=[]
            week3=[]
            week4=[]
            if (int(timeStampFmt.tm_mday / 7) == 0):
                week1.append(fillLevel)
            elif (int(timeStampFmt.tm_mday / 7) == 1):
                week2.append(fillLevel)
            elif (int(timeStampFmt.tm_mday / 7) == 2):
                week3.append(fillLevel)
            else:
                week4.append(fillLevel)
            SmartBins[binId] = {"id": binId, "Latitude":latitude, "Longitude":longitude,"Address":address,"Area":areaName,"city":cityName, months[timeStampFmt.tm_mon-1]:{"week1": week1, "week2": week2, "week3":week3, "week4":week4}}
      
    # disconnect from server
    closeBinDb(db)
    
    finalBins = {}
    binArray = []
    binEntry = {}
    
    for key,values in SmartBins.items():
        binEntry = {"id":values['id'], "Latitude":values['Latitude'], "Longitude":values['Longitude'],"Address":values['Address'],"Area":values['Area'],"city":values['city']}
        for monthEntry in months:
            if (values.has_key(monthEntry)):
                avgWeek1 = 0
                avgWeek2 = 0
                avgWeek3 = 0
                avgWeek4 = 0                
                if (len(values[monthEntry]['week1']) > 0):
                    avgWeek1 = sum(values[monthEntry]['week1'])/float(len(values[monthEntry]['week1']))
                if (len(values[monthEntry]['week2']) > 0):
                    avgWeek2 = sum(values[monthEntry]['week2'])/float(len(values[monthEntry]['week2']))     
                if (len(values[monthEntry]['week3']) > 0):           
                    avgWeek3 = sum(values[monthEntry]['week3'])/float(len(values[monthEntry]['week3']))
                if (len(values[monthEntry]['week4']) > 0):
                    avgWeek4 = sum(values[monthEntry]['week4'])/float(len(values[monthEntry]['week4']))
                    
                entry = {monthEntry:{"week1": avgWeek1, "week2": avgWeek2, "week3":avgWeek3, "week4":avgWeek4}}
                binEntry.update(entry)
                
        binArray.append(binEntry)
        
    finalBins['Bins'] = binArray
    
    return finalBins

def getFillLevelsForAnalysePerCityPerArea(city, area):
    """
    Output is as follows:
    {
     "Bins": [
          {
               "city": "bengaluru", 
               "October": {
                    "week1": 39.6, 
                    "week3": 46.0, 
                    "week2": 18.0, 
                    "week4": 49.0
               }, 
               "Area": "hongasandra", 
               "September": {
                    "week1": 0, 
                    "week3": 0, 
                    "week2": 0, 
                    "week4": 41.166666666666664
               }, 
               "Longitude": 77.637527, 
               "Address": "Ozone Manay Tech Park", 
               "Latitude": 12.891341, 
               "id": 8
          }, 
.......................
          {
               "city": "bengaluru", 
               "October": {
                    "week1": 41.8, 
                    "week3": 40.0, 
                    "week2": 20.333333333333332, 
                    "week4": 44.625
               }, 
               "Area": "hongasandra", 
               "September": {
                    "week1": 0, 
                    "week3": 0, 
                    "week2": 0, 
                    "week4": 38.5
               }, 
               "Longitude": 77.635531, 
               "Address": "Surya Nissan", 
               "Latitude": 12.897178, 
               "id": 6
          }
        ]
    }
    """
    SmartBins = {}
    months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
    
    # Establish connection with database
    db = connectBinDb()
    
    # prepare a cursor object using cursor() method
    cursor = db.cursor()
    
    # Execute the query to retrieve Highly filled bins at (area, city)
    sqlQuery = "select s.Longitude,s.Latitude,s.Address,a.AreaName,c.Name,f.filllevel,f.TimeStamp,s.BinId from smartbin s inner join smartbinfilllevel f  on f.BinId = s.BinId inner Join area a on a.areaId = s.AreaId inner Join city c on c.CityId = a.cityId where c.Name = '"+city.lower()+"' AND a.AreaName = '"+area.lower()+"'"

    try:
        cursor.execute(sqlQuery);
        results = cursor.fetchall();
    except:
        print "Error: Unable to fetch data"
    
    for row in results:
        longitude = row[0]
        latitude = row[1]
        address = row[2]
        areaName = row[3]
        cityName = row[4]
        fillLevel = row[5]
        timeStamp = row[6]
        binId = row[7]
        
        timeStampFmt = time.strptime(str(timeStamp), "%Y-%m-%d %H:%M:%S")          
        #timeEntry = str(timeStampFmt.tm_mday)+"-"+str(months[timeStampFmt.tm_mon-1])

        if (SmartBins.has_key(binId)):
            if (SmartBins[binId].has_key(months[timeStampFmt.tm_mon-1])):                 
                if (int(timeStampFmt.tm_mday / 7) == 0):
                    SmartBins[binId][months[timeStampFmt.tm_mon-1]]['week1'].append(fillLevel)
                elif (int(timeStampFmt.tm_mday / 7) == 1):
                    SmartBins[binId][months[timeStampFmt.tm_mon-1]]['week2'].append(fillLevel)
                elif (int(timeStampFmt.tm_mday / 7) == 2):
                    SmartBins[binId][months[timeStampFmt.tm_mon-1]]['week3'].append(fillLevel)
                else:
                    SmartBins[binId][months[timeStampFmt.tm_mon-1]]['week4'].append(fillLevel)
            else:
                week1=[]
                week2=[]
                week3=[]
                week4=[]
                if (int(timeStampFmt.tm_mday / 7) == 0):
                    week1.append(fillLevel)
                elif (int(timeStampFmt.tm_mday / 7) == 1):
                    week2.append(fillLevel)
                elif (int(timeStampFmt.tm_mday / 7) == 2):
                    week3.append(fillLevel)
                else:
                    week4.append(fillLevel)
                   
                entry = {months[timeStampFmt.tm_mon-1]:{"week1": week1, "week2": week2, "week3":week3, "week4":week4}}
                SmartBins[binId].update(entry)
        else:
            week1=[]
            week2=[]
            week3=[]
            week4=[]
            if (int(timeStampFmt.tm_mday / 7) == 0):
                week1.append(fillLevel)
            elif (int(timeStampFmt.tm_mday / 7) == 1):
                week2.append(fillLevel)
            elif (int(timeStampFmt.tm_mday / 7) == 2):
                week3.append(fillLevel)
            else:
                week4.append(fillLevel)
            SmartBins[binId] = {"id": binId, "Latitude":latitude, "Longitude":longitude,"Address":address,"Area":areaName,"city":cityName, months[timeStampFmt.tm_mon-1]:{"week1": week1, "week2": week2, "week3":week3, "week4":week4}}
      
    # disconnect from server
    closeBinDb(db)
    
    finalBins = {}
    binArray = []
    binEntry = {}
    
    for key,values in SmartBins.items():
        binEntry = {"id":values['id'], "Latitude":values['Latitude'], "Longitude":values['Longitude'],"Address":values['Address'],"Area":values['Area'],"city":values['city']}
        for monthEntry in months:
            if (values.has_key(monthEntry)):
                avgWeek1 = 0
                avgWeek2 = 0
                avgWeek3 = 0
                avgWeek4 = 0                
                if (len(values[monthEntry]['week1']) > 0):
                    avgWeek1 = sum(values[monthEntry]['week1'])/float(len(values[monthEntry]['week1']))
                if (len(values[monthEntry]['week2']) > 0):
                    avgWeek2 = sum(values[monthEntry]['week2'])/float(len(values[monthEntry]['week2']))     
                if (len(values[monthEntry]['week3']) > 0):           
                    avgWeek3 = sum(values[monthEntry]['week3'])/float(len(values[monthEntry]['week3']))
                if (len(values[monthEntry]['week4']) > 0):
                    avgWeek4 = sum(values[monthEntry]['week4'])/float(len(values[monthEntry]['week4']))
                    
                entry = {monthEntry:{"week1": avgWeek1, "week2": avgWeek2, "week3":avgWeek3, "week4":avgWeek4}}
                binEntry.update(entry)
                
        binArray.append(binEntry)
        
    finalBins['Bins'] = binArray
          
    return finalBins

def getFillLevelOfBinsAtAreaCity(area, city):
    """
    This function returns a dictionary of Smart Bins based on fill levels of the bins at specific 'area' and 'city'.
    
    Args:
        area(string): Area 
        city(string): City  
    
    Returns:
        dictionary: dictionary of the SmartBins at 'city' and 'area'.
    
    Sample output for bins at area:'Hongasandra' and city:'Bangalore'
    
    {
     "High": [
          {
               "city": "Bengaluru", 
               "Area": "Hongasandra", 
               "fillLevel": 74.0, 
               "Longitude": 77.639329, 
               "Address": "Nandi Toyota", 
               "Latitude": 12.891656
          }, 
          {
               "city": "Bengaluru", 
               "Area": "Hongasandra", 
               "fillLevel": 72.0, 
               "Longitude": 77.637527, 
               "Address": "Ozone Manay Tech Park", 
               "Latitude": 12.891341
          }
     ], 
     "Medium": [
          {
               "city": "Bengaluru", 
               "Area": "Hongasandra", 
               "fillLevel": 52.0, 
               "Longitude": 77.633761, 
               "Address": "Vasan Eye Care", 
               "Latitude": 12.898035
          }, 
          {
               "city": "Bengaluru", 
               "Area": "Hongasandra", 
               "fillLevel": 66.0, 
               "Longitude": 77.635531, 
               "Address": "Surya Nissan", 
               "Latitude": 12.897178
          }, 
          {
               "city": "Bengaluru", 
               "Area": "Hongasandra", 
               "fillLevel": 67.0, 
               "Longitude": 77.627742, 
               "Address": "ING Vyasa Bank", 
               "Latitude": 12.908199
          }
     ], 
     "Low": []
}
    """
    SmartBins = {}
    bins = []
    binList = {}
    
    # Establish connection with database
    db = connectBinDb()
    
    # prepare a cursor object using cursor() method
    cursor = db.cursor()
    
    # Execute the query to retrieve Highly filled bins at (area, city)
    sqlQuery = "select s.Longitude,s.Latitude,s.Address,a.AreaName,c.Name,f.filllevel,s.BinId from smartbin s inner join smartbinfilllevel f  on f.BinId = s.BinId inner Join area a on a.areaId = s.AreaId inner Join city c on c.CityId = a.cityId where c.Name = '"+city.lower()+"' AND a.AreaName = '"+area.lower()+"' AND f.filllevel >= 70 AND f.isValid = 1"

    try:
        cursor.execute(sqlQuery);
        results = cursor.fetchall();
    except:
        print "Error: Unable to fetch data"
    
    for row in results:
        longitude = row[0]
        latitude = row[1]
        address = row[2]
        areaName = row[3]
        cityName = row[4]
        fillLevel = row[5]
        binId = row[6]
        #print latitude,longitude,address,areaName,cityName,fillLevel
        binList = {"id":binId, "Latitude":latitude, "Longitude":longitude,"Address":address,"Area":areaName,"city":cityName, "fillLevel": fillLevel, "Type":'Waypoints'}
        bins.append(binList)
    
    SmartBins['High'] = bins
    
    # Retrieve bins which are medium filled
    bins = []
    binList = {}
    
    sqlQuery = "select s.Longitude,s.Latitude,s.Address,a.AreaName,c.Name,f.filllevel,s.BinId from smartbin s inner join smartbinfilllevel f  on f.BinId = s.BinId inner Join area a on a.areaId = s.AreaId inner Join city c on c.CityId = a.cityId where c.Name = '"+city+"' AND a.AreaName = '"+area+"' AND f.filllevel < 70 AND f.filllevel >=40 AND f.isValid = 1"

    try:
        cursor.execute(sqlQuery);
        results = cursor.fetchall();
    except:
        print "Error: Unable to fetch data"
        
    for row in results:
        longitude = row[0]
        latitude = row[1]
        address = row[2]
        areaName = row[3]
        cityName = row[4]
        fillLevel = row[5]
        binId = row[6]
        #print latitude,longitude,address,areaName,cityName
        binList = {"id":binId, "Latitude":latitude, "Longitude":longitude,"Address":address,"Area":areaName,"city":cityName,"fillLevel":fillLevel, "Type":'Waypoints'}
        bins.append(binList)
    
    SmartBins['Medium'] = bins
    
    # Smart Bins with low fill level
    bins = []
    binList = {}
    
    sqlQuery = "select s.Longitude,s.Latitude,s.Address,a.AreaName,c.Name,f.filllevel from smartbin s inner join smartbinfilllevel f  on f.BinId = s.BinId inner Join area a on a.areaId = s.AreaId inner Join city c on c.CityId = a.cityId where c.Name = '"+city+"' AND a.AreaName = '"+area+"' AND f.filllevel < 40 AND f.isValid = 1"

    try:
        cursor.execute(sqlQuery);
        results = cursor.fetchall();
    except:
        print "Error: Unable to fetch data"
        
    for row in results:
        longitude = row[0]
        latitude = row[1]
        address = row[2]
        areaName = row[3]
        cityName = row[4]
        fillLevel = row[5]
        binId = row[6]
        #print latitude,longitude,address,areaName,cityName,fillLevel
        binList = {"id": binId, "Latitude":latitude, "Longitude":longitude,"Address":address,"Area":areaName,"city":cityName,"fillLevel":fillLevel, "Type":'Waypoints'}
        bins.append(binList)
    
    SmartBins['Low'] = bins    
    
    # disconnect from server
    closeBinDb(db)
    
    return SmartBins

def getFillLevelOfBinsAtCity( city):
    """
    This function returns a dictionary of Smart Bins based on fill levels of the bins at specific 'city'.
    
    Args:
        city(string): City  
    
    Returns:
        dictionary: dictionary of the SmartBins at 'city'.
    
    Sample output for bins at city:'Bengaluru'
    
{
     "High": [
          {
               "city": "Bengaluru", 
               "Area": "Hongasandra", 
               "fillLevel": 74.0, 
               "Longitude": 77.639329, 
               "Address": "Nandi Toyota", 
               "Latitude": 12.891656
          }, 
          {
               "city": "Bengaluru", 
               "Area": "Hongasandra", 
               "fillLevel": 72.0, 
               "Longitude": 77.637527, 
               "Address": "Ozone Manay Tech Park", 
               "Latitude": 12.891341
          }
     ], 
     "Medium": [
          {
               "city": "Bengaluru", 
               "Area": "Bommanahalli", 
               "fillLevel": 51.0, 
               "Longitude": 77.623541, 
               "Address": "Golden Heritage Apartments", 
               "Latitude": 12.910673
          }, 
          {
               "city": "Bengaluru", 
               "Area": "Bommanahalli", 
               "fillLevel": 53.0, 
               "Longitude": 77.630748, 
               "Address": "Oxford Dental College", 
               "Latitude": 12.901162
          }, 
          {
               "city": "Bengaluru", 
               "Area": "Bommanahalli", 
               "fillLevel": 50.0, 
               "Longitude": 77.623541, 
               "Address": "Laa Heritage Apartments Rupena Agrahara", 
               "Latitude": 12.910673
          }, 
          {
               "city": "Bengaluru", 
               "Area": "Bommanahalli", 
               "fillLevel": 54.0, 
               "Longitude": 77.625473, 
               "Address": "Mahindra Showroom", 
               "Latitude": 12.912057
          }, 
          {
               "city": "Bengaluru", 
               "Area": "Hongasandra", 
               "fillLevel": 52.0, 
               "Longitude": 77.633761, 
               "Address": "Vasan Eye Care", 
               "Latitude": 12.898035
          }, 
          {
               "city": "Bengaluru", 
               "Area": "Hongasandra", 
               "fillLevel": 66.0, 
               "Longitude": 77.635531, 
               "Address": "Surya Nissan", 
               "Latitude": 12.897178
          }, 
          {
               "city": "Bengaluru", 
               "Area": "Hongasandra", 
               "fillLevel": 67.0, 
               "Longitude": 77.627742, 
               "Address": "ING Vyasa Bank", 
               "Latitude": 12.908199
          }
     ], 
     "Low": []
}
    """
    SmartBins = {}
    bins = []
    binList = {}
    type = "WayPoints"
    
    # Establish connection with database
    db = connectBinDb()
    
    # prepare a cursor object using cursor() method
    cursor = db.cursor()
    
    # Execute the query to retrieve Highly filled bins at (area, city)
    sqlQuery = "select s.Longitude,s.Latitude,s.Address,a.AreaName,c.Name,f.filllevel,s.BinId from smartbin s inner join smartbinfilllevel f  on f.BinId = s.BinId inner Join area a on a.areaId = s.AreaId inner Join city c on c.CityId = a.cityId where c.Name = '"+city.lower()+"' AND f.filllevel >= 70 AND f.isValid = 1"

    try:
        cursor.execute(sqlQuery);
        results = cursor.fetchall();
    except:
        print "Error: Unable to fetch data"
    
    for row in results:
        longitude = row[0]
        latitude = row[1]
        address = row[2]
        areaName = row[3]
        cityName = row[4]
        fillLevel = row[5]
        binId = row[6]
        #print latitude,longitude,address,areaName,cityName,fillLevel
        binList = {"id": binId, "Latitude":latitude, "Longitude":longitude,"Address":address,"Area":areaName,"city":cityName, "fillLevel": fillLevel,"Type":type}
        bins.append(binList)
    
    SmartBins['High'] = bins
    
    # Retrieve bins which are medium filled
    bins = []
    binList = {}
    
    sqlQuery = "select s.Longitude,s.Latitude,s.Address,a.AreaName,c.Name,f.filllevel,s.BinId from smartbin s inner join smartbinfilllevel f  on f.BinId = s.BinId inner Join area a on a.areaId = s.AreaId inner Join city c on c.CityId = a.cityId where c.Name = '"+city+"' AND f.filllevel < 70 AND f.filllevel >=40 AND f.isValid = 1"

    try:
        cursor.execute(sqlQuery);
        results = cursor.fetchall();
    except:
        print "Error: Unable to fetch data"
        
    for row in results:
        longitude = row[0]
        latitude = row[1]
        address = row[2]
        areaName = row[3]
        cityName = row[4]
        fillLevel = row[5]
        binId = row[6]
        #print latitude,longitude,address,areaName,cityName
        binList = {"id": binId, "Latitude":latitude, "Longitude":longitude,"Address":address,"Area":areaName,"city":cityName,"fillLevel":fillLevel,"Type":type}
        bins.append(binList)
    
    SmartBins['Medium'] = bins
    
    # Smart Bins with low fill level
    bins = []
    binList = {}
    
    sqlQuery = "select s.Longitude,s.Latitude,s.Address,a.AreaName,c.Name,f.filllevel,s.BinId from smartbin s inner join smartbinfilllevel f  on f.BinId = s.BinId inner Join area a on a.areaId = s.AreaId inner Join city c on c.CityId = a.cityId where c.Name = '"+city+"' AND f.filllevel < 40 AND f.isValid = 1"

    try:
        cursor.execute(sqlQuery);
        results = cursor.fetchall();
    except:
        print "Error: Unable to fetch data"
        
    for row in results:
        longitude = row[0]
        latitude = row[1]
        address = row[2]
        areaName = row[3]
        cityName = row[4]
        fillLevel = row[5]
        binId = row[6]
        #print latitude,longitude,address,areaName,cityName,fillLevel
        binList = {"id": binId, "Latitude":latitude, "Longitude":longitude,"Address":address,"Area":areaName,"city":cityName,"fillLevel":fillLevel,"Type":type}
        bins.append(binList)
    
    SmartBins['Low'] = bins    
    
    print SmartBins
    
    # disconnect from server
    closeBinDb(db)
    
    return SmartBins

def getOrigin(cLat, cLong, bins):
    origin = (cLat, cLong)
    tempOrigin = 0.000
    distance = 0.000
    element = -1
    
    print "Inside getOrigin", origin
    for i in range(len(bins)):
        tempOrigin = (bins[i]['Latitude'], bins[i]['Longitude'])
        tempDistance = vincenty(tempOrigin, origin).miles
        print tempDistance, i
        if (distance == 0 or tempDistance < distance):
            print element
            distance = tempDistance
            element = i
            
    return element
        
def getDestination(cLat, cLong, bins):
    origin = (cLat, cLong)
    tempOrigin = 0.000
    distance = 0.000
    element = -1
    
    for i in range(len(bins)):
        if (bins[i]['Type'] == 'Waypoints'):
            tempOrigin = (bins[i]['Latitude'], bins[i]['Longitude'])
            tempDistance = vincenty(tempOrigin, origin).miles
            
            if (distance == 0 or tempDistance > distance):
                distance = tempDistance
                element = i
            
    return element
        
def getOriginDestWaypointsForHighBins(city,area,cLat,cLong):
    """
    Function provides the origin, destination and way points of all bins with high fill levels.
    
    Args:
        city(string): name of city
        area(string): name of area
        cLat(float/double): latitude of current location
        cLog(float/double): Longitude of current location
        
    Returns:
        The dictionary of all elememts with 'Type' field updated.
        
        {
     "High": [
          {
               "city": "Bengaluru", 
               "Area": "Hongasandra", 
               "fillLevel": 74.0, 
               "Longitude": 77.639329, 
               "Address": "Nandi Toyota", 
               "Latitude": 12.891656, 
               "Type": "Destination"
          }, 
          {
               "city": "Bengaluru", 
               "Area": "Hongasandra", 
               "fillLevel": 72.0, 
               "Longitude": 77.637527, 
               "Address": "Ozone Manay Tech Park", 
               "Latitude": 12.891341, 
               "Type": "Origin"
          }
     ], 
     "Medium": [
          {
               "city": "Bengaluru", 
               "Area": "Hongasandra", 
               "fillLevel": 52.0, 
               "Longitude": 77.633761, 
               "Address": "Vasan Eye Care", 
               "Latitude": 12.898035, 
               "Type": "Waypoints"
          }, 
          {
               "city": "Bengaluru", 
               "Area": "Hongasandra", 
               "fillLevel": 66.0, 
               "Longitude": 77.635531, 
               "Address": "Surya Nissan", 
               "Latitude": 12.897178, 
               "Type": "Waypoints"
          }, 
          {
               "city": "Bengaluru", 
               "Area": "Hongasandra", 
               "fillLevel": 67.0, 
               "Longitude": 77.627742, 
               "Address": "ING Vyasa Bank", 
               "Latitude": 12.908199, 
               "Type": "Waypoints"
          }
     ], 
     "Low": []
}

    """
    smartBin = getFillLevelOfBinsAtAreaCity(area, city)
    keys = 'High'
    bins = smartBin.get(keys)
    if (len(bins) == 0):
        print "Inside 0"
        return smartBin
    
    if (len(bins) == 1):
        print "Inside 1"
        smartBin[keys][0]['Type'] = 'Origin'
        return smartBin
    
    element = -1
    
    element = getOrigin(cLat, cLong, bins)
    if (element != -1):
        smartBin[keys][element]['Type'] = "Origin"
  
    origin = element
    element = -1  
    element = getDestination(smartBin[keys][origin]['Latitude'], smartBin[keys][origin]['Longitude'], bins)   
    if (element != -1):
        smartBin[keys][element]['Type'] = "Destination"    
    
    return smartBin

def getOriginDestWaypointsForBins(city, area, cLat, cLong, keys):
    if (keys == 'High'):
        smartBin = getOriginDestWaypointsForHighBins(city, area, cLat, cLong)
    
    return smartBin

def getFillLevelOfAllBins():
    """
    This function returns a dictionary of Smart Bins based on fill levels of the bins at specific 'area' and 'city'.
    
    Args:
        area(string): Area 
        city(string): City  
    
    Returns:
        dictionary: dictionary of the SmartBins at 'city' and 'area'.
    
    Sample output for bins at area:'Hongasandra' and city:'Bangalore'
    
    {
     "High": [
          {
               "city": "Bengaluru", 
               "Area": "Hongasandra", 
               "fillLevel": 74.0, 
               "Longitude": 77.639329, 
               "Address": "Nandi Toyota", 
               "Latitude": 12.891656
          }, 
          {
               "city": "Bengaluru", 
               "Area": "Hongasandra", 
               "fillLevel": 72.0, 
               "Longitude": 77.637527, 
               "Address": "Ozone Manay Tech Park", 
               "Latitude": 12.891341
          }
     ], 
     "Medium": [
          {
               "city": "Bengaluru", 
               "Area": "Hongasandra", 
               "fillLevel": 52.0, 
               "Longitude": 77.633761, 
               "Address": "Vasan Eye Care", 
               "Latitude": 12.898035
          }, 
          {
               "city": "Bengaluru", 
               "Area": "Hongasandra", 
               "fillLevel": 66.0, 
               "Longitude": 77.635531, 
               "Address": "Surya Nissan", 
               "Latitude": 12.897178
          }, 
          {
               "city": "Bengaluru", 
               "Area": "Hongasandra", 
               "fillLevel": 67.0, 
               "Longitude": 77.627742, 
               "Address": "ING Vyasa Bank", 
               "Latitude": 12.908199
          }
     ], 
     "Low": []
}
    """
    SmartBins = {}
    bins = []
    binList = {}
    
    # Establish connection with database
    db = connectBinDb()
    
    # prepare a cursor object using cursor() method
    cursor = db.cursor()
    
    # Execute the query to retrieve Highly filled bins at (area, city)
    sqlQuery = "select s.Longitude,s.Latitude,s.Address,a.AreaName,c.Name,f.filllevel,s.BinId from smartbin s inner join smartbinfilllevel f  on f.BinId = s.BinId inner Join area a on a.areaId = s.AreaId inner Join city c on c.CityId = a.cityId where f.isValid = 1 AND f.filllevel >= 70 "

    try:
        cursor.execute(sqlQuery);
        results = cursor.fetchall();
    except:
        print "Error: Unable to fetch data"
    
    for row in results:
        longitude = row[0]
        latitude = row[1]
        address = row[2]
        areaName = row[3]
        cityName = row[4]
        fillLevel = row[5]
        binId = row[6]
        #print latitude,longitude,address,areaName,cityName,fillLevel
        binList = {"id": binId, "Latitude":latitude, "Longitude":longitude,"Address":address,"Area":areaName,"city":cityName, "fillLevel": fillLevel, "Type":'Waypoints'}
        bins.append(binList)
    
    SmartBins['High'] = bins
    
    # Retrieve bins which are medium filled
    bins = []
    binList = {}
    
    sqlQuery = "select s.Longitude,s.Latitude,s.Address,a.AreaName,c.Name,f.filllevel,s.BinId from smartbin s inner join smartbinfilllevel f  on f.BinId = s.BinId inner Join area a on a.areaId = s.AreaId inner Join city c on c.CityId = a.cityId where  f.isValid = 1 AND f.filllevel BETWEEN 40 AND 70"

    try:
        cursor.execute(sqlQuery);
        results = cursor.fetchall();
    except:
        print "Error: Unable to fetch data"
        
    for row in results:
        longitude = row[0]
        latitude = row[1]
        address = row[2]
        areaName = row[3]
        cityName = row[4]
        fillLevel = row[5]
        binId = row[6]
        #print latitude,longitude,address,areaName,cityName
        binList = {"id": binId, "Latitude":latitude, "Longitude":longitude,"Address":address,"Area":areaName,"city":cityName,"fillLevel":fillLevel, "Type":'Waypoints'}
        bins.append(binList)
    
    SmartBins['Medium'] = bins
    
    # Smart Bins with low fill level
    bins = []
    binList = {}
    
    sqlQuery = "select s.Longitude,s.Latitude,s.Address,a.AreaName,c.Name,f.filllevel,s.BinId from smartbin s inner join smartbinfilllevel f  on f.BinId = s.BinId inner Join area a on a.areaId = s.AreaId inner Join city c on c.CityId = a.cityId where f.isValid = 1 AND f.filllevel <= 40"

    try:
        cursor.execute(sqlQuery);
        results = cursor.fetchall();
    except:
        print "Error: Unable to fetch data"
        
    for row in results:
        longitude = row[0]
        latitude = row[1]
        address = row[2]
        areaName = row[3]
        cityName = row[4]
        fillLevel = row[5]
        binId = row[6]
        #print latitude,longitude,address,areaName,cityName,fillLevel
        binList = {"id": binId, "Latitude":latitude, "Longitude":longitude,"Address":address,"Area":areaName,"city":cityName,"fillLevel":fillLevel, "Type":'Waypoints'}
        bins.append(binList)
    
    SmartBins['Low'] = bins    
    
    # disconnect from server
    closeBinDb(db)
    
    return SmartBins
def insertUserInfo(userId, passwd, phone, email):
    error = {}
    db = connectBinDb()
    
    # prepare a cursor object using cursor() method
    cursor = db.cursor()
    
    sqlQuery = "select * from user where userId LIKE '"+userId+"'"
    
    try:
        cursor.execute(sqlQuery)
        results = cursor.fetchall()
    except:
        entry = {"error":1}
        error.update(entry)
        print "Error: Unable to fetch data"
                    
    if (len(results) == 0):
        sqlQuery = "INSERT INTO `smartbin_db1`.`user` (`userId`, `password`, `phone`, `email`, `userPriviledge`) VALUES ('"+userId+"', '"+passwd+"', '"+phone+"', '"+email+"', '')"
        print sqlQuery
        try:
            cursor.execute(sqlQuery)
            db.commit()
        except:
            entry = {"error":1}
            error.update(entry)
            print "Error: Unable to insert data"
            db.rollback()
    else:
        print "Record already exists"
        entry = {"error":2}
        error.update(entry)
        
    closeBinDb(db)
    return error

def getUserInfo(userId, passwd):
    user = {}
    error = 0
    db = connectBinDb()
    
    # prepare a cursor object using cursor() method
    cursor = db.cursor()
    
    sqlQuery = "select phone, email from user where userId LIKE '"+userId+"' AND password LIKE '"+passwd+"'"
    
    try:
        cursor.execute(sqlQuery)
        results = cursor.fetchall()
    except:
        entry = {"phone":"", "email":"", "error": 1}
        print "Error: Unable to fetch data"
                    
    if (len(results) == 0):
        entry = {"phone":"", "email":"", "error": 2}
        user.update(entry)
    else:
        for row in results:
            phone = row[0]
            email = row[1]
            entry = {"phone": phone, "email": email, "error": error}
            user.update(entry)

    closeBinDb(db)
    return user