import numpy as np
import pandas as pd
from pandas import DataFrame
import talib.abstract as ta
from freqtrade.strategy import (
    IStrategy,
    DecimalParameter,
    IntParameter,
    BooleanParameter,
)
import freqtrade.vendor.qtpylib.indicators as qtpylib


class FreqaiExampleStrategy(IStrategy):
    """
    Example strategy showing how to use FreqAI.
    This strategy uses FreqAI to make predictions on price movements.
    """

    INTERFACE_VERSION: int = 3

    # Strategy metadata
    minimal_roi = {"0": 0.1, "15": 0.05, "30": 0.025, "60": 0}
    stoploss = -0.1
    timeframe = "3m"

    # Strategy parameters
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False

    # Number of candles the strategy requires before producing valid signals
    startup_candle_count: int = 30

    # Optional order type mapping
    order_types = {
        "entry": "limit",
        "exit": "limit",
        "stoploss": "market",
        "stoploss_on_exchange": False,
    }

    # Optional order time in force
    order_time_in_force = {"entry": "gtc", "exit": "gtc"}

    def feature_engineering_expand_all(
        self, dataframe: DataFrame, period: int, metadata: dict, **kwargs
    ) -> DataFrame:
        """
        *Only functional with FreqAI enabled strategies*
        This function will automatically expand the defined features
        on the base timeframe (3m in this case) to other higher timeframes
        """
        dataframe["%-rsi-period"] = ta.RSI(dataframe, timeperiod=period)
        dataframe["%-mfi-period"] = ta.MFI(dataframe, timeperiod=period)
        dataframe["%-adx-period"] = ta.ADX(dataframe, timeperiod=period)
        dataframe["%-sma-period"] = ta.SMA(dataframe, timeperiod=period)
        dataframe["%-ema-period"] = ta.EMA(dataframe, timeperiod=period)
        dataframe["%-close-period"] = dataframe["close"]
        dataframe["%-high-period"] = dataframe["high"]
        dataframe["%-low-period"] = dataframe["low"]
        dataframe["%-volume-period"] = dataframe["volume"]

        return dataframe

    def feature_engineering_expand_basic(
        self, dataframe: DataFrame, metadata: dict, **kwargs
    ) -> DataFrame:
        """
        *Only functional with FreqAI enabled strategies*
        This function will automatically expand the defined features
        on the base timeframe (3m in this case) to other higher timeframes
        """
        dataframe["%-pct-change"] = dataframe["close"].pct_change()
        dataframe["%-raw_volume"] = dataframe["volume"]
        dataframe["%-raw_price"] = dataframe["close"]

        return dataframe

    def feature_engineering_standard(
        self, dataframe: DataFrame, metadata: dict, **kwargs
    ) -> DataFrame:
        """
        *Only functional with FreqAI enabled strategies*
        This function is called once with the dataframe intended to be
        used for the features
        """
        # All indicators must be populated before this function is called
        dataframe["%-day_of_week"] = (dataframe["date"].dt.dayofweek + 1) / 7
        dataframe["%-hour_of_day"] = (dataframe["date"].dt.hour + 1) / 25

        # RSI
        dataframe["%-rsi"] = ta.RSI(dataframe, timeperiod=14)

        # MFI
        dataframe["%-mfi"] = ta.MFI(dataframe)

        # SMA
        dataframe["%-sma_200"] = ta.SMA(dataframe, timeperiod=200)
        dataframe["%-sma_50"] = ta.SMA(dataframe, timeperiod=50)

        # EMA
        dataframe["%-ema_50"] = ta.EMA(dataframe, timeperiod=50)
        dataframe["%-ema_200"] = ta.EMA(dataframe, timeperiod=200)

        # Williams %R
        dataframe["%-willr"] = ta.WILLR(dataframe)

        # Bollinger Bands
        bollinger = qtpylib.bollinger_bands(
            qtpylib.typical_price(dataframe), window=20, stds=2
        )
        dataframe["%-bb_lowerband"] = bollinger["lower"]
        dataframe["%-bb_upperband"] = bollinger["upper"]
        dataframe["%-bb_middleband"] = bollinger["mid"]

        # Volume
        dataframe["%-volume"] = dataframe["volume"]

        # Price
        dataframe["%-close"] = dataframe["close"]
        dataframe["%-open"] = dataframe["open"]
        dataframe["%-high"] = dataframe["high"]
        dataframe["%-low"] = dataframe["low"]

        return dataframe

    def set_freqai_targets(
        self, dataframe: DataFrame, metadata: dict, **kwargs
    ) -> DataFrame:
        """
        *Only functional with FreqAI enabled strategies*
        Required function to set the targets for the model.
        All targets must be prepended with `&` to be recognized by the FreqAI internals.

        More details about feature engineering available:

        https://www.freqtrade.io/en/stable/freqai-feature-engineering
        """
        dataframe["&-s_close"] = (
            dataframe["close"]
            .shift(-self.freqai_info["feature_parameters"]["label_period_candles"])
            .rolling(self.freqai_info["feature_parameters"]["label_period_candles"])
            .mean()
            / dataframe["close"]
            - 1
        )

        return dataframe

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Add all the indicators to the dataframe.
        """
        # RSI
        dataframe["rsi"] = ta.RSI(dataframe)

        # MFI
        dataframe["mfi"] = ta.MFI(dataframe)

        # ADX
        dataframe["adx"] = ta.ADX(dataframe)

        # MACD
        macd, macdsignal, macdhist = ta.MACD(
            dataframe, fastperiod=12, slowperiod=26, signalperiod=9
        )
        dataframe["macd"] = macd
        dataframe["macdsignal"] = macdsignal
        dataframe["macdhist"] = macdhist

        # Bollinger Bands
        bollinger = qtpylib.bollinger_bands(
            qtpylib.typical_price(dataframe), window=20, stds=2
        )
        dataframe["bb_lowerband"] = bollinger["lower"]
        dataframe["bb_upperband"] = bollinger["upper"]
        dataframe["bb_middleband"] = bollinger["mid"]

        # EMA - Exponential Moving Average
        dataframe["ema50"] = ta.EMA(dataframe, timeperiod=50)
        dataframe["ema200"] = ta.EMA(dataframe, timeperiod=200)

        # SMA - Simple Moving Average
        dataframe["sma50"] = ta.SMA(dataframe, timeperiod=50)
        dataframe["sma200"] = ta.SMA(dataframe, timeperiod=200)

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Based on TA indicators, populates the entry signal for the given dataframe
        """
        dataframe.loc[
            (
                (dataframe["rsi"] < 30)
                & (dataframe["close"] < dataframe["bb_lowerband"])
                & (dataframe["volume"] > 0)
            ),
            "enter_long",
        ] = 1

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Based on TA indicators, populates the exit signal for the given dataframe
        """
        dataframe.loc[
            (
                (dataframe["rsi"] > 70)
                & (dataframe["close"] > dataframe["bb_upperband"])
            ),
            "exit_long",
        ] = 1

        return dataframe

    def leverage(
        self,
        pair: str,
        current_time,
        current_rate: float,
        proposed_leverage: float,
        max_leverage: float,
        entry_tag: str | None,
        side: str,
        **kwargs,
    ) -> float:
        """
        Customize leverage for each new trade. This method is only called in futures mode.

        :param pair: Pair that's currently analyzed
        :param current_time: datetime object, containing the current datetime
        :param current_rate: Rate, calculated based on pricing settings in exit_pricing.
        :param proposed_leverage: A leverage proposed by the bot.
        :param max_leverage: Max leverage allowed on this pair
        :param entry_tag: Optional entry_tag (buy_tag) if provided with the buy signal.
        :param side: 'long' or 'short' - indicating the direction of the proposed trade
        :return: A leverage amount, which is between 1.0 and max_leverage.
        """
        return 1.0
