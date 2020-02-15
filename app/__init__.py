from flask import Flask

from app.routes.api import api
from settings import Settings

app = Flask(__name__)

if __name__ == "__main__":
    app.config.from_object(Settings)
    app.register_blueprint(api, url_prefix='/api')
    app.run(host=Settings.HOST, port=Settings.PORT)
