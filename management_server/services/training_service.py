import subprocess
import json
from pathlib import Path
from typing import Dict, Tuple

class TrainingService:
    """
    A service dedicated to running Freqtrade model training processes.
    This service is synchronous and designed to be run in a separate thread.
    It does not interact with the database directly.
    """

    def run_training_process(self, model_name: str, bot_config: Dict) -> Tuple[bool, str]:
        """
        Executes the `freqtrade train-model` command.

        Args:
            model_name: The identifier for the new FreqAI model.
            bot_config: The bot's configuration dictionary.

        Returns:
            A tuple containing a success flag and the process output.
        """
        temp_config_path = Path(f"/tmp/train_config_{model_name}.json")
        try:
            with open(temp_config_path, "w") as f:
                json.dump(bot_config, f)

            strategy_name = bot_config.get("strategy")
            if not strategy_name:
                return False, "Strategy not defined in bot config."

            command = [
                "freqtrade",
                "train-model",
                "--config", str(temp_config_path),
                "--strategy", strategy_name,
                "--identifier", model_name,
            ]

            print(f"Executing training command: {' '.join(command)}")

            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate()

            if process.returncode == 0:
                return True, stdout
            else:
                return False, stderr

        except Exception as e:
            return False, str(e)

        finally:
            if temp_config_path.exists():
                temp_config_path.unlink()
