import threading

import app
from app.job import Job
# from config import Config
from settings import Settings


def start_app():
    # config = Config()
    config = Settings()
    jobs = Job(config)

    job_thread = threading.Thread(name="job_thread", target=jobs.send_periodically_messages, args=())
    job_thread.setDaemon(True)
    job_thread.start()

    app.run(config)
