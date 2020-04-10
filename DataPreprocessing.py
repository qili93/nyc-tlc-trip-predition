import numpy as np
import pandas as pd
import os, sys
import argparse
from datetime import datetime, timedelta

DATA_PATH = os.path.join("/home/qilibj/github/nyc-tlc-trip-predition", "data")

# Get days of month in 2018
def getDaysMonth(month):
    if month == 2: return 28
    if month % 2 == 1: return 31
    return 30

# Get Time Bin Start of month
def getTimeBinStart(month):
    if month == 1: return 0
    days = 0
    for index in range(1, month):
        days += getDaysMonth(index)
    return round(((24*60)/30)*days)

# Filter PULocationID in Manhattan
def filterLocationID(month):
    # load zone data
    data_zone = pd.read_csv(os.path.join(DATA_PATH, "taxi+_zone_lookup.csv"))
    data_zone_Manhattan = data_zone[data_zone.Borough == "Manhattan"]

    # filter trip data
    fileName = "yellow_tripdata_2018-"+"{0:02}".format(month)+".csv"
    data_trip = pd.read_csv(os.path.join(DATA_PATH, fileName))
    data_trip_Manhattan = data_trip[data_trip.PULocationID.isin(data_zone_Manhattan["LocationID"])]
    
    return data_trip_Manhattan

# Filter Based on Pickup Time
def timeToUnix(t):
    newtime = datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
    timestamp = datetime.timestamp(newtime)
    return timestamp

def dfWithTripTimes(df):
    startTime = datetime.now()
    duration = df.loc[:,["tpep_pickup_datetime", "tpep_dropoff_datetime"]]
    pickup_time = [timeToUnix(pkup) for pkup in duration["tpep_pickup_datetime"].values]
    dropoff_time = [timeToUnix(drpof) for drpof in duration["tpep_dropoff_datetime"].values]
    trip_duration = (np.array(dropoff_time) - np.array(pickup_time))/float(60)  #trip duration in minutes
    
    NewFrame = df.loc[:,['trip_distance','PULocationID','DOLocationID','total_amount','tpep_pickup_datetime']]
    NewFrame["pickup_time"] = pickup_time
    NewFrame["dropoff_time"] = dropoff_time
    NewFrame["trip_duration"] = trip_duration
    NewFrame["speed"] = (NewFrame["trip_distance"]/NewFrame["trip_duration"])*60
    
    print("Time taken for creation of dataframe is {}".format(datetime.now() - startTime))
    return NewFrame

def filterPickupTime(data_trip_Manhattan, month):
    new_data_trip = dfWithTripTimes(data_trip_Manhattan)
    
    monthStart = timeToUnix("2018-"+"{0:02}".format(month)+"-01 00:00:00")
    monthEnd = timeToUnix("2018-"+"{0:02}".format(month+1)+"-01 00:00:00")

    new_data_trip = new_data_trip[(new_data_trip.pickup_time < new_data_trip.dropoff_time)]
    new_data_trip = new_data_trip[(new_data_trip.pickup_time > monthStart) & (new_data_trip.pickup_time < monthEnd)]
    return new_data_trip

# Filter Based on Trip Duration
def filterTripDuration(new_data_trip):
    new_data_trip = new_data_trip[(new_data_trip.trip_duration>1) & (new_data_trip.trip_duration<720)]
    return new_data_trip

# Filter Based on SPEED
def filterSPEED(new_data_trip):
    new_data_trip = new_data_trip[(new_data_trip.speed>0) & (new_data_trip.speed<50)]
    return new_data_trip

# Filter Based on Trip Distance
def filterTripDistance(new_data_trip):
    new_data_trip = new_data_trip[(new_data_trip.trip_distance>0) & (new_data_trip.trip_distance<30)]
    return new_data_trip

# Filter based on Total Fare
def filterTotalFare(new_data_trip):
    new_data_trip = new_data_trip[(new_data_trip.total_amount>0) & (new_data_trip.total_amount<100)]
    return new_data_trip

# Time Binning
yearStart = timeToUnix("2018-01-01 00:00:00")
yearEnd = timeToUnix("2019-01-01 00:00:00")
def pickup_30min_bins(dataframe, month, year):
    pickupTime = dataframe["pickup_time"].values
    unixTime = [yearStart, yearEnd]
    unix_year = unixTime[year-2018]
    time_30min_bin = [int((i - unix_year)/(30*60)) for i in pickupTime]
    dataframe["time_bin"] = np.array(time_30min_bin)
    return dataframe

# get unique time bins
def getUniqueTimeBins(month_2018_data, PU_LOC_LIST, TIME_BIN_NUM):
    unqiueTimeBins = []
    numZERO = 0
    for item in PU_LOC_LIST:
        timeBins = month_2018_data.loc[(month_2018_data["PULocationID"] == item), ["time_bin"]]
        timeBinsUnique = np.unique(timeBins["time_bin"])
        unqiueTimeBins.append(timeBinsUnique)
        numZERO += TIME_BIN_NUM - len(timeBinsUnique)
    print("Total ZERO number is", numZERO)
    
    return unqiueTimeBins

