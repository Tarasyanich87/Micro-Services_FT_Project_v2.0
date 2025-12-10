import pytest
from management_server.services.strategy_analysis_service import StrategyAnalysisService

@pytest.fixture
def analysis_service():
    """Provides an instance of the StrategyAnalysisService."""
    return StrategyAnalysisService()

# A valid strategy using modern method names
VALID_MODERN_STRATEGY = """
from freqtrade.strategy import IStrategy

class MyModernStrategy(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = '1h'
    can_short = True

    def populate_indicators(self, dataframe, metadata: dict):
        return dataframe

    def populate_entry_trend(self, dataframe, metadata: dict):
        return dataframe

    def populate_exit_trend(self, dataframe, metadata: dict):
        return dataframe
"""

# A valid strategy using legacy method names
VALID_LEGACY_STRATEGY = """
from freqtrade.strategy import IStrategy

class MyLegacyStrategy(IStrategy):
    INTERFACE_VERSION = 2
    timeframe = '5m'

    def populate_indicators(self, dataframe, metadata: dict):
        return dataframe

    def populate_buy_trend(self, dataframe, metadata: dict):
        return dataframe

    def populate_sell_trend(self, dataframe, metadata: dict):
        return dataframe
"""

# An invalid strategy missing the timeframe attribute
INVALID_MISSING_TIMEFRAME = """
from freqtrade.strategy import IStrategy

class InvalidStrategy(IStrategy):
    INTERFACE_VERSION = 3

    def populate_indicators(self, dataframe, metadata: dict):
        return dataframe

    def populate_entry_trend(self, dataframe, metadata: dict):
        return dataframe

    def populate_exit_trend(self, dataframe, metadata: dict):
        return dataframe
"""

# An invalid strategy missing a required method
INVALID_MISSING_METHOD = """
from freqtrade.strategy import IStrategy

class InvalidStrategy(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = '1h'

    def populate_indicators(self, dataframe, metadata: dict):
        return dataframe

    def populate_exit_trend(self, dataframe, metadata: dict):
        return dataframe
"""

# Code with a Python syntax error
SYNTAX_ERROR_CODE = """
from freqtrade.strategy import IStrategy

class MyStrategy(IStrategy) # Missing colon
    pass
"""

# Code that does not inherit from IStrategy
NOT_A_STRATEGY_CODE = """
class NotAStrategy:
    timeframe = '1h'
"""

def test_analyze_valid_modern_strategy(analysis_service):
    """
    Tests that a strategy with modern method names ('populate_entry_trend', 'populate_exit_trend') is considered valid.
    """
    result = analysis_service.analyze(VALID_MODERN_STRATEGY)
    assert result['valid'] is True
    assert not result['errors']
    assert result['parameters']['timeframe'] == '1h'
    assert result['parameters']['can_short'] is True
    assert result['parameters']['INTERFACE_VERSION'] == 3

def test_analyze_valid_legacy_strategy(analysis_service):
    """
    Tests that a strategy with legacy method names ('populate_buy_trend', 'populate_sell_trend') is also considered valid for backward compatibility.
    """
    result = analysis_service.analyze(VALID_LEGACY_STRATEGY)
    assert result['valid'] is True
    assert not result['errors']
    assert result['parameters']['timeframe'] == '5m'
    assert result['parameters']['INTERFACE_VERSION'] == 2

def test_analyze_missing_timeframe(analysis_service):
    """
    Tests that the analysis fails if the required 'timeframe' attribute is missing.
    """
    result = analysis_service.analyze(INVALID_MISSING_TIMEFRAME)
    assert result['valid'] is False
    assert "Missing required attribute: 'timeframe'." in result['errors']

def test_analyze_missing_method(analysis_service):
    """
    Tests that the analysis fails if a required method (e.g., 'populate_entry_trend') is missing.
    """
    result = analysis_service.analyze(INVALID_MISSING_METHOD)
    assert result['valid'] is False
    assert "Missing required method: 'populate_entry_trend' (or legacy 'populate_buy_trend')." in result['errors']

def test_analyze_syntax_error(analysis_service):
    """
    Tests that the analysis correctly identifies a Python syntax error in the code.
    """
    result = analysis_service.analyze(SYNTAX_ERROR_CODE)
    assert result['valid'] is False
    assert "Invalid Python syntax" in result['errors'][0]

def test_analyze_not_a_strategy(analysis_service):
    """
    Tests that the analysis fails if the code does not contain a class inheriting from 'IStrategy'.
    """
    result = analysis_service.analyze(NOT_A_STRATEGY_CODE)
    assert result['valid'] is False
    assert "Could not find a class inheriting from 'IStrategy'." in result['errors']
