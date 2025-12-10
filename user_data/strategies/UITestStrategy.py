
from freqtrade.strategy import IStrategy
from typing import Dict, List
import numpy as np
import pandas as pd

class UITestStrategy(IStrategy):
    """
    Test strategy for UI testing
    """

    INTERFACE_VERSION = 3
    minimal_roi = {"0": 0.10}
    stoploss = -0.10
    timeframe = '5m'

    def populate_indicators(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        dataframe['rsi'] = ta.RSI(dataframe)
        return dataframe

    def populate_buy_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        dataframe.loc[dataframe['rsi'] < 30, 'buy'] = 1
        return dataframe

    def populate_sell_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        dataframe.loc[dataframe['rsi'] > 70, 'sell'] = 1
        return dataframe
