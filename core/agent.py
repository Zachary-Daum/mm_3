import pandas as pd
import random
import math

from .intern.logging import Logger
from .types import agent_types

logging = Logger('main','./logs/market.LOG')
order_book = Logger('order_book','./logs/books.LOG')
agent_log = Logger('agent_log','./logs/agents.LOG')

class Agent:
    def __init__(self,name=None, type=None, reversion_factor=None, extrapolation_degree=None, memory=None, misalignment_sensativity=None, type_change_proclivity=None):
        self.name = name
        self.tick = 1

        # - Fitted Params - #
        self._reversion_factor = reversion_factor # 'Private' variables are for run() function, Series params are for uptick()
        self._extrapolation_degree = extrapolation_degree
        self._memory = memory
        self._misalignment_sensativity = misalignment_sensativity
        # type_change_provlicity does not need a private variable because it is only called on upticks

        self.params = pd.Series({'reversion_factor':reversion_factor,'extrapolation_degree':extrapolation_degree,'memory':memory,'misalignment_sensativity':misalignment_sensativity,'type_change_proclivity':type_change_proclivity})

        # - Variables - #
        # * NOTE: Type is only ever modified on upticks so it doesn't need a private variable
        self._cash = random.uniform(100_000,1_000_000)
        self.vars = pd.DataFrame({'type':[type,type],'cash':[self._cash,self._cash],'holdings':[{},{}]})

        # - Operators - #
        # * Keep different set for runs() and make sure that gets regularly cleared
        # * All indexed by asset
        self._price_expectations = {}
        self._expected_returns = {}
        self._returns_variance = {}
        self._risk_aversion = {}
        self._optimal_shares = {}

        self.ops = pd.DataFrame({'price_expectations':[{},{}],'expected_returns':[{},{}],'returns_variance':[{},{}],'risk_aversion':[{},{}],'optimal_shares':[{},{}]})

        order_book.debug(f"Created asset {name}")

    # === Utils === #
    # * Getters and setters for type, cash
    @property
    def type(self):
        return self.vars.at[self.tick,'type']

    @type.setter
    def type(self,new_type):
        self.var.at[self.tick+1,'type'] = new_type

    @property
    def cash(self,tick=None):
        return self.vars.at[self.tick,'cash'] if tick==None else self.vars.at[tick,'cash']

    def update_cash(self,amount):
        self.vars.at[self.tick,'cash'] += amount

    # === Calculations === #
    def calc_expectations(self, asset_obj=None, reversion_factor=None, extrapolation_degree=None, memory=None):
        '''Args being passed must be specified (ex. reversion_factor=[reversion_factor param] when calling calc_expectations()) when this function is called as it needs to work for all types'''
        # NOTE:
        # * Price expectations are for the price of an asset at t+1
        # * Params are passed as variables so that they can be changed from run() and uptick()
        # * The past expectations used are always from the last uptick()
        asset_price = asset_obj.vars.at[self.tick,'price']
        
        if self.type == 0:
            # Fundamentalist Expectation
            price_expectation = asset_price + reversion_factor * ( self.ops.at[self.tick-1,'price_expectations'][asset_obj.ticker] - asset_price )
            return price_expectation

        else:
            # Momentum Trader & Contrarian Expectations
            sum = 0
            j = 0
            while j < self.tick:
                '''If j = self.tick then this well return a KeyError with t-1-j'''
                sum +=  pow( 1 - memory , j ) * ( asset_obj.vars.at[self.tick - j,'price'] - asset_obj.vars.at[self.tick - 1 -j,'price'] )
                j += 1

            price_expectation = asset_price + extrapolation_degree * memory * sum
            return price_expectation

    @staticmethod
    def calc_expected_returns(expected_price=None, current_price=None):
        return expected_price - current_price

    def calc_returns_variance(self, asset_obj=None, expected_returns=None):
        sum = 0
        j = 1
        while j <= self.tick:
            temp1 = ( asset_obj.vars.at[j,'price'] - asset_obj.vars.at[j-1,'price'] ) / asset_obj.vars.at[j-1,'price']
            temp2 = expected_returns / asset_obj.price

            sum += (temp1 - temp2)**2

            j += 1

        return (sum / self.tick)

    def calc_risk_aversion(self, asset_obj=None, universal_risk_aversion=None, misalignment_sensativity=None):
        if self.type == 0:
            price_change = asset_obj.vars.at[self.tick,'price'] - asset_obj.vars.at[self.tick-1,'price']
            risk_aversion = ( universal_risk_aversion ) / ( 1 + misalignment_sensativity * price_change )
            return risk_aversion

        else:
            return universal_risk_aversion

    @staticmethod
    def calc_optimal_shares(expected_returns=None, risk_aversion=None, returns_variance=None):
        optimal_shares = math.floor( expected_returns / ( risk_aversion * returns_variance ) )
        return optimal_shares if optimal_shares > 0 else 0
     
    def calc_wealth(self, asset_dict=None):
        '''This function is necessary for calculating the return on wealth for the eval_type() funciton.'''
        sum = 0
        for asset in self.vars.at[self.tick,'holdings']:
            # Sum of the value of all holdings
            sum += self.vars.at[self.tick,'holdings'][asset] * asset_dict[asset].vars.at[self.tick,'price']

        wealth = self.cash + sum
        return wealth

    '''def eval_type(self):
        type_change_proclivity = self.params.at['type_change_proclivity']
        # Evauluate sum first bc it is used multiple times
        sum = 0
        for type in agent_types:
            sum += math.exp( type_change_proclivity * agent_types[type].score )
        
        def calc_choice_probability(type=None):

            probability = math.exp( agent_types[type].score ) / sum
            return probability

        selected_type = random.choices([0,1,2], weights = [calc_choice_probability(0),calc_choice_probability(1),calc_choice_probability(2)])
        return selected_type'''
        
    # === Functions === #
    def init_ops(self,asset_dict=None):
        for asset in asset_dict:
            '''All operators that the agent performs need to have initial values'''
            self.ops.at[0,'price_expectations'][asset] = asset_dict[asset].price
            self.ops.at[0,'expected_returns'][asset] = 0
            self.ops.at[0,'returns_variance'][asset] = 1
            self.ops.at[0,'risk_aversion'][asset] = 0
            self.ops.at[0,'optimal_shares'][asset] = 0

            # Set the same values for t=1
            self.ops.at[1,'price_expectations'][asset] = asset_dict[asset].price
            self.ops.at[1,'expected_returns'][asset] = 0
            self.ops.at[1,'returns_variance'][asset] = 1
            self.ops.at[1,'risk_aversion'][asset] = 0
            self.ops.at[1,'optimal_shares'][asset] = 0

            # So that holdings doesn't thrown an error
            self.vars.at[0,'holdings'][asset] = 0
            self.vars.at[1,'holdings'][asset] = 0

    def prep_uptick(self,asset_dict=None):
        price_expectations = {}
        expected_returns = {}
        returns_variance = {}
        risk_aversion = {}
        optimal_shares = {}

        holdings = {}

        for asset in asset_dict:
            price_expectations[asset] = 0 # Stored as 0 just as a placeholder for now
            expected_returns[asset] = 0
            returns_variance[asset] = 0
            risk_aversion[asset] = 0
            optimal_shares[asset] = 0

            holdings[asset] = self.vars.at[self.tick,'holdings'][asset]

        # Append to ops DF
        self.ops = self.ops.append({'price_expectations':price_expectations,'expected_returns':expected_returns,'returns_variance':returns_variance,'risk_aversion':risk_aversion,'optimal_shares':optimal_shares}, ignore_index=True)

        # - Update self.vars DF - #
        cash = self.vars.at[self.tick,'cash'] # Temporary
        
        self.vars = self.vars.append({'type':self.vars.at[self.tick-1,'type'],'cash':cash,'holdings':holdings}, ignore_index=True)

    def run(self,params=None,asset_dict=None):
        for asset in asset_dict:
            working_asset = asset_dict[asset]

            self._price_expectations[asset] = self.calc_expectations(
                asset_obj = working_asset,
                reversion_factor = params.at[f'{self.name}_reversion_factor'],
                extrapolation_degree = params.at[f'{self.name}_extrapolation_degree'],
                memory = params.at[f'{self.name}_memory']
            )

            self._expected_returns[asset] = self.calc_expected_returns(
                expected_price = self._price_expectations[asset],
                current_price = working_asset.price # We don't use a similuated price here because prices are always calcuated for one tick ahead
            )

            self._returns_variance[asset] = self.calc_returns_variance(
                asset_obj = working_asset,
                expected_returns = self._expected_returns[asset]
            )

            self._risk_aversion[asset] = self.calc_risk_aversion(
                asset_obj = working_asset,
                universal_risk_aversion = params.at['universal_risk_aversion'], 
                misalignment_sensativity = params.at[f'{self.name}_misalignment_sensativity']
            )

            self._optimal_shares[asset] = self.calc_optimal_shares(
                expected_returns = self._expected_returns[asset],
                risk_aversion = self._risk_aversion[asset],
                returns_variance = self._returns_variance[asset]
            )

        # - Place Order - #
        # FIXME:
        # * Order sizes are too large
        #    * IS THIS ONLY THE CASE FOR SOME TYPES?
        # * Asset prices in run() aren't changing
        for asset in asset_dict:
            '''
            Since this is just in run() the only thing that matters is that volumes get updated
            * No fractional orders so all orders are rounded down
            '''
            if self.vars.at[self.tick,'holdings'][asset] < self._optimal_shares[asset]:
                # "buy" order
                order_size = math.floor ( self._optimal_shares[asset] - self.vars.at[self.tick,'holdings'][asset] )

                # Make sure buy price isn't greater than balance.
                if order_size * asset_dict[asset].price > self.cash:
                    order_size = math.floor( self.cash / asset_dict[asset].price )

                asset_dict[asset]._bid_volume += order_size

            elif self.vars.at[self.tick,'holdings'][asset] > self._optimal_shares[asset]:
                # "sell" order
                order_size = math.floor( self.vars.at[self.tick,'holdings'][asset] - self._optimal_shares[asset] )
                asset_dict[asset]._offer_volume += order_size

            else:
                pass

    def uptick(self,params=None,asset_dict=None):
        # - Prep Uptick - #
        self.prep_uptick(asset_dict)

        self.tick += 1

        logging.info(f"Agent {self.name} vars at {self.tick}:\n{self.vars}\n")

        # - Update Paramaters - #
        self.params.at['reversion_factor'] = params.at[f'{self.name}_reversion_factor']
        self.params.at['extrapolation_degree'] = params.at[f'{self.name}_extrapolation_degree']
        self.params.at['memory'] = params.at[f'{self.name}_memory']
        self.params.at['misalignment_sensativity'] = params.at[f'{self.name}_misalignment_sensativity']
        self.params.at['type_change_proclivity'] = params.at[f'{self.name}_type_change_proclivity']

        # - Calculations - #
        for asset in asset_dict:
            working_asset = asset_dict[asset]

            self.ops.at[self.tick,'price_expectations'][asset] = self.calc_expectations(asset_obj=working_asset, reversion_factor=self.params.at['reversion_factor'] , extrapolation_degree=self.params.at['extrapolation_degree'], memory=self.params.at['memory'])

            self.ops.at[self.tick,'expected_returns'][asset] = self.calc_expected_returns(
                expected_price = self.ops.at[self.tick,'price_expectations'][asset],
                current_price = working_asset.price
            )

            self.ops.at[self.tick,'returns_variance'][asset] = self.calc_returns_variance(
                asset_obj = working_asset,
                expected_returns = self.ops.at[self.tick,'expected_returns'][asset]
            )

            self.ops.at[self.tick,'risk_aversion'][asset] = self.calc_risk_aversion(
                asset_obj = working_asset,
                universal_risk_aversion = params.at['universal_risk_aversion'],
                misalignment_sensativity = self.params.at['misalignment_sensativity']
            )

            self.ops.at[self.tick,'optimal_shares'][asset] = self.calc_optimal_shares(
                expected_returns = self.ops.at[self.tick,'expected_returns'][asset],
                risk_aversion = self.ops.at[self.tick,'risk_aversion'][asset],
                returns_variance = self.ops.at[self.tick,'returns_variance'][asset]
            )
        # - Place Orders - #
        # * No fractional orders allowed. (We'll just round down)
        # * Make sure orders go towards the .vars DF for each asset
        for asset in asset_dict:
            if self.vars.at[self.tick,'holdings'][asset] < self.ops.at[self.tick,'optimal_shares'][asset]:
                # Buy
                order_size = math.floor( self.ops.at[self.tick,'optimal_shares'][asset] - self.vars.at[self.tick,'holdings'][asset] )

                order_price = order_size * asset_dict[asset].price

                if order_price > self.cash:
                    # Not enough money
                    order_size = math.floor( self.cash / asset_dict[asset].price )

                    order_price = order_size * asset_dict[asset].price

                # Change cash levels 
                self.vars.at[self.tick,'cash'] -= order_price

                # Change Holdings
                self.vars.at[self.tick,'holdings'][asset] += order_size

                # Change volume
                asset_dict[asset].update_bid_volume(order_size)

                order_book.info(f'Agent {self.name} bought {order_size} shares of {asset}.')

            elif self.vars.at[self.tick,'holdings'][asset] > self.ops.at[self.tick,'optimal_shares'][asset]:
                # Sell
                order_size = math.floor( self.vars.at[self.tick,'holdings'][asset] - self.ops.at[self.tick,'optimal_shares'][asset] )

                order_price = order_size * asset_dict[asset].price

                # Add Balance 
                self.vars.at[self.tick,'cash'] += order_price

                # Change Holdings
                self.vars.at[self.tick,'holdings'][asset] -= order_size

                # Change offer volume
                asset_dict[asset].update_offer_volume(order_size)

                order_book.info(f'Agent {self.name} sold {order_size} shares of {asset}.')


            else:
                order_book.info(f"Agent {self.name} passed on {asset}.")

        # - Record Uptick - #
        agent_log.debug(f"""
        ==== Agent {self.name} [{self.vars.at[self.tick,'type']}] | Tick: {self.tick} ====
        --- Price Expectations ---
        {self.ops.at[self.tick,'price_expectations']}
        --- Expected Returns ---
        {self.ops.at[self.tick,'expected_returns']}
        --- Returns Variance ---
        {self.ops.at[self.tick,'returns_variance']}
        --- Risk Aversion ---
        {self.ops.at[self.tick,'risk_aversion']}
        --- Optimal Shares ---
        {self.ops.at[self.tick,'optimal_shares']}
        --- Holdings ---
        {self.vars.at[self.tick,'holdings']}
        """)

        # Append chage in wealth to type

