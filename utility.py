import pandas as pd
relevantColumns = ['Date&Time', 'Inverter Output', 'Consumption']
columnNaming = {'Date&Time': 'tmstmp', 'Inverter Output': 'pv_yield', 'Consumption': 'consumption'}
START_TIME = '2025-01-01 00:00:00'

def read_solaredge(inputFP):
    # data for simulation
    inputData = pd.read_csv(inputFP, skiprows=2, header=None)
    headers = pd.read_csv(inputFP, nrows=1)

    inputData = inputData.iloc[:,:len(headers.columns)]
    inputData.columns = headers.columns
    return inputData

def trans_solaredge(inputData, headers, relevantColumns=relevantColumns):
    inputData = inputData.iloc[:,:len(headers.columns)]
    inputData.columns = headers.columns
    solaredgeDF = inputData[relevantColumns]
    solaredgeDF.rename(columns=columnNaming, inplace=True)
    timestamps = pd.date_range(start=START_TIME, periods=len(solaredgeDF), freq='h', tz='UTC')
    solaredgeDF['tmstmp'] = timestamps
    solaredgeDF = solaredgeDF.set_index('tmstmp')
    return solaredgeDF

def reduce_data(inputData):
    solaredgeDF = inputData[relevantColumns]
    solaredgeDF.rename(columns=columnNaming, inplace=True)
    timestamps = pd.date_range(start=START_TIME, periods=len(solaredgeDF), freq='h', tz='UTC')
    solaredgeDF['tmstmp'] = timestamps
    solaredgeDF = solaredgeDF.set_index('tmstmp')
    return solaredgeDF

def prep_data(solaredgeDF, relevantColumns=relevantColumns):
    solaredgeDF = solaredgeDF[relevantColumns]
    solaredgeDF.rename(columns=columnNaming, inplace=True)
    timestamps = pd.date_range(start=START_TIME, periods=len(solaredgeDF), freq='h', tz='UTC')
    solaredgeDF['tmstmp'] = timestamps
    solaredgeDF = solaredgeDF.set_index('tmstmp')
    return solaredgeDF

seasons = {
    '0': {
        'name': 'spring',
        'months': [3,4,5]
    },
    '1': {
        'name': 'summer',
        'months': [6,7,8]
    },
    '2': {
        'name': 'fall',
        'months': [9,10,11]
    },
    '3': {
        'name': 'winter',
        'months': [12,1,2]
    },
}


