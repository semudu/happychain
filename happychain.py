from flask import Flask

from app.routes.api import api
from settings import Settings

app = Flask(__name__)

app.config.from_object(Settings)
app.logger.setLevel(Settings.LOG_LEVEL)

app.register_blueprint(api, url_prefix='/api')
