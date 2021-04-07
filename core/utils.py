import numpy as np
import pandas as pd

def mean_squared_error(actual=None, pred=None): 
    actual, pred = np.array(actual), np.array(pred)
    return np.square(np.subtract(actual,pred)).mean() 

def historical_asset_data(asset=None):
    return pd.read_csv(f'./training_data/{asset}.csv')['Open']