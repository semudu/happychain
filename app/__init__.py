from flask import Flask

from app.route.api import api
from config import APP, FlaskConf
import flask_excel as excel

app = Flask(__name__)
excel.init_excel(app)

app.config.from_object(FlaskConf)
app.logger.setLevel(APP.LOG_LEVEL)
app.register_blueprint(api, url_prefix='/api')
