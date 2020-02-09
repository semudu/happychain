from app.flask_app import App
from app.schedule import Schedule

if __name__ == "__main__":
    try:
        scheduled_jobs = Schedule()
        flask_app = App()
        scheduled_jobs.setDaemon(True)
        flask_app.setDaemon(True)

        scheduled_jobs.start()
        flask_app.start()

        scheduled_jobs.join()
        flask_app.join()

    except (KeyboardInterrupt, SystemExit):
        print("Threads finished.")
