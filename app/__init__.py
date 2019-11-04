from .api import create_app


def run(config):
    app = create_app(config)
    app.run(host=config.HOST, port=config.PORT)
