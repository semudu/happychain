from flask import Flask

from app.routes.api import api
from settings import Settings

app = Flask(__name__)

app.config.from_object(Settings)
app.register_blueprint(api, url_prefix='/api')

# if __name__ == "__main__":
#    app.run()
