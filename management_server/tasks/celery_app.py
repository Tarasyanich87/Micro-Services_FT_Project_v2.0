from celery import Celery
from management_server.core import config

celery_app = Celery(
    "tasks",
    broker=config.settings.CELERY_BROKER_URL,
    backend=config.settings.CELERY_RESULT_BACKEND,
    include=["management_server.tasks.tasks"]
)

celery_app.conf.update(
    task_track_started=True,
)

if __name__ == "__main__":
    celery_app.start()
