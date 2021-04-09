from core.market import Market
from core.utils import mean_squared_error, historical_asset_data

from core.intern.logging import Logger

from multiprocessing import Pool, cpu_count
from copy import deepcopy

import pandas as pd

# Clear Logs Before Running
from clear_logs import clr_logs

logging = Logger('main','./logs/market.LOG')
model_log = Logger('model','./logs/model.LOG')

'''Agents and Assets Created'''
assets = ['AXP','AMGN','AAPL','BA','CAT','CSCO','CVX','GS','HD','HON','IBM','INTC','JNJ','KO','JPM'] # ,'MCD','MMM','MRK','MSFT','NKE','PG','TRV','UNH','CRM','VZ','V','WBA','WMT','DIS','DOW'
agents = range(5) 

'''Train Model'''
def gradient(args=None):
    # - Calculate Gradient Slope - #
    market = args[0]
    working_param = args[1]
    # * Given a parameter +1 and -1  
    param_set = (args[2],args[3])
    
    dx = 2*args[4]

    # Run model w/ params 1 & 2 - Return list of new calculated asset prices
    param_down_results = market.run(param_set[0])
    param_up_results = market.run(param_set[1])

    # _ Training Data for MSE _ #
    actual_price_list = []
    for asset in market.asset_dict:
        actual_price_list.append(historical_asset_data(asset)[market.tick])

    # Errors of each parameter set (Cost Function
    param_down_mse = mean_squared_error(actual_price_list,param_down_results)
    param_up_mse = mean_squared_error(actual_price_list,param_up_results)

    # Return slope of cost function dy/dx
    return (working_param ,( param_up_mse - param_down_mse ) / dx) # Return tuple of ([working_param],[slope])

def train(model=None, learn_rate=10e-5, n_iter=10, adj_factor=0.1):
    # - Run Iterations - #
    for _ in range(n_iter):
        model_log.info(f'\n==== Initial Params ====\n{model.params}\n')
        # Create args=[] which have adjusted parameters
        args = []
        for param, value in model.params.items():
            # _ Adjust Parameter Up _ #
            working_params1 = deepcopy(model.params)
            working_params1.at[param] += adj_factor
            
            # _ Adjust Parameter Down _ #
            working_params2 = deepcopy(model.params)
            working_params2.at[param] -= adj_factor

            args.append((model,param,working_params1,working_params2,adj_factor))
        
        pool = Pool(cpu_count())
        res = pool.map(gradient,args) # Result is partial slopes of cost function

        model_log.info(f'\n==== Gradient ====\n{res}\n')

        # - Adjust Parameters - #
        diff = pd.Series({},dtype='float64')

        for item in res:
            diff.at[item[0]] = item[1] * -learn_rate
            
        for index, value in model.params.items():
            model.params.at[index] += diff.at[index]

        model_log.info(f'\n==== Adjusted Params ====\n{model.params}\n')

        # - Uptick - #
        model.uptick()
        print("Training: Model Upticked")

def test(model=None, n_iter=range(5)):
    for _ in n_iter:
        model.uptick()
        print("Testing: Model Upticked")

    for agent in model.agent_dict:
        working_agent = model.agent_dict[agent]
        working_agent.vars.to_csv(f'./model_data/agents/vars/{working_agent.name}_vars.csv',mode='w+')
        working_agent.ops.to_csv(f'./model_data/agents/ops/{working_agent.name}_ops.csv',mode='w+')

    for asset in model.asset_dict:
        working_asset = model.asset_dict[asset]
        working_asset.vars.to_csv(f'./model_data/assets/vars/{working_asset.ticker}_vars.csv',mode='w+')


if __name__ == "__main__":
    # Clear Logs before running
    clr_logs()

    '''Create Market'''
    simulation = Market(assets,agents)

    train(model=simulation)

    test(model=simulation)