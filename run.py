from app.flask_app import App
from app.schedule import Schedule


def start_app():
    scheduled_jobs = Schedule()
    flask_app = App()

    scheduled_jobs.start()
    flask_app.start()

    scheduled_jobs.join()
    flask_app.join()
