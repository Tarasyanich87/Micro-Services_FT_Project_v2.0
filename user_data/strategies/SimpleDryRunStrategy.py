# Simple Strategy for Dry Run Testing
from freqtrade.strategy import IStrategy
from pandas import DataFrame


class SimpleDryRunStrategy(IStrategy):
    """
    Simple strategy for testing Freqtrade dry-run functionality.
    Uses basic pandas operations without external dependencies.
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
        dataframe['sma'] = dataframe['close'].rolling(window=20).mean()

        # Simple RSI-like indicator (simplified)
        delta = dataframe['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        dataframe['rsi'] = 100 - (100 / (1 + rs))

        return dataframe

    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """Generate buy signals"""
        dataframe.loc[
            (
                (dataframe['rsi'] < 35) &  # RSI oversold
                (dataframe['close'] > dataframe['sma'])  # Price above SMA
            ),
            'buy'] = 1
        return dataframe

    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """Generate sell signals"""
        dataframe.loc[
            (
                (dataframe['rsi'] > 65)  # RSI overbought
            ),
            'sell'] = 1
        return dataframe</content>
<parameter name="filePath">jules_freqtrade_project/user_data/strategies/SimpleDryRunStrategy.py