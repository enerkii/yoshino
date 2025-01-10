import numpy_financial as npf

def calculate_cost(capacity, price, interest_rate, equity_share, duration):
    creditAmount = capacity * price * (1 - equity_share)
    return npf.pmt(interest_rate, duration, -creditAmount)