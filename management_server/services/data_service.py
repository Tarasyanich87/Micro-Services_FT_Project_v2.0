import subprocess
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple

class DataService:
    """
    A service for managing Freqtrade historical data.
    This service is synchronous and designed to be run in a separate thread.
    """

    def run_download_data_process(self, exchanges: List[str], pairs: List[str], days: int, timeframe: str) -> Tuple[bool, str]:
        """
        Executes the `freqtrade download-data` command.
        """
        try:
            command = [
                "freqtrade",
                "download-data",
                "--exchange", *exchanges,
                "--pairs", *pairs,
                "--days", str(days),
                "-t", timeframe
            ]

            print(f"Executing download-data command: {' '.join(command)}")

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
                # Freqtrade often prints progress to stderr, so we return stdout on error as well
                return False, f"Stdout: {stdout}\nStderr: {stderr}"

        except Exception as e:
            return False, str(e)

    def list_available_data(self) -> List[Dict[str, Any]]:
        """
        Executes `freqtrade list-data --json` to get a list of available historical data.
        """
        try:
            command = [
                "freqtrade",
                "list-data",
                "--json"
            ]

            process = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True
            )

            # The output is a list of JSON objects, one per line.
            # We need to parse this into a proper JSON list.
            lines = process.stdout.strip().split('\n')
            json_data = [json.loads(line) for line in lines]
            return json_data

        except subprocess.CalledProcessError as e:
            print(f"Error listing data: {e.stderr}")
            return []
        except Exception as e:
            print(f"An exception occurred while listing data: {e}")
            return []
