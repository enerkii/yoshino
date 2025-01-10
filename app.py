from re import M
import pandas as pd
import json
import utility
import self_sufficiency
import peak_shaving
import finance


headers = ['Date&Time', 'GHI', 'DHI', 'DNI', 'GTI', 'Temperature', 'GTI Loss',
       'Irradiance Shading Loss', 'IAM Loss', 'Soiling and Snow Loss',
       'Nominal Energy', 'Irradiance Level Loss', 'Shading Electrical Loss',
       'Temperature Loss', 'Optimizer Loss', 'Yield Factor Loss',
       'Module Quality Loss', 'Rear Side Shading Electrical Loss', 'LID Loss',
       'Ohmic Loss', 'String Clipping Loss', 'Array Energy',
       'Inverter Efficiency Loss', 'Clipping Loss',
       'System Unavailability Loss', 'Export Limitation Loss',
       'Battery charge', 'Battery Discharge', 'Battery State Of Energy',
       'Inverter Output', 'Consumption', 'Self-consumption', 'Imported',
       'Exported', 'Performance Ratio']

def calculate(parameters, solaredgeData):
    """
    Prep Data
    """
    solaredgeData = solaredgeData.iloc[:,:len(headers)]
    solaredgeData.columns = headers
    solaredgeData = utility.reduce_data(solaredgeData)
    solaredgeData[['pv_yield', 'consumption']] = solaredgeData[['pv_yield', 'consumption']] / 1000
    solaredgeData['hour'] = solaredgeData.index.hour

    battery = parameters['battery']
    batterySizes = list(range(int(battery['capacity_start']), int(battery['capacity_end']) + 1, int(battery['capacity_step'])))

    # Prepare Status Quo
    mean_per_hour = solaredgeData.groupby('hour')['consumption'].mean()
    max_per_hour = solaredgeData.groupby('hour')['consumption'].max()
    min_per_hour = solaredgeData.groupby('hour')['consumption'].min()

    statusQuoLoad = {
        "mean": list(mean_per_hour),
        "max": list(max_per_hour),
        "min": list(min_per_hour)
    }


    '''
    for each battery size calculate a self-sufficiency optimization, peak shaving and financials
    '''
    results = []

    for batCap in batterySizes:
        '''
        SELF-SUFFICIENCY OPTIMIZATION
        '''
        pvYieldTS = solaredgeData['pv_yield'].to_numpy()
        consumptionTS = solaredgeData['consumption'].to_numpy()
        optimizedTS = self_sufficiency.optimize_year(pvYield_ts=pvYieldTS,
                                    consumption_ts=consumptionTS,
                                    batteryCap=batCap,
                                    efficiency=battery['conversion_efficiency'],
                                    duration=battery['duration'])

        '''
        PEAK SHAVING
        '''
        hourly_load = solaredgeData.copy()
        hourly_load['hour'] = hourly_load.index.hour
        hourly_load = hourly_load.groupby('hour')['consumption'].max()
        new_peak = peak_shaving.shave_peaks(hourly_load, batCap)

        '''
        FINANCES
        '''
        annualCost = finance.calculate_cost(batCap, parameters['financials']['battery_price'],
                        parameters['financials']['interest_rate'],
                        parameters['financials']['equity_share'],
                        parameters['financials']['credit_duration'])

        '''
        STATS
        '''
        # self consumption
        optimizedDF = pd.DataFrame.from_dict(optimizedTS)
        batteryOwnConsumption = optimizedDF['batteryOwnConsumption'].sum()
        directOwnConsumption = optimizedDF['directOwnConsumption'].sum()
        totalOwnConsumption = batteryOwnConsumption + directOwnConsumption
        selfSufficiency = totalOwnConsumption / optimizedDF['consumption'].sum()

        selfConsumption = {
            "fromBattery": batteryOwnConsumption,
            "direct": directOwnConsumption,
            "total": totalOwnConsumption,
            "selfSufficiency": selfSufficiency
            }

        # peak shaving
        peakShaving  = {
            "newPeak": new_peak,
            "peakReduction": max(consumptionTS) - new_peak
        }

        oldHours = sum(consumptionTS) / max(consumptionTS)
        newHours = optimizedDF['gridImp'].sum() / new_peak

        if oldHours >= 2500:
            oldPowerPrice = max(consumptionTS) * parameters['grid_fees']['above_2500']['power_price']
        else:
            oldPowerPrice = max(consumptionTS) * parameters['grid_fees']['below_2500']['power_price']

        if newHours >= 2500:
            newPowerPrice = optimizedDF['gridImp'].max() * parameters['grid_fees']['above_2500']['power_price']
        else:
            newPowerPrice = optimizedDF['gridImp'].max() * parameters['grid_fees']['below_2500']['power_price']

        peakPriceSavings = max(0, oldPowerPrice - newPowerPrice)

        # financial
        lostRevenue = (optimizedDF['conversionLoss'].sum() + optimizedDF['batteryOwnConsumption'].sum()) * parameters['power_prices']['feed_in_price']
        newPpaRevenue = optimizedDF['batteryOwnConsumption'].sum() * parameters['power_prices']['ppa_price']

        if newHours >= 2500:
            consumptionPrice = parameters['grid_fees']['above_2500']['consumption_price']
        else:
            consumptionPrice = parameters['grid_fees']['below_2500']['consumption_price']

        ppaCost =  totalOwnConsumption.sum() * parameters['power_prices']['ppa_price']
        gridCost = directOwnConsumption.sum() * parameters['power_prices']['net_power_price']
        gridFee = newPowerPrice + (totalOwnConsumption.sum() * consumptionPrice)
        otherFee = directOwnConsumption.sum() * parameters['grid_fees']['below_2500']['other_fees']

        totalCost = ppaCost + gridCost + gridFee + otherFee

        allCosts = {
            "PPA": ppaCost,
            "Grid": gridCost,
            "GFee": gridFee,
            "OFEE": otherFee,
            "TFE": totalCost
        }


        financial = {
            "annualInterest": annualCost,
            "lostRevenue": lostRevenue,
            "newPpaRevenue": newPpaRevenue,
            "peakPriceSavings": peakPriceSavings,
            "totalCost": allCosts
        }

        # power metrics
        powerMetrics = {
            "usageHours": newHours,
            "gridImport": optimizedDF['gridImp'].sum(),
            "powerConsumption": optimizedDF['consumption'].sum()
        }

        '''
        Result
        '''
        result = {
            "capacity": batCap,
            "selfConsumption": selfConsumption,
            "peakShaving": peakShaving,
            "financial": financial,
            "powerMetrics": powerMetrics
            }

        results.append(result)


    return results, statusQuoLoad