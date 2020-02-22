from flask import Flask

from app.route.api import api
from config import APP, FlaskConf

app = Flask(__name__)

app.config.from_object(FlaskConf)
app.logger.setLevel(APP.LOG_LEVEL)
app.register_blueprint(api, url_prefix='/api')