# data filling with ZERO
def fillingZERO(month_2018_data, unqiueTimeBins, TIME_BIN_NUM, TIME_BIN_START):
    month_2018_timeBin_groupBy = month_2018_data[["PULocationID", "time_bin", "trip_distance"]].groupby(by = ["PULocationID", "time_bin"]).count()
    numberOfPickups = month_2018_timeBin_groupBy["trip_distance"].values
    
    index = 0
    month_2018_fillZero = []
    for item in range(len(unqiueTimeBins)):
        smoothed_bins = []
        for t in range(TIME_BIN_NUM):
            newtime = t + TIME_BIN_START
            if newtime in unqiueTimeBins[item]:
                smoothed_bins.append(numberOfPickups[index])
                index += 1
            else:
                smoothed_bins.append(0)
        month_2018_fillZero.extend(smoothed_bins)
    
    print("Total time bins number shoud equal to 67 x ", TIME_BIN_NUM, "=", len(month_2018_fillZero))
    print("ZERO number in month_2018_fillZero is:", month_2018_fillZero.count(0))
    return month_2018_fillZero

# data output to CSV file
def output2CSV(month_2018_data, month_2018_fillZero, PU_LOC_LIST, DATA_MONTH, TIME_BIN_NUM, TIME_BIN_START):    
    startDate = datetime.strptime("2018-"+"{0:02}".format(DATA_MONTH)+"-01 00:00:00", "%Y-%m-%d %H:%M:%S")

    for index in range(len(PU_LOC_LIST)):
        pickLocationID = "{0:03}".format(PU_LOC_LIST[index])
        outputData = pd.DataFrame(columns=['PULocationID', 'PUTimeDate', 'PUTimeBin' , 'PUNum'])
        for t in range(TIME_BIN_NUM):
            currentDate = startDate + timedelta(minutes=30*t)
            currentTimeBin = TIME_BIN_START + t
            currentPickup = month_2018_fillZero[index*TIME_BIN_NUM+t]
            outputData = outputData.append(pd.Series([pickLocationID, currentDate, currentTimeBin ,currentPickup], index=outputData.columns), ignore_index=True)
        outputFileName = "2018_"+str(pickLocationID)+"_"+"{0:02}".format(DATA_MONTH)+".csv"
        outputFilePath = os.path.join("/home/qilibj/github/nyc-tlc-trip-predition/clean",outputFileName)
        print(outputFilePath)
        outputData.to_csv(outputFilePath, index=False)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--month", type=int,
                        default=1,
                        help='month of the data. (Default 1)')
    args = parser.parse_args()
    DATA_MONTH = args.month
    DATA_MONTH_DAYS = getDaysMonth(args.month)
    TIME_BIN_START = getTimeBinStart(DATA_MONTH)
    TIME_BIN_NUM = round(((24*60)/30)*DATA_MONTH_DAYS)
    TIME_BIN_END = TIME_BIN_START + TIME_BIN_NUM - 1
    print("Current Month is {}".format(DATA_MONTH))
    print("Days in Month is {}".format(DATA_MONTH_DAYS))  
    print("TimeBin Start is {}".format(TIME_BIN_START)) 
    print("TimeBin End is {}".format(TIME_BIN_END)) 
    print("TimeBin Number is {}".format(TIME_BIN_NUM))
    
    # Filter PULocationID in Manhattan
    data_trip_Manhattan = filterLocationID(DATA_MONTH)
    
    # write location file to CSV
    PU_LOC_LIST = np.unique(data_trip_Manhattan["PULocationID"])
    assert len(PU_LOC_LIST) == 67
    writeLocation = pd.DataFrame(PU_LOC_LIST)
    locationFilePath = os.path.join("/home/qilibj/github/nyc-tlc-trip-predition/clean","LocationID.csv")
    if not os.path.exists(locationFilePath):
        writeLocation.to_csv(locationFilePath, index=False)
    
    # Filter Based on Pickup Time
    new_data_trip = filterPickupTime(data_trip_Manhattan, DATA_MONTH)
    # Filter Based on Trip Duration
    new_data_trip = filterTripDuration(new_data_trip)
    # Filter Based on SPEED
    new_data_trip = filterSPEED(new_data_trip)
    # Filter Based on Trip Distance
    new_data_trip = filterTripDistance(new_data_trip)
    # Filter based on Total Fare
    new_data_trip = filterTotalFare(new_data_trip)
    
    print("Fraction of cleaned points",str(new_data_trip.shape[0]/data_trip_Manhattan.shape[0]))
    print("Total number of outliers and erroneous points removed = ",str(data_trip_Manhattan.shape[0] - new_data_trip.shape[0]))
    
    # time binning
    month_2018_data = pickup_30min_bins(new_data_trip, DATA_MONTH, 2018)
    print(month_2018_data['time_bin'].min())
    print(month_2018_data['time_bin'].max())
    print("There should be", round(((24*60)/30)*DATA_MONTH_DAYS) ,"unique 30 minutes time bins for the month of 2018:", DATA_MONTH)
    print("Actual unique 30 minute time bins", str(len(np.unique(month_2018_data["time_bin"]))))
    
    # Fill with ZERO
    unqiueTimeBins = getUniqueTimeBins(month_2018_data, PU_LOC_LIST, TIME_BIN_NUM)
    month_2018_fillZero = fillingZERO(month_2018_data, unqiueTimeBins, TIME_BIN_NUM, TIME_BIN_START)
    
    # output to CSV file
    output2CSV(month_2018_data, month_2018_fillZero, PU_LOC_LIST, DATA_MONTH, TIME_BIN_NUM, TIME_BIN_START)

if __name__ == "__main__":
    main()
