from .agent import Agent
from .asset import Asset

import pandas as pd
import random
from copy import deepcopy

class Market:
    def __init__(self,asset_range=None,agent_range=None):
        self.tick = 1
        
        self.asset_dict = {}
        self.agent_dict = {}

        # - Model Parameters - #
        self.universal_risk_aversion = random.random()
        self.params = pd.Series({'universal_risk_aversion':self.universal_risk_aversion})
    
        # - Create Agents & Assets - #
        for asset in asset_range:
            # _ Asset Params _ #
            price_change_factor = random.uniform(.05,.005)
            self.params = self.params.append( pd.Series({f'{asset}_price_change_factor':price_change_factor}) )
            # _ Init Asset _ #
            self.asset_dict[asset] = Asset(asset,price_change_factor)

        for agent in agent_range:
            # _ Agent Params _ #
            type = random.randint(0,2)
            reversion_factor = random.random()
            extrapolation_degree = random.random() if type==1 else random.uniform(-1,0)
            memory = random.random()
            misalignment_sensativity = random.random()
            type_change_proclivity = random.random()

            self.params = self.params.append( pd.Series({f'{agent}_reversion_factor':reversion_factor,f'{agent}_extrapolation_degree':extrapolation_degree,f'{agent}_memory':memory,f'{agent}_misalignment_sensativity':misalignment_sensativity,f'{agent}_type_change_proclivity':type_change_proclivity}) )
            # _  Init Agent _ #
            self.agent_dict[agent] = Agent(agent, type, reversion_factor, extrapolation_degree, memory, misalignment_sensativity, type_change_proclivity)
            self.agent_dict[agent].init_ops(self.asset_dict)

        print("Market Initialized")

    # = Run Model = #    
    def run(self, param_set=None):
        # FIXME: Ensure all variables are reset
        for agent in self.agent_dict:
            self.agent_dict[agent].run(param_set,self.asset_dict)

        pred_prices = []
        for asset in self.asset_dict:
            pred_prices.append( self.asset_dict[asset].run(param_set) ) # Return asset_price
            self.asset_dict[asset].clear_volumes()
 
        return pred_prices

    # = Uptick Model = #
    def uptick(self):
        self.tick += 1
        for asset in self.asset_dict:
            '''Needs to be called so that volumes can be assembled when agents place their orders'''
            self.asset_dict[asset].prep_uptick()

        for agent in self.agent_dict:
            self.agent_dict[agent].uptick(self.params,self.asset_dict)

        for asset in self.asset_dict:
            self.asset_dict[asset].uptick(self.params)

        # Log Params to File
        working_params = deepcopy(self.params)

        working_params = working_params.to_frame().T
        working_params.to_csv('./model_data/params.csv',header=False,mode='a')