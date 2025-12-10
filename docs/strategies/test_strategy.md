# MyTestStrategy
## timeframe: 1h
## stoploss: -0.15
## minimal_roi
```json
{
    "0": 0.1,
    "30": 0.05
}
```
## populate_indicators
```python
dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)
return dataframe
```
## populate_entry_trend
```python
dataframe.loc[
    (
        (dataframe['rsi'] < 30)
    ),
    'enter_long'] = 1
return dataframe
```
## populate_exit_trend
```python
dataframe.loc[
    (
        (dataframe['rsi'] > 70)
    ),
    'exit_long'] = 1
return dataframe
```
