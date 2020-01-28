import threading

import app
from app.job import Job
from config import Config

if __name__ == '__main__':
    config = Config()
    jobs = Job(config)

    job_thread = threading.Thread(name="job_thread", target=jobs.send_periodically_messages, args=())
    job_thread.setDaemon(True)
    job_thread.start()

    app.run(config)
