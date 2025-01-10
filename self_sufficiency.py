import pandas as pd
import numpy as np
import numpy_financial as npf

'''
FUNCTIONS
'''
def dis_charge(pvYield, consumption, batterySoc, batteryCap, efficiency, duration):
    batteryPower = batteryCap / duration
    batteryCharge = 0
    batteryDischarge = 0
    gridImp = 0
    gridExp = 0
    
    productionSurplus = pvYield - consumption

    # charge battery if production > consumption
    if productionSurplus > 0:
        spareCapacity = batteryCap - batterySoc
        maxCharge = min(spareCapacity * efficiency, batteryPower)
        batteryCharge = min(productionSurplus, maxCharge)
        gridExp = productionSurplus - batteryCharge
    
    # discharge battery if consumption > production
    elif productionSurplus <= 0:
        productionDeficit = - productionSurplus
        remainingCapacity = batterySoc
        maxDischarge = min(remainingCapacity, batteryPower)
        batteryDischarge = min(maxDischarge, productionDeficit / efficiency)
        gridImp = consumption - pvYield - (batteryDischarge * efficiency)
    
    # adjust battery charge
    newBatterySoc = batterySoc - batteryDischarge + batteryCharge * 0.96

    return gridImp, gridExp, batteryCharge, batteryDischarge, newBatterySoc

def optimize_year(pvYield_ts, consumption_ts, batteryCap, efficiency, duration):
    '''
    LOOP OVER ENTIRE YEAR
    '''
    batterySoc_ts = np.zeros(len(pvYield_ts), dtype=float)
    batteryPower = batteryCap / duration
    decisions = []
    for i in range(len(pvYield_ts)):
        startSoc = batterySoc_ts[i]

        # calculate charges
        gridImp, gridExp, batteryCharge, batteryDischarge, batterySoc = dis_charge(pvYield_ts[i], consumption_ts[i], startSoc, batteryCap, efficiency, duration)
        directOwnConsumption = pvYield_ts[i] - batteryCharge - gridExp
        batteryOwnConsumption = batteryDischarge * efficiency
        conversionLoss = (batteryCharge + batteryDischarge) * (1 - efficiency) 

        # update battery soc
        endSoc = batterySoc
        if i < len(pvYield_ts) - 1:
            batterySoc_ts[i + 1] = endSoc

        # append decision
        decision = {'pvYield': pvYield_ts[i], 'consumption': consumption_ts[i], 'gridImp': gridImp, 'gridExp': gridExp,
                    'batteryCharge': batteryCharge, 'batteryDischarge': batteryDischarge, 'batterySoc': startSoc,
                    'directOwnConsumption': directOwnConsumption, 'batteryOwnConsumption': batteryOwnConsumption, 
                    'conversionLoss': conversionLoss}
        decisions.append(decision)
    return decisions
