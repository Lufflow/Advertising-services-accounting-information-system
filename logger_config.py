import os
import logging
from logging.handlers import RotatingFileHandler


def setup_logger(app):
    os.makedirs('logs', exist_ok=True)

    handler = RotatingFileHandler(
        'logs/service.log',
        maxBytes=100000,
        backupCount=10
    )

    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    )

    handler.setFormatter(formatter)
    handler.setLevel(logging.INFO)
    app.logger.setLevel(logging.INFO)
    app.logger.addHandler(handler)
