from management_server.tasks.tasks import run_hyperopt_task

class HyperoptService:
    """
    A service for queuing Freqtrade hyperopt tasks using Celery.
    """

    def create_hyperopt_task(self, strategy_name: str, bot_config: dict, epochs: int, spaces: str, result_id: int):
        """
        Queues a hyperopt task in Celery.

        Returns:
            AsyncResult: An object that can be used to check the task's status.
        """
        task = run_hyperopt_task.delay(
            strategy_name=strategy_name,
            bot_config=bot_config,
            epochs=epochs,
            spaces=spaces,
            result_id=result_id
        )
        return task
