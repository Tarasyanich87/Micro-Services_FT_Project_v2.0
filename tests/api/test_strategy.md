# SampleStrategy

## parameter: timeframe = "1h"
## parameter: stoploss = -0.10

## method_name: populate_indicators
```python
def populate_indicators(self, dataframe, metadata):
    dataframe['rsi'] = ta.RSI(dataframe)
    return dataframe
```

## method_name: populate_buy_trend
```python
def populate_buy_trend(self, dataframe, metadata):
    dataframe.loc[:, 'buy'] = dataframe['rsi'] < 30
    return dataframe
```

## method_name: populate_sell_trend
```python
def populate_sell_trend(self, dataframe, metadata):
    dataframe.loc[:, 'sell'] = dataframe['rsi'] > 70
    return dataframe
```
