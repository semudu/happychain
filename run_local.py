import threading

import app
from app.schedule import Schedule
from config import Config

# from settings import Settings


if __name__ == "__main__":
    config = Config()
    jobs = Schedule(config)
    jobs.start()

    app.run(config)

    jobs.join()
