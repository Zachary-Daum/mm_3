import pandas as pd

from .intern.logging import Logger

asset_log = Logger('asset_log','./logs/assets.LOG')

class Asset:
    def __init__(self,ticker=None, price_change_factor=None):
        self.ticker = ticker
        self.tick = 1

        # - Fitted Params - #
        self.params = pd.Series({'price_change_factor':price_change_factor}) # Permanent, only for upticks

        # - Variables - #
        # * Get initial price from real data
        historical_data = pd.read_csv(f'./training_data/{self.ticker}.csv')['Open']

        # * Need getters and setters for all of these
        self._bid_volume = 0
        self._offer_volume = 0
        self.vars = pd.DataFrame({'price':historical_data[0:3].tolist(),'bid_volume':[0,0,0],'offer_volume':[0,0,0]})

    # === Utils === #
    @property
    def price(self,tick=None): 
        # Only a getter so its okay if this is called on run() ticks
        return self.vars.at[self.tick,'price'] if tick==None else self.vars.at[tick,'price']

    @price.setter
    def price(self, new_price):
        '''Only called so set new price on upticks'''
        self.vars.at[self.tick+1,'price'] = new_price

    # === Calculations === #
    def adjust_price(self, price_change_factor=None, bid_volume=None, offer_volume=None):
        return self.price + ( price_change_factor * (bid_volume - offer_volume) )
    
    # === Functions === #
    def clear_volumes(self):
        '''Called after each run so that bid and offer volumes aren't adding up over time'''
        self._bid_volume = 0
        self._offer_volume = 0

    def run(self,params=None):
        # _ Return Predicted asset price _ #
        return self.adjust_price(price_change_factor=params.at[f'{self.ticker}_price_change_factor'], bid_volume=self._bid_volume, offer_volume=self._offer_volume)

    def prep_uptick(self):
        # * Set volume for the coming tick to 0
        self.vars.at[self.tick+1, 'bid_volume'] = 0 # Needs to be zero so the += operation can be done
        self.vars.at[self.tick+1, 'offer_volume'] = 0

    def uptick(self,params=None):
        self.tick += 1
        asset_log.debug(f"Agent {self.ticker} uptick to {self.tick}")

        # Update ALL params
        self.params.at['price_change_factor'] = params.at[f'{self.ticker}_price_change_factor']

        # - Run Asset - #
        # * Calculate the next price
        self.vars.at[self.tick+1,'price'] = self.adjust_price(price_change_factor=self.params.at['price_change_factor'],bid_volume=self.vars.at[self.tick,'bid_volume'],offer_volume=self.vars.at[self.tick,'offer_volume'])

        asset_log.debug(f"""
        ==== Asset {self.ticker} | Tick: {self.tick} ====
        --- Price ---
        {self.price}
        --- Bid Volume ---
        {self.vars.at[self.tick,'bid_volume']}
        --- Offer Volume ---
        {self.vars.at[self.tick,'offer_volume']}
        """)