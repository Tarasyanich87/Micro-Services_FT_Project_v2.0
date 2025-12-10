import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict

from .freqtrade_service import FreqtradeBacktestingService

logger = logging.getLogger(__name__)


@dataclass
class Task:
    """Simplified task model for local development"""

    task_id: str
    task_type: str
    status: str
    strategy_name: str
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class TaskService:
    """Simplified task service for local development"""

    def __init__(self):
        self.active_tasks: Dict[str, Task] = {}
        self.freqtrade_service = FreqtradeBacktestingService()
        self.max_concurrent_tasks = 3

    async def start_backtest(
        self,
        strategy_name: str,
        config_dict: dict,
        request_id: str,
        freqai_model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Start backtest task"""

        # Check limits
        if len(self.active_tasks) >= self.max_concurrent_tasks:
            return {"error": "too_many_tasks"}

        task_id = f"backtest_{request_id}_{datetime.now().timestamp()}"

        task = Task(
            task_id=task_id,
            task_type="backtest",
            status="pending",
            strategy_name=strategy_name,
            created_at=datetime.now(),
        )

        self.active_tasks[task_id] = task

        # Start in background
        asyncio.create_task(self._run_backtest(task, config_dict, freqai_model))

        return {
            "task_id": task_id,
            "status": "started",
            "message": f"Backtest for {strategy_name} started",
        }

    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get task status"""
        if task_id not in self.active_tasks:
            return {"error": "task_not_found"}

        task = self.active_tasks[task_id]
        return asdict(task)

    async def get_active_tasks(self) -> list:
        """Get all active tasks"""
        return [asdict(task) for task in self.active_tasks.values()]

    async def _run_backtest(
        self, task: Task, config_dict: dict, freqai_model: Optional[str] = None
    ):
        """Run backtest task"""
        try:
            task.status = "running"
            task.started_at = datetime.now()

            logger.info(f"Running backtest for {task.strategy_name}")

            # Run backtest
            result = await self.freqtrade_service.run_backtest(
                task.strategy_name, config_dict, freqai_model
            )

            task.status = "completed"
            task.result = result
            task.completed_at = datetime.now()

            logger.info(f"Backtest completed: {task.task_id}")

        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            task.completed_at = datetime.now()

            logger.error(f"Backtest failed: {task.task_id} - {e}")

        # Keep in memory for some time, then cleanup
        await asyncio.sleep(300)  # 5 minutes
        if task.task_id in self.active_tasks:
            del self.active_tasks[task.task_id]
