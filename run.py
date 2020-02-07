import app
from app.schedule import Schedule
from settings import Settings


def start_app():
    config = Settings()
    jobs = Schedule(config)
    jobs.start()

    app.run(config)

    jobs.join()
