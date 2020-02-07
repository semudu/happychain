import threading

from flask import Flask

from app.routes.api import api
from settings import Settings


class App(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self, name="app-thread")
        return

    def run(self):
        try:
            app = Flask(__name__)
            app.config.from_object(Settings)
            app.register_blueprint(api, url_prefix='/api')
            app.run(host=Settings.HOST, port=Settings.PORT)
        finally:
            print("Flask app thread finished.")
