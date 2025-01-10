import numpy as np

def shave_peaks(hourly_load, batCap):
    batterySoC = batCap
    adj_hourly_loads = hourly_load.copy().sort_values(ascending=False).reset_index(drop=True)

    for i in range(len(hourly_load)):
        currentMaximum = adj_hourly_loads.max()
        numMaximums = np.sum(currentMaximum == adj_hourly_loads)
        
        # Check if all values are equal to the maximum
        if numMaximums == len(adj_hourly_loads):
            break  # No more peaks to shave
        
        secondHighest = max([value for value in adj_hourly_loads if value != currentMaximum])

        amountToDeduct = currentMaximum - secondHighest
        totalAmountToDedcut = amountToDeduct * numMaximums

        possibleAmountToDeduct = min(batterySoC, totalAmountToDedcut)
        batterySoC -= possibleAmountToDeduct

        amountPerHour = possibleAmountToDeduct / numMaximums

        for i in range(numMaximums):
            adj_hourly_loads[i] -= amountPerHour
    
    return adj_hourly_loads.max()

