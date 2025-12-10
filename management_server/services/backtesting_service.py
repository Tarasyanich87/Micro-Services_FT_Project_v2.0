import subprocess
import json
from pathlib import Path
from typing import Dict, Tuple
from management_server.tasks.tasks import run_backtest_task

class BacktestingService:
    """
    A service for managing Freqtrade backtesting processes.
    """

    def create_strategy_backtest_task(self, strategy_name: str, bot_config: Dict, result_id: int):
        """
        Queues a strategy backtesting task in Celery.
        """
        task = run_backtest_task.delay(
            strategy_name=strategy_name,
            bot_config=bot_config,
            result_id=result_id
        )
        return task

    def run_freqai_backtesting_process(self, model_name: str, model_path: str, bot_config: Dict) -> Tuple[bool, str]:
        """
        Executes the `freqtrade backtesting` command synchronously for a FreqAI model.
        NOTE: This remains synchronous for now as FreqAI backtesting is handled differently.
        """
        temp_config_path = Path(f"/tmp/backtest_config_{model_name}.json")
        try:
            with open(temp_config_path, "w") as f:
                json.dump(bot_config, f)

            strategy_name = bot_config.get("strategy")
            if not strategy_name:
                return False, "Strategy not defined in bot config."

            if not model_path or not Path(model_path).exists():
                return False, f"Model file not found at {model_path}."

            command = [
                "freqtrade",
                "backtesting",
                "--config", str(temp_config_path),
                "--strategy", strategy_name,
                "--freqaimodel", model_name,
                "--json"
            ]

            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = process.communicate()

            if process.returncode == 0:
                return True, stdout
            else:
                return False, stderr

        finally:
            if temp_config_path.exists():
                temp_config_path.unlink()
