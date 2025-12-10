import subprocess
import json
import os
from pathlib import Path
from sqlalchemy.future import select
from .celery_app import celery_app
from management_server.database.connection import SyncSessionLocal
from management_server.models.models import (
    StrategyBacktestResult,
    HyperoptResult,
    FreqAIModel,
)


def run_subprocess(command: list) -> tuple[bool, str]:
    """Helper to run a subprocess and return its output."""
    process = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    stdout, stderr = process.communicate()
    success = process.returncode == 0
    output = stdout if success else stderr
    return success, output


@celery_app.task(bind=True)
def run_backtest_task(self, strategy_name: str, bot_config: dict, result_id: int):
    """Celery task to run a backtesting process and update the DB."""
    temp_config_path = Path(f"/tmp/celery_backtest_{result_id}.json")
    try:
        with open(temp_config_path, "w") as f:
            json.dump(bot_config, f)

        command = [
            "freqtrade",
            "backtesting",
            "--config",
            str(temp_config_path),
            "--strategy",
            strategy_name,
        ]

        success, output = run_subprocess(command)

        # Store the raw output as results
        results_data = {"success": success, "output": output}

        # Update the database record with the result
        with SyncSessionLocal() as db:
            result = db.execute(
                select(StrategyBacktestResult).where(
                    StrategyBacktestResult.id == result_id
                )
            )
            backtest_result = result.scalar_one()
            backtest_result.status = "completed" if success else "failed"
            backtest_result.results = results_data
            db.commit()
        return {"status": "completed" if success else "failed"}
    finally:
        if temp_config_path.exists():
            temp_config_path.unlink()


@celery_app.task(bind=True)
def run_freqai_backtest_task(self, model_id: int, bot_config: dict):
    """Celery task to run a FreqAI model backtesting process and update the DB."""
    temp_config_path = Path(f"/tmp/celery_freqai_backtest_{model_id}.json")
    try:
        with SyncSessionLocal() as db:
            model = db.execute(
                select(FreqAIModel).where(FreqAIModel.id == model_id)
            ).scalar_one_or_none()
            if not model:
                return {"status": "failed", "error": "Model not found"}

            model.status = "running"
            db.commit()

            # The config needs the strategy, which should be part of the bot_config
            strategy_name = bot_config.get("strategy")
            if not strategy_name:
                raise ValueError(
                    "Strategy not defined in bot config for FreqAI backtest."
                )

            with open(temp_config_path, "w") as f:
                json.dump(bot_config, f)

            command = [
                "freqtrade",
                "backtesting",
                "--config",
                str(temp_config_path),
                "--strategy",
                strategy_name,
                "--freqaimodel",
                model.name,
                "--json",
            ]

            success, output = run_subprocess(command)

            # Re-fetch model in the same session to update it
            model = db.execute(
                select(FreqAIModel).where(FreqAIModel.id == model_id)
            ).scalar_one_or_none()
            if success:
                model.status = "completed"
                model.backtest_results = json.loads(output)
            else:
                model.status = "failed"
                model.backtest_results = {"error": output}
            db.commit()

        return {"status": "completed" if success else "failed"}
    finally:
        if temp_config_path.exists():
            temp_config_path.unlink()


@celery_app.task(bind=True, queue="training")
def run_freqai_training_task(self, model_name: str, bot_config: dict):
    """Celery task to run FreqAI model training via backtesting."""
    temp_config_path = Path(f"/tmp/celery_training_{model_name}.json")
    try:
        with open(temp_config_path, "w") as f:
            json.dump(bot_config, f)

        strategy_name = bot_config.get("strategy")
        if not strategy_name:
            return {"status": "error", "error": "Strategy not defined in bot config"}

        # FreqAI training happens during backtesting when FreqAI is enabled
        # Use a reasonable timerange for training data
        command = [
            "freqtrade",
            "backtesting",
            "--config",
            str(temp_config_path),
            "--strategy",
            strategy_name,
            "--timerange",
            "20240101-20241201",  # 1 year of recent data for training
            "--freqaimodel",
            model_name,
        ]

        success, output = run_subprocess(command)

        return {
            "status": "success" if success else "error",
            "output": output if success else None,
            "error": None if success else output,
        }
    finally:
        if temp_config_path.exists():
            temp_config_path.unlink()


@celery_app.task(bind=True)
def run_hyperopt_task(
    self, strategy_name: str, bot_config: dict, epochs: int, spaces: str, result_id: int
):
    """Celery task to run a hyperopt process and update the DB."""
    temp_config_path = Path(f"/tmp/celery_hyperopt_{result_id}.json")
    try:
        with open(temp_config_path, "w") as f:
            json.dump(bot_config, f)

        # Use available CPU cores for parallel execution, leaving one free.
        job_workers = max(1, os.cpu_count() - 1)

        command = [
            "freqtrade",
            "hyperopt",
            "--config",
            str(temp_config_path),
            "--strategy",
            strategy_name,
            "--epochs",
            str(epochs),
            "--spaces",
            *spaces.split(),
            "--job-workers",
            str(job_workers),
            "--non-interactive",
            "--json",
        ]

        success, output = run_subprocess(command)

        with SyncSessionLocal() as db:
            result = db.execute(
                select(HyperoptResult).where(HyperoptResult.id == result_id)
            ).scalar_one_or_none()
            if result:
                if success:
                    result.status = "completed"
                    result.results = {"results": json.loads(output)}
                else:
                    result.status = "failed"
                    result.results = {"error": output}
                db.commit()
        return {"status": "completed" if success else "failed"}
    finally:
        if temp_config_path.exists():
            temp_config_path.unlink()
