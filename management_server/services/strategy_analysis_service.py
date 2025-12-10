import ast
from typing import Dict, Any, List, Tuple

class StrategyAnalysisService:
    """
    A service to analyze and verify Freqtrade strategy code based on official requirements.
    It uses Abstract Syntax Trees (AST) for safe code inspection.
    """

    # Modern method names (as of Freqtrade versions post-2021)
    REQUIRED_METHODS_MODERN = {
        "populate_indicators",
        "populate_entry_trend",
        "populate_exit_trend",
    }
    # Legacy method names for backward compatibility
    REQUIRED_METHODS_LEGACY = {
        "populate_indicators",
        "populate_buy_trend",
        "populate_sell_trend",
    }

    REQUIRED_ATTRIBUTES = {
        "timeframe",
    }


    def analyze(self, code: str) -> Dict[str, Any]:
        """
        Analyzes strategy code to extract parameters and verify its structure.

        Returns a dictionary with:
        - 'parameters': Extracted strategy attributes.
        - 'errors': A list of verification errors found.
        - 'valid': A boolean indicating if the strategy is valid.
        """
        errors = []
        parameters: Dict[str, Any] = {}
        found_methods = set()
        found_attributes = set()

        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            errors.append(f"Invalid Python syntax: {e}")
            return {"parameters": {}, "errors": errors, "valid": False}

        strategy_class_node = None
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                is_strategy = any(
                    isinstance(base, ast.Name) and base.id == 'IStrategy'
                    for base in node.bases
                )
                if is_strategy:
                    strategy_class_node = node
                    break

        if not strategy_class_node:
            errors.append("Could not find a class inheriting from 'IStrategy'.")
            # Return early if no strategy class is found
            return {"parameters": parameters, "errors": errors, "valid": False}

        # Extract attributes and methods from the strategy class
        for node in strategy_class_node.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        param_name = target.id
                        found_attributes.add(param_name)
                        try:
                            parameters[param_name] = ast.literal_eval(node.value)
                        except (ValueError, SyntaxError):
                            parameters[param_name] = "Complex/Dynamic Value"

            elif isinstance(node, ast.FunctionDef):
                found_methods.add(node.name)

        # Verify required attributes
        missing_attributes = self.REQUIRED_ATTRIBUTES - found_attributes
        if missing_attributes:
            for attr in missing_attributes:
                errors.append(f"Missing required attribute: '{attr}'.")

        # Verify required methods (modern or legacy names)
        has_modern_methods = self.REQUIRED_METHODS_MODERN.issubset(found_methods)
        has_legacy_methods = self.REQUIRED_METHODS_LEGACY.issubset(found_methods)

        if not (has_modern_methods or has_legacy_methods):
            if 'populate_entry_trend' not in found_methods and 'populate_buy_trend' not in found_methods:
                 errors.append("Missing required method: 'populate_entry_trend' (or legacy 'populate_buy_trend').")
            if 'populate_exit_trend' not in found_methods and 'populate_sell_trend' not in found_methods:
                 errors.append("Missing required method: 'populate_exit_trend' (or legacy 'populate_sell_trend').")
            if 'populate_indicators' not in found_methods:
                errors.append("Missing required method: 'populate_indicators'.")

        # Check for INTERFACE_VERSION, as it's a strong indicator of a valid strategy
        if 'INTERFACE_VERSION' not in found_attributes:
            errors.append("Attribute 'INTERFACE_VERSION' is highly recommended for compatibility.")


        return {
            "parameters": parameters,
            "errors": errors,
            "valid": not bool(errors)
        }

    def convert_md_to_py(self, md_content: str) -> str:
        """
        Converts a Markdown string with a specific format into a Freqtrade strategy Python file.

        The format is as follows:
        # StrategyName
        ## parameter: value
        ## method_name
        ```python
        # code for method
        ```
        """
        lines = md_content.split('\n')

        class_name = "MyStrategy"
        params = []
        methods = {}
        current_method = None
        in_code_block = False

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if line.startswith('# '):
                class_name = line[2:].strip()
            elif line.startswith('## '):
                if ':' in line:
                    # It's a parameter
                    key, value = line[3:].split(':', 1)
                    key = key.strip()
                    value = value.strip()
                    # Attempt to convert to number, otherwise treat as string
                    try:
                        if '.' in value:
                            val = float(value)
                        else:
                            val = int(value)
                        params.append(f"    {key} = {val}")
                    except ValueError:
                        params.append(f"    {key} = '{value}'")
                else:
                    # It's a method definition
                    current_method = line[3:].strip()
                    methods[current_method] = []
            elif line.startswith('```python'):
                in_code_block = True
            elif line.startswith('```'):
                in_code_block = False
                current_method = None
            elif in_code_block and current_method:
                methods[current_method].append(line)

        # Build the Python code string
        py_code = [
            "from freqtrade.strategy import IStrategy",
            "from pandas import DataFrame",
            "import talib.abstract as ta",
            "import freqtrade.vendor.qtpylib.indicators as qtpylib",
            "\n",
            f"class {class_name}(IStrategy):"
        ]

        py_code.extend(params)
        py_code.append("\n")

        # Define method signatures
        method_signatures = {
            "populate_indicators": "def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:",
            "populate_buy_trend": "def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:",
            "populate_sell_trend": "def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:",
        }

        for method_name, method_lines in methods.items():
            signature = method_signatures.get(method_name, f"def {method_name}(self, dataframe: DataFrame, metadata: dict) -> DataFrame:")
            py_code.append(f"    {signature}")
            if not method_lines:
                py_code.append("        return dataframe")
            for line in method_lines:
                py_code.append(f"        {line}")
            py_code.append("\n")

        return "\n".join(py_code)
