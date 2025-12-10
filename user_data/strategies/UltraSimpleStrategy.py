# Ultra Simple Strategy for Dry Run Testing
from freqtrade.strategy import IStrategy
from pandas import DataFrame


class UltraSimpleStrategy(IStrategy):
    """
    Ultra simple strategy for testing Freqtrade dry-run functionality.
    No external dependencies, just basic logic.
    """

    timeframe = "5m"

    # Minimal ROI
    minimal_roi = {
        "0": 0.05  # 5% profit
    }

    # Stoploss
    stoploss = -0.03  # 3% stop loss

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """Add basic indicators"""
        # Simple moving average
        dataframe['sma'] = dataframe['close'].rolling(window=10).mean()
        return dataframe

    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """Simple buy signal"""
        dataframe.loc[
            (
                (dataframe['close'] > dataframe['sma']) &  # Price above SMA
                (dataframe['volume'] > 0)  # Has volume
            ),
            'buy'] = 1
        return dataframe

    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """Simple sell signal"""
        dataframe.loc[
            (
                (dataframe['close'] < dataframe['sma'])  # Price below SMA
            ),
            'sell'] = 1
        return dataframe</content>
<parameter name="filePath">jules_freqtrade_project/user_data/strategies/UltraSimpleStrategy.py